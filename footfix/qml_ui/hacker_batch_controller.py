#!/usr/bin/env python3
"""
Phase 3 Hacker-style QML batch processing interface for FootFix.
Integrates with existing BatchProcessor to provide movie-style batch processing
with multiple terminals, queue visualization, and real-time monitoring.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtQml import qmlRegisterType, QQmlApplicationEngine
from PySide6.QtCore import QObject, QUrl, Signal, Slot, Property, QTimer

# Import the core batch processor
from ..core.batch_processor import BatchProcessor, BatchItem, BatchProgress, ProcessingStatus
from ..utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


class HackerBatchController(QObject):
    """
    Enhanced QML-Python bridge for the Phase 3 hacker batch interface.
    Manages batch processing queue, progress tracking, and multi-terminal logging.
    """
    
    # Signals for QML
    queueUpdated = Signal('QVariant')  # Queue data as list
    batchStarted = Signal()
    batchStopped = Signal()
    batchCompleted = Signal('QVariant')  # Results dict
    itemProgress = Signal('QVariant', float)  # Item, progress
    itemCompleted = Signal('QVariant', bool, str)  # Item, success, message
    statusUpdate = Signal(str)  # Status message
    debugMessage = Signal(str)  # Debug message
    
    def __init__(self):
        super().__init__()
        self.batch_processor = BatchProcessor()
        self.current_preset = "editorial_web"
        self.output_folder = Path.home() / "Downloads"
        self.is_processing = False
        
        # Register callbacks with batch processor
        self.batch_processor.register_progress_callback(self._on_batch_progress)
        self.batch_processor.register_item_complete_callback(self._on_item_complete)
        
        # Simulate processing updates
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self._simulate_progress)
        self.current_processing_item = None
        self.processing_progress = 0.0
        
    @Slot('QVariant')
    def addFiles(self, file_urls):
        """Add files to the batch queue from drag-drop or file dialog."""
        try:
            added_count = 0
            
            for url_variant in file_urls:
                file_path = url_variant.toString()
                
                # Handle file:// URLs
                if file_path.startswith("file://"):
                    file_path = file_path[7:]
                
                path = Path(file_path)
                
                # Check if it's a supported image format
                if path.is_file() and path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
                    # Create batch item
                    batch_item = BatchItem(source_path=path)
                    
                    # Add to queue
                    self.batch_processor.add_image(path)
                    added_count += 1
                    
                    self.debugMessage.emit(f"Added to queue: {path.name}")
                
                elif path.is_dir():
                    # Add all images from directory
                    folder_added = self.batch_processor.add_folder(path)
                    added_count += folder_added
            
            if added_count > 0:
                self.statusUpdate.emit(f"> Added {added_count} files to batch queue")
                self._emit_queue_update()
            else:
                self.statusUpdate.emit("> No valid image files found")
                
        except Exception as e:
            self.statusUpdate.emit(f"> Error adding files: {str(e)}")
            logger.error(f"Error adding files: {e}")
    
    @Slot()
    def showFileDialog(self):
        """Show file selection dialog for adding multiple files."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            None,
            "Select Images for Batch Processing",
            str(Path.home()),
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif);;All Files (*.*)"
        )
        
        if file_paths:
            # Convert to QUrl objects for addFiles
            from PySide6.QtCore import QUrl
            urls = [QUrl.fromLocalFile(path) for path in file_paths]
            self.addFiles(urls)
        else:
            self.statusUpdate.emit("> File selection cancelled")
    
    @Slot()
    def showFolderDialog(self):
        """Show folder selection dialog for adding all images from a folder."""
        folder_path = QFileDialog.getExistingDirectory(
            None,
            "Select Folder with Images",
            str(Path.home())
        )
        
        if folder_path:
            from PySide6.QtCore import QUrl
            self.addFiles([QUrl.fromLocalFile(folder_path)])
        else:
            self.statusUpdate.emit("> Folder selection cancelled")
    
    @Slot(int)
    def removeItem(self, index):
        """Remove an item from the batch queue."""
        try:
            if not self.is_processing and 0 <= index < len(self.batch_processor.queue):
                removed_item = self.batch_processor.queue.pop(index)
                self.statusUpdate.emit(f"> Removed from queue: {removed_item.source_path.name}")
                self._emit_queue_update()
        except Exception as e:
            self.statusUpdate.emit(f"> Error removing item: {str(e)}")
            logger.error(f"Error removing item: {e}")
    
    @Slot()
    def clearQueue(self):
        """Clear the entire batch queue."""
        if not self.is_processing:
            count = len(self.batch_processor.queue)
            self.batch_processor.queue.clear()
            self.statusUpdate.emit(f"> Cleared queue: {count} items removed")
            self._emit_queue_update()
    
    @Slot()
    def startBatch(self):
        """Start batch processing."""
        if self.is_processing:
            self.statusUpdate.emit("> Batch processing already active")
            return
        
        if not self.batch_processor.queue:
            self.statusUpdate.emit("> No items in queue")
            return
        
        try:
            self.is_processing = True
            self.batchStarted.emit()
            self.statusUpdate.emit(f"> Starting batch processing: {len(self.batch_processor.queue)} items")
            
            # Start processing in a separate thread (simplified simulation)
            self._start_processing_simulation()
            
        except Exception as e:
            self.is_processing = False
            self.statusUpdate.emit(f"> Error starting batch: {str(e)}")
            logger.error(f"Error starting batch: {e}")
    
    @Slot()
    def stopBatch(self):
        """Stop batch processing."""
        if self.is_processing:
            self.is_processing = False
            self.processing_timer.stop()
            self.batchStopped.emit()
            self.statusUpdate.emit("> Batch processing stopped by user")
    
    def _start_processing_simulation(self):
        """Start simulated batch processing (replace with real processing)."""
        self.current_item_index = 0
        self.processing_progress = 0.0
        self.completed_count = 0
        self.failed_count = 0
        
        # Start processing timer
        self.processing_timer.start(200)  # Update every 200ms
    
    def _simulate_progress(self):
        """Simulate processing progress."""
        if not self.is_processing or self.current_item_index >= len(self.batch_processor.queue):
            # Batch complete
            self._finish_batch()
            return
        
        current_item = self.batch_processor.queue[self.current_item_index]
        
        # Update item status to processing
        if current_item.status == ProcessingStatus.PENDING:
            current_item.status = ProcessingStatus.PROCESSING
            self.current_processing_item = current_item
            self.processing_progress = 0.0
            self._emit_queue_update()
        
        # Simulate progress
        self.processing_progress += 0.05  # 5% per tick
        
        # Emit progress
        self.itemProgress.emit(self._item_to_dict(current_item), self.processing_progress)
        
        if self.processing_progress >= 1.0:
            # Item complete - simulate success/failure
            import random
            success = random.random() > 0.1  # 90% success rate
            
            if success:
                current_item.status = ProcessingStatus.COMPLETED
                current_item.processing_time = 2.5  # Simulated processing time
                self.completed_count += 1
                self.itemCompleted.emit(self._item_to_dict(current_item), True, "Processing completed successfully")
            else:
                current_item.status = ProcessingStatus.FAILED
                current_item.error_message = "Simulated processing error"
                self.failed_count += 1
                self.itemCompleted.emit(self._item_to_dict(current_item), False, "Simulated processing error")
            
            # Move to next item
            self.current_item_index += 1
            self.processing_progress = 0.0
            self._emit_queue_update()
    
    def _finish_batch(self):
        """Finish batch processing."""
        self.is_processing = False
        self.processing_timer.stop()
        
        results = {
            "completed": self.completed_count,
            "failed": self.failed_count,
            "total": len(self.batch_processor.queue)
        }
        
        self.batchCompleted.emit(results)
        
    def _emit_queue_update(self):
        """Emit queue update signal with current queue data."""
        queue_data = []
        for item in self.batch_processor.queue:
            queue_data.append(self._item_to_dict(item))
        
        self.queueUpdated.emit(queue_data)
    
    def _item_to_dict(self, item: BatchItem) -> Dict[str, Any]:
        """Convert BatchItem to dictionary for QML."""
        return {
            "fileName": item.source_path.name,
            "filePath": str(item.source_path),
            "status": item.status.value,
            "fileSize": self._format_file_size(item.file_size),
            "processingTime": item.processing_time,
            "errorMessage": item.error_message,
            "progress": self.processing_progress if item == self.current_processing_item else 0.0
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size as human readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _on_batch_progress(self, progress: BatchProgress):
        """Handle batch progress callback."""
        self.debugMessage.emit(f"Batch progress: {progress.completed_items}/{progress.total_items}")
    
    def _on_item_complete(self, item: BatchItem):
        """Handle item completion callback."""
        self.debugMessage.emit(f"Item completed: {item.source_path.name} - {item.status.value}")


def main():
    """Run the Phase 3 hacker batch interface."""
    # Set up logging
    setup_logging(log_level=logging.INFO, log_to_file=True)
    logger = logging.getLogger(__name__)
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Set application metadata
        app.setApplicationName("FootFix Hacker Batch UI Phase 3")
        app.setOrganizationName("FootFix")
        app.setApplicationDisplayName("FootFix - Advanced Batch Processing Interface")
        
        # Create QML engine
        engine = QQmlApplicationEngine()
        
        # Register our controller with QML
        controller = HackerBatchController()
        engine.rootContext().setContextProperty("hackerBatchController", controller)
        
        # Load QML file
        qml_file = Path(__file__).parent / "HackerBatchMain.qml"
        engine.load(QUrl.fromLocalFile(str(qml_file)))
        
        if not engine.rootObjects():
            logger.error("Failed to load QML file")
            sys.exit(1)
        
        logger.info("Phase 3 hacker batch interface started successfully")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()