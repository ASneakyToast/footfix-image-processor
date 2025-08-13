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
    QProgressBar, QLabel, QFileDialog, QMessageBox,
    QTabWidget, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon

from ..core.batch_processor import BatchProcessor, BatchItem, BatchProgress, ProcessingStatus
from ..core.alt_text_generator import AltTextStatus
from ..utils.notifications import NotificationManager
from ..utils.preferences import PreferencesManager
from ..utils.alt_text_exporter import AltTextExporter, ExportFormat, ExportOptions
from .alt_text_widget import AltTextWidget

logger = logging.getLogger(__name__)


class BatchProcessingThread(QThread):
    """Thread for batch processing images without blocking the UI."""
    
    # Signals
    progress_updated = Signal(object)  # BatchProgress
    item_completed = Signal(object)    # BatchItem
    batch_completed = Signal(dict)     # Results dict
    status_message = Signal(str)
    alt_text_progress = Signal(int, int, str)  # current, total, message
    
    def __init__(self, batch_processor: BatchProcessor, preset_name: str, output_folder: Path, generate_alt_text: bool = False):
        super().__init__()
        self.batch_processor = batch_processor
        self.preset_name = preset_name
        self.output_folder = output_folder
        self.generate_alt_text = generate_alt_text
        self._is_cancelled = False
        
    def run(self):
        """Run the batch processing."""
        try:
            # Register callbacks
            self.batch_processor.register_progress_callback(self._on_progress)
            self.batch_processor.register_item_complete_callback(self._on_item_complete)
            
            # Start processing
            self.status_message.emit(f"Starting batch processing with {self.preset_name} preset...")
            
            # Use appropriate processing method based on alt text setting
            if self.generate_alt_text:
                results = self.batch_processor.process_batch_with_alt_text(self.preset_name, self.output_folder)
            else:
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
        
        # Tab widget for Image Processing and Alt Text
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Image Processing Tab
        processing_tab = QWidget()
        processing_layout = QVBoxLayout(processing_tab)
        self.tab_widget.addTab(processing_tab, "Image Processing")
        
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
        
        # Quick export button (only visible when alt text results are available)
        self.quick_export_btn = QPushButton("Export Alt Text")
        self.quick_export_btn.setToolTip("Quick export alt text results to CSV")
        self.quick_export_btn.clicked.connect(self.quick_export_alt_text)
        self.quick_export_btn.setVisible(False)
        toolbar_layout.addWidget(self.quick_export_btn)
        
        toolbar_layout.addStretch()
        
        self.queue_label = QLabel("0 images in queue")
        toolbar_layout.addWidget(self.queue_label)
        
        processing_layout.addLayout(toolbar_layout)
        
        # Image queue table
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(5)
        self.queue_table.setHorizontalHeaderLabels(["Filename", "Size", "Status", "Error", "Actions"])
        self.queue_table.horizontalHeader().setStretchLastSection(True)
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.queue_table.itemSelectionChanged.connect(self.on_selection_changed)
        processing_layout.addWidget(self.queue_table)
        
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
        
        processing_layout.addLayout(progress_layout)
        
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
        
        processing_layout.addLayout(control_layout)
        
        # Timer for UI updates during processing
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_display)
        
        # Alt Text Tab
        self.alt_text_widget = AltTextWidget()
        self.alt_text_widget.alt_text_updated.connect(self.on_alt_text_updated)
        self.alt_text_widget.regenerate_requested.connect(self.on_regenerate_requested)
        self.tab_widget.addTab(self.alt_text_widget, "Alt Text")
        
        # Alt Text Generation Options (at bottom of main layout)
        alt_text_options_layout = QHBoxLayout()
        
        self.enable_alt_text_cb = QCheckBox("Generate Alt Text")
        self.enable_alt_text_cb.setToolTip(
            "Enable automatic alt text generation using AI after image processing"
        )
        self.enable_alt_text_cb.toggled.connect(self.on_alt_text_toggled)
        alt_text_options_layout.addWidget(self.enable_alt_text_cb)
        
        # Check if API key is configured
        self.refresh_alt_text_availability()
        
        # Cost estimation label
        self.cost_estimate_label = QLabel("")
        self.cost_estimate_label.setStyleSheet("color: #666; margin-left: 10px;")
        alt_text_options_layout.addWidget(self.cost_estimate_label)
        
        alt_text_options_layout.addStretch()
        
        self.alt_text_status_label = QLabel("")
        alt_text_options_layout.addWidget(self.alt_text_status_label)
        
        layout.addLayout(alt_text_options_layout)
        
    def refresh_alt_text_availability(self):
        """Refresh alt text checkbox availability based on API key configuration."""
        logger.info("Refreshing alt text checkbox availability")
        
        # Create a fresh PreferencesManager instance to ensure we get the latest saved values
        # This is important because the preferences dialog might have its own instance
        fresh_prefs = PreferencesManager()
        
        api_key = fresh_prefs.get('alt_text.api_key')
        logger.info(f"API key check: {'[REDACTED]' if api_key else '[EMPTY]'} (type: {type(api_key)})")
        
        if api_key and api_key.strip():
            logger.info("API key found - enabling alt text checkbox")
            self.enable_alt_text_cb.setEnabled(True)
            self.enable_alt_text_cb.setToolTip(
                "Enable automatic alt text generation using AI after image processing"
            )
            # Check the checkbox if it was previously selected
            enabled_by_default = fresh_prefs.get('alt_text.enabled', False)
            if enabled_by_default:
                self.enable_alt_text_cb.setChecked(True)
        else:
            logger.info("No API key found - disabling alt text checkbox")
            self.enable_alt_text_cb.setEnabled(False)
            self.enable_alt_text_cb.setChecked(False)  # Uncheck if disabled
            self.enable_alt_text_cb.setToolTip(
                "Configure Anthropic API key in Preferences → Alt Text to enable alt text generation"
            )
            
        # Update our instance's preferences manager too
        self.prefs_manager = fresh_prefs
        
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
        
        # Update cost estimate
        self.update_cost_estimate()
        
        # Show/hide export button based on alt text availability
        has_alt_text = any(
            item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text
            for item in self.batch_processor.queue
        )
        self.quick_export_btn.setVisible(has_alt_text)
        
    def update_cost_estimate(self):
        """Update the cost estimate for alt text generation."""
        if not self.enable_alt_text_cb.isChecked():
            self.cost_estimate_label.setText("")
            return
            
        queue_count = len(self.batch_processor.queue)
        if queue_count == 0:
            self.cost_estimate_label.setText("")
            return
            
        # Get cost estimate from alt text generator
        if self.batch_processor.alt_text_generator:
            estimates = self.batch_processor.alt_text_generator.estimate_batch_cost(queue_count)
            total_cost = estimates['total']
            self.cost_estimate_label.setText(f"Est. cost: ${total_cost:.2f}")
        else:
            # Fallback estimate if generator not initialized
            cost_per_image = 0.006
            total_cost = queue_count * cost_per_image
            self.cost_estimate_label.setText(f"Est. cost: ${total_cost:.2f}")
        
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
            output_folder,
            generate_alt_text=self.enable_alt_text_cb.isChecked()
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
            
        # Update labels based on current phase
        if progress.current_item_name and "Alt text:" in progress.current_item_name:
            # Alt text generation phase
            self.overall_progress_label.setText(
                f"Generating alt text - {progress.completed_items} of {progress.total_items} completed"
            )
        else:
            # Image processing phase
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
        
        # Update alt text widget with processed items
        if self.enable_alt_text_cb.isChecked():
            self.alt_text_widget.set_batch_items(self.batch_processor.queue)
            
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
        
        # Add alt text results if applicable
        if 'alt_text_generated' in results:
            message += f"\n\nAlt text generated: {results.get('alt_text_generated', 0)}"
            if results.get('alt_text_failed', 0) > 0:
                message += f"\nAlt text failed: {results.get('alt_text_failed', 0)}"
        
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
            
    def on_alt_text_toggled(self, checked: bool):
        """Handle alt text generation toggle."""
        if checked:
            # Check API key again
            api_key = self.prefs_manager.get('alt_text.api_key')
            if not api_key:
                self.enable_alt_text_cb.setChecked(False)
                QMessageBox.warning(
                    self,
                    "API Key Required",
                    "Please configure your Anthropic API key in preferences to enable alt text generation."
                )
                return
                
            # Configure batch processor
            self.batch_processor.set_alt_text_generation(True, api_key)
            context = self.prefs_manager.get('alt_text.default_context', 'editorial image')
            self.batch_processor.set_alt_text_context(context)
            
            self.alt_text_status_label.setText("Alt text generation enabled")
            self.alt_text_status_label.setStyleSheet("color: green;")
        else:
            self.batch_processor.set_alt_text_generation(False)
            self.alt_text_status_label.setText("Alt text generation disabled")
            self.alt_text_status_label.setStyleSheet("color: #666;")
            
        # Update cost estimate
        self.update_cost_estimate()
            
    def on_alt_text_updated(self, updates: dict):
        """Handle alt text updates from the widget."""
        # Update batch items with new alt text
        for filename, alt_text in updates.items():
            for item in self.batch_processor.queue:
                if item.source_path.name == filename:
                    item.alt_text = alt_text
                    break
                    
        logger.info(f"Updated alt text for {len(updates)} items")
        
    def on_regenerate_requested(self, filenames: list):
        """Handle alt text regeneration requests."""
        if not self.batch_processor.alt_text_generator:
            QMessageBox.warning(
                self,
                "Alt Text Not Configured",
                "Please enable alt text generation first."
            )
            return
            
        # Mark items for regeneration
        items_to_regenerate = []
        for filename in filenames:
            for item in self.batch_processor.queue:
                if item.source_path.name == filename:
                    item.alt_text_status = AltTextStatus.PENDING
                    items_to_regenerate.append(item)
                    break
                    
        if items_to_regenerate:
            # Start regeneration in a separate thread
            # This would need to be implemented similar to batch processing
            logger.info(f"Marked {len(items_to_regenerate)} items for alt text regeneration")
            
    def quick_export_alt_text(self):
        """Quick export alt text results to CSV."""
        # Check if we have any completed alt text items
        completed_items = [
            item for item in self.batch_processor.queue
            if item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text
        ]
        
        if not completed_items:
            QMessageBox.information(
                self,
                "No Data to Export",
                "No completed alt text results to export."
            )
            return
            
        # Generate default filename
        exporter = AltTextExporter()
        default_filename = exporter.generate_filename(ExportFormat.CSV)
        
        # Get save location
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Alt Text Results",
            str(Path.home() / "Downloads" / default_filename),
            "CSV Files (*.csv)"
        )
        
        if not output_path:
            return
            
        output_path = Path(output_path)
        
        # Export all completed items
        success, message = exporter.export_csv(
            self.batch_processor.queue,
            output_path,
            ExportOptions.COMPLETED_ONLY
        )
        
        if success:
            QMessageBox.information(
                self,
                "Export Complete",
                f"Alt text results exported to:\n{output_path.name}"
            )
            
            # Open in finder
            import subprocess
            subprocess.run(["open", "-R", str(output_path)])
        else:
            QMessageBox.critical(
                self,
                "Export Failed",
                message
            )