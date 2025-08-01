"""
Batch processing functionality for FootFix.
Manages queuing and processing of multiple images with progress tracking.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading
import gc
import os
import asyncio

from .processor import ImageProcessor
from ..presets.profiles import PresetProfile, get_preset
from .alt_text_generator import AltTextStatus, AltTextGenerator

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Status of image processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchItem:
    """Represents a single item in the batch processing queue."""
    source_path: Path
    output_path: Optional[Path] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    processing_time: float = 0.0
    file_size: int = 0
    # Alt text fields
    alt_text: Optional[str] = None
    alt_text_status: AltTextStatus = AltTextStatus.PENDING
    alt_text_error: Optional[str] = None
    alt_text_generation_time: float = 0.0
    
    def __post_init__(self):
        """Initialize file size."""
        if self.source_path.exists():
            self.file_size = self.source_path.stat().st_size


@dataclass
class BatchProgress:
    """Tracks progress of batch processing."""
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    current_item_index: int = -1
    current_item_name: str = ""
    elapsed_time: float = 0.0
    estimated_time_remaining: float = 0.0
    average_processing_time: float = 0.0
    is_cancelled: bool = False


class BatchProcessor:
    """
    Manages batch processing of multiple images.
    Supports queuing, progress tracking, and error handling.
    """
    
    def __init__(self, max_workers: int = 1):
        """
        Initialize the batch processor.
        
        Args:
            max_workers: Maximum number of concurrent processing threads
        """
        self.queue: List[BatchItem] = []
        self.progress = BatchProgress()
        self.max_workers = max_workers
        self._cancel_flag = threading.Event()
        self._processing_lock = threading.Lock()
        self._progress_callbacks: List[Callable[[BatchProgress], None]] = []
        self._item_complete_callbacks: List[Callable[[BatchItem], None]] = []
        
        # Memory management settings
        self.memory_limit_mb = 2048  # Default 2GB limit
        self.enable_memory_optimization = True
        self.images_per_gc = 5  # Run garbage collection every N images
        
        # Alt text generation settings
        self.alt_text_generator: Optional[AltTextGenerator] = None
        self.enable_alt_text = False
        self.alt_text_context = "editorial image"  # Default context for alt text generation
        
    def add_image(self, image_path: Path) -> bool:
        """
        Add an image to the processing queue.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            bool: True if image was added, False if invalid
        """
        if not image_path.exists():
            logger.error(f"File does not exist: {image_path}")
            return False
            
        if image_path.suffix.lower() not in ImageProcessor.SUPPORTED_FORMATS:
            logger.error(f"Unsupported format: {image_path.suffix}")
            return False
            
        # Check for duplicates
        for item in self.queue:
            if item.source_path == image_path:
                logger.warning(f"Image already in queue: {image_path}")
                return False
                
        self.queue.append(BatchItem(source_path=image_path))
        self.progress.total_items = len(self.queue)
        logger.info(f"Added to queue: {image_path.name}")
        return True
        
    def add_folder(self, folder_path: Path, recursive: bool = True) -> int:
        """
        Add all compatible images from a folder to the queue.
        
        Args:
            folder_path: Path to the folder
            recursive: Whether to search subdirectories
            
        Returns:
            int: Number of images added
        """
        if not folder_path.is_dir():
            logger.error(f"Not a directory: {folder_path}")
            return 0
            
        added_count = 0
        pattern = "**/*" if recursive else "*"
        
        for file_path in folder_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in ImageProcessor.SUPPORTED_FORMATS:
                if self.add_image(file_path):
                    added_count += 1
                    
        logger.info(f"Added {added_count} images from {folder_path}")
        return added_count
        
    def remove_image(self, index: int) -> bool:
        """
        Remove an image from the queue by index.
        
        Args:
            index: Index of the image to remove
            
        Returns:
            bool: True if removed, False if invalid index
        """
        if 0 <= index < len(self.queue):
            removed = self.queue.pop(index)
            self.progress.total_items = len(self.queue)
            logger.info(f"Removed from queue: {removed.source_path.name}")
            return True
        return False
        
    def clear_queue(self):
        """Clear all items from the queue."""
        self.queue.clear()
        self.progress = BatchProgress()
        logger.info("Queue cleared")
        
    def set_output_paths(self, output_folder: Path, preset: PresetProfile):
        """
        Set output paths for all items in the queue based on preset.
        
        Args:
            output_folder: Destination folder for processed images
            preset: Preset profile to use for filename generation
        """
        output_folder.mkdir(parents=True, exist_ok=True)
        
        for item in self.queue:
            filename = preset.get_suggested_filename(item.source_path)
            item.output_path = output_folder / filename
            
    def register_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """Register a callback for progress updates."""
        self._progress_callbacks.append(callback)
        
    def register_item_complete_callback(self, callback: Callable[[BatchItem], None]):
        """Register a callback for when an item completes processing."""
        self._item_complete_callbacks.append(callback)
        
    def _notify_progress(self):
        """Notify all registered progress callbacks."""
        for callback in self._progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
                
    def _notify_item_complete(self, item: BatchItem):
        """Notify all registered item complete callbacks."""
        for callback in self._item_complete_callbacks:
            try:
                callback(item)
            except Exception as e:
                logger.error(f"Error in item complete callback: {e}")
                
    def _check_memory_usage(self):
        """Check and manage memory usage during processing."""
        try:
            # Get current process memory usage
            import resource
            memory_usage_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            
            # On macOS, ru_maxrss is in bytes, on Linux it's in KB
            if os.name == 'posix' and os.uname().sysname == 'Darwin':
                memory_usage_mb = memory_usage_mb / 1024 / 1024
            else:
                memory_usage_mb = memory_usage_mb / 1024
                
            logger.debug(f"Current memory usage: {memory_usage_mb:.1f} MB")
            
            # If approaching limit, force garbage collection
            if memory_usage_mb > self.memory_limit_mb * 0.8:
                logger.warning(f"Memory usage high ({memory_usage_mb:.1f} MB), running garbage collection")
                gc.collect()
                
        except Exception as e:
            logger.debug(f"Could not check memory usage: {e}")
            
    def set_memory_limit(self, limit_mb: int):
        """Set the memory limit for batch processing."""
        self.memory_limit_mb = limit_mb
        logger.info(f"Memory limit set to {limit_mb} MB")
        
    def set_memory_optimization(self, enabled: bool):
        """Enable or disable memory optimization."""
        self.enable_memory_optimization = enabled
        logger.info(f"Memory optimization {'enabled' if enabled else 'disabled'}")
        
    def set_alt_text_generation(self, enabled: bool, api_key: Optional[str] = None):
        """
        Enable or disable alt text generation.
        
        Args:
            enabled: Whether to enable alt text generation
            api_key: Anthropic API key (if not provided, will use from preferences)
        """
        self.enable_alt_text = enabled
        if enabled and not self.alt_text_generator:
            self.alt_text_generator = AltTextGenerator(api_key)
        elif enabled and api_key:
            self.alt_text_generator.set_api_key(api_key)
        logger.info(f"Alt text generation {'enabled' if enabled else 'disabled'}")
        
    def set_alt_text_context(self, context: str):
        """Set the context for alt text generation."""
        self.alt_text_context = context
        logger.info(f"Alt text context set to: {context}")
                
    def process_batch(self, preset_name: str, output_folder: Path) -> Dict[str, Any]:
        """
        Process all images in the queue with the specified preset.
        
        Args:
            preset_name: Name of the preset to apply
            output_folder: Destination folder for processed images
            
        Returns:
            Dict containing processing results and statistics
        """
        if not self.queue:
            logger.warning("No images in queue")
            return {"success": False, "message": "No images to process"}
            
        preset = get_preset(preset_name)
        if not preset:
            logger.error(f"Invalid preset: {preset_name}")
            return {"success": False, "message": f"Invalid preset: {preset_name}"}
            
        # Set output paths
        self.set_output_paths(output_folder, preset)
        
        # Reset progress
        self.progress = BatchProgress(total_items=len(self.queue))
        self._cancel_flag.clear()
        
        # Track timing
        start_time = time.time()
        processing_times = []
        
        # Process each image
        for index, item in enumerate(self.queue):
            if self._cancel_flag.is_set():
                item.status = ProcessingStatus.SKIPPED
                continue
                
            # Update progress
            self.progress.current_item_index = index
            self.progress.current_item_name = item.source_path.name
            self._notify_progress()
            
            # Process the image
            item_start_time = time.time()
            item.status = ProcessingStatus.PROCESSING
            
            try:
                processor = ImageProcessor()
                
                # Check memory before loading
                if self.enable_memory_optimization:
                    self._check_memory_usage()
                
                # Load image
                if not processor.load_image(item.source_path):
                    raise Exception("Failed to load image")
                    
                # Apply preset
                if not preset.process(processor):
                    raise Exception("Failed to apply preset")
                    
                # Save image
                output_config = preset.get_output_config()
                if not processor.save_image(item.output_path, output_config):
                    raise Exception("Failed to save image")
                    
                item.status = ProcessingStatus.COMPLETED
                self.progress.completed_items += 1
                logger.info(f"Processed: {item.source_path.name}")
                
            except Exception as e:
                item.status = ProcessingStatus.FAILED
                item.error_message = str(e)
                self.progress.failed_items += 1
                logger.error(f"Failed to process {item.source_path.name}: {e}")
                
            # Update timing
            item.processing_time = time.time() - item_start_time
            processing_times.append(item.processing_time)
            
            # Calculate average and estimate remaining time
            self.progress.average_processing_time = sum(processing_times) / len(processing_times)
            remaining_items = len(self.queue) - index - 1
            self.progress.estimated_time_remaining = remaining_items * self.progress.average_processing_time
            self.progress.elapsed_time = time.time() - start_time
            
            # Notify callbacks
            self._notify_item_complete(item)
            self._notify_progress()
            
            # Periodic garbage collection for memory optimization
            if self.enable_memory_optimization and (index + 1) % self.images_per_gc == 0:
                gc.collect()
                logger.debug(f"Garbage collection performed after {index + 1} images")
            
        # Final progress update
        self.progress.elapsed_time = time.time() - start_time
        self.progress.is_cancelled = self._cancel_flag.is_set()
        self._notify_progress()
        
        # Generate results
        results = {
            "success": self.progress.failed_items == 0,
            "total_processed": self.progress.completed_items + self.progress.failed_items,
            "successful": self.progress.completed_items,
            "failed": self.progress.failed_items,
            "skipped": sum(1 for item in self.queue if item.status == ProcessingStatus.SKIPPED),
            "elapsed_time": self.progress.elapsed_time,
            "average_time_per_image": self.progress.average_processing_time,
            "cancelled": self.progress.is_cancelled
        }
        
        logger.info(f"Batch processing complete: {results}")
        return results
        
    def process_batch_with_alt_text(self, preset_name: str, output_folder: Path) -> Dict[str, Any]:
        """
        Process all images in the queue with the specified preset and optional alt text generation.
        
        Args:
            preset_name: Name of the preset to apply
            output_folder: Destination folder for processed images
            
        Returns:
            Dict containing processing results and statistics
        """
        # First, process images normally
        results = self.process_batch(preset_name, output_folder)
        
        # Then, if alt text is enabled, generate descriptions
        if self.enable_alt_text and self.alt_text_generator:
            logger.info("Starting alt text generation phase")
            
            # Run alt text generation in async context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                alt_text_results = loop.run_until_complete(
                    self._generate_alt_text_batch()
                )
                
                # Update results with alt text statistics
                results['alt_text_generated'] = sum(
                    1 for item in self.queue 
                    if item.alt_text_status == AltTextStatus.COMPLETED
                )
                results['alt_text_failed'] = sum(
                    1 for item in self.queue 
                    if item.alt_text_status == AltTextStatus.ERROR
                )
                
            except Exception as e:
                logger.error(f"Alt text generation failed: {e}")
                results['alt_text_error'] = str(e)
                
            finally:
                loop.close()
                
        return results
        
    async def _generate_alt_text_batch(self):
        """Generate alt text for all processed images in the queue."""
        async with self.alt_text_generator:
            tasks = []
            
            for index, item in enumerate(self.queue):
                # Only generate alt text for successfully processed images
                if item.status == ProcessingStatus.COMPLETED and item.output_path:
                    # Update progress
                    self.progress.current_item_name = f"Alt text: {item.source_path.name}"
                    self._notify_progress()
                    
                    # Create async task
                    task = self._generate_alt_text_for_item(item)
                    tasks.append(task)
                    
            # Wait for all tasks to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
    async def _generate_alt_text_for_item(self, item: BatchItem):
        """Generate alt text for a single item."""
        try:
            start_time = time.time()
            result = await self.alt_text_generator.generate_alt_text(
                item.output_path,  # Use processed image for better quality
                context=self.alt_text_context
            )
            
            # Update item with results
            item.alt_text = result.alt_text
            item.alt_text_status = result.status
            item.alt_text_error = result.error_message
            item.alt_text_generation_time = time.time() - start_time
            
            # Notify callbacks
            self._notify_item_complete(item)
            
        except Exception as e:
            logger.error(f"Alt text generation failed for {item.source_path.name}: {e}")
            item.alt_text_status = AltTextStatus.ERROR
            item.alt_text_error = str(e)
        
    def cancel_processing(self):
        """Cancel the current batch processing operation."""
        self._cancel_flag.set()
        logger.info("Batch processing cancelled")
        
    def get_queue_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all items in the queue.
        
        Returns:
            List of dicts containing item information
        """
        return [{
            "index": i,
            "filename": item.source_path.name,
            "path": str(item.source_path),
            "size": item.file_size,
            "status": item.status.value,
            "error": item.error_message,
            "alt_text": item.alt_text,
            "alt_text_status": item.alt_text_status.value,
            "alt_text_error": item.alt_text_error
        } for i, item in enumerate(self.queue)]