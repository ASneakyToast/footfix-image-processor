"""
Tests for the ImageProcessor class.
Verifies core image processing functionality.
"""

import pytest
from pathlib import Path
from PIL import Image
import tempfile
import os

from footfix.core.processor import ImageProcessor
from footfix.presets.profiles import EditorialWebPreset


class TestImageProcessor:
    """Test cases for ImageProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a fresh ImageProcessor instance."""
        return ImageProcessor()
        
    @pytest.fixture
    def test_image(self):
        """Create a temporary test image."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Create a test image
            img = Image.new('RGB', (3000, 2000), color='red')
            img.save(tmp.name, 'JPEG')
            yield tmp.name
            # Cleanup
            os.unlink(tmp.name)
            
    def test_load_image_success(self, processor, test_image):
        """Test successful image loading."""
        assert processor.load_image(test_image) is True
        assert processor.current_image is not None
        assert processor.original_image is not None
        assert processor.source_path == Path(test_image)
        
    def test_load_image_invalid_path(self, processor):
        """Test loading with invalid path."""
        assert processor.load_image("/path/that/does/not/exist.jpg") is False
        assert processor.current_image is None
        
    def test_load_image_unsupported_format(self, processor):
        """Test loading unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=True) as tmp:
            tmp.write(b"Not an image")
            tmp.flush()
            assert processor.load_image(tmp.name) is False
            
    def test_resize_to_fit(self, processor, test_image):
        """Test resizing to fit within dimensions."""
        processor.load_image(test_image)
        original_size = (processor.current_image.width, processor.current_image.height)
        
        processor.resize_to_fit(1000, 1000)
        
        # Check that image was resized
        assert processor.current_image.width <= 1000
        assert processor.current_image.height <= 1000
        
        # Check aspect ratio maintained
        original_ratio = original_size[0] / original_size[1]
        new_ratio = processor.current_image.width / processor.current_image.height
        assert abs(original_ratio - new_ratio) < 0.01
        
    def test_resize_to_exact(self, processor, test_image):
        """Test resizing to exact dimensions."""
        processor.load_image(test_image)
        
        processor.resize_to_exact(800, 600)
        
        assert processor.current_image.width == 800
        assert processor.current_image.height == 600
        
    def test_save_image(self, processor, test_image):
        """Test saving processed image."""
        processor.load_image(test_image)
        processor.resize_to_fit(1000, 1000)
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            output_path = tmp.name
            
        try:
            assert processor.save_image(output_path) is True
            assert Path(output_path).exists()
            
            # Verify saved image
            saved_img = Image.open(output_path)
            assert saved_img.width <= 1000
            assert saved_img.height <= 1000
        finally:
            os.unlink(output_path)
            
    def test_get_image_info(self, processor, test_image):
        """Test getting image information."""
        processor.load_image(test_image)
        info = processor.get_image_info()
        
        assert info['width'] == 3000
        assert info['height'] == 2000
        assert info['size_pixels'] == '3000x2000'
        assert info['mode'] == 'RGB'
        
    def test_reset_to_original(self, processor, test_image):
        """Test resetting to original image."""
        processor.load_image(test_image)
        original_size = (processor.current_image.width, processor.current_image.height)
        
        # Modify image
        processor.resize_to_fit(500, 500)
        assert processor.current_image.width <= 500
        
        # Reset
        processor.reset_to_original()
        assert processor.current_image.width == original_size[0]
        assert processor.current_image.height == original_size[1]


class TestPresetProfiles:
    """Test cases for preset profiles."""
    
    @pytest.fixture
    def processor_with_image(self, test_image):
        """Create processor with loaded test image."""
        processor = ImageProcessor()
        processor.load_image(test_image)
        return processor
        
    @pytest.fixture
    def test_image(self):
        """Create a temporary test image."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Create a test image
            img = Image.new('RGB', (3000, 2000), color='blue')
            img.save(tmp.name, 'JPEG')
            yield tmp.name
            # Cleanup
            os.unlink(tmp.name)
            
    def test_editorial_web_preset(self, processor_with_image):
        """Test Editorial Web preset processing."""
        preset = EditorialWebPreset()
        
        # Apply preset
        assert preset.process(processor_with_image) is True
        
        # Check dimensions
        assert processor_with_image.current_image.width <= 2560
        assert processor_with_image.current_image.height <= 1440
        
    def test_preset_output_config(self):
        """Test preset output configuration."""
        preset = EditorialWebPreset()
        config = preset.get_output_config()
        
        assert config['format'] == 'JPEG'
        assert config['quality'] == 85
        assert config['target_size_kb'] == 750
        
    def test_preset_suggested_filename(self):
        """Test preset filename generation."""
        preset = EditorialWebPreset()
        original_path = Path("/path/to/test_image.png")
        
        suggested = preset.get_suggested_filename(original_path)
        assert suggested == "test_image_editorial_web.jpg"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])