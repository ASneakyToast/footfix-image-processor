"""
Preferences window for FootFix.
Provides a comprehensive interface for application settings.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QGroupBox, QLabel, QPushButton,
    QSpinBox, QCheckBox, QComboBox, QLineEdit,
    QDialogButtonBox, QFileDialog, QListWidget,
    QMessageBox, QSlider
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path

from ..utils.preferences import PreferencesManager


class PreferencesWindow(QDialog):
    """Main preferences window with tabbed interface."""
    
    preferences_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.prefs_manager = PreferencesManager()
        
        self.setWindowTitle("FootFix Preferences")
        self.setMinimumSize(700, 500)
        self.setup_ui()
        self.load_preferences()
        
    def setup_ui(self):
        """Set up the preferences UI."""
        layout = QVBoxLayout(self)
        
        # Tab widget for different preference categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.tab_widget.addTab(self.create_general_tab(), "General")
        self.tab_widget.addTab(self.create_output_tab(), "Output")
        self.tab_widget.addTab(self.create_processing_tab(), "Processing")
        self.tab_widget.addTab(self.create_interface_tab(), "Interface")
        self.tab_widget.addTab(self.create_advanced_tab(), "Advanced")
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        # Reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_button)
        
        button_layout.addStretch()
        
        # Standard buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_preferences)
        button_layout.addWidget(buttons)
        
        layout.addLayout(button_layout)
        
    def create_general_tab(self):
        """Create the general preferences tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Recent items
        recent_group = QGroupBox("Recent Items")
        recent_layout = QVBoxLayout()
        
        # Max recent items
        max_recent_layout = QHBoxLayout()
        max_recent_layout.addWidget(QLabel("Maximum recent items:"))
        
        self.max_recent_spin = QSpinBox()
        self.max_recent_spin.setRange(5, 50)
        self.max_recent_spin.setSuffix(" items")
        max_recent_layout.addWidget(self.max_recent_spin)
        max_recent_layout.addStretch()
        
        recent_layout.addLayout(max_recent_layout)
        
        # Clear recent buttons
        clear_layout = QHBoxLayout()
        
        clear_files_btn = QPushButton("Clear Recent Files")
        clear_files_btn.clicked.connect(lambda: self.clear_recent('files'))
        clear_layout.addWidget(clear_files_btn)
        
        clear_presets_btn = QPushButton("Clear Recent Presets")
        clear_presets_btn.clicked.connect(lambda: self.clear_recent('presets'))
        clear_layout.addWidget(clear_presets_btn)
        
        clear_layout.addStretch()
        recent_layout.addLayout(clear_layout)
        
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        # Updates
        updates_group = QGroupBox("Updates")
        updates_layout = QVBoxLayout()
        
        self.check_updates_cb = QCheckBox("Automatically check for updates")
        updates_layout.addWidget(self.check_updates_cb)
        
        updates_group.setLayout(updates_layout)
        layout.addWidget(updates_group)
        
        layout.addStretch()
        return widget
        
    def create_output_tab(self):
        """Create the output preferences tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Default output folder
        folder_group = QGroupBox("Default Output Folder")
        folder_layout = QVBoxLayout()
        
        folder_h_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setReadOnly(True)
        folder_h_layout.addWidget(self.output_folder_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output_folder)
        folder_h_layout.addWidget(browse_btn)
        
        folder_layout.addLayout(folder_h_layout)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # Filename template
        template_group = QGroupBox("Default Filename Template")
        template_layout = QVBoxLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.setEditable(True)
        self.template_combo.addItems([
            '{original_name}_{preset}',
            '{original_name}_{date}_{preset}',
            '{original_name}_{dimensions}_{preset}',
            '{original_name}_{counter:03}_{preset}'
        ])
        template_layout.addWidget(self.template_combo)
        
        template_help = QLabel(
            "Available variables: {original_name}, {preset}, {date}, {time}, "
            "{dimensions}, {width}, {height}, {counter}"
        )
        template_help.setWordWrap(True)
        template_help.setStyleSheet("color: #666; font-size: 11px;")
        template_layout.addWidget(template_help)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # Duplicate handling
        duplicate_group = QGroupBox("Default Duplicate Handling")
        duplicate_layout = QVBoxLayout()
        
        self.duplicate_combo = QComboBox()
        self.duplicate_combo.addItems(["Rename (add number)", "Overwrite", "Skip"])
        duplicate_layout.addWidget(self.duplicate_combo)
        
        duplicate_group.setLayout(duplicate_layout)
        layout.addWidget(duplicate_group)
        
        layout.addStretch()
        return widget
        
    def create_processing_tab(self):
        """Create the processing preferences tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Batch processing
        batch_group = QGroupBox("Batch Processing")
        batch_layout = QVBoxLayout()
        
        # Max concurrent
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("Maximum concurrent processes:"))
        
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setSuffix(" images")
        concurrent_layout.addWidget(self.concurrent_spin)
        concurrent_layout.addStretch()
        
        batch_layout.addLayout(concurrent_layout)
        
        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)
        
        # Processing options
        options_group = QGroupBox("Processing Options")
        options_layout = QVBoxLayout()
        
        self.preserve_metadata_cb = QCheckBox("Preserve image metadata (EXIF)")
        options_layout.addWidget(self.preserve_metadata_cb)
        
        self.auto_preview_cb = QCheckBox("Automatically show preview for single images")
        options_layout.addWidget(self.auto_preview_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Notifications
        notify_group = QGroupBox("Notifications")
        notify_layout = QVBoxLayout()
        
        self.completion_notify_cb = QCheckBox("Show notification when batch completes")
        notify_layout.addWidget(self.completion_notify_cb)
        
        self.completion_sound_cb = QCheckBox("Play sound when batch completes")
        notify_layout.addWidget(self.completion_sound_cb)
        
        notify_group.setLayout(notify_layout)
        layout.addWidget(notify_group)
        
        layout.addStretch()
        return widget
        
    def create_interface_tab(self):
        """Create the interface preferences tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Interface options
        interface_group = QGroupBox("Interface Options")
        interface_layout = QVBoxLayout()
        
        self.show_tooltips_cb = QCheckBox("Show tooltips")
        interface_layout.addWidget(self.show_tooltips_cb)
        
        self.confirm_cancel_cb = QCheckBox("Confirm when canceling batch processing")
        interface_layout.addWidget(self.confirm_cancel_cb)
        
        interface_group.setLayout(interface_layout)
        layout.addWidget(interface_group)
        
        # Window state
        window_group = QGroupBox("Window State")
        window_layout = QVBoxLayout()
        
        restore_layout = QHBoxLayout()
        restore_btn = QPushButton("Reset Window Size and Position")
        restore_btn.clicked.connect(self.reset_window_state)
        restore_layout.addWidget(restore_btn)
        restore_layout.addStretch()
        
        window_layout.addLayout(restore_layout)
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        layout.addStretch()
        return widget
        
    def create_advanced_tab(self):
        """Create the advanced preferences tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Memory settings
        memory_group = QGroupBox("Memory Settings")
        memory_layout = QVBoxLayout()
        
        memory_h_layout = QHBoxLayout()
        memory_h_layout.addWidget(QLabel("Memory limit for processing:"))
        
        self.memory_spin = QSpinBox()
        self.memory_spin.setRange(512, 8192)
        self.memory_spin.setSingleStep(256)
        self.memory_spin.setSuffix(" MB")
        memory_h_layout.addWidget(self.memory_spin)
        memory_h_layout.addStretch()
        
        memory_layout.addLayout(memory_h_layout)
        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)
        
        # Temporary files
        temp_group = QGroupBox("Temporary Files")
        temp_layout = QVBoxLayout()
        
        temp_h_layout = QHBoxLayout()
        self.temp_dir_edit = QLineEdit()
        self.temp_dir_edit.setPlaceholderText("System default")
        temp_h_layout.addWidget(self.temp_dir_edit)
        
        temp_browse_btn = QPushButton("Browse...")
        temp_browse_btn.clicked.connect(self.browse_temp_dir)
        temp_h_layout.addWidget(temp_browse_btn)
        
        temp_layout.addLayout(temp_h_layout)
        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)
        
        # Logging
        log_group = QGroupBox("Logging")
        log_layout = QVBoxLayout()
        
        log_h_layout = QHBoxLayout()
        log_h_layout.addWidget(QLabel("Log level:"))
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_h_layout.addWidget(self.log_level_combo)
        log_h_layout.addStretch()
        
        log_layout.addLayout(log_h_layout)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Import/Export
        import_export_group = QGroupBox("Import/Export Settings")
        import_export_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export Settings...")
        export_btn.clicked.connect(self.export_settings)
        import_export_layout.addWidget(export_btn)
        
        import_btn = QPushButton("Import Settings...")
        import_btn.clicked.connect(self.import_settings)
        import_export_layout.addWidget(import_btn)
        
        import_export_layout.addStretch()
        import_export_group.setLayout(import_export_layout)
        layout.addWidget(import_export_group)
        
        layout.addStretch()
        return widget
        
    def load_preferences(self):
        """Load preferences into UI controls."""
        # General
        self.max_recent_spin.setValue(self.prefs_manager.get('recent.max_recent_items', 10))
        self.check_updates_cb.setChecked(self.prefs_manager.get('advanced.check_updates', True))
        
        # Output
        self.output_folder_edit.setText(self.prefs_manager.get('output.default_folder', ''))
        self.template_combo.setCurrentText(self.prefs_manager.get('output.filename_template', ''))
        
        strategies = ['rename', 'overwrite', 'skip']
        strategy = self.prefs_manager.get('output.duplicate_strategy', 'rename')
        if strategy in strategies:
            self.duplicate_combo.setCurrentIndex(strategies.index(strategy))
            
        # Processing
        self.concurrent_spin.setValue(self.prefs_manager.get('processing.max_concurrent_batch', 3))
        self.preserve_metadata_cb.setChecked(self.prefs_manager.get('processing.preserve_metadata', True))
        self.auto_preview_cb.setChecked(self.prefs_manager.get('processing.auto_preview', False))
        self.completion_notify_cb.setChecked(self.prefs_manager.get('processing.completion_notification', True))
        self.completion_sound_cb.setChecked(self.prefs_manager.get('processing.completion_sound', True))
        
        # Interface
        self.show_tooltips_cb.setChecked(self.prefs_manager.get('interface.show_tooltips', True))
        self.confirm_cancel_cb.setChecked(self.prefs_manager.get('interface.confirm_batch_cancel', True))
        
        # Advanced
        self.memory_spin.setValue(self.prefs_manager.get('advanced.memory_limit_mb', 2048))
        self.temp_dir_edit.setText(self.prefs_manager.get('advanced.temp_directory', '') or '')
        self.log_level_combo.setCurrentText(self.prefs_manager.get('advanced.log_level', 'INFO'))
        
    def save_preferences(self):
        """Save UI values to preferences."""
        # General
        self.prefs_manager.set('recent.max_recent_items', self.max_recent_spin.value())
        self.prefs_manager.set('advanced.check_updates', self.check_updates_cb.isChecked())
        
        # Output
        self.prefs_manager.set('output.default_folder', self.output_folder_edit.text())
        self.prefs_manager.set('output.filename_template', self.template_combo.currentText())
        
        strategies = ['rename', 'overwrite', 'skip']
        self.prefs_manager.set('output.duplicate_strategy', strategies[self.duplicate_combo.currentIndex()])
        
        # Processing
        self.prefs_manager.set('processing.max_concurrent_batch', self.concurrent_spin.value())
        self.prefs_manager.set('processing.preserve_metadata', self.preserve_metadata_cb.isChecked())
        self.prefs_manager.set('processing.auto_preview', self.auto_preview_cb.isChecked())
        self.prefs_manager.set('processing.completion_notification', self.completion_notify_cb.isChecked())
        self.prefs_manager.set('processing.completion_sound', self.completion_sound_cb.isChecked())
        
        # Interface
        self.prefs_manager.set('interface.show_tooltips', self.show_tooltips_cb.isChecked())
        self.prefs_manager.set('interface.confirm_batch_cancel', self.confirm_cancel_cb.isChecked())
        
        # Advanced
        self.prefs_manager.set('advanced.memory_limit_mb', self.memory_spin.value())
        temp_dir = self.temp_dir_edit.text()
        self.prefs_manager.set('advanced.temp_directory', temp_dir if temp_dir else None)
        self.prefs_manager.set('advanced.log_level', self.log_level_combo.currentText())
        
        # Save to disk
        self.prefs_manager.save()
        
    def apply_preferences(self):
        """Apply preferences without closing dialog."""
        self.save_preferences()
        self.preferences_changed.emit()
        
    def accept(self):
        """Save preferences and close dialog."""
        self.save_preferences()
        self.preferences_changed.emit()
        super().accept()
        
    def browse_output_folder(self):
        """Browse for default output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Default Output Folder",
            self.output_folder_edit.text()
        )
        
        if folder:
            self.output_folder_edit.setText(folder)
            
    def browse_temp_dir(self):
        """Browse for temporary directory."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Temporary Directory",
            self.temp_dir_edit.text()
        )
        
        if folder:
            self.temp_dir_edit.setText(folder)
            
    def clear_recent(self, category):
        """Clear a recent items list."""
        self.prefs_manager.set(f'recent.{category}', [])
        QMessageBox.information(
            self,
            "Recent Items Cleared",
            f"Recent {category} have been cleared."
        )
        
    def reset_window_state(self):
        """Reset window state preferences."""
        self.prefs_manager.set('interface.window_geometry', None)
        self.prefs_manager.set('interface.window_state', None)
        QMessageBox.information(
            self,
            "Window State Reset",
            "Window size and position will be reset on next launch."
        )
        
    def reset_to_defaults(self):
        """Reset all preferences to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all preferences to their default values?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.prefs_manager.reset_to_defaults()
            self.load_preferences()
            
    def export_settings(self):
        """Export preferences to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            str(Path.home() / "footfix_settings.json"),
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.prefs_manager.export_preferences(Path(file_path)):
                QMessageBox.information(
                    self,
                    "Export Successful",
                    "Settings exported successfully."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    "Failed to export settings."
                )
                
    def import_settings(self):
        """Import preferences from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.prefs_manager.import_preferences(Path(file_path)):
                self.load_preferences()
                QMessageBox.information(
                    self,
                    "Import Successful",
                    "Settings imported successfully."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Import Failed",
                    "Failed to import settings."
                )