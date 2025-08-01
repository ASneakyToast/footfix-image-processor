"""
Comprehensive test suite for alt text functionality.
Tests all components of the alt text generation system including unit tests,
integration tests, performance tests, and error handling.
"""

import pytest
import asyncio
import json
import csv
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import tempfile
import shutil
import aiohttp

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from footfix.core.alt_text_generator import (
    AltTextGenerator, AltTextResult, AltTextStatus
)
from footfix.core.batch_processor import BatchItem, ProcessingStatus
from footfix.gui.alt_text_widget import AltTextWidget, AltTextEditWidget
from footfix.utils.alt_text_exporter import (
    AltTextExporter, ExportFormat, ExportOptions
)
from footfix.utils.preferences import PreferencesManager


@pytest.fixture
def app():
    """Create Qt application for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample test image."""
    from PIL import Image
    
    img_path = temp_dir / "test_image.jpg"
    img = Image.new('RGB', (800, 600), color='red')
    img.save(img_path, 'JPEG')
    return img_path


@pytest.fixture
def batch_items(sample_image):
    """Create sample batch items for testing."""
    items = []
    for i in range(3):
        item = BatchItem(sample_image)
        item.status = ProcessingStatus.COMPLETED
        item.alt_text = f"Test alt text for image {i}"
        item.alt_text_status = AltTextStatus.COMPLETED
        items.append(item)
    return items


class TestAltTextGenerator:
    """Unit tests for AltTextGenerator class."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = AltTextGenerator()
        assert generator.api_key is None
        assert generator.session is None
        assert generator.MAX_REQUESTS_PER_MINUTE == 50
        assert generator.COST_PER_IMAGE == 0.006
        
    def test_api_key_setting(self):
        """Test API key configuration."""
        generator = AltTextGenerator()
        test_key = "test-api-key-123"
        generator.set_api_key(test_key)
        assert generator.api_key == test_key
        
    def test_image_encoding(self, sample_image):
        """Test image encoding functionality."""
        generator = AltTextGenerator()
        encoded = generator._encode_image(sample_image)
        
        assert encoded is not None
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        
    def test_image_encoding_invalid_path(self):
        """Test image encoding with invalid path."""
        generator = AltTextGenerator()
        encoded = generator._encode_image(Path("/nonexistent/image.jpg"))
        assert encoded is None
        
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        generator = AltTextGenerator()
        
        # Simulate reaching rate limit
        for _ in range(generator.MAX_REQUESTS_PER_MINUTE):
            assert generator._check_rate_limit() is True
            
        # Next request should be rate limited
        assert generator._check_rate_limit() is False
        
    @pytest.mark.asyncio
    async def test_generate_alt_text_no_api_key(self, sample_image):
        """Test generation without API key."""
        generator = AltTextGenerator()
        result = await generator.generate_alt_text(sample_image)
        
        assert result.status == AltTextStatus.ERROR
        assert result.error_message == "API key not configured"
        assert result.alt_text is None
        
    @pytest.mark.asyncio
    async def test_generate_alt_text_success(self, sample_image):
        """Test successful alt text generation."""
        generator = AltTextGenerator("test-key")
        
        # Mock API response
        mock_response = {
            "content": [{"text": "A beautiful red square image"}]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            
            result = await generator.generate_alt_text(sample_image)
            
            assert result.status == AltTextStatus.COMPLETED
            assert result.alt_text == "A beautiful red square image"
            assert result.api_cost == generator.COST_PER_IMAGE
            assert result.generation_time > 0
            
    @pytest.mark.asyncio
    async def test_generate_alt_text_rate_limited(self, sample_image):
        """Test handling of rate limiting."""
        generator = AltTextGenerator("test-key")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 429
            mock_post.return_value.__aenter__.return_value.headers = {"retry-after": "5"}
            
            result = await generator.generate_alt_text(sample_image)
            
            assert result.status == AltTextStatus.ERROR
            assert "Rate limited" in result.error_message
            
    @pytest.mark.asyncio
    async def test_generate_alt_text_network_error(self, sample_image):
        """Test network error handling."""
        generator = AltTextGenerator("test-key")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = aiohttp.ClientError("Network error")
            
            result = await generator.generate_alt_text(sample_image)
            
            assert result.status == AltTextStatus.ERROR
            assert "Network error" in result.error_message
            
    @pytest.mark.asyncio
    async def test_batch_generation(self, temp_dir):
        """Test batch alt text generation."""
        generator = AltTextGenerator("test-key")
        
        # Create multiple test images
        images = []
        for i in range(3):
            img_path = temp_dir / f"test_{i}.jpg"
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(img_path)
            images.append(img_path)
            
        # Mock API responses
        with patch.object(generator, 'generate_alt_text') as mock_generate:
            mock_generate.side_effect = [
                AltTextResult(alt_text=f"Alt text {i}", status=AltTextStatus.COMPLETED)
                for i in range(3)
            ]
            
            results = await generator.generate_batch(images)
            
            assert len(results) == 3
            for i, img_path in enumerate(images):
                assert results[img_path].alt_text == f"Alt text {i}"
                
    def test_cost_estimation(self):
        """Test batch cost estimation."""
        generator = AltTextGenerator()
        
        estimates = generator.estimate_batch_cost(100)
        assert estimates['per_image'] == generator.COST_PER_IMAGE
        assert estimates['total'] == generator.COST_PER_IMAGE * 100
        assert estimates['monthly_estimate'] == generator.COST_PER_IMAGE * 100 * 20
        
    @pytest.mark.asyncio
    async def test_api_key_validation(self):
        """Test API key validation."""
        generator = AltTextGenerator()
        
        # Test with no key
        is_valid, message = await generator.validate_api_key()
        assert is_valid is False
        assert "No API key" in message
        
        # Test with valid key
        generator.set_api_key("test-key")
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            
            is_valid, message = await generator.validate_api_key()
            assert is_valid is True
            assert "valid" in message
            
    def test_usage_tracking(self):
        """Test API usage tracking."""
        with patch('footfix.utils.preferences.PreferencesManager') as mock_prefs:
            mock_manager = Mock()
            mock_manager.get.return_value = True
            mock_prefs.return_value = mock_manager
            
            generator = AltTextGenerator()
            generator._track_usage(0.006)
            
            # Verify tracking was called
            mock_manager.set.assert_called()


class TestAltTextWidget:
    """Unit tests for AltTextWidget GUI component."""
    
    def test_initialization(self, app):
        """Test widget initialization."""
        widget = AltTextWidget()
        assert widget.batch_items == []
        assert widget.item_widgets == {}
        assert widget.status_label.text() == "No items to review"
        
    def test_set_batch_items(self, app, batch_items):
        """Test setting batch items."""
        widget = AltTextWidget()
        widget.set_batch_items(batch_items)
        
        assert len(widget.batch_items) == 3
        assert widget.items_table.rowCount() == 3
        
    def test_alt_text_editing(self, app):
        """Test alt text edit widget functionality."""
        edit_widget = AltTextEditWidget()
        
        # Test character counting
        test_text = "This is a test alt text description"
        edit_widget.setPlainText(test_text)
        
        assert edit_widget.toPlainText() == test_text
        
        # Test validation styling
        long_text = "a" * 130  # Over limit
        edit_widget.setPlainText(long_text)
        assert "background-color" in edit_widget.styleSheet()
        
    def test_selection_functionality(self, app, batch_items):
        """Test item selection in the widget."""
        widget = AltTextWidget()
        widget.set_batch_items(batch_items)
        
        # Test select all
        widget.select_all_cb.setChecked(True)
        assert widget.regenerate_selected_btn.isEnabled()
        
    def test_export_button_states(self, app, batch_items):
        """Test export button enabling/disabling."""
        widget = AltTextWidget()
        
        # Initially disabled
        assert not widget.export_btn.isEnabled()
        
        # Enabled after adding items
        widget.set_batch_items(batch_items)
        assert widget.export_btn.isEnabled()
        
    def test_progress_updates(self, app):
        """Test progress display updates."""
        widget = AltTextWidget()
        
        widget.update_progress(5, 10, "Processing")
        assert widget.progress_bar.isVisible()
        assert widget.progress_bar.value() == 5
        assert widget.progress_bar.maximum() == 10
        assert "50%" in widget.progress_label.text()


class TestAltTextExporter:
    """Unit tests for AltTextExporter class."""
    
    def test_initialization(self):
        """Test exporter initialization."""
        exporter = AltTextExporter()
        assert exporter.default_export_dir == Path.home() / "Downloads"
        
    def test_filename_generation(self):
        """Test export filename generation."""
        exporter = AltTextExporter()
        
        csv_filename = exporter.generate_filename(ExportFormat.CSV)
        assert csv_filename.endswith('.csv')
        assert 'alttext_export' in csv_filename
        
        json_filename = exporter.generate_filename(ExportFormat.JSON)
        assert json_filename.endswith('.json')
        
    def test_metadata_gathering(self, batch_items):
        """Test metadata extraction from batch items."""
        exporter = AltTextExporter()
        item = batch_items[0]
        
        metadata = exporter._gather_metadata(item)
        
        assert metadata['filename'] == item.source_path.name
        assert metadata['alt_text'] == item.alt_text
        assert metadata['status'] == 'completed'
        assert 'width' in metadata
        assert 'height' in metadata
        
    def test_csv_export(self, temp_dir, batch_items):
        """Test CSV export functionality."""
        exporter = AltTextExporter()
        output_path = temp_dir / "test_export.csv"
        
        success, message = exporter.export_csv(batch_items, output_path)
        
        assert success is True
        assert output_path.exists()
        
        # Verify CSV content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3
            assert rows[0]['alt_text'] == "Test alt text for image 0"
            
    def test_json_export(self, temp_dir, batch_items):
        """Test JSON export functionality."""
        exporter = AltTextExporter()
        output_path = temp_dir / "test_export.json"
        
        success, message = exporter.export_json(batch_items, output_path)
        
        assert success is True
        assert output_path.exists()
        
        # Verify JSON content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data['total_items'] == 3
            assert len(data['items']) == 3
            assert 'summary' in data
            assert data['summary']['completed_items'] == 3
            
    def test_filtered_export(self, temp_dir, batch_items):
        """Test export with filtering options."""
        exporter = AltTextExporter()
        
        # Mark one item as error
        batch_items[1].alt_text_status = AltTextStatus.ERROR
        
        output_path = temp_dir / "filtered_export.csv"
        success, message = exporter.export_csv(
            batch_items, 
            output_path,
            ExportOptions.COMPLETED_ONLY
        )
        
        assert success is True
        
        # Should only export 2 completed items
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            
    def test_cms_export(self, temp_dir, batch_items):
        """Test CMS-specific export format."""
        exporter = AltTextExporter()
        output_path = temp_dir / "wordpress_export.csv"
        
        success, message = exporter.export_for_cms(
            batch_items, 
            output_path,
            "wordpress"
        )
        
        assert success is True
        assert output_path.exists()
        
        # Verify WordPress format
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == ['filename', 'title', 'alt_text', 'caption', 'description']
            
    def test_path_validation(self, temp_dir):
        """Test export path validation."""
        exporter = AltTextExporter()
        
        # Valid path
        valid_path = temp_dir / "test.csv"
        is_valid, message = exporter.validate_export_path(valid_path)
        assert is_valid is True
        
        # Invalid path (directory)
        is_valid, message = exporter.validate_export_path(temp_dir)
        assert is_valid is False


class TestIntegration:
    """Integration tests for alt text functionality."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, temp_dir, sample_image):
        """Test complete workflow from generation to export."""
        # Setup
        generator = AltTextGenerator("test-key")
        exporter = AltTextExporter()
        
        # Mock API response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"content": [{"text": "End-to-end test alt text"}]}
            )
            
            # Generate alt text
            result = await generator.generate_alt_text(sample_image)
            assert result.status == AltTextStatus.COMPLETED
            
            # Create batch item
            item = BatchItem(sample_image)
            item.alt_text = result.alt_text
            item.alt_text_status = result.status
            item.status = ProcessingStatus.COMPLETED
            
            # Export to CSV
            output_path = temp_dir / "e2e_export.csv"
            success, message = exporter.export_csv([item], output_path)
            assert success is True
            
            # Verify export
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                row = next(reader)
                assert row['alt_text'] == "End-to-end test alt text"
                
    @pytest.mark.asyncio
    async def test_batch_processing_with_errors(self, temp_dir):
        """Test batch processing with mixed success/error results."""
        generator = AltTextGenerator("test-key")
        
        # Create test images
        images = []
        for i in range(5):
            img_path = temp_dir / f"batch_test_{i}.jpg"
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='green')
            img.save(img_path)
            images.append(img_path)
            
        # Mock mixed responses
        call_count = 0
        async def mock_generate(image_path, context=None):
            nonlocal call_count
            call_count += 1
            
            if call_count % 2 == 0:
                # Simulate error
                return AltTextResult(
                    status=AltTextStatus.ERROR,
                    error_message="Simulated error"
                )
            else:
                # Simulate success
                return AltTextResult(
                    alt_text=f"Alt text for image {call_count}",
                    status=AltTextStatus.COMPLETED,
                    api_cost=0.006
                )
                
        with patch.object(generator, 'generate_alt_text', side_effect=mock_generate):
            results = await generator.generate_batch(images)
            
            # Verify mixed results
            successful = sum(1 for r in results.values() if r.status == AltTextStatus.COMPLETED)
            failed = sum(1 for r in results.values() if r.status == AltTextStatus.ERROR)
            
            assert successful == 3
            assert failed == 2


class TestPerformance:
    """Performance tests for alt text functionality."""
    
    @pytest.mark.asyncio
    async def test_large_batch_performance(self, temp_dir):
        """Test performance with large batch of images."""
        generator = AltTextGenerator("test-key")
        
        # Create 30 test images
        images = []
        for i in range(30):
            img_path = temp_dir / f"perf_test_{i}.jpg"
            from PIL import Image
            img = Image.new('RGB', (800, 600), color='blue')
            img.save(img_path)
            images.append(img_path)
            
        # Mock fast API responses
        async def mock_generate(image_path, context=None):
            await asyncio.sleep(0.1)  # Simulate API delay
            return AltTextResult(
                alt_text=f"Performance test alt text",
                status=AltTextStatus.COMPLETED,
                api_cost=0.006,
                generation_time=0.1
            )
            
        start_time = time.time()
        
        with patch.object(generator, 'generate_alt_text', side_effect=mock_generate):
            results = await generator.generate_batch(images)
            
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all completed
        assert len(results) == 30
        assert all(r.status == AltTextStatus.COMPLETED for r in results.values())
        
        # Performance assertions
        assert total_time < 10  # Should complete in under 10 seconds
        avg_time = total_time / 30
        assert avg_time < 0.5  # Average under 500ms per image
        
    def test_memory_usage_large_export(self, temp_dir):
        """Test memory efficiency with large exports."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large batch
        items = []
        for i in range(1000):
            item = BatchItem(Path(f"test_{i}.jpg"))
            item.alt_text = f"Alt text description for image {i}" * 10
            item.alt_text_status = AltTextStatus.COMPLETED
            item.status = ProcessingStatus.COMPLETED
            items.append(item)
            
        exporter = AltTextExporter()
        output_path = temp_dir / "large_export.csv"
        
        success, message = exporter.export_csv(items, output_path)
        assert success is True
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100
        
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self):
        """Test concurrent API request handling."""
        generator = AltTextGenerator("test-key")
        
        # Test semaphore limiting
        request_times = []
        
        async def mock_post(*args, **kwargs):
            request_times.append(time.time())
            await asyncio.sleep(0.1)
            
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"content": [{"text": "Concurrent test"}]}
            )
            return mock_response
            
        with patch('aiohttp.ClientSession.post', side_effect=mock_post):
            # Create multiple concurrent requests
            tasks = []
            for i in range(10):
                task = generator.generate_alt_text(Path(f"test_{i}.jpg"))
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify semaphore limited concurrent requests
            # Should not have more than 5 concurrent requests
            for i in range(len(request_times) - 5):
                time_diff = request_times[i + 5] - request_times[i]
                assert time_diff >= 0.09  # At least 90ms apart


class TestErrorHandling:
    """Error handling and edge case tests."""
    
    @pytest.mark.asyncio
    async def test_invalid_image_handling(self, temp_dir):
        """Test handling of invalid image files."""
        generator = AltTextGenerator("test-key")
        
        # Create invalid image file
        invalid_path = temp_dir / "invalid.jpg"
        invalid_path.write_text("This is not an image")
        
        result = await generator.generate_alt_text(invalid_path)
        
        assert result.status == AltTextStatus.ERROR
        assert result.error_message is not None
        
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, sample_image):
        """Test handling of API timeouts."""
        generator = AltTextGenerator("test-key")
        
        async def mock_timeout(*args, **kwargs):
            raise asyncio.TimeoutError("Request timeout")
            
        with patch('aiohttp.ClientSession.post', side_effect=mock_timeout):
            result = await generator.generate_alt_text(sample_image)
            
            assert result.status == AltTextStatus.ERROR
            assert "timeout" in result.error_message.lower()
            
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, sample_image):
        """Test retry mechanism for transient failures."""
        generator = AltTextGenerator("test-key")
        generator.MAX_RETRIES = 3
        
        call_count = 0
        async def mock_flaky_api(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                # Fail first 2 attempts
                mock_response = Mock()
                mock_response.status = 500
                mock_response.text = AsyncMock(return_value="Server error")
                return mock_response
            else:
                # Succeed on 3rd attempt
                mock_response = Mock()
                mock_response.status = 200
                mock_response.json = AsyncMock(
                    return_value={"content": [{"text": "Success after retries"}]}
                )
                return mock_response
                
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.side_effect = mock_flaky_api
            
            result = await generator.generate_alt_text(sample_image)
            
            assert result.status == AltTextStatus.COMPLETED
            assert result.alt_text == "Success after retries"
            assert call_count == 3
            
    def test_export_with_special_characters(self, temp_dir):
        """Test export handling of special characters."""
        exporter = AltTextExporter()
        
        # Create item with special characters
        item = BatchItem(Path("test.jpg"))
        item.alt_text = 'Alt text with "quotes", commas, and 新line\ncharacters'
        item.alt_text_status = AltTextStatus.COMPLETED
        item.status = ProcessingStatus.COMPLETED
        
        # Test CSV export
        csv_path = temp_dir / "special_chars.csv"
        success, message = exporter.export_csv([item], csv_path)
        assert success is True
        
        # Verify CSV handles special characters
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert '"quotes"' in row['alt_text']
            assert '\n' in row['alt_text']
            
        # Test JSON export
        json_path = temp_dir / "special_chars.json"
        success, message = exporter.export_json([item], json_path)
        assert success is True
        
        # Verify JSON handles special characters
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert '"quotes"' in data['items'][0]['alt_text']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])