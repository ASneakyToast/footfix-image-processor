"""
Clean preferences window using MVVM pattern.
Pure view layer with data binding to ViewModel.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QGroupBox, QLabel, QPushButton,
    QSpinBox, QCheckBox, QComboBox, QLineEdit,
    QDialogButtonBox, QFileDialog, QMessageBox,
    QFormLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from pathlib import Path
import asyncio
import logging

from ..utils.preferences_controller import PreferencesController

logger = logging.getLogger(__name__)


class PreferenceWidget(QWidget):
    """Base widget for preference sections."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.title = title
        self._form_layout = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up basic widget structure."""
        if self.title:
            title_label = QLabel(f"<h3>{self.title}</h3>")
            self.layout().addWidget(title_label)
    
    def add_form_section(self, section_title: str = None) -> QFormLayout:
        """Add a form section with optional title."""
        if section_title:
            group = QGroupBox(section_title)
            form_layout = QFormLayout()
            group.setLayout(form_layout)
            self.layout().addWidget(group)
        else:
            form_layout = QFormLayout()
            self.layout().addLayout(form_layout)
        
        self._form_layout = form_layout
        return form_layout
    
    def add_form_row(self, label: str, widget: QWidget, tooltip: str = None) -> None:
        """Add a row to the current form layout."""
        if not self._form_layout:
            self.add_form_section()
        
        if tooltip:
            widget.setToolTip(tooltip)
        
        self._form_layout.addRow(label, widget)


class GeneralPreferencesWidget(PreferenceWidget):
    """Widget for general preferences."""
    
    def __init__(self, controller: PreferencesController, parent=None):
        self.controller = controller
        super().__init__("General Settings", parent)
        self._create_controls()
        self._load_values()
    
    def _create_controls(self):
        """Create form controls."""
        # Recent items section
        form = self.add_form_section("Recent Items")
        
        self.max_recent_spin = QSpinBox()
        self.max_recent_spin.setRange(5, 50)
        self.max_recent_spin.setSuffix(" items")
        form.addRow("Maximum recent items:", self.max_recent_spin)
        
        # Clear buttons
        clear_layout = QHBoxLayout()
        clear_files_btn = QPushButton("Clear Recent Files")
        clear_presets_btn = QPushButton("Clear Recent Presets")
        clear_files_btn.clicked.connect(self._clear_recent_files)
        clear_presets_btn.clicked.connect(self._clear_recent_presets)
        clear_layout.addWidget(clear_files_btn)
        clear_layout.addWidget(clear_presets_btn)
        clear_layout.addStretch()
        
        self.layout().addLayout(clear_layout)
        
        # Updates section
        form = self.add_form_section("Updates")
        
        self.check_updates_cb = QCheckBox()
        form.addRow("Check for updates:", self.check_updates_cb)
    
    def _load_values(self):
        """Load current preference values."""
        self.max_recent_spin.setValue(self.controller.get_int('recent.max_recent_items', 10))
        self.check_updates_cb.setChecked(self.controller.get_bool('advanced.check_updates', True))
    
    def save_values(self):
        """Save current form values."""
        self.controller.set('recent.max_recent_items', self.max_recent_spin.value())
        self.controller.set('advanced.check_updates', self.check_updates_cb.isChecked())
    
    def _clear_recent_files(self):
        """Clear recent files."""
        self.controller.clear_recent_files()
        QMessageBox.information(self, "Cleared", "Recent files have been cleared.")
    
    def _clear_recent_presets(self):
        """Clear recent presets."""
        self.controller.clear_recent_presets()
        QMessageBox.information(self, "Cleared", "Recent presets have been cleared.")


class OutputPreferencesWidget(PreferenceWidget):
    """Widget for output preferences."""
    
    def __init__(self, controller: PreferencesController, parent=None):
        self.controller = controller
        super().__init__("Output Settings", parent)
        self._create_controls()
        self._load_values()
    
    def _create_controls(self):
        """Create form controls."""
        # Output folder section
        form = self.add_form_section("Default Output Folder")
        
        folder_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output_folder)
        folder_layout.addWidget(self.output_folder_edit)
        folder_layout.addWidget(browse_btn)
        
        form.addRow("Folder:", folder_layout)
        
        # Filename template section
        form = self.add_form_section("Filename Template")
        
        self.template_combo = QComboBox()
        self.template_combo.setEditable(True)
        self.template_combo.addItems([
            '{original_name}_{preset}',
            '{original_name}_{date}_{preset}',
            '{original_name}_{dimensions}_{preset}',
            '{original_name}_{counter:03}_{preset}'
        ])
        form.addRow("Template:", self.template_combo)
        
        # Help text
        help_label = QLabel(
            "Available: {original_name}, {preset}, {date}, {time}, "
            "{dimensions}, {width}, {height}, {counter}"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        self.layout().addWidget(help_label)
        
        # Duplicate handling section
        form = self.add_form_section("Duplicate Handling")
        
        self.duplicate_combo = QComboBox()
        self.duplicate_combo.addItems(["Rename (add number)", "Overwrite", "Skip"])
        form.addRow("When file exists:", self.duplicate_combo)
    
    def _load_values(self):
        """Load current preference values."""
        self.output_folder_edit.setText(self.controller.get_output_folder())
        self.template_combo.setCurrentText(self.controller.get_filename_template())
        
        strategies = ['rename', 'overwrite', 'skip']
        strategy = self.controller.get_str('output.duplicate_strategy', 'rename')
        if strategy in strategies:
            self.duplicate_combo.setCurrentIndex(strategies.index(strategy))
    
    def save_values(self):
        """Save current form values."""
        self.controller.set_output_folder(self.output_folder_edit.text())
        self.controller.set_filename_template(self.template_combo.currentText())
        
        strategies = ['rename', 'overwrite', 'skip']
        self.controller.set('output.duplicate_strategy', strategies[self.duplicate_combo.currentIndex()])
    
    def _browse_output_folder(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Default Output Folder", self.output_folder_edit.text()
        )
        if folder:
            self.output_folder_edit.setText(folder)


class ProcessingPreferencesWidget(PreferenceWidget):
    """Widget for processing preferences."""
    
    def __init__(self, controller: PreferencesController, parent=None):
        self.controller = controller
        super().__init__("Processing Settings", parent)
        self._create_controls()
        self._load_values()
    
    def _create_controls(self):
        """Create form controls."""
        # Batch processing section
        form = self.add_form_section("Batch Processing")
        
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setSuffix(" images")
        form.addRow("Max concurrent:", self.concurrent_spin)
        
        # Processing options section
        form = self.add_form_section("Processing Options")
        
        self.preserve_metadata_cb = QCheckBox()
        form.addRow("Preserve EXIF metadata:", self.preserve_metadata_cb)
        
        self.auto_preview_cb = QCheckBox()
        form.addRow("Auto-preview single images:", self.auto_preview_cb)
        
        # Notifications section
        form = self.add_form_section("Notifications")
        
        self.completion_notify_cb = QCheckBox()
        form.addRow("Show completion notification:", self.completion_notify_cb)
        
        self.completion_sound_cb = QCheckBox()
        form.addRow("Play completion sound:", self.completion_sound_cb)
    
    def _load_values(self):
        """Load current preference values."""
        self.concurrent_spin.setValue(self.controller.get_concurrent_processes())
        self.preserve_metadata_cb.setChecked(self.controller.get_bool('processing.preserve_metadata', True))
        self.auto_preview_cb.setChecked(self.controller.get_bool('processing.auto_preview', False))
        self.completion_notify_cb.setChecked(self.controller.get_bool('processing.completion_notification', True))
        self.completion_sound_cb.setChecked(self.controller.get_bool('processing.completion_sound', True))
    
    def save_values(self):
        """Save current form values."""
        self.controller.set_concurrent_processes(self.concurrent_spin.value())
        self.controller.set('processing.preserve_metadata', self.preserve_metadata_cb.isChecked())
        self.controller.set('processing.auto_preview', self.auto_preview_cb.isChecked())
        self.controller.set('processing.completion_notification', self.completion_notify_cb.isChecked())
        self.controller.set('processing.completion_sound', self.completion_sound_cb.isChecked())


class InterfacePreferencesWidget(PreferenceWidget):
    """Widget for interface preferences."""
    
    def __init__(self, controller: PreferencesController, parent=None):
        self.controller = controller
        super().__init__("Interface Settings", parent)
        self._create_controls()
        self._load_values()
    
    def _create_controls(self):
        """Create form controls."""
        form = self.add_form_section("Interface Options")
        
        self.show_tooltips_cb = QCheckBox()
        form.addRow("Show tooltips:", self.show_tooltips_cb)
        
        self.confirm_cancel_cb = QCheckBox()
        form.addRow("Confirm batch cancel:", self.confirm_cancel_cb)
        
        # Window state section
        form = self.add_form_section("Window State")
        
        reset_btn = QPushButton("Reset Window Position")
        reset_btn.clicked.connect(self._reset_window_state)
        form.addRow("Window:", reset_btn)
    
    def _load_values(self):
        """Load current preference values."""
        self.show_tooltips_cb.setChecked(self.controller.get_bool('interface.show_tooltips', True))
        self.confirm_cancel_cb.setChecked(self.controller.get_bool('interface.confirm_batch_cancel', True))
    
    def save_values(self):
        """Save current form values."""
        self.controller.set('interface.show_tooltips', self.show_tooltips_cb.isChecked())
        self.controller.set('interface.confirm_batch_cancel', self.confirm_cancel_cb.isChecked())
    
    def _reset_window_state(self):
        """Reset window state."""
        self.controller.reset_window_state()
        QMessageBox.information(self, "Reset", "Window position will be reset on next launch.")


class AltTextPreferencesWidget(PreferenceWidget):
    """Widget for alt text preferences."""
    
    def __init__(self, controller: PreferencesController, parent=None):
        self.controller = controller
        super().__init__("Alt Text Settings", parent)
        self._create_controls()
        self._load_values()
        self._setup_validation()
    
    def _create_controls(self):
        """Create form controls."""
        # API configuration section
        form = self.add_form_section("API Configuration")
        
        # API key with visibility toggle
        key_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter your Anthropic API key")
        
        self.show_key_btn = QPushButton("Show")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.toggled.connect(self._toggle_key_visibility)
        
        self.test_key_btn = QPushButton("Test")
        self.test_key_btn.clicked.connect(self._test_api_key)
        
        key_layout.addWidget(self.api_key_edit)
        key_layout.addWidget(self.show_key_btn)
        key_layout.addWidget(self.test_key_btn)
        
        form.addRow("API Key:", key_layout)
        
        # API status
        self.api_status_label = QLabel()
        self.api_status_label.setWordWrap(True)
        form.addRow("Status:", self.api_status_label)
        
        # Help link
        help_label = QLabel(
            '<a href="https://console.anthropic.com/">Get API key from Anthropic Console</a>'
        )
        help_label.setOpenExternalLinks(True)
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        form.addRow("", help_label)
        
        # Generation settings section
        form = self.add_form_section("Generation Settings")
        
        self.enable_alt_text_cb = QCheckBox()
        form.addRow("Enable by default:", self.enable_alt_text_cb)
        
        self.context_combo = QComboBox()
        self.context_combo.setEditable(True)
        self.context_combo.addItems([
            "editorial image",
            "product photo",
            "news photograph",
            "social media post",
            "marketing material"
        ])
        form.addRow("Default context:", self.context_combo)
        
        self.concurrent_requests_spin = QSpinBox()
        self.concurrent_requests_spin.setRange(1, 10)
        self.concurrent_requests_spin.setSuffix(" requests")
        form.addRow("Max concurrent requests:", self.concurrent_requests_spin)
        
        # Cost tracking section
        form = self.add_form_section("Cost Tracking")
        
        self.enable_cost_tracking_cb = QCheckBox()
        self.enable_cost_tracking_cb.toggled.connect(self._update_usage_stats)
        form.addRow("Track usage and costs:", self.enable_cost_tracking_cb)
        
        # Usage statistics
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        
        # Current month stats
        current_group = QGroupBox("Current Month")
        current_layout = QVBoxLayout(current_group)
        self.current_requests_label = QLabel("Requests: 0")
        self.current_cost_label = QLabel("Cost: $0.00")
        self.avg_cost_label = QLabel("Avg: $0.00")
        current_layout.addWidget(self.current_requests_label)
        current_layout.addWidget(self.current_cost_label)
        current_layout.addWidget(self.avg_cost_label)
        stats_layout.addWidget(current_group)
        
        # Total stats
        total_group = QGroupBox("All Time")
        total_layout = QVBoxLayout(total_group)
        self.total_requests_label = QLabel("Requests: 0")
        self.total_cost_label = QLabel("Cost: $0.00")
        reset_stats_btn = QPushButton("Reset Statistics")
        reset_stats_btn.clicked.connect(self._reset_usage_stats)
        total_layout.addWidget(self.total_requests_label)
        total_layout.addWidget(self.total_cost_label)
        total_layout.addWidget(reset_stats_btn)
        stats_layout.addWidget(total_group)
        
        form.addRow("Usage Statistics:", stats_widget)
    
    def _setup_validation(self):
        """Set up validation signal connections."""
        self.controller.api_key_validated.connect(self._on_api_validation_result)
    
    def _load_values(self):
        """Load current preference values."""
        api_key = self.controller.get_api_key()
        if api_key:
            self.api_key_edit.setText(api_key)
        
        self.enable_alt_text_cb.setChecked(self.controller.get_bool('alt_text.enabled', False))
        self.context_combo.setCurrentText(self.controller.get_str('alt_text.default_context', 'editorial image'))
        self.concurrent_requests_spin.setValue(self.controller.get_int('alt_text.max_concurrent_requests', 5))
        self.enable_cost_tracking_cb.setChecked(self.controller.get_bool('alt_text.enable_cost_tracking', True))
        
        self._update_usage_stats()
    
    def save_values(self):
        """Save current form values."""
        self.controller.set_api_key(self.api_key_edit.text())
        self.controller.set('alt_text.enabled', self.enable_alt_text_cb.isChecked())
        self.controller.set('alt_text.default_context', self.context_combo.currentText())
        self.controller.set('alt_text.max_concurrent_requests', self.concurrent_requests_spin.value())
        self.controller.set('alt_text.enable_cost_tracking', self.enable_cost_tracking_cb.isChecked())
    
    def _toggle_key_visibility(self, show: bool):
        """Toggle API key visibility."""
        if show:
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.show_key_btn.setText("Hide")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.show_key_btn.setText("Show")
    
    def _test_api_key(self):
        """Test API key validation."""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            self.api_status_label.setText("Please enter an API key to test.")
            self.api_status_label.setStyleSheet("color: orange;")
            return
        
        self.test_key_btn.setEnabled(False)
        self.api_status_label.setText("Testing API key...")
        self.api_status_label.setStyleSheet("color: blue;")
        
        self.controller.validate_api_key(api_key)
    
    def _on_api_validation_result(self, success: bool, message: str):
        """Handle API validation result."""
        self.test_key_btn.setEnabled(True)
        self.api_status_label.setText(message)
        
        if success:
            self.api_status_label.setStyleSheet("color: green;")
        else:
            self.api_status_label.setStyleSheet("color: red;")
    
    def _update_usage_stats(self):
        """Update usage statistics display."""
        if not self.enable_cost_tracking_cb.isChecked():
            return
        
        stats = self.controller.get_usage_stats()
        
        current = stats.get('current_month', {})
        self.current_requests_label.setText(f"Requests: {current.get('requests', 0)}")
        self.current_cost_label.setText(f"Cost: ${current.get('cost', 0):.2f}")
        self.avg_cost_label.setText(f"Avg: ${stats.get('avg_cost_per_request', 0):.3f}")
        
        total = stats.get('total', {})
        self.total_requests_label.setText(f"Requests: {total.get('requests', 0)}")
        self.total_cost_label.setText(f"Cost: ${total.get('cost', 0):.2f}")
    
    def _reset_usage_stats(self):
        """Reset usage statistics."""
        reply = QMessageBox.question(
            self, "Reset Statistics",
            "Are you sure you want to reset all usage statistics?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.controller.reset_usage_stats()
            self._update_usage_stats()
            QMessageBox.information(self, "Reset", "Statistics have been reset.")


class AdvancedPreferencesWidget(PreferenceWidget):
    """Widget for advanced preferences."""
    
    def __init__(self, controller: PreferencesController, parent=None):
        self.controller = controller
        super().__init__("Advanced Settings", parent)
        self._create_controls()
        self._load_values()
    
    def _create_controls(self):
        """Create form controls."""
        # Memory settings section
        form = self.add_form_section("Memory Settings")
        
        self.memory_spin = QSpinBox()
        self.memory_spin.setRange(512, 8192)
        self.memory_spin.setSingleStep(256)
        self.memory_spin.setSuffix(" MB")
        form.addRow("Memory limit:", self.memory_spin)
        
        # Temporary files section
        form = self.add_form_section("Temporary Files")
        
        temp_layout = QHBoxLayout()
        self.temp_dir_edit = QLineEdit()
        self.temp_dir_edit.setPlaceholderText("System default")
        temp_browse_btn = QPushButton("Browse...")
        temp_browse_btn.clicked.connect(self._browse_temp_dir)
        temp_layout.addWidget(self.temp_dir_edit)
        temp_layout.addWidget(temp_browse_btn)
        
        form.addRow("Temp directory:", temp_layout)
        
        # Logging section
        form = self.add_form_section("Logging")
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        form.addRow("Log level:", self.log_level_combo)
        
        # Import/Export section
        form = self.add_form_section("Settings Management")
        
        import_export_layout = QHBoxLayout()
        export_btn = QPushButton("Export Settings...")
        import_btn = QPushButton("Import Settings...")
        export_btn.clicked.connect(self._export_settings)
        import_btn.clicked.connect(self._import_settings)
        import_export_layout.addWidget(export_btn)
        import_export_layout.addWidget(import_btn)
        import_export_layout.addStretch()
        
        form.addRow("Backup:", import_export_layout)
    
    def _load_values(self):
        """Load current preference values."""
        self.memory_spin.setValue(self.controller.get_memory_limit_mb())
        self.temp_dir_edit.setText(self.controller.get_str('advanced.temp_directory', ''))
        self.log_level_combo.setCurrentText(self.controller.get_str('advanced.log_level', 'INFO'))
    
    def save_values(self):
        """Save current form values."""
        self.controller.set_memory_limit(self.memory_spin.value())
        
        temp_dir = self.temp_dir_edit.text().strip()
        self.controller.set('advanced.temp_directory', temp_dir if temp_dir else None)
        self.controller.set('advanced.log_level', self.log_level_combo.currentText())
    
    def _browse_temp_dir(self):
        """Browse for temporary directory."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Temporary Directory", self.temp_dir_edit.text()
        )
        if folder:
            self.temp_dir_edit.setText(folder)
    
    def _export_settings(self):
        """Export preferences to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings",
            str(Path.home() / "footfix_settings.json"),
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.controller.export_preferences(file_path):
                QMessageBox.information(self, "Success", "Settings exported successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to export settings.")
    
    def _import_settings(self):
        """Import preferences from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.controller.import_preferences(file_path):
                # Reload all widget values
                for widget in self.parent().parent().findChildren(PreferenceWidget):
                    if hasattr(widget, '_load_values'):
                        widget._load_values()
                QMessageBox.information(self, "Success", "Settings imported successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to import settings.")


class PreferencesWindow(QDialog):
    """Clean, MVVM-based preferences window."""
    
    preferences_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = PreferencesController.get_instance()
        
        self.setWindowTitle("FootFix Preferences")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        self._preference_widgets = []
        self._setup_ui()
        self._setup_signals()
    
    def _setup_ui(self):
        """Set up the UI structure."""
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create preference widgets
        widgets = [
            ("General", GeneralPreferencesWidget(self.controller)),
            ("Output", OutputPreferencesWidget(self.controller)),
            ("Processing", ProcessingPreferencesWidget(self.controller)),
            ("Interface", InterfacePreferencesWidget(self.controller)),
            ("Alt Text", AltTextPreferencesWidget(self.controller)),
            ("Advanced", AdvancedPreferencesWidget(self.controller)),
        ]
        
        for title, widget in widgets:
            self.tab_widget.addTab(widget, title)
            self._preference_widgets.append(widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self._apply_preferences)
        button_layout.addWidget(buttons)
        
        layout.addLayout(button_layout)
    
    def _setup_signals(self):
        """Set up signal connections."""
        self.controller.preferences_changed.connect(self.preferences_changed.emit)
    
    def _save_all_preferences(self):
        """Save all preference widget values."""
        for widget in self._preference_widgets:
            if hasattr(widget, 'save_values'):
                widget.save_values()
        
        # Force save to disk
        self.controller.save_preferences()
    
    def _apply_preferences(self):
        """Apply preferences without closing."""
        self._save_all_preferences()
        self.preferences_changed.emit()
    
    def accept(self):
        """Save and close."""
        self._save_all_preferences()
        self.preferences_changed.emit()
        super().accept()
    
    def _reset_to_defaults(self):
        """Reset all preferences to defaults."""
        reply = QMessageBox.question(
            self, "Reset to Defaults",
            "Are you sure you want to reset all preferences to their default values?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.controller.reset_to_defaults()
            
            # Reload all widget values
            for widget in self._preference_widgets:
                if hasattr(widget, '_load_values'):
                    widget._load_values()
            
            QMessageBox.information(self, "Reset", "Preferences have been reset to defaults.")