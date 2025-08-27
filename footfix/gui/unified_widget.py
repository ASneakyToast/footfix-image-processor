"""
Unified processing widget for FootFix GUI.
Combines single and batch processing into one intelligent interface.
"""

import logging
from pathlib import Path
from typing import Optional, List
from datetime import timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QLabel, QFileDialog, QMessageBox,
    QGroupBox, QComboBox, QLineEdit, QCheckBox,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QFont

from ..core.batch_processor import BatchProcessor, BatchItem, BatchProgress, ProcessingStatus
from ..core.alt_text_generator import AltTextStatus
from ..core.tag_manager import TagStatus, TagManager
from ..core.processor import ImageProcessor
from ..presets.profiles import PRESET_REGISTRY, get_preset, PresetConfig
from ..utils.notifications import NotificationManager
from ..utils.preferences import PreferencesManager
from ..utils.filename_template import FilenameTemplate
from ..utils.alt_text_exporter import AltTextExporter, ExportFormat, ExportOptions
from ..utils.api_validator import ApiKeyValidator
from ..utils.tag_csv_exporter import TagCsvExporter, TagExportOptions
from ..utils.widget_configurator import WidgetConfigurator
from .batch_widget import BatchProcessingThread
from .alt_text_widget import AltTextWidget
from .tag_widget import TagWidget
from .components.queue_widget import QueueManagementWidget

logger = logging.getLogger(__name__)


class UnifiedProcessingWidget(QWidget):
    """Unified widget that handles both single and batch image processing."""
    
    # Signals
    processing_started = Signal()
    processing_completed = Signal(dict)
    queue_changed = Signal(int)  # Number of items in queue
    image_loaded = Signal(str)   # For single image compatibility
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.batch_processor = BatchProcessor()
        self.processing_thread: Optional[BatchProcessingThread] = None
        self.is_processing = False
        
        # Initialize managers
        self.notification_manager = NotificationManager()
        self.prefs_manager = PreferencesManager.get_instance()
        self.filename_template = FilenameTemplate()
        self.tag_manager = TagManager()
        self.api_validator = ApiKeyValidator(self.prefs_manager)
        self.widget_configurator = WidgetConfigurator(self.prefs_manager)
        
        # Configure business logic components
        self.widget_configurator.configure_batch_processor(self.batch_processor, self.tag_manager)
        
        # Load configuration settings
        self.config = self.widget_configurator.configure_widget_components(
            self, self.batch_processor, self.tag_manager
        )
        
        # Store specific settings for easy access
        self.output_settings = self.config['output']
        self.output_folder = self.output_settings['output_folder']
        
        # Connect to preferences changes for real-time updates
        self.prefs_manager.preferences_changed.connect(self.on_preferences_changed)
        
        self.setup_ui()
        
        # Timer for UI updates during processing
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_display)
        
    def setup_ui(self):
        """Set up the unified user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Queue Management Widget
        self.queue_widget = QueueManagementWidget()
        self.setup_queue_connections()
        main_layout.addWidget(self.queue_widget)
        
        # Processing Controls - always visible
        self.setup_processing_controls(main_layout)
        
        # Action Buttons - always visible  
        self.setup_action_buttons(main_layout)
        
        # Progress Area - shown during processing
        self.setup_progress_area(main_layout)
        
        # Alt Text Integration
        self.setup_alt_text_integration(main_layout)
        
        # Tag Integration
        self.setup_tag_integration(main_layout)
        
        # Initialize UI state for empty queue
        self.update_queue_display()
        
    def setup_queue_connections(self):
        """Connect queue widget signals to handlers."""
        self.queue_widget.add_images_requested.connect(self.add_images)
        self.queue_widget.add_folder_requested.connect(self.add_folder)
        self.queue_widget.clear_queue_requested.connect(self.clear_queue)
        self.queue_widget.remove_item_requested.connect(self.remove_item)
        self.queue_widget.selection_changed.connect(self.on_queue_selection_changed)
        self.queue_widget.files_dropped.connect(self.on_files_dropped)
        
    def setup_processing_controls(self, main_layout):
        """Set up the processing controls section."""
        controls_group = QGroupBox("Processing Options")
        controls_layout = QVBoxLayout(controls_group)
        
        # Preset selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Editorial Web (Max 2560×1440, 0.5-1MB)", "editorial_web")
        self.preset_combo.addItem("Email (Max 600px width, <100KB)", "email")
        self.preset_combo.addItem("Instagram Story (1080×1920)", "instagram_story")
        self.preset_combo.addItem("Instagram Feed Portrait (1080×1350)", "instagram_feed_portrait")
        
        # Add tooltips for each preset
        self.preset_combo.setItemData(0, 
            "Optimized for web articles and galleries.\n"
            "Maximum dimensions: 2560×1440 pixels\n"
            "Target file size: 0.5-1MB\n"
            "Perfect for editorial content and blog posts.",
            Qt.ToolTipRole
        )
        self.preset_combo.setItemData(1,
            "Small file size for email attachments.\n"
            "Maximum width: 600 pixels\n"
            "Target file size: <100KB\n"
            "Ensures images load quickly in email clients.",
            Qt.ToolTipRole
        )
        self.preset_combo.setItemData(2,
            "Instagram Stories format.\n"
            "Exact dimensions: 1080×1920 pixels (9:16)\n"
            "Images will be cropped to fit if needed.\n"
            "Optimized for mobile viewing.",
            Qt.ToolTipRole
        )
        self.preset_combo.setItemData(3,
            "Instagram Feed portrait format.\n"
            "Exact dimensions: 1080×1350 pixels (4:5)\n"
            "Images will be cropped to fit if needed.\n"
            "Ideal for Instagram posts.",
            Qt.ToolTipRole
        )
        
        preset_layout.addWidget(self.preset_combo, 1)
        
        # Advanced settings button
        self.advanced_button = QPushButton("Advanced...")
        self.advanced_button.clicked.connect(self.show_advanced_settings)
        preset_layout.addWidget(self.advanced_button)
        
        controls_layout.addLayout(preset_layout)
        
        # Output folder selection
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        
        self.output_folder_edit = QLineEdit(str(self.output_folder))
        self.output_folder_edit.setReadOnly(True)
        output_layout.addWidget(self.output_folder_edit, 1)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(browse_button)
        
        # Output settings button
        output_settings_button = QPushButton("Settings...")
        output_settings_button.clicked.connect(self.show_output_settings)
        output_layout.addWidget(output_settings_button)
        
        controls_layout.addLayout(output_layout)
        
        main_layout.addWidget(controls_group)
        
    def setup_action_buttons(self, main_layout):
        """Set up the action buttons that adapt based on queue size."""
        button_layout = QHBoxLayout()
        
        # Preview button
        self.preview_button = QPushButton("Preview Selected")
        self.preview_button.clicked.connect(self.show_preview)
        self.preview_button.setEnabled(False)
        self.preview_button.setMinimumHeight(40)
        self.preview_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
            }
            QPushButton:enabled {
                background-color: #28a745;
                color: white;
            }
        """)
        button_layout.addWidget(self.preview_button)
        
        # Main process button - text adapts to queue size
        self.process_button = QPushButton("Add Images to Start")
        self.process_button.clicked.connect(self.start_processing)
        self.process_button.setEnabled(False)
        self.process_button.setMinimumHeight(40)
        self.process_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background-color: #007AFF;
                color: white;
            }
        """)
        button_layout.addWidget(self.process_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setMinimumHeight(40)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
    def setup_progress_area(self, main_layout):
        """Set up the progress display area."""
        self.progress_group = QGroupBox("Processing Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
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
        
        # Initially hidden
        self.progress_group.setVisible(False)
        main_layout.addWidget(self.progress_group)
        
    def setup_alt_text_integration(self, main_layout):
        """Set up alt text generation integration."""
        # Alt text options
        alt_text_layout = QHBoxLayout()
        
        self.enable_alt_text_cb = QCheckBox("Generate Alt Text")
        self.enable_alt_text_cb.setToolTip(
            "Enable automatic alt text generation using AI after image processing"
        )
        self.enable_alt_text_cb.toggled.connect(self.on_alt_text_toggled)
        alt_text_layout.addWidget(self.enable_alt_text_cb)
        
        # Quick export button (only visible when alt text results are available)
        self.quick_export_btn = QPushButton("Export Alt Text")
        self.quick_export_btn.setToolTip("Quick export alt text results to CSV")
        self.quick_export_btn.clicked.connect(self.quick_export_alt_text)
        self.quick_export_btn.setVisible(False)
        alt_text_layout.addWidget(self.quick_export_btn)
        
        alt_text_layout.addStretch()
        
        self.alt_text_status_label = QLabel("")
        alt_text_layout.addWidget(self.alt_text_status_label)
        
        main_layout.addLayout(alt_text_layout)
        
        # Check if API key is configured
        self.refresh_alt_text_availability()
        
        # Alt text widget for managing generated text
        self.alt_text_widget = AltTextWidget()
        self.alt_text_widget.alt_text_updated.connect(self.on_alt_text_updated)
        self.alt_text_widget.regenerate_requested.connect(self.on_regenerate_requested)
        self.alt_text_widget.setVisible(False)  # Hidden until we have alt text results
        main_layout.addWidget(self.alt_text_widget)
        
    def refresh_alt_text_availability(self):
        """Refresh alt text checkbox availability based on API key configuration."""
        logger.info("Refreshing alt text checkbox availability")
        
        if self.api_validator.is_alt_text_available():
            logger.info("API key found - enabling alt text checkbox")
            self.enable_alt_text_cb.setEnabled(True)
            self.enable_alt_text_cb.setToolTip(
                "Enable automatic alt text generation using AI after image processing"
            )
            # Check the checkbox if it was previously selected
            enabled_by_default = self.prefs_manager.get('alt_text.enabled', False)
            if enabled_by_default:
                self.enable_alt_text_cb.setChecked(True)
        else:
            logger.info("No API key found - disabling alt text checkbox")
            self.enable_alt_text_cb.setEnabled(False)
            self.enable_alt_text_cb.setChecked(False)
            self.enable_alt_text_cb.setToolTip(
                self.api_validator.get_alt_text_error_message()
            )
        
        # Also refresh AI tag availability since they can share the same API key
        if hasattr(self, 'enable_ai_tags_cb'):
            self.refresh_ai_tag_availability()
    
    def setup_tag_integration(self, main_layout):
        """Set up tag assignment integration."""
        # Tag options
        tag_layout = QHBoxLayout()
        
        self.enable_tags_cb = QCheckBox("Enable Tagging")
        self.enable_tags_cb.setToolTip(
            "Enable tag assignment to images during processing"
        )
        self.enable_tags_cb.toggled.connect(self.on_tags_toggled)
        tag_layout.addWidget(self.enable_tags_cb)
        
        # AI tagging toggle
        self.enable_ai_tags_cb = QCheckBox("AI Tag Generation")
        self.enable_ai_tags_cb.setToolTip(
            "Enable automatic AI-powered tag generation based on image content"
        )
        self.enable_ai_tags_cb.toggled.connect(self.on_ai_tags_toggled)
        tag_layout.addWidget(self.enable_ai_tags_cb)
        
        # Quick tag export button (only visible when tags are available)
        self.quick_tag_export_btn = QPushButton("Export Tags")
        self.quick_tag_export_btn.setToolTip("Quick export tag data to CSV")
        self.quick_tag_export_btn.clicked.connect(self.quick_export_tags)
        self.quick_tag_export_btn.setVisible(False)
        tag_layout.addWidget(self.quick_tag_export_btn)
        
        tag_layout.addStretch()
        
        self.tag_status_label = QLabel("")
        tag_layout.addWidget(self.tag_status_label)
        
        main_layout.addLayout(tag_layout)
        
        # Check tag preferences
        self.refresh_tag_availability()
        self.refresh_ai_tag_availability()
        
        # Tag widget for managing tags (hidden - handled by main window tab)
        self.tag_widget = TagWidget()
        self.tag_widget.tag_updated.connect(self.on_tags_updated)
        self.tag_widget.tag_assignment_requested.connect(self.on_tag_assignment_requested)
        self.tag_widget.setVisible(False)  # Hidden - managed by dedicated tab
        main_layout.addWidget(self.tag_widget)
    
    def refresh_tag_availability(self):
        """Refresh tag checkbox availability based on preferences."""
        logger.info("Refreshing tag checkbox availability")
        
        # Tags are always available (no API key required)
        tags_enabled = self.prefs_manager.get('tags.enabled', True)
        
        self.enable_tags_cb.setEnabled(True)
        self.enable_tags_cb.setChecked(tags_enabled)
        self.enable_tags_cb.setToolTip(
            "Enable tag assignment to images during processing"
        )
        
        self._update_tag_status_display()
            
    def refresh_ai_tag_availability(self):
        """Refresh AI tag checkbox availability based on API key configuration."""
        logger.info("Refreshing AI tag checkbox availability")
        
        if self.api_validator.is_ai_tags_available():
            logger.info("API key found - enabling AI tag checkbox")
            self.enable_ai_tags_cb.setEnabled(True)
            self.enable_ai_tags_cb.setToolTip(
                "Enable automatic AI-powered tag generation based on image content"
            )
            # Check the checkbox if it was previously selected
            ai_enabled_by_default = self.prefs_manager.get('tags.ai_generation_enabled', False)
            if ai_enabled_by_default:
                self.enable_ai_tags_cb.setChecked(True)
        else:
            logger.info("No API key found - disabling AI tag checkbox")
            self.enable_ai_tags_cb.setEnabled(False)
            self.enable_ai_tags_cb.setChecked(False)
            self.enable_ai_tags_cb.setToolTip(
                self.api_validator.get_ai_tags_error_message()
            )
        
        self._update_tag_status_display()
    
    def _update_tag_status_display(self):
        """Update the tag status display based on current settings."""
        tags_enabled = self.enable_tags_cb.isChecked()
        ai_tags_enabled = self.enable_ai_tags_cb.isChecked() and self.enable_ai_tags_cb.isEnabled()
        
        if tags_enabled and ai_tags_enabled:
            self.tag_status_label.setText("Tagging + AI enabled")
            self.tag_status_label.setStyleSheet("color: green; font-weight: bold;")
        elif tags_enabled:
            self.tag_status_label.setText("Tagging enabled")
            self.tag_status_label.setStyleSheet("color: green;")
        elif ai_tags_enabled:
            self.tag_status_label.setText("AI tagging only")
            self.tag_status_label.setStyleSheet("color: orange;")
        else:
            self.tag_status_label.setText("Tagging disabled")
            self.tag_status_label.setStyleSheet("color: #666;")
            
    def load_preferences(self):
        """Load preferences using the configurator."""
        self.output_settings = self.widget_configurator.load_output_settings()
        self.output_folder = self.output_settings['output_folder']
        
    def on_preferences_changed(self, key: str):
        """Handle preferences changes using the configurator."""
        updated_config = self.widget_configurator.handle_preference_change(key, self)
        
        # Update local configuration
        for category, config in updated_config.items():
            self.config[category] = config
        
        # Apply UI updates based on changes
        if 'output' in updated_config:
            self.output_settings = updated_config['output']
            self.output_folder = self.output_settings['output_folder']
            # Update the UI to reflect the changes
            if hasattr(self, 'output_folder_edit'):
                self.output_folder_edit.setText(str(self.output_folder))
            logger.info(f"Updated output settings from preferences: {key}")
        
        # Refresh availability for alt text and tags if their settings changed
        if 'alt_text' in updated_config and hasattr(self, 'enable_alt_text_cb'):
            self.refresh_alt_text_availability()
        
        if 'tags' in updated_config and hasattr(self, 'enable_ai_tags_cb'):
            self.refresh_ai_tag_availability()
        
    def update_queue_display(self):
        """Update the queue display based on current queue state."""
        queue_info = self.batch_processor.get_queue_info()
        queue_size = len(queue_info)
        
        # Delegate queue display to the queue widget
        self.queue_widget.update_queue_display(queue_info)
        
        # Update process button text and state
        if queue_size == 0:
            self.process_button.setText("Add Images to Start")
            self.process_button.setEnabled(False)
            self.preview_button.setEnabled(False)
        else:
            # Update process button text
            if queue_size == 1:
                self.process_button.setText("Process Image")
            else:
                self.process_button.setText(f"Process {queue_size} Images")
            self.process_button.setEnabled(not self.is_processing)
            
        # Update preview button based on selection
        selected_rows = self.queue_widget.get_selected_indices()
        self.preview_button.setEnabled(len(selected_rows) == 1 and not self.is_processing)
        
        # Show/hide export button based on alt text availability
        has_alt_text = any(
            item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text
            for item in self.batch_processor.queue
        )
        self.quick_export_btn.setVisible(has_alt_text)
        
        # Update alt text widget data but keep it hidden (handled by dedicated tab now)
        if has_alt_text and self.enable_alt_text_cb.isChecked():
            self.alt_text_widget.set_batch_items(self.batch_processor.queue)
        # Keep alt text widget hidden - alt text review is now handled by dedicated tab
        self.alt_text_widget.setVisible(False)
            
        # Emit signal
        self.queue_changed.emit(queue_size)
        
        # For single image compatibility
        if queue_size == 1:
            self.image_loaded.emit(str(self.batch_processor.queue[0].source_path))
            
    def on_queue_selection_changed(self, selected_indices: List[int]):
        """Handle queue selection changes from the queue widget."""
        # Update preview button based on selection
        self.preview_button.setEnabled(len(selected_indices) == 1 and not self.is_processing)
        
    def on_files_dropped(self, file_paths: List[Path]):
        """Handle files dropped on the queue widget."""
        added_count = self.add_images_to_queue(file_paths)
        if added_count > 0:
            QMessageBox.information(
                self,
                "Images Added", 
                f"Added {added_count} images to processing queue."
            )
            
    # Queue Management Methods
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
                    
            self.update_queue_display()
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
            self.update_queue_display()
            if added_count > 0:
                logger.info(f"Added {added_count} images from folder")
            else:
                QMessageBox.warning(
                    self,
                    "No Images Found",
                    "No compatible images found in the selected folder."
                )
                
    def add_images_to_queue(self, file_paths: List[Path]):
        """Add multiple images to the queue."""
        added_count = 0
        for path in file_paths:
            if self.batch_processor.add_image(path):
                added_count += 1
                
        self.update_queue_display()
        return added_count
        
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
                self.update_queue_display()
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
            self.update_queue_display()
            
    # Processing Methods
    def start_processing(self):
        """Start processing with current settings."""
        if not self.batch_processor.queue:
            return
            
        # Get preset and output folder
        preset_name = self.preset_combo.currentData()
        output_folder = self.output_folder
        
        # Start processing
        self.is_processing = True
        self.processing_started.emit()
        
        # Update UI
        self.process_button.setText("Processing...")
        self.process_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        # Update queue widget processing state
        self.queue_widget.set_processing_state(True)
        
        # Show progress area
        self.progress_group.setVisible(True)
        self.overall_progress_bar.setValue(0)
        self.current_item_label.setVisible(True)
        
        # Start timer
        self.update_timer.start(100)  # Update every 100ms
        
        # Create and start processing thread
        self.processing_thread = BatchProcessingThread(
            self.batch_processor,
            preset_name,
            output_folder,
            generate_alt_text=self.enable_alt_text_cb.isChecked(),
            enable_tagging=self.enable_tags_cb.isChecked(),
            enable_ai_tagging=self.enable_ai_tags_cb.isChecked() and self.enable_ai_tags_cb.isEnabled(),
            filename_template=self.output_settings.get('filename_template')
        )
        
        self.processing_thread.progress_updated.connect(self.on_progress_updated)
        self.processing_thread.item_completed.connect(self.on_item_completed)
        self.processing_thread.batch_completed.connect(self.on_batch_completed)
        self.processing_thread.status_message.connect(lambda msg: logger.info(msg))
        
        self.processing_thread.start()
        
    def cancel_processing(self):
        """Cancel the current processing."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.cancel()
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancelling...")
            
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
        self.update_queue_display()
        
    def on_batch_completed(self, results: dict):
        """Handle processing completion."""
        self.is_processing = False
        self.update_timer.stop()
        
        # Update UI
        queue_size = len(self.batch_processor.queue)
        if queue_size == 0:
            self.process_button.setText("Add Images to Start")
        elif queue_size == 1:
            self.process_button.setText("Process Image")
        else:
            self.process_button.setText(f"Process {queue_size} Images")
            
        self.process_button.setEnabled(queue_size > 0)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancel")
        # Update queue widget processing state
        self.queue_widget.set_processing_state(False)
        self.current_item_label.setVisible(False)
        
        # Hide progress area if all items are processed
        if results.get('success', False) and not results.get('cancelled', False):
            self.progress_group.setVisible(False)
        
        # Update displays
        self.update_queue_display()
        
        # Show results
        if results.get('cancelled'):
            message = f"Processing cancelled.\n\n"
        else:
            message = f"Processing completed.\n\n"
            
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
            self.notification_manager.set_sound_enabled(
                self.prefs_manager.get('processing.completion_sound', True)
            )
            
            if not results.get('cancelled'):
                if queue_size == 1:
                    # Single image notification
                    item_name = self.batch_processor.queue[0].source_path.name if self.batch_processor.queue else "image"
                    self.notification_manager.show_single_completion(
                        item_name,
                        results.get('successful', 0) > 0
                    )
                else:
                    # Batch notification
                    self.notification_manager.show_batch_completion(
                        successful=results.get('successful', 0),
                        failed=results.get('failed', 0),
                        elapsed_time=results.get('elapsed_time', 0)
                    )
        
        # Show dialog
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
            
    # Preview and Settings Methods
    def show_preview(self):
        """Show preview for the selected image."""
        selected_indices = self.queue_widget.get_selected_indices()
        if not selected_indices:
            return
            
        # Get the selected item
        row = selected_indices[0]
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
            
    def show_advanced_settings(self):
        """Show the advanced settings dialog."""
        # Get parent window to access its advanced settings method
        parent = self.window()
        if hasattr(parent, 'show_advanced_settings'):
            parent.show_advanced_settings()
            
    def select_output_folder(self):
        """Open folder dialog to select output directory."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(self.output_folder)
        )
        
        if folder:
            self.output_folder = Path(folder)
            self.output_folder_edit.setText(str(self.output_folder))
            self.output_settings['output_folder'] = self.output_folder
            
    def show_output_settings(self):
        """Show the output settings dialog."""
        # Get parent window to access its output settings method
        parent = self.window()
        if hasattr(parent, 'show_output_settings'):
            parent.show_output_settings()
            
    # Alt Text Methods
    def on_alt_text_toggled(self, checked: bool):
        """Handle alt text generation toggle."""
        if checked:
            # Validate API key
            is_valid, api_key, error_message = self.api_validator.validate_alt_text_api_key()
            if not is_valid:
                self.enable_alt_text_cb.setChecked(False)
                QMessageBox.warning(
                    self,
                    "API Key Required",
                    error_message or "Please configure your Anthropic API key in preferences to enable alt text generation."
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
            
    # Tag-related methods
    def on_tags_toggled(self, checked: bool):
        """Handle tag assignment toggle."""
        # Update preferences
        self.prefs_manager.set('tags.enabled', checked)
        self.prefs_manager.save()
        
        self._update_tag_status_display()
        
        if checked:
            logger.info("Tag assignment enabled")
        else:
            logger.info("Tag assignment disabled")
    
    def on_ai_tags_toggled(self, checked: bool):
        """Handle AI tag generation toggle."""
        if checked:
            # Validate API key
            is_valid, api_key, error_message = self.api_validator.validate_ai_tag_api_key()
            if not is_valid:
                self.enable_ai_tags_cb.setChecked(False)
                QMessageBox.warning(
                    self,
                    "API Key Required",
                    error_message or "Please configure your Anthropic API key in preferences to enable AI tag generation."
                )
                return
                
            # Configure tag manager with AI capabilities
            success = self.tag_manager.enable_ai_generation(api_key)
            if not success:
                self.enable_ai_tags_cb.setChecked(False)
                QMessageBox.warning(
                    self,
                    "AI Tag Generation Failed",
                    "Failed to initialize AI tag generation. Please check your API key."
                )
                return
            
            # Update preferences
            self.prefs_manager.set('tags.ai_generation_enabled', True)
            self.prefs_manager.save()
            
            logger.info("AI tag generation enabled")
        else:
            self.tag_manager.disable_ai_generation()
            
            # Update preferences
            self.prefs_manager.set('tags.ai_generation_enabled', False)
            self.prefs_manager.save()
            
            logger.info("AI tag generation disabled")
            
        self._update_tag_status_display()
    
    def on_tags_updated(self, updates: dict):
        """Handle tag updates from the tag widget."""
        # Update batch processor items
        for filename, tags in updates.items():
            for item in self.batch_processor.queue:
                if item.source_path.name == filename:
                    item.tags = tags
                    item.tag_status = TagStatus.COMPLETED if tags else TagStatus.PENDING
                    break
        
        # Refresh UI
        self.update_queue_display()
        logger.info(f"Updated tags for {len(updates)} items")
    
    def on_tag_assignment_requested(self, tags: List[str], filenames: List[str]):
        """Handle tag assignment requests from the tag widget."""
        # Apply tags to specified items
        for filename in filenames:
            for item in self.batch_processor.queue:
                if item.source_path.name == filename:
                    # Use tag manager to validate and apply tags
                    result = self.tag_manager.apply_tags(tags, filename)
                    
                    item.tags = result.tags
                    item.tag_status = result.status
                    item.tag_error = result.error_message
                    item.tag_application_time = result.application_time
                    break
        
        # Refresh UI
        self.update_queue_display()
        logger.info(f"Applied tags {tags} to {len(filenames)} items")
    
    def quick_export_tags(self):
        """Quick export tag data to CSV using dedicated exporter."""
        # Create tag exporter
        exporter = TagCsvExporter()
        
        # Check if we have any tagged items
        tagged_items = exporter.filter_items(self.batch_processor.queue, TagExportOptions.COMPLETED_ONLY)
        
        if not tagged_items:
            QMessageBox.information(
                self,
                "No Data to Export",
                "No tagged items to export."
            )
            return
        
        # Generate default filename
        default_filename = exporter.generate_filename()
        
        # Get save location
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Tag Data",
            str(exporter.get_default_export_path(default_filename)),
            "CSV Files (*.csv)"
        )
        
        if not output_path:
            return
            
        output_path = Path(output_path)
        
        # Export using the dedicated service
        success, message = exporter.export_csv(
            self.batch_processor.queue,
            output_path,
            TagExportOptions.COMPLETED_ONLY,
            include_metadata=True
        )
        
        if success:
            QMessageBox.information(
                self,
                "Export Complete",
                f"Tag data exported to:\n{output_path.name}\n\n{message}"
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