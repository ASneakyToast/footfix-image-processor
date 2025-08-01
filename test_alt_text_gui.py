#!/usr/bin/env python3
"""
Test script for Alt Text GUI integration in FootFix.
Tests the Week 2 deliverables.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from footfix.gui.alt_text_widget import AltTextWidget
from footfix.core.batch_processor import BatchItem, ProcessingStatus
from footfix.core.alt_text_generator import AltTextStatus


def create_sample_batch_items():
    """Create sample batch items for testing."""
    items = []
    
    # Sample item 1 - Completed with alt text
    item1 = BatchItem(source_path=Path("/tmp/test1.jpg"))
    item1.status = ProcessingStatus.COMPLETED
    item1.alt_text = "A person working on a laptop in a modern office environment"
    item1.alt_text_status = AltTextStatus.COMPLETED
    items.append(item1)
    
    # Sample item 2 - Completed, pending alt text
    item2 = BatchItem(source_path=Path("/tmp/test2.jpg"))
    item2.status = ProcessingStatus.COMPLETED
    item2.alt_text_status = AltTextStatus.PENDING
    items.append(item2)
    
    # Sample item 3 - Completed with error
    item3 = BatchItem(source_path=Path("/tmp/test3.jpg"))
    item3.status = ProcessingStatus.COMPLETED
    item3.alt_text_status = AltTextStatus.ERROR
    item3.alt_text_error = "API rate limit exceeded"
    items.append(item3)
    
    return items


class TestWindow(QMainWindow):
    """Test window for Alt Text Widget."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alt Text Widget Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create and add alt text widget
        self.alt_text_widget = AltTextWidget()
        layout.addWidget(self.alt_text_widget)
        
        # Set sample data
        items = create_sample_batch_items()
        self.alt_text_widget.set_batch_items(items)
        
        # Connect signals
        self.alt_text_widget.alt_text_updated.connect(self.on_alt_text_updated)
        self.alt_text_widget.regenerate_requested.connect(self.on_regenerate_requested)
        
    def on_alt_text_updated(self, updates):
        """Handle alt text updates."""
        print(f"Alt text updated: {updates}")
        
    def on_regenerate_requested(self, filenames):
        """Handle regeneration requests."""
        print(f"Regeneration requested for: {filenames}")


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show window
    window = TestWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()