"""
Processing orchestration service for FootFix.
Coordinates batch processing execution, thread management, and result handling.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QThread

from .batch_processor import BatchProcessor, BatchProgress, BatchItem, ProcessingStatus
from .alt_text_generator import AltTextStatus
from .tag_manager import TagStatus
from ..utils.notifications import NotificationManager
from ..utils.preferences import PreferencesManager

logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """Configuration for processing orchestration."""
    preset_name: str
    output_folder: Path
    generate_alt_text: bool = False
    enable_tagging: bool = False
    enable_ai_tagging: bool = False
    filename_template: Optional[str] = None
    show_notifications: bool = True
    play_sound: bool = True


@dataclass 
class ProcessingResults:
    """Results from batch processing."""
    success: bool
    cancelled: bool = False
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    elapsed_time: float = 0.0
    alt_text_generated: int = 0
    alt_text_failed: int = 0
    tags_applied: int = 0
    tags_failed: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary."""
        return {
            'success': self.success,
            'cancelled': self.cancelled,
            'total_processed': self.total_processed,
            'successful': self.successful,
            'failed': self.failed,
            'elapsed_time': self.elapsed_time,
            'alt_text_generated': self.alt_text_generated,
            'alt_text_failed': self.alt_text_failed,
            'tags_applied': self.tags_applied,
            'tags_failed': self.tags_failed,
            'error_message': self.error_message
        }


class ProcessingThread(QThread):
    """Thread for batch processing images without blocking the UI."""
    
    # Signals
    progress_updated = Signal(object)  # BatchProgress
    item_completed = Signal(object)    # BatchItem
    batch_completed = Signal(dict)     # Results dict
    status_message = Signal(str)
    alt_text_progress = Signal(int, int, str)  # current, total, message
    
    def __init__(self, batch_processor: BatchProcessor, config: ProcessingConfig):
        super().__init__()
        self.batch_processor = batch_processor
        self.config = config
        self._is_cancelled = False
        
    def run(self):
        """Run the batch processing."""
        try:
            # Register callbacks
            self.batch_processor.register_progress_callback(self._on_progress)
            self.batch_processor.register_item_complete_callback(self._on_item_complete)
            
            # Start processing
            self.status_message.emit(f"Starting batch processing with {self.config.preset_name} preset...")
            
            # Use appropriate processing method based on features enabled
            if self.config.generate_alt_text or self.config.enable_tagging or self.config.enable_ai_tagging:
                # One or more features enabled - use unified features method
                results = self.batch_processor.process_batch_with_features(
                    self.config.preset_name, 
                    self.config.output_folder,
                    generate_alt_text=self.config.generate_alt_text,
                    enable_tagging=self.config.enable_tagging,
                    enable_ai_tagging=self.config.enable_ai_tagging,
                    filename_template=self.config.filename_template
                )
            else:
                # No features enabled - standard processing
                results = self.batch_processor.process_batch(
                    self.config.preset_name, 
                    self.config.output_folder, 
                    self.config.filename_template
                )
            
            # Emit completion
            self.batch_completed.emit(results)
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            self.batch_completed.emit({
                "success": False,
                "cancelled": False,
                "message": str(e),
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "elapsed_time": 0.0
            })
            
    def _on_progress(self, progress: BatchProgress):
        """Handle progress updates."""
        self.progress_updated.emit(progress)
        
    def _on_item_complete(self, item: BatchItem):
        """Handle item completion."""
        self.item_completed.emit(item)
        
    def cancel(self):
        """Cancel the batch processing."""
        self._is_cancelled = True
        self.batch_processor.cancel_processing()


class ProcessingOrchestrator(QObject):
    """
    Orchestrates batch processing operations.
    Manages processing threads, coordinates results, and handles notifications.
    """
    
    # Signals
    processing_started = Signal()
    processing_completed = Signal(ProcessingResults)
    progress_updated = Signal(BatchProgress)
    item_completed = Signal(BatchItem)
    status_message = Signal(str)
    
    def __init__(self, batch_processor: BatchProcessor):
        """
        Initialize the processing orchestrator.
        
        Args:
            batch_processor: The batch processor instance to use
        """
        super().__init__()
        self.batch_processor = batch_processor
        self.processing_thread: Optional[ProcessingThread] = None
        self.notification_manager = NotificationManager()
        self.prefs_manager = PreferencesManager.get_instance()
        self.is_processing = False
        self._current_config: Optional[ProcessingConfig] = None
        
    def start_processing(self, config: ProcessingConfig) -> bool:
        """
        Start batch processing with the given configuration.
        
        Args:
            config: Processing configuration
            
        Returns:
            True if processing started successfully, False otherwise
        """
        # Check preconditions
        if self.is_processing:
            logger.warning("Processing already in progress")
            return False
            
        if not self.batch_processor.queue:
            logger.warning("No items in queue to process")
            return False
            
        # Store configuration
        self._current_config = config
        
        # Start processing
        self.is_processing = True
        self.processing_started.emit()
        
        # Create and configure processing thread
        self.processing_thread = ProcessingThread(self.batch_processor, config)
        
        # Connect thread signals
        self.processing_thread.progress_updated.connect(self._on_progress_updated)
        self.processing_thread.item_completed.connect(self._on_item_completed)
        self.processing_thread.batch_completed.connect(self._on_batch_completed)
        self.processing_thread.status_message.connect(self._on_status_message)
        
        # Start the thread
        self.processing_thread.start()
        
        logger.info(f"Started processing {len(self.batch_processor.queue)} items with preset '{config.preset_name}'")
        return True
        
    def cancel_processing(self) -> bool:
        """
        Cancel the current processing operation.
        
        Returns:
            True if cancellation initiated, False if no processing to cancel
        """
        if not self.is_processing or not self.processing_thread:
            logger.warning("No active processing to cancel")
            return False
            
        if self.processing_thread.isRunning():
            logger.info("Cancelling batch processing...")
            self.processing_thread.cancel()
            return True
            
        return False
        
    def _on_progress_updated(self, progress: BatchProgress):
        """Handle progress updates from processing thread."""
        self.progress_updated.emit(progress)
        
    def _on_item_completed(self, item: BatchItem):
        """Handle item completion from processing thread."""
        self.item_completed.emit(item)
        
    def _on_status_message(self, message: str):
        """Handle status messages from processing thread."""
        self.status_message.emit(message)
        logger.info(message)
        
    def _on_batch_completed(self, results_dict: Dict[str, Any]):
        """Handle batch completion from processing thread."""
        self.is_processing = False
        
        # Convert results to ProcessingResults object
        results = ProcessingResults(
            success=results_dict.get('success', False),
            cancelled=results_dict.get('cancelled', False),
            total_processed=results_dict.get('total_processed', 0),
            successful=results_dict.get('successful', 0),
            failed=results_dict.get('failed', 0),
            elapsed_time=results_dict.get('elapsed_time', 0.0),
            alt_text_generated=results_dict.get('alt_text_generated', 0),
            alt_text_failed=results_dict.get('alt_text_failed', 0),
            tags_applied=results_dict.get('tags_applied', 0),
            tags_failed=results_dict.get('tags_failed', 0),
            error_message=results_dict.get('message')
        )
        
        # Show notifications if enabled
        if self._current_config and self._current_config.show_notifications:
            self._show_completion_notifications(results)
            
        # Emit completion signal
        self.processing_completed.emit(results)
        
        # Log completion
        if results.cancelled:
            logger.info("Batch processing cancelled")
        elif results.success:
            logger.info(f"Batch processing completed successfully: {results.successful}/{results.total_processed} items")
        else:
            logger.error(f"Batch processing failed: {results.error_message}")
            
    def _show_completion_notifications(self, results: ProcessingResults):
        """Show system notifications for processing completion."""
        if not self.prefs_manager.get('processing.completion_notification', True):
            return
            
        # Configure sound
        self.notification_manager.set_sound_enabled(
            self.prefs_manager.get('processing.completion_sound', True)
        )
        
        # Don't show notification for cancelled processing
        if results.cancelled:
            return
            
        queue_size = len(self.batch_processor.queue)
        
        if queue_size == 1:
            # Single image notification
            item_name = self.batch_processor.queue[0].source_path.name if self.batch_processor.queue else "image"
            self.notification_manager.show_single_completion(
                item_name,
                results.successful > 0
            )
        else:
            # Batch notification
            self.notification_manager.show_batch_completion(
                successful=results.successful,
                failed=results.failed,
                elapsed_time=results.elapsed_time
            )
            
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get current processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        if not self.batch_processor.queue:
            return {
                'total_items': 0,
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'has_alt_text': 0,
                'has_tags': 0
            }
            
        stats = {
            'total_items': len(self.batch_processor.queue),
            'pending': sum(1 for item in self.batch_processor.queue if item.status == ProcessingStatus.PENDING),
            'processing': sum(1 for item in self.batch_processor.queue if item.status == ProcessingStatus.PROCESSING),
            'completed': sum(1 for item in self.batch_processor.queue if item.status == ProcessingStatus.COMPLETED),
            'failed': sum(1 for item in self.batch_processor.queue if item.status == ProcessingStatus.FAILED),
            'has_alt_text': sum(1 for item in self.batch_processor.queue 
                               if item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text),
            'has_tags': sum(1 for item in self.batch_processor.queue 
                          if item.tag_status == TagStatus.COMPLETED and item.tags)
        }
        
        return stats
        
    @property
    def has_items_with_alt_text(self) -> bool:
        """Check if any items have generated alt text."""
        return any(
            item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text
            for item in self.batch_processor.queue
        )
        
    @property
    def has_items_with_tags(self) -> bool:
        """Check if any items have applied tags."""
        return any(
            item.tag_status == TagStatus.COMPLETED and item.tags
            for item in self.batch_processor.queue
        )