#!/usr/bin/env python3
"""
Phase 2 Hacker-style QML interface for FootFix.
Enhanced with preset selection, progress visualization, drag-and-drop,
and retro-futuristic image preview capabilities.
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtQml import qmlRegisterType, QQmlApplicationEngine
from PySide6.QtCore import QObject, QUrl, Signal, Slot, Property, QTimer
from PySide6.QtQuick import QQuickView

# Import the core processor
from ..core.processor import ImageProcessor
from ..utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


class HackerUIController(QObject):
    """
    Enhanced QML-Python bridge for the Phase 2 hacker interface.
    Adds progress tracking, preset management, and enhanced feedback.
    """
    
    # Signals for QML
    imageLoaded = Signal(str)  # image path
    processingStarted = Signal()
    processingProgress = Signal(float)  # 0.0 to 1.0
    processingFinished = Signal(bool, str)  # success, message
    statusUpdate = Signal(str)  # status message
    
    def __init__(self):
        super().__init__()
        self.processor = ImageProcessor()
        self.current_image_path = None
        
        # Progress simulation timer
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self.current_progress = 0.0
        self.progress_increment = 0.0
        
    @Slot(str)
    def selectImage(self, file_path: str):
        """Handle image selection from QML."""
        try:
            # Handle file:// URLs
            if file_path.startswith("file://"):
                file_path = file_path[7:]
            
            path = Path(file_path)
            if self.processor.load_image(path):
                self.current_image_path = path
                self.imageLoaded.emit(str(path))
                self.statusUpdate.emit(f"> Image analysis complete: {path.name}")
                self.statusUpdate.emit(f"> Dimensions: {self._get_image_dimensions()}")
                self.statusUpdate.emit(f"> File size: {self._get_file_size()}")
                logger.info(f"Image loaded: {path.name}")
            else:
                self.statusUpdate.emit(f"> ERROR: Failed to load {path.name}")
                logger.error(f"Failed to load image: {path.name}")
        except Exception as e:
            self.statusUpdate.emit(f"> ERROR: {str(e)}")
            logger.error(f"Image selection error: {e}")
    
    @Slot(str)
    def processImage(self, preset_name: str = "editorial_web"):
        """Handle image processing from QML with progress tracking."""
        if not self.current_image_path:
            self.statusUpdate.emit("> ERROR: No image selected")
            return
            
        try:
            self.processingStarted.emit()
            self.statusUpdate.emit(f"> Initializing {preset_name.upper()} processing protocol...")
            
            # Start progress simulation
            self.current_progress = 0.0
            self.progress_increment = 0.02  # 2% increments
            self.progress_timer.start(100)  # Update every 100ms
            
            # Import preset functionality
            from ..presets.profiles import get_preset
            
            preset = get_preset(preset_name)
            if not preset:
                self._finish_processing(False, f"Preset '{preset_name}' not found")
                return
            
            # Simulate processing phases
            QTimer.singleShot(500, lambda: self.statusUpdate.emit("> Analyzing image parameters..."))
            QTimer.singleShot(1000, lambda: self.statusUpdate.emit("> Applying preset transformations..."))
            QTimer.singleShot(1500, lambda: self.statusUpdate.emit("> Optimizing file size..."))
            QTimer.singleShot(2000, lambda: self._execute_processing(preset))
            
        except Exception as e:
            self._finish_processing(False, f"Processing error: {str(e)}")
            logger.error(f"Processing error: {e}")
    
    def _execute_processing(self, preset):
        """Execute the actual image processing."""
        try:
            # Apply preset
            if preset.process(self.processor):
                # Generate output path
                output_path = Path.home() / "Downloads" / f"processed_{self.current_image_path.name}"
                
                # Save image
                output_config = preset.get_output_config()
                if self.processor.save_image(str(output_path), output_config):
                    self.statusUpdate.emit("> Writing processed data to disk...")
                    QTimer.singleShot(500, lambda: self._finish_processing(True, f"Image saved to: {output_path}"))
                else:
                    self._finish_processing(False, "Failed to save image")
            else:
                self._finish_processing(False, "Failed to apply preset")
        except Exception as e:
            self._finish_processing(False, f"Processing execution error: {str(e)}")
    
    def _update_progress(self):
        """Update processing progress simulation."""
        self.current_progress += self.progress_increment
        
        # Slow down as we approach completion
        if self.current_progress > 0.7:
            self.progress_increment = 0.01
        elif self.current_progress > 0.9:
            self.progress_increment = 0.005
            
        if self.current_progress >= 1.0:
            self.current_progress = 1.0
            self.progress_timer.stop()
            
        self.processingProgress.emit(self.current_progress)
    
    def _finish_processing(self, success: bool, message: str):
        """Finish processing and emit completion signal."""
        self.progress_timer.stop()
        self.current_progress = 1.0 if success else 0.0
        self.processingProgress.emit(self.current_progress)
        self.processingFinished.emit(success, message)
        
        if success:
            self.statusUpdate.emit("> Processing protocol completed successfully")
            logger.info(f"Processing completed: {message}")
        else:
            self.statusUpdate.emit(f"> Processing protocol failed: {message}")
            logger.error(f"Processing failed: {message}")
    
    @Slot()
    def showFileDialog(self):
        """Show file selection dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Image File - FootFix Hacker Interface",
            str(Path.home()),
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif);;All Files (*.*)"
        )
        
        if file_path:
            self.selectImage(file_path)
        else:
            self.statusUpdate.emit("> File selection cancelled by user")

    @Slot()
    def showSettings(self):
        """Handle settings dialog from QML."""
        self.statusUpdate.emit("> Accessing configuration database...")
        # TODO: Implement settings dialog
        logger.info("Settings requested")
    
    @Slot(result=str)
    def getImageInfo(self):
        """Get current image information for QML display."""
        if self.processor.current_image and self.current_image_path:
            info = self.processor.get_image_info()
            return (f"File: {self.current_image_path.name}\n"
                   f"Size: {info.get('size_pixels', 'Unknown')}\n"
                   f"Format: {info.get('format', 'Unknown')}\n"
                   f"File Size: {self._get_file_size()}")
        return "No image loaded\nAwaiting input..."
    
    def _get_image_dimensions(self):
        """Get image dimensions as string."""
        if self.processor.current_image:
            return f"{self.processor.current_image.width}×{self.processor.current_image.height}"
        return "Unknown"
    
    def _get_file_size(self):
        """Get file size as formatted string."""
        if self.current_image_path and self.current_image_path.exists():
            size_bytes = self.current_image_path.stat().st_size
            if size_bytes < 1024:
                return f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        return "Unknown"


def main():
    """Run the Phase 2 hacker interface."""
    # Set up logging
    setup_logging(log_level=logging.INFO, log_to_file=True)
    logger = logging.getLogger(__name__)
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Set application metadata
        app.setApplicationName("FootFix Hacker UI Phase 2")
        app.setOrganizationName("FootFix")
        app.setApplicationDisplayName("FootFix - Advanced Hacker Interface")
        
        # Create QML engine
        engine = QQmlApplicationEngine()
        
        # Register our controller with QML
        controller = HackerUIController()
        engine.rootContext().setContextProperty("hackerController", controller)
        
        # Load QML file
        qml_file = Path(__file__).parent / "HackerMainPhase2.qml"
        engine.load(QUrl.fromLocalFile(str(qml_file)))
        
        if not engine.rootObjects():
            logger.error("Failed to load QML file")
            sys.exit(1)
        
        logger.info("Phase 2 hacker interface started successfully")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()