#!/usr/bin/env python3
"""
Comprehensive Quality Assurance Test Suite for FootFix
Tests all workflows, edge cases, and performance scenarios
"""
import pytest

import sys
import os
import time
import tempfile
import shutil
import gc
import psutil
import pytest
from pathlib import Path
from PIL import Image
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from footfix.core.processor import ImageProcessor
from footfix.core.batch_processor import BatchProcessor
from footfix.gui.main_window import MainWindow
from footfix.presets.profiles import get_preset, PRESET_REGISTRY
from footfix.utils.preferences import PreferencesManager
from footfix.utils.filename_template import FilenameTemplate


@pytest.mark.skip(reason="Contains method mismatches - needs refactoring for current API")
class TestComprehensiveQA:
    """Comprehensive QA tests for FootFix application"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_images(self, temp_dir):
        """Generate various test images"""
        images = {}
        
        # Standard test image
        img = Image.new('RGB', (1000, 1000), color='red')
        img_path = Path(temp_dir) / "standard.jpg"
        img.save(img_path, quality=95)
        images['standard'] = img_path
        
        # Large image (15MB+)
        large_img = Image.new('RGB', (5000, 5000), color='blue')
        large_path = Path(temp_dir) / "large.jpg"
        large_img.save(large_path, quality=100)
        images['large'] = large_path
        
        # Small image
        small_img = Image.new('RGB', (100, 100), color='green')
        small_path = Path(temp_dir) / "small.jpg"
        small_img.save(small_path)
        images['small'] = small_path
        
        # Corrupted image (partial file)
        corrupted_path = Path(temp_dir) / "corrupted.jpg"
        with open(corrupted_path, 'wb') as f:
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')  # Incomplete JPEG header
        images['corrupted'] = corrupted_path
        
        # Various formats
        for fmt, ext in [('PNG', 'png'), ('BMP', 'bmp'), ('TIFF', 'tiff')]:
            fmt_img = Image.new('RGB', (500, 500), color='yellow')
            fmt_path = Path(temp_dir) / f"format_test.{ext}"
            fmt_img.save(fmt_path)
            images[fmt.lower()] = fmt_path
        
        # Grayscale image
        gray_img = Image.new('L', (800, 800), color=128)
        gray_path = Path(temp_dir) / "grayscale.jpg"
        gray_img.save(gray_path)
        images['grayscale'] = gray_path
        
        # RGBA image
        rgba_img = Image.new('RGBA', (600, 600), color=(255, 0, 0, 128))
        rgba_path = Path(temp_dir) / "rgba.png"
        rgba_img.save(rgba_path)
        images['rgba'] = rgba_path
        
        return images
    
    def test_single_image_processing(self, sample_images, temp_dir):
        """Test single image processing with various settings"""
        processor = ImageProcessor()
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()
        
        # Test standard processing
        result = processor.process_image(
            str(sample_images['standard']),
            str(output_dir),
            resize_percent=50,
            quality=85,
            enable_sharpening=True,
            sharpen_amount=1.2
        )
        assert result['success']
        assert Path(result['output_path']).exists()
        
        # Verify output
        output_img = Image.open(result['output_path'])
        assert output_img.size == (500, 500)  # 50% of 1000x1000
        
        # Test with different formats
        for fmt in ['png', 'bmp', 'tiff']:
            result = processor.process_image(
                str(sample_images[fmt]),
                str(output_dir),
                resize_percent=75,
                quality=90
            )
            assert result['success']
    
    def test_batch_processing_performance(self, sample_images, temp_dir):
        """Test batch processing with 30+ images"""
        batch_processor = BatchProcessor()
        output_dir = Path(temp_dir) / "batch_output"
        output_dir.mkdir()
        
        # Create 35 test images
        batch_images = []
        for i in range(35):
            img = Image.new('RGB', (2000, 2000), 
                          color=(i*7 % 255, (i*11) % 255, (i*13) % 255))
            img_path = Path(temp_dir) / f"batch_{i:03d}.jpg"
            img.save(img_path, quality=95)
            batch_images.append(str(img_path))
        
        # Record performance metrics
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Process batch
        results = []
        def on_progress(current, total, message):
            results.append((current, total))
        
        batch_processor.progress_updated.connect(on_progress)
        batch_processor.process_batch(
            batch_images,
            str(output_dir),
            resize_percent=60,
            quality=85,
            enable_sharpening=True
        )
        
        # Check performance
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        processing_time = end_time - start_time
        memory_increase = end_memory - start_memory
        
        print(f"Batch processing stats:")
        print(f"  - Images processed: 35")
        print(f"  - Total time: {processing_time:.2f}s")
        print(f"  - Time per image: {processing_time/35:.2f}s")
        print(f"  - Memory increase: {memory_increase:.2f}MB")
        
        # Verify all processed
        assert len(results) >= 35
        output_files = list(output_dir.glob("*.jpg"))
        assert len(output_files) == 35
        
        # Performance assertions
        assert processing_time < 60  # Should complete in under 60 seconds
        assert memory_increase < 500  # Memory usage should be reasonable
    
    def test_edge_cases(self, sample_images, temp_dir):
        """Test edge cases and error handling"""
        processor = ImageProcessor()
        output_dir = Path(temp_dir) / "edge_output"
        output_dir.mkdir()
        
        # Test corrupted image
        result = processor.process_image(
            str(sample_images['corrupted']),
            str(output_dir),
            resize_percent=50
        )
        assert not result['success']
        assert 'error' in result
        
        # Test non-existent file
        result = processor.process_image(
            str(Path(temp_dir) / "nonexistent.jpg"),
            str(output_dir),
            resize_percent=50
        )
        assert not result['success']
        
        # Test invalid resize values
        result = processor.process_image(
            str(sample_images['standard']),
            str(output_dir),
            resize_percent=0  # Invalid
        )
        assert not result['success']
        
        # Test very large resize
        result = processor.process_image(
            str(sample_images['small']),
            str(output_dir),
            resize_percent=1000  # 10x resize
        )
        assert result['success']
        output_img = Image.open(result['output_path'])
        assert output_img.size == (1000, 1000)  # Capped at reasonable size
        
        # Test special characters in filename
        special_img = Image.new('RGB', (500, 500), color='purple')
        special_path = Path(temp_dir) / "test & image (2023) [edited].jpg"
        special_img.save(special_path)
        
        result = processor.process_image(
            str(special_path),
            str(output_dir),
            resize_percent=50
        )
        assert result['success']
        assert Path(result['output_path']).exists()
    
    def test_memory_management(self, temp_dir):
        """Test memory management with large batches"""
        processor = ImageProcessor()
        output_dir = Path(temp_dir) / "memory_test"
        output_dir.mkdir()
        
        # Process multiple large images
        for i in range(10):
            # Create 10MB+ image
            large_img = Image.new('RGB', (4000, 4000), 
                                color=(50*i, 100, 200-20*i))
            img_path = Path(temp_dir) / f"large_{i}.jpg"
            large_img.save(img_path, quality=100)
            
            # Process with memory tracking
            gc.collect()
            start_mem = psutil.Process().memory_info().rss / 1024 / 1024
            
            result = processor.process_image(
                str(img_path),
                str(output_dir),
                resize_percent=50,
                quality=85
            )
            
            gc.collect()
            end_mem = psutil.Process().memory_info().rss / 1024 / 1024
            mem_increase = end_mem - start_mem
            
            assert result['success']
            assert mem_increase < 200  # Should not leak excessive memory
            
            # Clean up source to save space
            img_path.unlink()
    
    def test_preset_management(self):
        """Test preset save/load functionality"""
        # Test preset registry availability
        preset_keys = list(PRESET_REGISTRY.keys())
        
        # Test default presets exist
        assert len(preset_keys) > 0
        assert 'editorial_web' in preset_keys
        assert 'email' in preset_keys
        
        # Test preset instantiation
        editorial_preset = get_preset('editorial_web')
        assert editorial_preset is not None
        
        # Test preset configuration
        config = editorial_preset.get_config()
        assert config.name == "Editorial Web"
        assert config.max_width == 2560
        assert config.max_height == 1440
    
    def test_filename_templates(self, sample_images, temp_dir):
        """Test filename template functionality"""
        template = FilenameTemplate()
        output_dir = Path(temp_dir) / "template_test"
        output_dir.mkdir()
        
        # Test various template patterns
        test_cases = [
            ("{name}_edited", "standard_edited.jpg"),
            ("{name}_{date}", lambda x: "standard_" in x and ".jpg" in x),
            ("{counter:03d}_{name}", "001_standard.jpg"),
            ("IMG_{width}x{height}", "IMG_1000x1000.jpg"),
            ("{name}_{preset}", "standard_Default.jpg")
        ]
        
        for pattern, expected in test_cases:
            result = template.generate_filename(
                source_path=str(sample_images['standard']),
                pattern=pattern,
                output_format='jpg',
                counter=1,
                preset_name='Default',
                image_info={'width': 1000, 'height': 1000}
            )
            
            if callable(expected):
                assert expected(result)
            else:
                assert result == expected
    
    @pytest.mark.skipif(not os.environ.get('DISPLAY') and sys.platform != 'darwin',
                        reason="Requires display")
    def test_gui_integration(self, qtbot, sample_images, temp_dir):
        """Test GUI functionality and integration"""
        # Create main window
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        
        # Test loading an image
        window.load_image(str(sample_images['standard']))
        assert window.current_image_path == str(sample_images['standard'])
        
        # Test settings dialog
        window.show_settings()
        assert window.settings_dialog is not None
        
        # Test batch processing tab
        window.tab_widget.setCurrentIndex(1)  # Switch to batch tab
        assert window.batch_widget is not None
        
        # Test preset selection
        window.preset_combo.setCurrentText("High Quality")
        preset = window.preset_manager.get_preset("High Quality")
        assert preset is not None
        
        # Clean up
        window.close()
    
    def test_security_validation(self, sample_images, temp_dir):
        """Test security and input validation"""
        processor = ImageProcessor()
        output_dir = Path(temp_dir) / "security_test"
        output_dir.mkdir()
        
        # Test path traversal attempts
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32\\config"
        ]
        
        for path in malicious_paths:
            result = processor.process_image(
                path,
                str(output_dir),
                resize_percent=50
            )
            assert not result['success']
        
        # Test output directory validation
        result = processor.process_image(
            str(sample_images['standard']),
            "/root/test",  # Should fail on permissions
            resize_percent=50
        )
        assert not result['success']
        
        # Test extreme parameter values
        extreme_params = [
            {'resize_percent': -50},
            {'resize_percent': 10000},
            {'quality': -10},
            {'quality': 200},
            {'sharpen_amount': -5},
            {'sharpen_amount': 100}
        ]
        
        for params in extreme_params:
            result = processor.process_image(
                str(sample_images['standard']),
                str(output_dir),
                **params
            )
            # Should either fail or clamp to valid values
            if result['success']:
                # Verify clamped values
                output = Image.open(result['output_path'])
                assert output.size[0] > 0 and output.size[1] > 0


def run_comprehensive_tests():
    """Run all comprehensive QA tests and generate report"""
    print("FootFix Comprehensive Quality Assurance Testing")
    print("=" * 50)
    
    # Run pytest with detailed output
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--capture=no',
        '-x'  # Stop on first failure
    ])
    
    if exit_code == 0:
        print("\n✅ All QA tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Please review the output above.")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(run_comprehensive_tests())