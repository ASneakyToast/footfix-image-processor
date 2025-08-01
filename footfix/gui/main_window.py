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
    QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QPixmap

from ..core.processor import ImageProcessor
from ..presets.profiles import PRESET_REGISTRY, get_preset

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
        
        self.setup_ui()
        self.setup_logging()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("FootFix - Image Processor")
        self.setMinimumSize(800, 600)
        
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
        main_layout.addWidget(file_group)
        
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
        preset_h_layout.addWidget(self.preset_combo, 1)
        
        preset_layout.addLayout(preset_h_layout)
        
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
        main_layout.addWidget(preset_group)
        
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
        main_layout.addWidget(self.process_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
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
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.load_image(file_path)
            
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