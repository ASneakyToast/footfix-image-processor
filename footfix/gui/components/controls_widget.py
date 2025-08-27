"""
Processing Controls Widget for FootFix.
Extracted from UnifiedProcessingWidget to handle preset selection and output settings.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFileDialog, QGroupBox, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal

logger = logging.getLogger(__name__)


class ProcessingControlsWidget(QWidget):
    """
    Dedicated widget for processing controls and settings.
    Handles preset selection, output folder, and action buttons.
    """
    
    # Signals
    preset_changed = Signal(str)  # Preset name
    output_folder_changed = Signal(Path)  # New output folder path
    advanced_settings_requested = Signal()
    output_settings_requested = Signal()
    preview_requested = Signal()
    process_requested = Signal()
    processing_cancelled = Signal()
    
    def __init__(self, parent=None):
        """Initialize the processing controls widget."""
        super().__init__(parent)
        self.output_folder = Path.home() / "Downloads"
        self.is_processing = False
        self.queue_size = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the processing controls UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # Processing options
        self.setup_processing_options(main_layout)
        
        # Action buttons
        self.setup_action_buttons(main_layout)
        
    def setup_processing_options(self, main_layout):
        """Set up the processing options section."""
        controls_group = QGroupBox("Processing Options")
        controls_layout = QVBoxLayout(controls_group)
        
        # Preset selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        
        self.preset_combo = QComboBox()
        self.setup_preset_combo()
        preset_layout.addWidget(self.preset_combo, 1)
        
        # Advanced settings button
        self.advanced_button = QPushButton("Advanced...")
        self.advanced_button.clicked.connect(self.advanced_settings_requested.emit)
        preset_layout.addWidget(self.advanced_button)
        
        controls_layout.addLayout(preset_layout)
        
        # Output folder selection
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        
        self.output_folder_edit = QLineEdit(str(self.output_folder))
        self.output_folder_edit.setReadOnly(True)
        output_layout.addWidget(self.output_folder_edit, 1)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(browse_button)
        
        # Output settings button
        output_settings_button = QPushButton("Settings...")
        output_settings_button.clicked.connect(self.output_settings_requested.emit)
        output_layout.addWidget(output_settings_button)
        
        controls_layout.addLayout(output_layout)
        
        main_layout.addWidget(controls_group)
        
    def setup_preset_combo(self):
        """Set up the preset combo box with options and tooltips."""
        presets = [
            ("Editorial Web (Max 2560×1440, 0.5-1MB)", "editorial_web", 
             "Optimized for web articles and galleries.\n"
             "Maximum dimensions: 2560×1440 pixels\n"
             "Target file size: 0.5-1MB\n"
             "Perfect for editorial content and blog posts."),
            
            ("Email (Max 600px width, <100KB)", "email",
             "Small file size for email attachments.\n"
             "Maximum width: 600 pixels\n"
             "Target file size: <100KB\n"
             "Ensures images load quickly in email clients."),
            
            ("Instagram Story (1080×1920)", "instagram_story",
             "Instagram Stories format.\n"
             "Exact dimensions: 1080×1920 pixels (9:16)\n"
             "Images will be cropped to fit if needed.\n"
             "Optimized for mobile viewing."),
            
            ("Instagram Feed Portrait (1080×1350)", "instagram_feed_portrait",
             "Instagram Feed portrait format.\n"
             "Exact dimensions: 1080×1350 pixels (4:5)\n"
             "Images will be cropped to fit if needed.\n"
             "Ideal for Instagram posts.")
        ]
        
        for i, (display_name, preset_name, tooltip) in enumerate(presets):
            self.preset_combo.addItem(display_name, preset_name)
            self.preset_combo.setItemData(i, tooltip, Qt.ToolTipRole)
        
        # Connect preset change signal
        self.preset_combo.currentTextChanged.connect(lambda: self.preset_changed.emit(
            self.preset_combo.currentData()
        ))
        
    def setup_action_buttons(self, main_layout):
        """Set up the action buttons section."""
        button_layout = QHBoxLayout()
        
        # Preview button
        self.preview_button = QPushButton("Preview Selected")
        self.preview_button.clicked.connect(self.preview_requested.emit)
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
        self.process_button.clicked.connect(self.process_requested.emit)
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
        self.cancel_button.clicked.connect(self.processing_cancelled.emit)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setMinimumHeight(40)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
    def get_selected_preset(self) -> str:
        """Get the currently selected preset name."""
        return self.preset_combo.currentData()
        
    def set_selected_preset(self, preset_name: str):
        """Set the selected preset by name."""
        for i in range(self.preset_combo.count()):
            if self.preset_combo.itemData(i) == preset_name:
                self.preset_combo.setCurrentIndex(i)
                break
                
    def get_output_folder(self) -> Path:
        """Get the current output folder."""
        return self.output_folder
        
    def set_output_folder(self, folder_path: Path):
        """
        Set the output folder path.
        
        Args:
            folder_path: New output folder path
        """
        self.output_folder = folder_path
        self.output_folder_edit.setText(str(folder_path))
        self.output_folder_changed.emit(folder_path)
        
    def browse_output_folder(self):
        """Open folder dialog to select output directory."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(self.output_folder)
        )
        
        if folder:
            self.set_output_folder(Path(folder))
            
    def update_queue_state(self, queue_size: int, selected_count: int = 0):
        """
        Update button states based on queue size and selection.
        
        Args:
            queue_size: Number of items in the processing queue
            selected_count: Number of selected items (for preview)
        """
        self.queue_size = queue_size
        
        # Update process button text and state
        if queue_size == 0:
            self.process_button.setText("Add Images to Start")
            self.process_button.setEnabled(False)
        elif queue_size == 1:
            self.process_button.setText("Process Image")
            self.process_button.setEnabled(not self.is_processing)
        else:
            self.process_button.setText(f"Process {queue_size} Images")
            self.process_button.setEnabled(not self.is_processing)
            
        # Update preview button state
        self.preview_button.setEnabled(selected_count == 1 and not self.is_processing)
        
    def set_processing_state(self, is_processing: bool):
        """
        Update the widget state based on processing status.
        
        Args:
            is_processing: Whether processing is currently active
        """
        self.is_processing = is_processing
        
        if is_processing:
            # Processing state
            self.process_button.setText("Processing...")
            self.process_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.preview_button.setEnabled(False)
            self.preset_combo.setEnabled(False)
            self.advanced_button.setEnabled(False)
        else:
            # Not processing state
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancel")  # Reset text if it was "Cancelling..."
            self.preset_combo.setEnabled(True)
            self.advanced_button.setEnabled(True)
            
            # Update button states based on current queue
            self.update_queue_state(self.queue_size, 0)  # Reset selection count
            
    def set_cancel_state(self, is_cancelling: bool):
        """
        Update cancel button state during cancellation.
        
        Args:
            is_cancelling: Whether cancellation is in progress
        """
        if is_cancelling:
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancelling...")
        else:
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancel")
            
    def set_enabled(self, enabled: bool):
        """Enable or disable all controls."""
        self.preset_combo.setEnabled(enabled)
        self.advanced_button.setEnabled(enabled)
        self.output_folder_edit.setEnabled(enabled)
        self.process_button.setEnabled(enabled and self.queue_size > 0)
        self.preview_button.setEnabled(enabled)
        self.cancel_button.setEnabled(not enabled)  # Cancel only enabled when processing