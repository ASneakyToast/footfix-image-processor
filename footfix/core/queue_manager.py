"""
Queue management service for FootFix.
Handles image queue operations, file validation, and queue state management.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from PySide6.QtCore import QObject, Signal

from .batch_processor import BatchProcessor, BatchItem, ProcessingStatus
from .alt_text_generator import AltTextStatus
from .tag_manager import TagStatus

logger = logging.getLogger(__name__)


class QueueManager(QObject):
    """
    Manages the image processing queue.
    Handles adding/removing items, validation, and queue state changes.
    """
    
    # Signals
    queue_changed = Signal(int)  # Number of items in queue
    items_added = Signal(int)    # Number of items added
    items_removed = Signal(int)  # Number of items removed
    queue_cleared = Signal()
    validation_error = Signal(str)  # Error message
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    
    def __init__(self, batch_processor: BatchProcessor):
        """
        Initialize the queue manager.
        
        Args:
            batch_processor: The batch processor instance to manage
        """
        super().__init__()
        self.batch_processor = batch_processor
        self._processing_lock = False
        
    def add_images(self, file_paths: List[Path]) -> int:
        """
        Add multiple images to the queue.
        
        Args:
            file_paths: List of image file paths to add
            
        Returns:
            Number of images successfully added
        """
        if self._processing_lock:
            logger.warning("Cannot modify queue while processing is active")
            self.validation_error.emit("Cannot modify queue while processing is active.")
            return 0
            
        added_count = 0
        invalid_files = []
        duplicate_files = []
        
        for path in file_paths:
            # Validate file
            validation_result = self._validate_file(path)
            if not validation_result['valid']:
                invalid_files.append((path.name, validation_result['error']))
                continue
                
            # Check for duplicates
            if self._is_duplicate(path):
                duplicate_files.append(path.name)
                continue
                
            # Add to queue
            if self.batch_processor.add_image(path):
                added_count += 1
                logger.debug(f"Added image to queue: {path}")
            else:
                invalid_files.append((path.name, "Failed to add to queue"))
                
        # Report any issues
        if invalid_files:
            error_msg = "Invalid files:\n" + "\n".join(f"• {name}: {error}" for name, error in invalid_files)
            self.validation_error.emit(error_msg)
            
        if duplicate_files:
            logger.info(f"Skipped {len(duplicate_files)} duplicate files")
            
        # Emit signals
        if added_count > 0:
            self.items_added.emit(added_count)
            self.queue_changed.emit(len(self.batch_processor.queue))
            logger.info(f"Added {added_count} images to queue")
            
        return added_count
        
    def add_folder(self, folder_path: Path, recursive: bool = False) -> int:
        """
        Add all images from a folder to the queue.
        
        Args:
            folder_path: Path to folder containing images
            recursive: Whether to search subdirectories
            
        Returns:
            Number of images successfully added
        """
        if self._processing_lock:
            logger.warning("Cannot modify queue while processing is active")
            self.validation_error.emit("Cannot modify queue while processing is active.")
            return 0
            
        # Discover image files
        image_files = self._discover_images(folder_path, recursive)
        
        if not image_files:
            logger.info(f"No compatible images found in {folder_path}")
            self.validation_error.emit(f"No compatible images found in the selected folder.")
            return 0
            
        # Add discovered images
        return self.add_images(image_files)
        
    def remove_item(self, index: int) -> bool:
        """
        Remove an item from the queue by index.
        
        Args:
            index: Index of item to remove
            
        Returns:
            True if item was removed successfully
        """
        if self._processing_lock:
            logger.warning("Cannot modify queue while processing is active")
            self.validation_error.emit("Cannot modify queue while processing is active.")
            return False
            
        if self.batch_processor.remove_image(index):
            self.items_removed.emit(1)
            self.queue_changed.emit(len(self.batch_processor.queue))
            logger.debug(f"Removed item at index {index}")
            return True
            
        return False
        
    def remove_items(self, indices: List[int]) -> int:
        """
        Remove multiple items from the queue.
        
        Args:
            indices: List of indices to remove (should be sorted in descending order)
            
        Returns:
            Number of items removed
        """
        if self._processing_lock:
            logger.warning("Cannot modify queue while processing is active")
            self.validation_error.emit("Cannot modify queue while processing is active.")
            return 0
            
        # Sort indices in descending order to avoid index shifting issues
        indices = sorted(indices, reverse=True)
        
        removed_count = 0
        for index in indices:
            if 0 <= index < len(self.batch_processor.queue):
                if self.batch_processor.remove_image(index):
                    removed_count += 1
                    
        if removed_count > 0:
            self.items_removed.emit(removed_count)
            self.queue_changed.emit(len(self.batch_processor.queue))
            logger.info(f"Removed {removed_count} items from queue")
            
        return removed_count
        
    def clear_queue(self) -> bool:
        """
        Clear all items from the queue.
        
        Returns:
            True if queue was cleared successfully
        """
        if self._processing_lock:
            logger.warning("Cannot clear queue while processing is active")
            self.validation_error.emit("Cannot clear queue while processing is active.")
            return False
            
        previous_size = len(self.batch_processor.queue)
        self.batch_processor.clear_queue()
        
        self.queue_cleared.emit()
        self.queue_changed.emit(0)
        logger.info(f"Cleared queue ({previous_size} items removed)")
        
        return True
        
    def set_processing_lock(self, locked: bool):
        """
        Set the processing lock state.
        
        Args:
            locked: Whether to lock the queue (prevent modifications)
        """
        self._processing_lock = locked
        logger.debug(f"Queue processing lock set to: {locked}")
        
    def get_queue_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all items in the queue.
        
        Returns:
            List of dictionaries with queue item information
        """
        return self.batch_processor.get_queue_info()
        
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current queue.
        
        Returns:
            Dictionary with queue statistics
        """
        if not self.batch_processor.queue:
            return {
                'total_items': 0,
                'total_size_mb': 0.0,
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'has_alt_text': 0,
                'has_tags': 0,
                'average_size_mb': 0.0
            }
            
        total_size = sum(item.file_size for item in self.batch_processor.queue)
        
        stats = {
            'total_items': len(self.batch_processor.queue),
            'total_size_mb': total_size / (1024 * 1024),
            'pending': sum(1 for item in self.batch_processor.queue 
                          if item.status == ProcessingStatus.PENDING),
            'processing': sum(1 for item in self.batch_processor.queue 
                            if item.status == ProcessingStatus.PROCESSING),
            'completed': sum(1 for item in self.batch_processor.queue 
                           if item.status == ProcessingStatus.COMPLETED),
            'failed': sum(1 for item in self.batch_processor.queue 
                        if item.status == ProcessingStatus.FAILED),
            'has_alt_text': sum(1 for item in self.batch_processor.queue 
                              if item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text),
            'has_tags': sum(1 for item in self.batch_processor.queue 
                          if item.tag_status == TagStatus.COMPLETED and item.tags),
            'average_size_mb': (total_size / (1024 * 1024)) / len(self.batch_processor.queue)
        }
        
        return stats
        
    def reorder_items(self, from_index: int, to_index: int) -> bool:
        """
        Reorder an item in the queue.
        
        Args:
            from_index: Current index of the item
            to_index: Target index for the item
            
        Returns:
            True if reordering was successful
        """
        if self._processing_lock:
            logger.warning("Cannot reorder queue while processing is active")
            return False
            
        if not (0 <= from_index < len(self.batch_processor.queue)):
            return False
            
        if not (0 <= to_index < len(self.batch_processor.queue)):
            return False
            
        if from_index == to_index:
            return True
            
        # Reorder the item
        item = self.batch_processor.queue.pop(from_index)
        self.batch_processor.queue.insert(to_index, item)
        
        self.queue_changed.emit(len(self.batch_processor.queue))
        logger.debug(f"Reordered item from index {from_index} to {to_index}")
        
        return True
        
    def _validate_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate a file for adding to the queue.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Dictionary with validation result
        """
        result = {'valid': False, 'error': None}
        
        # Check if file exists
        if not file_path.exists():
            result['error'] = "File does not exist"
            return result
            
        # Check if it's a file (not directory)
        if not file_path.is_file():
            result['error'] = "Not a file"
            return result
            
        # Check file extension
        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            result['error'] = f"Unsupported format ({file_path.suffix})"
            return result
            
        # Check file size (optional - could add max size limit)
        file_size = file_path.stat().st_size
        if file_size == 0:
            result['error'] = "File is empty"
            return result
            
        # Max file size limit (100MB)
        max_size = 100 * 1024 * 1024
        if file_size > max_size:
            result['error'] = f"File too large ({file_size / (1024*1024):.1f}MB > 100MB)"
            return result
            
        result['valid'] = True
        return result
        
    def _is_duplicate(self, file_path: Path) -> bool:
        """
        Check if a file is already in the queue.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is already in queue
        """
        for item in self.batch_processor.queue:
            if item.source_path == file_path:
                return True
        return False
        
    def _discover_images(self, folder_path: Path, recursive: bool = False) -> List[Path]:
        """
        Discover image files in a folder.
        
        Args:
            folder_path: Path to folder to search
            recursive: Whether to search subdirectories
            
        Returns:
            List of discovered image file paths
        """
        image_files = []
        
        try:
            if recursive:
                # Recursive search
                for ext in self.SUPPORTED_FORMATS:
                    pattern = f"**/*{ext}"
                    image_files.extend(folder_path.glob(pattern))
                    # Also search for uppercase extensions
                    pattern_upper = f"**/*{ext.upper()}"
                    image_files.extend(folder_path.glob(pattern_upper))
            else:
                # Non-recursive search
                for ext in self.SUPPORTED_FORMATS:
                    pattern = f"*{ext}"
                    image_files.extend(folder_path.glob(pattern))
                    # Also search for uppercase extensions
                    pattern_upper = f"*{ext.upper()}"
                    image_files.extend(folder_path.glob(pattern_upper))
                    
            # Remove duplicates and sort
            image_files = sorted(list(set(image_files)))
            
            logger.info(f"Discovered {len(image_files)} image files in {folder_path}")
            
        except Exception as e:
            logger.error(f"Error discovering images in {folder_path}: {e}")
            
        return image_files
        
    @property
    def queue_size(self) -> int:
        """Get the current queue size."""
        return len(self.batch_processor.queue)
        
    @property
    def has_items(self) -> bool:
        """Check if queue has any items."""
        return len(self.batch_processor.queue) > 0
        
    @property
    def is_locked(self) -> bool:
        """Check if queue is locked (processing active)."""
        return self._processing_lock