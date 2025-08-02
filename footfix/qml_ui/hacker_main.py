#!/usr/bin/env python3
"""
Hacker-style QML interface prototype for FootFix.
This demonstrates the movie hacker aesthetic with irregular layouts,
animated backgrounds, and custom styling effects.
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtQml import qmlRegisterType, QQmlApplicationEngine
from PySide6.QtCore import QObject, QUrl, Signal, Slot, Property
from PySide6.QtQuick import QQuickView

# Import the core processor
from ..core.processor import ImageProcessor
from ..utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


class HackerUIController(QObject):
    """
    QML-Python bridge for the hacker interface.
    Connects QML UI events to the core image processing logic.
    """
    
    # Signals for QML
    imageLoaded = Signal(str)  # image path
    processingStarted = Signal()
    processingFinished = Signal(bool, str)  # success, message
    statusUpdate = Signal(str)  # status message
    
    def __init__(self):
        super().__init__()
        self.processor = ImageProcessor()
        self.current_image_path = None
        
    @Slot(str)
    def selectImage(self, file_path: str):
        """Handle image selection from QML."""
        try:
            path = Path(file_path)
            if self.processor.load_image(path):
                self.current_image_path = path
                self.imageLoaded.emit(str(path))
                self.statusUpdate.emit(f"> Image loaded: {path.name}")
                logger.info(f"Image loaded: {path.name}")
            else:
                self.statusUpdate.emit(f"> ERROR: Failed to load {path.name}")
                logger.error(f"Failed to load image: {path.name}")
        except Exception as e:
            self.statusUpdate.emit(f"> ERROR: {str(e)}")
            logger.error(f"Image selection error: {e}")
    
    @Slot(str)
    def processImage(self, preset_name: str = "editorial_web"):
        """Handle image processing from QML."""
        if not self.current_image_path:
            self.statusUpdate.emit("> ERROR: No image selected")
            return
            
        try:
            self.processingStarted.emit()
            self.statusUpdate.emit("> Processing image...")
            
            # Import preset functionality
            from ..presets.profiles import get_preset
            
            preset = get_preset(preset_name)
            if not preset:
                self.statusUpdate.emit(f"> ERROR: Preset '{preset_name}' not found")
                self.processingFinished.emit(False, f"Preset '{preset_name}' not found")
                return
            
            # Apply preset
            if preset.process(self.processor):
                # Generate output path
                output_path = Path.home() / "Downloads" / f"processed_{self.current_image_path.name}"
                
                # Save image
                output_config = preset.get_output_config()
                if self.processor.save_image(str(output_path), output_config):
                    self.statusUpdate.emit(f"> SUCCESS: Image saved to {output_path.name}")
                    self.processingFinished.emit(True, f"Image saved to: {output_path}")
                    logger.info(f"Image processed successfully: {output_path}")
                else:
                    self.statusUpdate.emit("> ERROR: Failed to save image")
                    self.processingFinished.emit(False, "Failed to save image")
            else:
                self.statusUpdate.emit("> ERROR: Failed to apply preset")
                self.processingFinished.emit(False, "Failed to apply preset")
                
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            self.statusUpdate.emit(f"> ERROR: {error_msg}")
            self.processingFinished.emit(False, error_msg)
            logger.error(f"Processing error: {e}")
    
    @Slot()
    def showFileDialog(self):
        """Show file selection dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Image File",
            str(Path.home()),
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif);;All Files (*.*)"
        )
        
        if file_path:
            self.selectImage(file_path)
        else:
            self.statusUpdate.emit("> File selection cancelled")

    @Slot()
    def showSettings(self):
        """Handle settings dialog from QML."""
        self.statusUpdate.emit("> Opening settings...")
        # TODO: Implement settings dialog
        logger.info("Settings requested")
    
    @Slot(result=str)
    def getImageInfo(self):
        """Get current image information for QML display."""
        if self.processor.current_image and self.current_image_path:
            info = self.processor.get_image_info()
            return f"Size: {info.get('size_pixels', 'Unknown')} | Format: {info.get('format', 'Unknown')}"
        return "No image loaded"


def main():
    """Run the hacker interface prototype."""
    # Set up logging
    setup_logging(log_level=logging.INFO, log_to_file=True)
    logger = logging.getLogger(__name__)
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Set application metadata
        app.setApplicationName("FootFix Hacker UI")
        app.setOrganizationName("FootFix")
        app.setApplicationDisplayName("FootFix - Hacker Interface Prototype")
        
        # Create QML engine
        engine = QQmlApplicationEngine()
        
        # Register our controller with QML
        controller = HackerUIController()
        engine.rootContext().setContextProperty("hackerController", controller)
        
        # Load QML file
        qml_file = Path(__file__).parent / "HackerMain.qml"
        engine.load(QUrl.fromLocalFile(str(qml_file)))
        
        if not engine.rootObjects():
            logger.error("Failed to load QML file")
            sys.exit(1)
        
        logger.info("Hacker interface prototype started successfully")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()