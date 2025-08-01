"""
Test suite for preset profiles validation.
Tests all preset configurations to ensure they meet specifications.
"""

import unittest
import tempfile
from pathlib import Path
from PIL import Image
import os

from ..presets.profiles import (
    EditorialWebPreset,
    EmailPreset,
    InstagramStoryPreset,
    InstagramFeedPortraitPreset,
    get_preset,
    PRESET_REGISTRY
)
from ..core.processor import ImageProcessor


class TestPresetProfiles(unittest.TestCase):
    """Test cases for all preset profiles."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = ImageProcessor()
        
        # Create test images of various sizes
        self.test_images = {
            'large': self._create_test_image(4000, 3000),  # Large landscape
            'portrait': self._create_test_image(2000, 3000),  # Portrait
            'small': self._create_test_image(800, 600),  # Small image
            'square': self._create_test_image(2000, 2000),  # Square
        }
        
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temp files
        for path in Path(self.temp_dir).glob('*'):
            path.unlink()
        os.rmdir(self.temp_dir)
        
    def _create_test_image(self, width: int, height: int) -> Path:
        """Create a test image with specified dimensions."""
        img = Image.new('RGB', (width, height), color='red')
        path = Path(self.temp_dir) / f'test_{width}x{height}.jpg'
        img.save(path, 'JPEG', quality=95)
        return path
        
    def test_editorial_web_preset(self):
        """Test Editorial Web preset: Max 2560×1440px, 0.5-1MB target."""
        preset = EditorialWebPreset()
        config = preset.get_config()
        
        # Verify configuration
        self.assertEqual(config.name, "Editorial Web")
        self.assertEqual(config.max_width, 2560)
        self.assertEqual(config.max_height, 1440)
        self.assertEqual(config.min_size_kb, 500)
        self.assertEqual(config.max_size_kb, 1024)
        self.assertEqual(config.target_size_kb, 750)
        self.assertEqual(config.format, 'JPEG')
        self.assertEqual(config.quality, 85)
        self.assertTrue(config.maintain_aspect)
        
        # Test with large image
        self.processor.load_image(self.test_images['large'])
        preset.process(self.processor)
        
        # Verify dimensions
        info = self.processor.get_image_info()
        self.assertLessEqual(info['width'], 2560)
        self.assertLessEqual(info['height'], 1440)
        
        # Test aspect ratio is maintained
        original_aspect = 4000 / 3000
        new_aspect = info['width'] / info['height']
        self.assertAlmostEqual(original_aspect, new_aspect, places=2)
        
    def test_email_preset(self):
        """Test Email preset: Max 600px width, <100KB target."""
        preset = EmailPreset()
        config = preset.get_config()
        
        # Verify configuration
        self.assertEqual(config.name, "Email")
        self.assertEqual(config.max_width, 600)
        self.assertEqual(config.max_height, 2000)
        self.assertEqual(config.target_size_kb, 80)
        self.assertEqual(config.format, 'JPEG')
        self.assertEqual(config.quality, 75)
        self.assertTrue(config.maintain_aspect)
        
        # Test with portrait image
        self.processor.load_image(self.test_images['portrait'])
        preset.process(self.processor)
        
        # Verify dimensions
        info = self.processor.get_image_info()
        self.assertLessEqual(info['width'], 600)
        self.assertLessEqual(info['height'], 2000)
        
        # Save and check file size
        output_path = Path(self.temp_dir) / 'email_test.jpg'
        output_config = preset.get_output_config()
        self.processor.save_image(output_path, output_config)
        
        file_size_kb = output_path.stat().st_size / 1024
        self.assertLess(file_size_kb, 100, f"File size {file_size_kb:.1f}KB exceeds 100KB limit")
        
    def test_instagram_story_preset(self):
        """Test Instagram Story preset: 1080×1920px (9:16 aspect ratio)."""
        preset = InstagramStoryPreset()
        config = preset.get_config()
        
        # Verify configuration
        self.assertEqual(config.name, "Instagram Story")
        self.assertEqual(config.exact_width, 1080)
        self.assertEqual(config.exact_height, 1920)
        self.assertEqual(config.format, 'JPEG')
        self.assertEqual(config.quality, 90)
        self.assertFalse(config.maintain_aspect)
        
        # Test with square image (will be cropped)
        self.processor.load_image(self.test_images['square'])
        preset.process(self.processor)
        
        # Verify exact dimensions
        info = self.processor.get_image_info()
        self.assertEqual(info['width'], 1080)
        self.assertEqual(info['height'], 1920)
        
        # Verify aspect ratio is 9:16
        aspect_ratio = info['width'] / info['height']
        expected_ratio = 9 / 16
        self.assertAlmostEqual(aspect_ratio, expected_ratio, places=3)
        
    def test_instagram_feed_portrait_preset(self):
        """Test Instagram Feed Portrait preset: 1080×1350px (4:5 aspect ratio)."""
        preset = InstagramFeedPortraitPreset()
        config = preset.get_config()
        
        # Verify configuration
        self.assertEqual(config.name, "Instagram Feed Portrait")
        self.assertEqual(config.exact_width, 1080)
        self.assertEqual(config.exact_height, 1350)
        self.assertEqual(config.format, 'JPEG')
        self.assertEqual(config.quality, 90)
        self.assertFalse(config.maintain_aspect)
        
        # Test with landscape image (will be cropped)
        self.processor.load_image(self.test_images['large'])
        preset.process(self.processor)
        
        # Verify exact dimensions
        info = self.processor.get_image_info()
        self.assertEqual(info['width'], 1080)
        self.assertEqual(info['height'], 1350)
        
        # Verify aspect ratio is 4:5
        aspect_ratio = info['width'] / info['height']
        expected_ratio = 4 / 5
        self.assertAlmostEqual(aspect_ratio, expected_ratio, places=3)
        
    def test_preset_registry(self):
        """Test preset registry functionality."""
        # Test all presets are registered
        expected_presets = ['editorial_web', 'email', 'instagram_story', 'instagram_feed_portrait']
        for preset_name in expected_presets:
            self.assertIn(preset_name, PRESET_REGISTRY)
            
        # Test get_preset function
        for preset_name in expected_presets:
            preset = get_preset(preset_name)
            self.assertIsNotNone(preset)
            
        # Test invalid preset
        invalid_preset = get_preset('invalid_preset')
        self.assertIsNone(invalid_preset)
        
    def test_suggested_filenames(self):
        """Test suggested filename generation for each preset."""
        test_path = Path('/test/image.jpg')
        
        presets_and_expected = [
            (EditorialWebPreset(), 'image_editorial_web.jpg'),
            (EmailPreset(), 'image_email.jpg'),
            (InstagramStoryPreset(), 'image_instagram_story.jpg'),
            (InstagramFeedPortraitPreset(), 'image_instagram_feed_portrait.jpg'),
        ]
        
        for preset, expected_filename in presets_and_expected:
            suggested = preset.get_suggested_filename(test_path)
            self.assertEqual(suggested, expected_filename)


if __name__ == '__main__':
    unittest.main()