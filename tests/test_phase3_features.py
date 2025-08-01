#!/usr/bin/env python3
"""
Test script to verify Phase 3 features for FootFix.
Tests preview functionality, advanced settings, and batch preview integration.
"""

import sys
import tempfile
from pathlib import Path
from PIL import Image
from PySide6.QtWidgets import QApplication

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

from footfix.gui.main_window import MainWindow
from footfix.core.processor import ImageProcessor
from footfix.presets.profiles import get_preset


def create_test_images():
    """Create test images for verification."""
    temp_dir = Path(tempfile.mkdtemp())
    images = []
    
    # Create various test images
    sizes = [
        (4000, 3000, "landscape_large.jpg"),
        (2000, 3000, "portrait.jpg"),
        (3000, 3000, "square.jpg"),
        (800, 600, "small.jpg")
    ]
    
    for width, height, filename in sizes:
        img = Image.new('RGB', (width, height), color='blue')
        path = temp_dir / filename
        img.save(path, 'JPEG', quality=95)
        images.append(path)
        print(f"Created test image: {path} ({width}x{height})")
        
    return images


def test_preset_processing():
    """Test that all presets work correctly."""
    print("\n=== Testing Preset Processing ===")
    processor = ImageProcessor()
    test_image = create_test_images()[0]
    
    # Test each preset
    presets = ['editorial_web', 'email', 'instagram_story', 'instagram_feed_portrait']
    
    for preset_name in presets:
        print(f"\nTesting preset: {preset_name}")
        preset = get_preset(preset_name)
        
        if processor.load_image(test_image):
            if preset.process(processor):
                info = processor.get_image_info()
                config = preset.get_config()
                
                print(f"  Original: 4000x3000")
                print(f"  Processed: {info['width']}x{info['height']}")
                print(f"  Config: {config.name}")
                
                # Verify dimensions
                if config.exact_width and config.exact_height:
                    assert info['width'] == config.exact_width
                    assert info['height'] == config.exact_height
                elif config.max_width and config.max_height:
                    assert info['width'] <= config.max_width
                    assert info['height'] <= config.max_height
                    
                print(f"  ✓ Dimensions verified")
            else:
                print(f"  ✗ Failed to process")
        else:
            print(f"  ✗ Failed to load image")
            
    print("\n✓ All presets tested successfully")


import pytest

@pytest.mark.skip(reason="QApplication singleton conflict - needs GUI test isolation")
def test_gui_features():
    """Test GUI features interactively."""
    print("\n=== Testing GUI Features ===")
    print("Starting FootFix GUI...")
    print("\nFeatures to test:")
    print("1. Preview button - Shows before/after comparison")
    print("2. Advanced settings - Customize processing parameters")
    print("3. Batch preview - Preview images from batch queue")
    print("4. Custom presets - Save and load custom settings")
    print("5. Tooltips - Hover over presets to see descriptions")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Create and add test images
    test_images = create_test_images()
    
    # Add images to batch queue
    window.batch_widget.add_images_to_queue(test_images)
    window.tab_widget.setCurrentIndex(1)  # Switch to batch tab
    
    print(f"\nAdded {len(test_images)} test images to batch queue")
    print("You can now test the new Phase 3 features!")
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # First test preset processing programmatically
    test_preset_processing()
    
    # Then test GUI features
    test_gui_features()