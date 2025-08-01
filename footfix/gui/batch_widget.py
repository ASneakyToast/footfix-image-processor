"""
Batch processing widget for FootFix GUI.
Provides queue management and batch processing controls.
"""

import logging
from pathlib import Path
from typing import Optional, List
from datetime import timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon

from ..core.batch_processor import BatchProcessor, BatchItem, BatchProgress, ProcessingStatus
from ..utils.notifications import NotificationManager
from ..utils.preferences import PreferencesManager

logger = logging.getLogger(__name__)


class BatchProcessingThread(QThread):
    """Thread for batch processing images without blocking the UI."""
    
    # Signals
    progress_updated = Signal(object)  # BatchProgress
    item_completed = Signal(object)    # BatchItem
    batch_completed = Signal(dict)     # Results dict
    status_message = Signal(str)
    
    def __init__(self, batch_processor: BatchProcessor, preset_name: str, output_folder: Path):
        super().__init__()
        self.batch_processor = batch_processor
        self.preset_name = preset_name
        self.output_folder = output_folder
        self._is_cancelled = False
        
    def run(self):
        """Run the batch processing."""
        try:
            # Register callbacks
            self.batch_processor.register_progress_callback(self._on_progress)
            self.batch_processor.register_item_complete_callback(self._on_item_complete)
            
            # Start processing
            self.status_message.emit(f"Starting batch processing with {self.preset_name} preset...")
            results = self.batch_processor.process_batch(self.preset_name, self.output_folder)
            
            # Emit completion
            self.batch_completed.emit(results)
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            self.batch_completed.emit({
                "success": False,
                "message": str(e),
                "total_processed": 0,
                "successful": 0,
                "failed": 0
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


class BatchProcessingWidget(QWidget):
    """Widget for managing batch image processing."""
    
    # Signals
    processing_started = Signal()
    processing_completed = Signal(dict)
    queue_changed = Signal(int)  # Number of items in queue
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.batch_processor = BatchProcessor()
        self.processing_thread: Optional[BatchProcessingThread] = None
        self.is_processing = False
        
        # Initialize notification manager and preferences
        self.notification_manager = NotificationManager()
        self.prefs_manager = PreferencesManager()
        
        # Apply memory optimization settings from preferences
        memory_limit = self.prefs_manager.get('advanced.memory_limit_mb', 2048)
        self.batch_processor.set_memory_limit(memory_limit)
        self.batch_processor.set_memory_optimization(True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_images_btn = QPushButton("Add Images")
        self.add_images_btn.clicked.connect(self.add_images)
        toolbar_layout.addWidget(self.add_images_btn)
        
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder)
        toolbar_layout.addWidget(self.add_folder_btn)
        
        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        toolbar_layout.addWidget(self.clear_queue_btn)
        
        toolbar_layout.addStretch()
        
        self.queue_label = QLabel("0 images in queue")
        toolbar_layout.addWidget(self.queue_label)
        
        layout.addLayout(toolbar_layout)
        
        # Image queue table
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(5)
        self.queue_table.setHorizontalHeaderLabels(["Filename", "Size", "Status", "Error", "Actions"])
        self.queue_table.horizontalHeader().setStretchLastSection(True)
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.queue_table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.queue_table)
        
        # Progress section
        progress_layout = QVBoxLayout()
        
        # Overall progress
        self.overall_progress_label = QLabel("Ready to process")
        progress_layout.addWidget(self.overall_progress_label)
        
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.overall_progress_bar)
        
        # Current item progress
        self.current_item_label = QLabel("")
        self.current_item_label.setVisible(False)
        progress_layout.addWidget(self.current_item_label)
        
        # Time estimation
        time_layout = QHBoxLayout()
        self.elapsed_label = QLabel("Elapsed: --:--")
        time_layout.addWidget(self.elapsed_label)
        
        time_layout.addStretch()
        
        self.remaining_label = QLabel("Remaining: --:--")
        time_layout.addWidget(self.remaining_label)
        
        progress_layout.addLayout(time_layout)
        
        layout.addLayout(progress_layout)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview Selected")
        self.preview_btn.clicked.connect(self.preview_selected)
        self.preview_btn.setEnabled(False)
        self.preview_btn.setMinimumHeight(40)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
            }
            QPushButton:enabled {
                background-color: #28a745;
                color: white;
            }
        """)
        control_layout.addWidget(self.preview_btn)
        
        self.process_btn = QPushButton("Start Processing")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        self.process_btn.setMinimumHeight(40)
        self.process_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background-color: #007AFF;
                color: white;
            }
        """)
        control_layout.addWidget(self.process_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setMinimumHeight(40)
        control_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(control_layout)
        
        # Timer for UI updates during processing
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_display)
        
    def add_images(self):
        """Open dialog to select multiple images."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            str(Path.home()),
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif)"
        )
        
        if files:
            added_count = 0
            for file_path in files:
                if self.batch_processor.add_image(Path(file_path)):
                    added_count += 1
                    
            self.refresh_queue_display()
            if added_count > 0:
                logger.info(f"Added {added_count} images to queue")
                
    def add_folder(self):
        """Open dialog to select a folder containing images."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder Containing Images",
            str(Path.home())
        )
        
        if folder:
            added_count = self.batch_processor.add_folder(Path(folder))
            self.refresh_queue_display()
            if added_count > 0:
                logger.info(f"Added {added_count} images from folder")
            else:
                QMessageBox.warning(
                    self,
                    "No Images Found",
                    "No compatible images found in the selected folder."
                )
                
    def clear_queue(self):
        """Clear all images from the queue."""
        if self.is_processing:
            QMessageBox.warning(
                self,
                "Processing Active",
                "Cannot clear queue while processing is active."
            )
            return
            
        if self.batch_processor.queue:
            reply = QMessageBox.question(
                self,
                "Clear Queue",
                f"Remove all {len(self.batch_processor.queue)} images from queue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.batch_processor.clear_queue()
                self.refresh_queue_display()
                logger.info("Queue cleared")
                
    def remove_item(self, index: int):
        """Remove an item from the queue."""
        if self.is_processing:
            QMessageBox.warning(
                self,
                "Processing Active",
                "Cannot modify queue while processing is active."
            )
            return
            
        if self.batch_processor.remove_image(index):
            self.refresh_queue_display()
            
    def refresh_queue_display(self):
        """Update the queue table display."""
        queue_info = self.batch_processor.get_queue_info()
        
        self.queue_table.setRowCount(len(queue_info))
        
        for row, item_info in enumerate(queue_info):
            # Filename
            self.queue_table.setItem(row, 0, QTableWidgetItem(item_info['filename']))
            
            # Size
            size_mb = item_info['size'] / (1024 * 1024)
            self.queue_table.setItem(row, 1, QTableWidgetItem(f"{size_mb:.1f} MB"))
            
            # Status
            status_item = QTableWidgetItem(item_info['status'])
            if item_info['status'] == 'completed':
                status_item.setForeground(Qt.green)
            elif item_info['status'] == 'failed':
                status_item.setForeground(Qt.red)
            elif item_info['status'] == 'processing':
                status_item.setForeground(Qt.blue)
            self.queue_table.setItem(row, 2, status_item)
            
            # Error
            error_text = item_info['error'] or ""
            self.queue_table.setItem(row, 3, QTableWidgetItem(error_text))
            
            # Remove button
            if not self.is_processing and item_info['status'] == 'pending':
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, idx=row: self.remove_item(idx))
                self.queue_table.setCellWidget(row, 4, remove_btn)
            else:
                self.queue_table.setCellWidget(row, 4, None)
                
        # Update queue count
        queue_count = len(queue_info)
        self.queue_label.setText(f"{queue_count} image{'s' if queue_count != 1 else ''} in queue")
        
        # Enable/disable process button
        self.process_btn.setEnabled(queue_count > 0 and not self.is_processing)
        
        # Update preview button based on selection
        selected_rows = self.queue_table.selectionModel().selectedRows()
        self.preview_btn.setEnabled(len(selected_rows) == 1 and not self.is_processing)
        
        # Emit signal
        self.queue_changed.emit(queue_count)
        
    def start_processing(self):
        """Start batch processing with current settings."""
        if not self.batch_processor.queue:
            return
            
        # Get preset and output folder from parent window
        main_window = self.window()  # Get the main window
        if not hasattr(main_window, 'preset_combo') or not hasattr(main_window, 'output_folder'):
            QMessageBox.critical(
                self,
                "Configuration Error",
                "Cannot access processing settings from main window."
            )
            return
            
        preset_name = main_window.preset_combo.currentData()
        output_folder = main_window.output_folder
        
        # Start processing
        self.is_processing = True
        self.processing_started.emit()
        
        # Update UI
        self.process_btn.setText("Processing...")
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.add_images_btn.setEnabled(False)
        self.add_folder_btn.setEnabled(False)
        self.clear_queue_btn.setEnabled(False)
        
        # Reset progress
        self.overall_progress_bar.setValue(0)
        self.current_item_label.setVisible(True)
        
        # Start timer
        self.update_timer.start(100)  # Update every 100ms
        
        # Create and start processing thread
        self.processing_thread = BatchProcessingThread(
            self.batch_processor,
            preset_name,
            output_folder
        )
        
        self.processing_thread.progress_updated.connect(self.on_progress_updated)
        self.processing_thread.item_completed.connect(self.on_item_completed)
        self.processing_thread.batch_completed.connect(self.on_batch_completed)
        self.processing_thread.status_message.connect(lambda msg: logger.info(msg))
        
        self.processing_thread.start()
        
    def cancel_processing(self):
        """Cancel the current batch processing."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.cancel()
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setText("Cancelling...")
            
    def on_progress_updated(self, progress: BatchProgress):
        """Handle progress updates from processing thread."""
        # Update progress bar
        if progress.total_items > 0:
            percentage = ((progress.completed_items + progress.failed_items) / progress.total_items) * 100
            self.overall_progress_bar.setValue(int(percentage))
            
        # Update labels
        self.overall_progress_label.setText(
            f"Processing {progress.current_item_index + 1} of {progress.total_items} - "
            f"{progress.completed_items} completed, {progress.failed_items} failed"
        )
        
        if progress.current_item_name:
            self.current_item_label.setText(f"Current: {progress.current_item_name}")
            
    def on_item_completed(self, item: BatchItem):
        """Handle item completion updates."""
        self.refresh_queue_display()
        
    def on_batch_completed(self, results: dict):
        """Handle batch processing completion."""
        self.is_processing = False
        self.update_timer.stop()
        
        # Update UI
        self.process_btn.setText("Start Processing")
        self.process_btn.setEnabled(len(self.batch_processor.queue) > 0)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel")
        self.add_images_btn.setEnabled(True)
        self.add_folder_btn.setEnabled(True)
        self.clear_queue_btn.setEnabled(True)
        self.current_item_label.setVisible(False)
        
        # Show results
        if results.get('cancelled'):
            message = f"Processing cancelled.\n\n"
        else:
            message = f"Batch processing completed.\n\n"
            
        message += (
            f"Total processed: {results.get('total_processed', 0)}\n"
            f"Successful: {results.get('successful', 0)}\n"
            f"Failed: {results.get('failed', 0)}\n"
            f"Time elapsed: {self._format_time(results.get('elapsed_time', 0))}"
        )
        
        # Show system notification if enabled
        if self.prefs_manager.get('processing.completion_notification', True):
            # Update notification manager settings
            self.notification_manager.set_sound_enabled(
                self.prefs_manager.get('processing.completion_sound', True)
            )
            
            # Show notification
            if not results.get('cancelled'):
                self.notification_manager.show_batch_completion(
                    successful=results.get('successful', 0),
                    failed=results.get('failed', 0),
                    elapsed_time=results.get('elapsed_time', 0)
                )
        
        if results.get('success'):
            QMessageBox.information(self, "Processing Complete", message)
        else:
            QMessageBox.warning(self, "Processing Complete with Errors", message)
            
        # Emit completion signal
        self.processing_completed.emit(results)
        
    def update_time_display(self):
        """Update time display during processing."""
        if not self.is_processing or not hasattr(self.batch_processor, 'progress'):
            return
            
        progress = self.batch_processor.progress
        
        # Update elapsed time
        self.elapsed_label.setText(f"Elapsed: {self._format_time(progress.elapsed_time)}")
        
        # Update remaining time
        if progress.estimated_time_remaining > 0:
            self.remaining_label.setText(f"Remaining: {self._format_time(progress.estimated_time_remaining)}")
        else:
            self.remaining_label.setText("Remaining: Calculating...")
            
    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to human-readable string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        else:
            td = timedelta(seconds=int(seconds))
            return str(td).split('.')[0]  # Remove microseconds
            
    def add_images_to_queue(self, file_paths: List[Path]):
        """Add multiple images to the queue."""
        added_count = 0
        for path in file_paths:
            if self.batch_processor.add_image(path):
                added_count += 1
                
        self.refresh_queue_display()
        return added_count
        
    def on_selection_changed(self):
        """Handle table selection changes."""
        # Enable/disable preview button based on selection
        selected_rows = self.queue_table.selectionModel().selectedRows()
        self.preview_btn.setEnabled(len(selected_rows) == 1 and not self.is_processing)
        
    def preview_selected(self):
        """Preview the selected image with current preset."""
        selected_rows = self.queue_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        # Get the selected item
        row = selected_rows[0].row()
        if row >= len(self.batch_processor.queue):
            return
            
        batch_item = self.batch_processor.queue[row]
        
        # Get parent window (main window)
        parent = self.window()
        if not hasattr(parent, 'show_preview'):
            logger.error("Parent window doesn't have show_preview method")
            return
            
        # Load the image and show preview
        if parent.processor.load_image(batch_item.source_path):
            parent.current_image_path = batch_item.source_path
            parent.show_preview()
        else:
            QMessageBox.warning(
                self,
                "Preview Error",
                f"Could not load image for preview: {batch_item.source_path.name}"
            )