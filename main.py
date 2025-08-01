#!/usr/bin/env python3
"""
FootFix - Image Processing Desktop Application
Main entry point for the application.
"""

import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from footfix.gui.main_window import MainWindow
from footfix.utils.logging_config import setup_logging


def main():
    """Main application entry point."""
    # Set up logging
    setup_logging(log_level=logging.INFO, log_to_file=True)
    logger = logging.getLogger(__name__)
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Set application metadata
        app.setApplicationName("FootFix")
        app.setOrganizationName("FootFix")
        app.setApplicationDisplayName("FootFix Image Processor")
        
        # Enable high DPI scaling for Retina displays
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
        # Set application style for macOS
        app.setStyle("Fusion")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info("FootFix application started successfully")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()