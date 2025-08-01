"""
Advanced settings dialog for customizing image processing parameters.
Allows power users to override preset settings and create custom configurations.
"""

import logging
from typing import Optional, Dict, Any
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QSpinBox, QSlider, QComboBox,
    QGroupBox, QLineEdit, QCheckBox, QFileDialog,
    QMessageBox, QDialogButtonBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator

from ..presets.profiles import PresetConfig

logger = logging.getLogger(__name__)


class AdvancedSettingsDialog(QDialog):
    """Dialog for advanced image processing settings."""
    
    # Signal emitted when settings are applied
    settings_applied = Signal(dict)
    
    def __init__(self, parent=None, current_preset: Optional[PresetConfig] = None):
        super().__init__(parent)
        self.current_preset = current_preset
        self.custom_presets_path = Path.home() / ".footfix" / "custom_presets.json"
        self.custom_presets = self.load_custom_presets()
        
        self.setup_ui()
        
        # Load current preset values if provided
        if current_preset:
            self.load_preset_values(current_preset)
            
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Advanced Settings")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget for organizing settings
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Basic settings tab
        basic_tab = QWidget()
        self.setup_basic_tab(basic_tab)
        self.tab_widget.addTab(basic_tab, "Basic Settings")
        
        # Advanced settings tab
        advanced_tab = QWidget()
        self.setup_advanced_tab(advanced_tab)
        self.tab_widget.addTab(advanced_tab, "Advanced Settings")
        
        # Custom presets tab
        presets_tab = QWidget()
        self.setup_presets_tab(presets_tab)
        self.tab_widget.addTab(presets_tab, "Custom Presets")
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(button_box)
        
    def setup_basic_tab(self, parent: QWidget):
        """Set up the basic settings tab."""
        layout = QVBoxLayout(parent)
        
        # Dimensions group
        dimensions_group = QGroupBox("Dimensions")
        dimensions_layout = QFormLayout()
        
        # Resize mode
        self.resize_mode_combo = QComboBox()
        self.resize_mode_combo.addItem("Fit within dimensions", "fit")
        self.resize_mode_combo.addItem("Exact dimensions (crop if needed)", "exact")
        self.resize_mode_combo.addItem("No resize", "none")
        self.resize_mode_combo.currentIndexChanged.connect(self.on_resize_mode_changed)
        dimensions_layout.addRow("Resize Mode:", self.resize_mode_combo)
        
        # Width
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(2560)
        self.width_spin.setSuffix(" px")
        dimensions_layout.addRow("Max/Exact Width:", self.width_spin)
        
        # Height
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(1440)
        self.height_spin.setSuffix(" px")
        dimensions_layout.addRow("Max/Exact Height:", self.height_spin)
        
        # Maintain aspect ratio
        self.maintain_aspect_check = QCheckBox("Maintain aspect ratio")
        self.maintain_aspect_check.setChecked(True)
        dimensions_layout.addRow("", self.maintain_aspect_check)
        
        dimensions_group.setLayout(dimensions_layout)
        layout.addWidget(dimensions_group)
        
        # File size group
        size_group = QGroupBox("File Size")
        size_layout = QFormLayout()
        
        # Enable file size optimization
        self.optimize_size_check = QCheckBox("Optimize for target file size")
        self.optimize_size_check.toggled.connect(self.on_optimize_size_toggled)
        size_layout.addRow("", self.optimize_size_check)
        
        # Target size
        self.target_size_spin = QSpinBox()
        self.target_size_spin.setRange(10, 10000)
        self.target_size_spin.setValue(750)
        self.target_size_spin.setSuffix(" KB")
        self.target_size_spin.setEnabled(False)
        size_layout.addRow("Target Size:", self.target_size_spin)
        
        # Min size
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(10, 10000)
        self.min_size_spin.setValue(500)
        self.min_size_spin.setSuffix(" KB")
        self.min_size_spin.setEnabled(False)
        size_layout.addRow("Minimum Size:", self.min_size_spin)
        
        # Max size
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(10, 10000)
        self.max_size_spin.setValue(1024)
        self.max_size_spin.setSuffix(" KB")
        self.max_size_spin.setEnabled(False)
        size_layout.addRow("Maximum Size:", self.max_size_spin)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        layout.addStretch()
        
    def setup_advanced_tab(self, parent: QWidget):
        """Set up the advanced settings tab."""
        layout = QVBoxLayout(parent)
        
        # Output format group
        format_group = QGroupBox("Output Format")
        format_layout = QFormLayout()
        
        # Format selection
        self.format_combo = QComboBox()
        self.format_combo.addItem("JPEG", "JPEG")
        self.format_combo.addItem("PNG", "PNG")
        self.format_combo.addItem("WebP", "WEBP")
        self.format_combo.currentIndexChanged.connect(self.on_format_changed)
        format_layout.addRow("Format:", self.format_combo)
        
        # Quality slider
        quality_layout = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        
        self.quality_label = QLabel("85")
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_label)
        
        format_layout.addRow("Quality:", quality_layout)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Filename options group
        filename_group = QGroupBox("Filename Options")
        filename_layout = QFormLayout()
        
        # Prefix
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("e.g., 'web_'")
        filename_layout.addRow("Prefix:", self.prefix_edit)
        
        # Suffix
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText("e.g., '_optimized'")
        filename_layout.addRow("Suffix:", self.suffix_edit)
        
        # Example filename
        self.filename_example = QLabel("Example: prefix_originalname_suffix.jpg")
        self.filename_example.setStyleSheet("color: #666;")
        filename_layout.addRow("", self.filename_example)
        
        filename_group.setLayout(filename_layout)
        layout.addWidget(filename_group)
        
        layout.addStretch()
        
    def setup_presets_tab(self, parent: QWidget):
        """Set up the custom presets tab."""
        layout = QVBoxLayout(parent)
        
        # Instructions
        instructions = QLabel(
            "Save your current settings as a custom preset for future use.\n"
            "Custom presets are stored locally and can be exported/imported."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Save preset group
        save_group = QGroupBox("Save Current Settings")
        save_layout = QHBoxLayout()
        
        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setPlaceholderText("Enter preset name...")
        save_layout.addWidget(self.preset_name_edit)
        
        save_button = QPushButton("Save as Preset")
        save_button.clicked.connect(self.save_custom_preset)
        save_layout.addWidget(save_button)
        
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)
        
        # Load preset group
        load_group = QGroupBox("Load Custom Preset")
        load_layout = QHBoxLayout()
        
        self.custom_preset_combo = QComboBox()
        self.update_custom_presets_combo()
        load_layout.addWidget(self.custom_preset_combo)
        
        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_custom_preset)
        load_layout.addWidget(load_button)
        
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_custom_preset)
        load_layout.addWidget(delete_button)
        
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Import/Export group
        import_export_group = QGroupBox("Import/Export")
        import_export_layout = QHBoxLayout()
        
        import_button = QPushButton("Import Presets...")
        import_button.clicked.connect(self.import_presets)
        import_export_layout.addWidget(import_button)
        
        export_button = QPushButton("Export Presets...")
        export_button.clicked.connect(self.export_presets)
        import_export_layout.addWidget(export_button)
        
        import_export_group.setLayout(import_export_layout)
        layout.addWidget(import_export_group)
        
        layout.addStretch()
        
    def on_resize_mode_changed(self, index: int):
        """Handle resize mode changes."""
        mode = self.resize_mode_combo.currentData()
        
        if mode == "none":
            self.width_spin.setEnabled(False)
            self.height_spin.setEnabled(False)
            self.maintain_aspect_check.setEnabled(False)
        elif mode == "exact":
            self.width_spin.setEnabled(True)
            self.height_spin.setEnabled(True)
            self.maintain_aspect_check.setEnabled(False)
            self.maintain_aspect_check.setChecked(False)
        else:  # fit
            self.width_spin.setEnabled(True)
            self.height_spin.setEnabled(True)
            self.maintain_aspect_check.setEnabled(True)
            
    def on_optimize_size_toggled(self, checked: bool):
        """Handle file size optimization toggle."""
        self.target_size_spin.setEnabled(checked)
        self.min_size_spin.setEnabled(checked)
        self.max_size_spin.setEnabled(checked)
        
    def on_format_changed(self, index: int):
        """Handle format changes."""
        format_type = self.format_combo.currentData()
        
        # PNG doesn't use quality setting
        if format_type == "PNG":
            self.quality_slider.setEnabled(False)
            self.quality_label.setText("N/A")
        else:
            self.quality_slider.setEnabled(True)
            self.quality_label.setText(str(self.quality_slider.value()))
            
    def on_quality_changed(self, value: int):
        """Handle quality slider changes."""
        self.quality_label.setText(str(value))
        
    def load_preset_values(self, preset: PresetConfig):
        """Load values from a preset configuration."""
        # Dimensions
        if preset.exact_width and preset.exact_height:
            self.resize_mode_combo.setCurrentIndex(1)  # Exact
            self.width_spin.setValue(preset.exact_width)
            self.height_spin.setValue(preset.exact_height)
        elif preset.max_width and preset.max_height:
            self.resize_mode_combo.setCurrentIndex(0)  # Fit
            self.width_spin.setValue(preset.max_width)
            self.height_spin.setValue(preset.max_height)
        else:
            self.resize_mode_combo.setCurrentIndex(2)  # None
            
        self.maintain_aspect_check.setChecked(preset.maintain_aspect)
        
        # File size
        if preset.target_size_kb:
            self.optimize_size_check.setChecked(True)
            self.target_size_spin.setValue(preset.target_size_kb)
            
            if preset.min_size_kb:
                self.min_size_spin.setValue(preset.min_size_kb)
            if preset.max_size_kb:
                self.max_size_spin.setValue(preset.max_size_kb)
        else:
            self.optimize_size_check.setChecked(False)
            
        # Format and quality
        format_index = self.format_combo.findData(preset.format)
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)
            
        self.quality_slider.setValue(preset.quality)
        
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings as a dictionary."""
        settings = {
            'resize_mode': self.resize_mode_combo.currentData(),
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'maintain_aspect': self.maintain_aspect_check.isChecked(),
            'format': self.format_combo.currentData(),
            'quality': self.quality_slider.value(),
            'prefix': self.prefix_edit.text(),
            'suffix': self.suffix_edit.text(),
        }
        
        if self.optimize_size_check.isChecked():
            settings['target_size_kb'] = self.target_size_spin.value()
            settings['min_size_kb'] = self.min_size_spin.value()
            settings['max_size_kb'] = self.max_size_spin.value()
            
        return settings
        
    def apply_settings(self):
        """Apply current settings without closing dialog."""
        settings = self.get_settings()
        self.settings_applied.emit(settings)
        
    def load_custom_presets(self) -> Dict[str, Dict]:
        """Load custom presets from file."""
        if not self.custom_presets_path.exists():
            return {}
            
        try:
            with open(self.custom_presets_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading custom presets: {e}")
            return {}
            
    def save_custom_presets(self):
        """Save custom presets to file."""
        self.custom_presets_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.custom_presets_path, 'w') as f:
                json.dump(self.custom_presets, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving custom presets: {e}")
            
    def save_custom_preset(self):
        """Save current settings as a custom preset."""
        name = self.preset_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a preset name.")
            return
            
        settings = self.get_settings()
        self.custom_presets[name] = settings
        self.save_custom_presets()
        
        self.preset_name_edit.clear()
        self.update_custom_presets_combo()
        
        QMessageBox.information(self, "Success", f"Preset '{name}' saved successfully.")
        
    def load_custom_preset(self):
        """Load selected custom preset."""
        preset_name = self.custom_preset_combo.currentText()
        if not preset_name or preset_name not in self.custom_presets:
            return
            
        settings = self.custom_presets[preset_name]
        
        # Apply settings to UI
        if 'resize_mode' in settings:
            index = self.resize_mode_combo.findData(settings['resize_mode'])
            if index >= 0:
                self.resize_mode_combo.setCurrentIndex(index)
                
        if 'width' in settings:
            self.width_spin.setValue(settings['width'])
        if 'height' in settings:
            self.height_spin.setValue(settings['height'])
        if 'maintain_aspect' in settings:
            self.maintain_aspect_check.setChecked(settings['maintain_aspect'])
            
        if 'target_size_kb' in settings:
            self.optimize_size_check.setChecked(True)
            self.target_size_spin.setValue(settings['target_size_kb'])
            if 'min_size_kb' in settings:
                self.min_size_spin.setValue(settings['min_size_kb'])
            if 'max_size_kb' in settings:
                self.max_size_spin.setValue(settings['max_size_kb'])
        else:
            self.optimize_size_check.setChecked(False)
            
        if 'format' in settings:
            index = self.format_combo.findData(settings['format'])
            if index >= 0:
                self.format_combo.setCurrentIndex(index)
                
        if 'quality' in settings:
            self.quality_slider.setValue(settings['quality'])
            
        if 'prefix' in settings:
            self.prefix_edit.setText(settings['prefix'])
        if 'suffix' in settings:
            self.suffix_edit.setText(settings['suffix'])
            
    def delete_custom_preset(self):
        """Delete selected custom preset."""
        preset_name = self.custom_preset_combo.currentText()
        if not preset_name or preset_name not in self.custom_presets:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the preset '{preset_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.custom_presets[preset_name]
            self.save_custom_presets()
            self.update_custom_presets_combo()
            
    def update_custom_presets_combo(self):
        """Update the custom presets combo box."""
        self.custom_preset_combo.clear()
        self.custom_preset_combo.addItems(sorted(self.custom_presets.keys()))
        
    def import_presets(self):
        """Import presets from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Presets",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                imported = json.load(f)
                
            # Merge with existing presets
            self.custom_presets.update(imported)
            self.save_custom_presets()
            self.update_custom_presets_combo()
            
            QMessageBox.information(
                self,
                "Success",
                f"Imported {len(imported)} presets successfully."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import presets: {str(e)}"
            )
            
    def export_presets(self):
        """Export presets to a file."""
        if not self.custom_presets:
            QMessageBox.warning(
                self,
                "No Presets",
                "No custom presets to export."
            )
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Presets",
            str(Path.home() / "footfix_presets.json"),
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w') as f:
                json.dump(self.custom_presets, f, indent=2)
                
            QMessageBox.information(
                self,
                "Success",
                f"Exported {len(self.custom_presets)} presets successfully."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export presets: {str(e)}"
            )