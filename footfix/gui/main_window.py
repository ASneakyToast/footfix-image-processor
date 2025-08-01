"""
Main window for the FootFix application.
Provides the primary user interface for image processing.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog,
    QMessageBox, QGroupBox, QLineEdit, QTextEdit,
    QProgressBar, QTabWidget, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QPixmap, QPalette

from ..core.processor import ImageProcessor
from ..presets.profiles import PRESET_REGISTRY, get_preset, PresetConfig
from .batch_widget import BatchProcessingWidget
from .preview_widget import PreviewWidget
from .settings_dialog import AdvancedSettingsDialog

logger = logging.getLogger(__name__)


class ProcessingThread(QThread):
    """Thread for processing images without blocking the UI."""
    progress = Signal(int)
    status = Signal(str)
    finished_processing = Signal(bool, str)
    
    def __init__(self, processor: ImageProcessor, preset_name: str, output_path: str):
        super().__init__()
        self.processor = processor
        self.preset_name = preset_name
        self.output_path = output_path
        
    def run(self):
        """Run the image processing."""
        try:
            self.status.emit("Applying preset...")
            self.progress.emit(30)
            
            preset = get_preset(self.preset_name)
            if not preset:
                self.finished_processing.emit(False, f"Preset '{self.preset_name}' not found")
                return
                
            if not preset.process(self.processor):
                self.finished_processing.emit(False, "Failed to apply preset")
                return
                
            self.progress.emit(60)
            self.status.emit("Saving image...")
            
            output_config = preset.get_output_config()
            if self.processor.save_image(self.output_path, output_config):
                self.progress.emit(100)
                self.finished_processing.emit(True, f"Image saved to: {self.output_path}")
            else:
                self.finished_processing.emit(False, "Failed to save image")
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.finished_processing.emit(False, str(e))


class MainWindow(QMainWindow):
    """Main application window for FootFix."""
    
    def __init__(self):
        super().__init__()
        self.processor = ImageProcessor()
        self.current_image_path: Optional[Path] = None
        self.output_folder = Path.home() / "Downloads"
        self.processing_thread: Optional[ProcessingThread] = None
        self.preview_window = None
        self.custom_settings = None  # Store custom settings from advanced dialog
        
        self.setup_ui()
        self.setup_logging()
        
    def setup_ui(self):
        """Set up the user interface."""
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
        
        subtitle_label = QLabel("Batch Image Processor for Editorial Teams")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # Create tab widget for single and batch processing
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Single processing tab
        single_tab = QWidget()
        single_layout = QVBoxLayout(single_tab)
        self.tab_widget.addTab(single_tab, "Single Image")
        
        # Batch processing tab
        self.batch_widget = BatchProcessingWidget()
        self.batch_widget.processing_completed.connect(self.on_batch_completed)
        self.tab_widget.addTab(self.batch_widget, "Batch Processing")
        
        # File selection area
        file_group = QGroupBox("Image Selection")
        file_layout = QVBoxLayout()
        
        # Drag and drop area
        self.drop_area = QLabel("Drag and drop an image here\nor click 'Select Image' below")
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setMinimumHeight(150)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f0f0f0;
            }
        """)
        file_layout.addWidget(self.drop_area)
        
        # File selection button
        select_button = QPushButton("Select Image")
        select_button.clicked.connect(self.select_image)
        file_layout.addWidget(select_button)
        
        # Selected file display
        self.selected_file_label = QLabel("No image selected")
        self.selected_file_label.setAlignment(Qt.AlignCenter)
        file_layout.addWidget(self.selected_file_label)
        
        file_group.setLayout(file_layout)
        single_layout.addWidget(file_group)
        
        # Preset selection
        preset_group = QGroupBox("Processing Options")
        preset_layout = QVBoxLayout()
        
        # Preset dropdown
        preset_h_layout = QHBoxLayout()
        preset_h_layout.addWidget(QLabel("Preset:"))
        
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
        
        # Connect to show description on hover
        self.preset_combo.currentIndexChanged.connect(self.update_preset_description)
        
        preset_h_layout.addWidget(self.preset_combo, 1)
        
        # Advanced settings button
        self.advanced_button = QPushButton("Advanced...")
        self.advanced_button.clicked.connect(self.show_advanced_settings)
        preset_h_layout.addWidget(self.advanced_button)
        
        preset_layout.addLayout(preset_h_layout)
        
        # Preset description
        self.preset_description = QLabel()
        self.preset_description.setWordWrap(True)
        self.preset_description.setStyleSheet("color: #666; padding: 5px;")
        preset_layout.addWidget(self.preset_description)
        
        # Initialize with first preset description
        self.update_preset_description(0)
        
        # Output folder selection
        output_h_layout = QHBoxLayout()
        output_h_layout.addWidget(QLabel("Output Folder:"))
        
        self.output_folder_edit = QLineEdit(str(self.output_folder))
        self.output_folder_edit.setReadOnly(True)
        output_h_layout.addWidget(self.output_folder_edit, 1)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.select_output_folder)
        output_h_layout.addWidget(browse_button)
        
        preset_layout.addLayout(output_h_layout)
        
        preset_group.setLayout(preset_layout)
        single_layout.addWidget(preset_group)
        
        # Process buttons
        process_button_layout = QHBoxLayout()
        
        # Preview button
        self.preview_button = QPushButton("Preview")
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
        process_button_layout.addWidget(self.preview_button)
        
        # Process button
        self.process_button = QPushButton("Process Image")
        self.process_button.clicked.connect(self.process_image)
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
        process_button_layout.addWidget(self.process_button)
        
        single_layout.addLayout(process_button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        single_layout.addWidget(self.progress_bar)
        
        # Status/Log area
        log_group = QGroupBox("Status")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
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
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any URL is a valid image or directory
            for url in event.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.is_dir() or path.suffix.lower() in ImageProcessor.SUPPORTED_FORMATS:
                    event.acceptProposedAction()
                    # Visual feedback
                    self.drop_area.setStyleSheet("""
                        QLabel {
                            border: 2px solid #007AFF;
                            border-radius: 10px;
                            padding: 20px;
                            background-color: #e6f2ff;
                        }
                    """)
                    return
            
    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        # Reset visual feedback
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f0f0f0;
            }
        """)
        
        urls = event.mimeData().urls()
        if not urls:
            return
            
        # Collect all valid image paths
        image_paths = []
        
        for url in urls:
            path = Path(url.toLocalFile())
            
            if path.is_file() and path.suffix.lower() in ImageProcessor.SUPPORTED_FORMATS:
                image_paths.append(path)
            elif path.is_dir():
                # Add all images from directory
                for img_path in path.rglob('*'):
                    if img_path.is_file() and img_path.suffix.lower() in ImageProcessor.SUPPORTED_FORMATS:
                        image_paths.append(img_path)
                        
        if not image_paths:
            QMessageBox.warning(
                self,
                "No Valid Images",
                "No valid image files were found in the dropped items."
            )
            return
            
        # Handle based on number of images
        if len(image_paths) == 1:
            # Single image - load in single processing tab
            self.load_image(str(image_paths[0]))
            self.tab_widget.setCurrentIndex(0)  # Switch to single tab
        else:
            # Multiple images - add to batch queue
            added = self.batch_widget.add_images_to_queue(image_paths)
            if added > 0:
                self.tab_widget.setCurrentIndex(1)  # Switch to batch tab
                QMessageBox.information(
                    self,
                    "Images Added",
                    f"Added {added} images to batch processing queue."
                )
            
    def select_image(self):
        """Open file dialog to select an image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            str(Path.home()),
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif)"
        )
        
        if file_path:
            self.load_image(file_path)
            
    def load_image(self, file_path: str):
        """Load an image into the processor."""
        path = Path(file_path)
        
        if self.processor.load_image(path):
            self.current_image_path = path
            self.selected_file_label.setText(f"Selected: {path.name}")
            self.process_button.setEnabled(True)
            self.preview_button.setEnabled(True)
            
            # Update drop area with image info
            info = self.processor.get_image_info()
            self.drop_area.setText(
                f"Image loaded: {path.name}\n"
                f"Size: {info.get('size_pixels', 'Unknown')}\n"
                f"Format: {info.get('format', 'Unknown')}"
            )
            
            logger.info(f"Image loaded: {path.name}")
        else:
            QMessageBox.warning(
                self,
                "Invalid Image",
                f"Could not load image: {path.name}\n"
                "Please ensure the file is a valid image format."
            )
            
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
            
    def process_image(self):
        """Process the currently loaded image with selected preset."""
        if not self.current_image_path:
            return
            
        # Get selected preset
        preset_name = self.preset_combo.currentData()
        preset = get_preset(preset_name)
        
        if not preset:
            QMessageBox.critical(self, "Error", "Invalid preset selected")
            return
            
        # Generate output filename
        output_filename = preset.get_suggested_filename(self.current_image_path)
        output_path = self.output_folder / output_filename
        
        # Disable UI during processing
        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start processing in thread
        self.processing_thread = ProcessingThread(
            self.processor,
            preset_name,
            str(output_path)
        )
        
        self.processing_thread.progress.connect(self.progress_bar.setValue)
        self.processing_thread.status.connect(lambda msg: logger.info(msg))
        self.processing_thread.finished_processing.connect(self.on_processing_finished)
        
        self.processing_thread.start()
        
    def on_processing_finished(self, success: bool, message: str):
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        
        if success:
            logger.info(message)
            QMessageBox.information(
                self,
                "Success",
                f"Image processed successfully!\n{message}"
            )
        else:
            logger.error(message)
            QMessageBox.critical(
                self,
                "Processing Failed",
                f"Failed to process image:\n{message}"
            )
            
    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        # Reset visual feedback
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f0f0f0;
            }
        """)
        
    def on_batch_completed(self, results: dict):
        """Handle batch processing completion."""
        logger.info(f"Batch processing completed: {results}")
        
    def show_preview(self):
        """Show the preview window for the current image and preset."""
        if not self.current_image_path or not self.processor.current_image:
            return
            
        # Get selected preset
        preset_name = self.preset_combo.currentData()
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
            
        # Process the image
        self.process_image()
        
    def on_preview_adjust(self):
        """Handle adjust settings from preview."""
        # Close preview and show advanced settings
        if self.preview_window:
            self.preview_window.close()
            
        self.show_advanced_settings()
        
    def show_advanced_settings(self):
        """Show the advanced settings dialog."""
        # Get current preset config
        preset_name = self.preset_combo.currentData()
        preset = get_preset(preset_name)
        preset_config = preset.get_config() if preset else None
        
        # Create and show dialog
        dialog = AdvancedSettingsDialog(self, preset_config)
        dialog.settings_applied.connect(self.on_custom_settings_applied)
        
        if dialog.exec() == QDialog.Accepted:
            self.custom_settings = dialog.get_settings()
            logger.info(f"Custom settings applied: {self.custom_settings}")
            
            # Update UI to indicate custom settings are active
            self.preset_combo.setItemText(
                self.preset_combo.currentIndex(),
                f"{self.preset_combo.itemText(self.preset_combo.currentIndex())} (Modified)"
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
        
    def update_preset_description(self, index: int):
        """Update the preset description label."""
        tooltip = self.preset_combo.itemData(index, Qt.ToolTipRole)
        if tooltip:
            self.preset_description.setText(tooltip.replace('\n', ' '))