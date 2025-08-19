"""
Main window for the FootFix application.
Provides the primary user interface for image processing.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFileDialog,
    QMessageBox, QGroupBox, QTextEdit, QDialog, QApplication,
    QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..core.processor import ImageProcessor
from ..presets.profiles import get_preset, PresetConfig
from ..utils.preferences import PreferencesManager
from ..utils.notifications import NotificationManager
from .unified_widget import UnifiedProcessingWidget
from .alt_text_widget import AltTextWidget
from .tag_widget import TagWidget
from .metadata_export_widget import MetadataExportWidget
from .preview_widget import PreviewWidget
from .settings_dialog import AdvancedSettingsDialog
from .menu_bar import MenuBarManager
from .output_settings_dialog import OutputSettingsDialog
from .preferences_window import PreferencesWindow

logger = logging.getLogger(__name__)



class MainWindow(QMainWindow):
    """Main application window for FootFix."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize preferences first (use singleton)
        self.prefs_manager = PreferencesManager.get_instance()
        
        self.processor = ImageProcessor(self.prefs_manager)
        self.current_image_path: Optional[Path] = None
        self.preview_window = None
        self.custom_settings = None  # Store custom settings from advanced dialog
        self.load_preferences()
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_logging()
        self.setup_preference_connections()
        self.restore_window_state()
        
    def setup_ui(self):
        """Set up the unified user interface."""
        self.setWindowTitle("FootFix - Image Processor")
        self.setMinimumSize(900, 700)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("FootFix")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Universal Image Processor for Editorial Teams")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Processing tab
        self.unified_widget = UnifiedProcessingWidget()
        self.unified_widget.processing_completed.connect(self.on_batch_completed)
        self.unified_widget.image_loaded.connect(self.on_image_loaded)
        self.unified_widget.queue_changed.connect(self.on_queue_changed)
        self.tab_widget.addTab(self.unified_widget, "Processing")
        
        # Alt Text tab  
        self.alt_text_widget = AltTextWidget()
        self.alt_text_widget.alt_text_updated.connect(self.on_alt_text_updated)
        self.alt_text_widget.regenerate_requested.connect(self.on_regenerate_requested)
        self.tab_widget.addTab(self.alt_text_widget, "Alt Text Review")
        
        # Tag Management tab
        self.tag_widget = TagWidget()
        self.tag_widget.tag_updated.connect(self.on_tags_updated)
        self.tag_widget.tag_assignment_requested.connect(self.on_tag_assignment_requested)
        self.tab_widget.addTab(self.tag_widget, "Tag Management")
        
        # Metadata Export tab
        self.metadata_export_widget = MetadataExportWidget()
        self.tab_widget.addTab(self.metadata_export_widget, "Metadata Export")
        
        # Status/Log area
        log_group = QGroupBox("Status")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Note: Drag and drop is now handled by the unified widget
        
    def setup_menu_bar(self):
        """Set up the application menu bar."""
        self.menu_manager = MenuBarManager(self)
        
        # Connect menu signals
        self.menu_manager.open_file.connect(self.unified_widget.add_images)
        self.menu_manager.open_folder.connect(self.unified_widget.add_folder)
        self.menu_manager.save_as.connect(self.save_as)
        self.menu_manager.show_preferences.connect(self.show_preferences)
        self.menu_manager.quit_app.connect(QApplication.quit)
        
        self.menu_manager.show_preview.connect(self.unified_widget.show_preview)
        self.menu_manager.toggle_fullscreen.connect(self.toggle_fullscreen)
        
        self.menu_manager.show_help.connect(self.show_help)
        self.menu_manager.show_shortcuts.connect(self.show_shortcuts)
        self.menu_manager.show_about.connect(self.show_about)
        
    def setup_logging(self):
        """Set up logging to display in the GUI."""
        # Create a custom handler that writes to our text widget
        class GuiLogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.append(msg)
                
        gui_handler = GuiLogHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Add handler to our logger
        logger.addHandler(gui_handler)
        logger.setLevel(logging.INFO)
        
    def setup_preference_connections(self):
        """Set up connections to preference change signals."""
        # Connect to preference change signals
        self.prefs_manager.preferences_changed.connect(self.on_preference_changed)
        self.prefs_manager.preferences_reloaded.connect(self.on_preferences_reloaded)
        logger.info("Connected to preference change signals")
        
    def on_preference_changed(self, key: str):
        """Handle individual preference changes."""
        logger.debug(f"Preference changed: {key}")
        
        # Handle specific preference changes
        if key.startswith('output.'):
            self.load_preferences()
        elif key.startswith('interface.'):
            # Apply interface preferences
            show_tooltips = self.prefs_manager.get('interface.show_tooltips', True)
            if not show_tooltips:
                # Disable tooltips (would need to implement tooltip management)
                pass
        elif key.startswith('alt_text.'):
            # Refresh alt text availability in unified widget
            if hasattr(self, 'unified_widget'):
                self.unified_widget.refresh_alt_text_availability()
                
    def on_preferences_reloaded(self):
        """Handle complete preference reload."""
        logger.info("Preferences reloaded - updating all UI elements")
        self.load_preferences()
        
        # Update UI elements
        self.menu_manager._update_recent_files(self.recent_files)
        
        # Refresh alt text availability in unified widget
        if hasattr(self, 'unified_widget'):
            self.unified_widget.refresh_alt_text_availability()
            
        # Apply interface preferences
        show_tooltips = self.prefs_manager.get('interface.show_tooltips', True)
        if not show_tooltips:
            # Disable tooltips (would need to implement tooltip management)
            pass
            
    def on_image_loaded(self, image_path: str):
        """Handle image loaded signal from unified widget (for single image compatibility)."""
        # Update current image path for menu actions and other compatibility
        self.current_image_path = Path(image_path)
        
        # Update menu bar actions
        self.menu_manager.enable_image_actions(True)
        
        # Update recent files in preferences
        self.prefs_manager.update_recent('files', str(self.current_image_path))
        self.recent_files = self.prefs_manager.get('recent.files', [])
        self.menu_manager._update_recent_files(self.recent_files)
        self.prefs_manager.save()
        
        logger.info(f"Image loaded in unified interface: {self.current_image_path.name}")
        
        
    def on_batch_completed(self, results: dict):
        """Handle batch processing completion."""
        logger.info(f"Batch processing completed: {results}")
        # Update alt text widget with latest batch data
        self.alt_text_widget.set_batch_items(self.unified_widget.batch_processor.queue)
        # Update tag widget with latest batch data
        self.tag_widget.set_batch_items(self.unified_widget.batch_processor.queue)
        # Update metadata export widget with latest batch data
        self.metadata_export_widget.set_batch_items(self.unified_widget.batch_processor.queue)
        
    def on_alt_text_updated(self, updates: dict):
        """Handle alt text updates from the review tab."""
        # Forward updates to the unified widget
        self.unified_widget.on_alt_text_updated(updates)
        
    def on_regenerate_requested(self, filenames: list):
        """Handle regenerate requests from the review tab."""
        # Forward to the unified widget for processing
        self.unified_widget.on_regenerate_requested(filenames)
        
    def on_queue_changed(self, count: int):
        """Handle queue changes to keep tabs updated."""
        # Update alt text widget with current batch data
        self.alt_text_widget.set_batch_items(self.unified_widget.batch_processor.queue)
        # Update tag widget with current batch data
        self.tag_widget.set_batch_items(self.unified_widget.batch_processor.queue)
        # Update metadata export widget with current batch data
        self.metadata_export_widget.set_batch_items(self.unified_widget.batch_processor.queue)
        
    def on_tags_updated(self, updates: dict):
        """Handle tag updates from the tag management tab."""
        # Forward updates to the unified widget
        self.unified_widget.on_tags_updated(updates)
        
    def on_tag_assignment_requested(self, tags: list, filenames: list):
        """Handle tag assignment requests from the tag management tab."""
        # Forward to the unified widget for processing
        self.unified_widget.on_tag_assignment_requested(tags, filenames)
        
    def show_preview(self):
        """Show the preview window for the current image and preset."""
        if not self.current_image_path or not self.processor.current_image:
            return
            
        # Get selected preset from unified widget
        preset_name = self.unified_widget.preset_combo.currentData()
        preset = get_preset(preset_name)
        
        if not preset:
            QMessageBox.critical(self, "Error", "Invalid preset selected")
            return
            
        # Create preview window if it doesn't exist
        if not self.preview_window:
            self.preview_window = QWidget()
            self.preview_window.setWindowTitle("FootFix - Preview")
            self.preview_window.setMinimumSize(1000, 700)
            
            # Add preview widget
            layout = QVBoxLayout(self.preview_window)
            self.preview_widget = PreviewWidget()
            layout.addWidget(self.preview_widget)
            
            # Connect signals
            self.preview_widget.apply_settings.connect(self.on_preview_apply)
            self.preview_widget.adjust_settings.connect(self.on_preview_adjust)
            
        # Load image and preset into preview
        self.preview_widget.load_image(self.processor, preset)
        
        # Show the window
        self.preview_window.show()
        self.preview_window.raise_()
        self.preview_window.activateWindow()
        
    def on_preview_apply(self):
        """Handle apply settings from preview."""
        # Close preview window
        if self.preview_window:
            self.preview_window.close()
            
        # Start processing via unified widget
        self.unified_widget.start_processing()
        
    def on_preview_adjust(self):
        """Handle adjust settings from preview."""
        # Close preview and show advanced settings
        if self.preview_window:
            self.preview_window.close()
            
        self.show_advanced_settings()
        
    def show_advanced_settings(self):
        """Show the advanced settings dialog."""
        # Get current preset config from unified widget
        preset_name = self.unified_widget.preset_combo.currentData()
        preset = get_preset(preset_name)
        preset_config = preset.get_config() if preset else None
        
        # Create and show dialog
        dialog = AdvancedSettingsDialog(self, preset_config, self.prefs_manager)
        dialog.settings_applied.connect(self.on_custom_settings_applied)
        
        if dialog.exec() == QDialog.Accepted:
            self.custom_settings = dialog.get_settings()
            logger.info(f"Custom settings applied: {self.custom_settings}")
            
            # Update UI to indicate custom settings are active in unified widget
            current_text = self.unified_widget.preset_combo.currentText()
            if "(Modified)" not in current_text:
                self.unified_widget.preset_combo.setItemText(
                    self.unified_widget.preset_combo.currentIndex(),
                    f"{current_text} (Modified)"
                )
            
    def on_custom_settings_applied(self, settings: dict):
        """Handle custom settings from advanced dialog."""
        self.custom_settings = settings
        logger.info(f"Custom settings preview: {settings}")
        
        # If preview window is open, update it
        if self.preview_window and self.preview_window.isVisible():
            # Create a custom preset config from settings
            custom_config = self._create_custom_preset_config(settings)
            self.preview_widget.current_preset = custom_config
            self.preview_widget.generate_preview()
            
    def _create_custom_preset_config(self, settings: dict) -> PresetConfig:
        """Create a PresetConfig from custom settings."""
        config = PresetConfig(name="Custom")
        
        # Apply resize settings
        resize_mode = settings.get('resize_mode', 'fit')
        if resize_mode == 'exact':
            config.exact_width = settings.get('width')
            config.exact_height = settings.get('height')
            config.maintain_aspect = False
        elif resize_mode == 'fit':
            config.max_width = settings.get('width')
            config.max_height = settings.get('height')
            config.maintain_aspect = settings.get('maintain_aspect', True)
            
        # Apply format and quality
        config.format = settings.get('format', 'JPEG')
        config.quality = settings.get('quality', 85)
        
        # Apply file size settings
        if 'target_size_kb' in settings:
            config.target_size_kb = settings['target_size_kb']
            config.min_size_kb = settings.get('min_size_kb')
            config.max_size_kb = settings.get('max_size_kb')
            
        return config
        
                
    def save_as(self):
        """Save the processed image using the unified batch processing system."""
        if not self.current_image_path:
            return
            
        # Clear the queue and add the current image
        self.unified_widget.clear_queue()
        self.unified_widget.add_images_to_queue([self.current_image_path])
        
        # Start processing using the unified system (which now uses custom filename templates)
        self.unified_widget.start_processing()
            
        
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
            self.menu_manager.update_fullscreen_text(False)
        else:
            self.showFullScreen()
            self.menu_manager.update_fullscreen_text(True)
            
    def show_help(self):
        """Show the help documentation."""
        help_text = """
        <h2>FootFix Help</h2>
        
        <h3>Getting Started</h3>
        <p>FootFix is a professional image processor designed for editorial teams with a unified interface that adapts to your workflow.</p>
        
        <h3>Processing Images</h3>
        <ol>
        <li>Drag and drop images anywhere on the interface or use "Add Images" button</li>
        <li>Add more images as needed - the interface adapts automatically</li>
        <li>Choose a preset or adjust settings</li>
        <li>Click "Process Image" or "Process X Images" to save</li>
        </ol>
        
        <h3>Smart Queue</h3>
        <p>The unified queue handles any number of images - from one to hundreds. Start with a single image and add more, or start with a batch. The interface adapts automatically.</p>
        
        <h3>Keyboard Shortcuts</h3>
        <p>Press Cmd+? to see all keyboard shortcuts.</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("FootFix Help")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.exec()
        
    def show_shortcuts(self):
        """Show keyboard shortcuts reference."""
        shortcuts_text = """
        <h2>Keyboard Shortcuts</h2>
        
        <h3>File Operations</h3>
        <table>
        <tr><td><b>Cmd+O</b></td><td>Add images to queue</td></tr>
        <tr><td><b>Cmd+Shift+O</b></td><td>Add folder to queue</td></tr>
        <tr><td><b>Cmd+Shift+S</b></td><td>Save as...</td></tr>
        <tr><td><b>Cmd+Q</b></td><td>Quit</td></tr>
        </table>
        
        <h3>View</h3>
        <table>
        <tr><td><b>Space</b></td><td>Show preview</td></tr>
        <tr><td><b>Cmd+Ctrl+F</b></td><td>Toggle fullscreen</td></tr>
        </table>
        
        <h3>Edit</h3>
        <table>
        <tr><td><b>Cmd+,</b></td><td>Preferences</td></tr>
        <tr><td><b>Cmd+A</b></td><td>Select all</td></tr>
        <tr><td><b>Cmd+C</b></td><td>Copy</td></tr>
        <tr><td><b>Cmd+V</b></td><td>Paste</td></tr>
        </table>
        
        <h3>Recent Files</h3>
        <table>
        <tr><td><b>Cmd+1-9</b></td><td>Open recent file</td></tr>
        </table>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setTextFormat(Qt.RichText)
        msg.setText(shortcuts_text)
        msg.exec()
        
    def show_about(self):
        """Show about dialog."""
        about_text = """
        <h2>FootFix</h2>
        <p><b>Version 1.0.0</b></p>
        <p>Professional image processor for editorial teams.</p>
        <br>
        <p>Optimized for:</p>
        <ul>
        <li>Web content optimization</li>
        <li>Email attachments</li>
        <li>Social media formats</li>
        <li>Batch processing</li>
        </ul>
        <br>
        <p>© 2024 FootFix. All rights reserved.</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About FootFix")
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.exec()
        
    def keyPressEvent(self, event):
        """Handle key press events."""
        # Space key for preview
        if event.key() == Qt.Key_Space and self.unified_widget.preview_button.isEnabled():
            self.unified_widget.show_preview()
            event.accept()
        else:
            super().keyPressEvent(event)
            
    def show_output_settings(self):
        """Show the output settings dialog."""
        dialog = OutputSettingsDialog(self, self.unified_widget.output_settings)
        
        # Connect to dialog's settings changed signal
        dialog.settings_changed.connect(self.on_output_settings_changed)
        
        if dialog.exec() == QDialog.Accepted:
            # Settings are already saved to preferences by the dialog
            # Just update the unified widget to reflect the changes
            self.unified_widget.load_preferences()
            
            # Reset filename template counter for new batch
            self.unified_widget.filename_template.reset_counter()
            
            logger.info(f"Output settings updated and saved to preferences")
            
    def on_output_settings_changed(self, settings):
        """Handle output settings changes from the dialog."""
        # Update the unified widget's UI to reflect the changes
        self.unified_widget.output_folder_edit.setText(str(settings['output_folder']))
        logger.info(f"Output settings UI updated: {settings}")
            
    def load_preferences(self):
        """Load preferences from the preferences manager."""
        # Only load preferences needed by main window - unified widget handles its own
        self.recent_files = self.prefs_manager.get('recent.files', [])
        
    def restore_window_state(self):
        """Restore window geometry and state from preferences."""
        geometry = self.prefs_manager.get('interface.window_geometry')
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
            except:
                pass
                
        state = self.prefs_manager.get('interface.window_state')
        if state:
            try:
                self.restoreState(bytes.fromhex(state))
            except:
                pass
                
    def save_window_state(self):
        """Save window geometry and state to preferences."""
        self.prefs_manager.set('interface.window_geometry', self.saveGeometry().toHex().data().decode())
        self.prefs_manager.set('interface.window_state', self.saveState().toHex().data().decode())
        self.prefs_manager.save()
        
    def closeEvent(self, event):
        """Handle window close event."""
        self.save_window_state()
        super().closeEvent(event)
        
    def show_preferences(self):
        """Show the preferences window."""
        logger.info("Opening preferences window")
        prefs_window = PreferencesWindow(self)
        
        # Connect the signal before showing the dialog
        prefs_window.preferences_changed.connect(self.on_preferences_dialog_changed)
        logger.info("Connected preferences_changed signal to on_preferences_dialog_changed")
        
        # Show the dialog (exec blocks until dialog is closed)
        result = prefs_window.exec()
        logger.info(f"Preferences dialog closed with result: {result} (Accepted={QDialog.Accepted})")
        
        # Note: We don't need to call on_preferences_dialog_changed here because
        # it should be called via the signal when Apply or OK is clicked
            
    def on_preferences_dialog_changed(self):
        """Handle preferences changes from the preferences dialog (legacy method)."""
        logger.info("on_preferences_dialog_changed called - triggering preference reload")
        
        # Force reload from disk to pick up any changes
        self.prefs_manager.reload_from_disk()
        
        logger.info("Preferences dialog changes processed")