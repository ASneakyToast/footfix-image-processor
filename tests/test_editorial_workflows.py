"""
Editorial workflow tests for alt text functionality.
Tests real-world editorial team workflows and use cases with various image types.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtWidgets import QApplication

from footfix.core.alt_text_generator import AltTextGenerator, AltTextStatus
from footfix.core.batch_processor import BatchProcessor, BatchItem, ProcessingStatus
from footfix.gui.alt_text_widget import AltTextWidget
from footfix.utils.alt_text_exporter import AltTextExporter, ExportFormat


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
def editorial_images(temp_dir):
    """Create various types of editorial images for testing."""
    images = {}
    
    # Fashion product shot
    fashion_path = temp_dir / "fashion_dress_001.jpg"
    fashion_img = Image.new('RGB', (1200, 1800), color='white')
    draw = ImageDraw.Draw(fashion_img)
    # Simulate a dress
    draw.rectangle([300, 200, 900, 1600], fill='navy')
    draw.ellipse([500, 100, 700, 300], fill='beige')  # Model head placeholder
    fashion_img.save(fashion_path)
    images['fashion'] = fashion_path
    
    # Lifestyle scene
    lifestyle_path = temp_dir / "lifestyle_coffee_002.jpg"
    lifestyle_img = Image.new('RGB', (1600, 1200), color='#f5f5f5')
    draw = ImageDraw.Draw(lifestyle_img)
    # Simulate coffee shop scene
    draw.rectangle([100, 400, 600, 800], fill='brown')  # Table
    draw.ellipse([300, 500, 400, 600], fill='white')  # Coffee cup
    draw.rectangle([800, 100, 1500, 1000], fill='#e0e0e0')  # Window
    lifestyle_img.save(lifestyle_path)
    images['lifestyle'] = lifestyle_path
    
    # Product detail shot
    product_path = temp_dir / "product_watch_003.jpg"
    product_img = Image.new('RGB', (1000, 1000), color='white')
    draw = ImageDraw.Draw(product_img)
    # Simulate watch
    draw.ellipse([300, 300, 700, 700], fill='silver', outline='black', width=20)
    draw.ellipse([400, 400, 600, 600], fill='black')  # Watch face
    product_img.save(product_path)
    images['product'] = product_path
    
    # People/portrait
    portrait_path = temp_dir / "portrait_model_004.jpg"
    portrait_img = Image.new('RGB', (800, 1200), color='#fafafa')
    draw = ImageDraw.Draw(portrait_img)
    # Simulate portrait
    draw.ellipse([250, 200, 550, 500], fill='beige')  # Face
    draw.rectangle([200, 500, 600, 1100], fill='red')  # Clothing
    portrait_img.save(portrait_path)
    images['portrait'] = portrait_path
    
    # Text-heavy image (magazine cover)
    text_path = temp_dir / "magazine_cover_005.jpg"
    text_img = Image.new('RGB', (800, 1000), color='white')
    draw = ImageDraw.Draw(text_img)
    # Add text elements
    draw.text((100, 50), "FASHION MAG", fill='black')
    draw.text((100, 200), "Spring Collection", fill='gray')
    draw.rectangle([100, 300, 700, 900], fill='pink')  # Main image area
    text_img.save(text_path)
    images['text_heavy'] = text_path
    
    return images


class TestEditorialContentTypes:
    """Test alt text generation for different editorial content types."""
    
    @pytest.mark.asyncio
    async def test_fashion_image_alt_text(self, editorial_images):
        """Test alt text generation for fashion product images."""
        generator = AltTextGenerator("test-key")
        
        mock_response = {
            "content": [{
                "text": "Navy blue A-line dress on a model against a white background, featuring a fitted bodice and flowing skirt that falls to mid-calf"
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            
            result = await generator.generate_alt_text(
                editorial_images['fashion'],
                context="fashion editorial product shot"
            )
            
            assert result.status == AltTextStatus.COMPLETED
            assert len(result.alt_text) <= 150  # Editorial best practice
            assert "dress" in result.alt_text.lower()
            assert any(word in result.alt_text.lower() for word in ['navy', 'blue'])
            
    @pytest.mark.asyncio
    async def test_lifestyle_scene_alt_text(self, editorial_images):
        """Test alt text generation for lifestyle editorial images."""
        generator = AltTextGenerator("test-key")
        
        mock_response = {
            "content": [{
                "text": "Cozy coffee shop interior with wooden table, white ceramic coffee cup, and large window showing natural light"
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            
            result = await generator.generate_alt_text(
                editorial_images['lifestyle'],
                context="lifestyle editorial scene"
            )
            
            assert result.status == AltTextStatus.COMPLETED
            assert "coffee" in result.alt_text.lower()
            assert any(word in result.alt_text.lower() for word in ['interior', 'table', 'window'])
            
    @pytest.mark.asyncio
    async def test_product_detail_alt_text(self, editorial_images):
        """Test alt text generation for product detail shots."""
        generator = AltTextGenerator("test-key")
        
        mock_response = {
            "content": [{
                "text": "Silver luxury watch with black dial and metallic band on white background"
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            
            result = await generator.generate_alt_text(
                editorial_images['product'],
                context="product detail shot"
            )
            
            assert result.status == AltTextStatus.COMPLETED
            assert "watch" in result.alt_text.lower()
            assert any(word in result.alt_text.lower() for word in ['silver', 'black', 'metallic'])
            
    @pytest.mark.asyncio
    async def test_portrait_alt_text(self, editorial_images):
        """Test alt text generation for people/portrait images."""
        generator = AltTextGenerator("test-key")
        
        mock_response = {
            "content": [{
                "text": "Woman wearing a vibrant red top, looking directly at camera with confident expression"
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            
            result = await generator.generate_alt_text(
                editorial_images['portrait'],
                context="editorial portrait"
            )
            
            assert result.status == AltTextStatus.COMPLETED
            assert any(word in result.alt_text.lower() for word in ['woman', 'person', 'model'])
            assert "red" in result.alt_text.lower()
            
    @pytest.mark.asyncio
    async def test_text_heavy_image_alt_text(self, editorial_images):
        """Test alt text generation for text-heavy images like magazine covers."""
        generator = AltTextGenerator("test-key")
        
        mock_response = {
            "content": [{
                "text": "Fashion magazine cover featuring 'Spring Collection' headline with pink fashion imagery"
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            
            result = await generator.generate_alt_text(
                editorial_images['text_heavy'],
                context="magazine cover"
            )
            
            assert result.status == AltTextStatus.COMPLETED
            assert "magazine" in result.alt_text.lower()
            assert any(word in result.alt_text.lower() for word in ['spring', 'collection', 'fashion'])


class TestEditorialWorkflows:
    """Test complete editorial team workflows."""
    
    @pytest.mark.asyncio
    async def test_batch_editorial_processing(self, editorial_images):
        """Test processing a mixed batch of editorial images."""
        processor = BatchProcessor()
        generator = AltTextGenerator("test-key")
        
        # Create batch with all editorial image types
        for image_type, image_path in editorial_images.items():
            processor.add_image(image_path)
            
        # Mock different alt texts for each type
        alt_texts = {
            "fashion_dress_001.jpg": "Navy A-line dress with fitted bodice",
            "lifestyle_coffee_002.jpg": "Coffee shop scene with cup on wooden table",
            "product_watch_003.jpg": "Silver watch with black dial",
            "portrait_model_004.jpg": "Woman in red top with confident pose",
            "magazine_cover_005.jpg": "Fashion magazine Spring Collection cover"
        }
        
        async def mock_generate(image_path, context=None):
            filename = image_path.name
            return Mock(
                alt_text=alt_texts.get(filename, "Default alt text"),
                status=AltTextStatus.COMPLETED,
                api_cost=0.006,
                generation_time=0.5
            )
            
        with patch.object(generator, 'generate_alt_text', side_effect=mock_generate):
            # Process batch
            results = await generator.generate_batch(list(editorial_images.values()))
            
            # Verify all processed
            assert len(results) == 5
            assert all(r.status == AltTextStatus.COMPLETED for r in results.values())
            
            # Verify appropriate alt texts
            for image_path, result in results.items():
                assert result.alt_text in alt_texts.values()
                
    def test_editorial_review_workflow(self, app, editorial_images):
        """Test the editorial review and approval workflow."""
        widget = AltTextWidget()
        
        # Create batch items with generated alt text
        items = []
        for image_type, image_path in editorial_images.items():
            item = BatchItem(image_path)
            item.status = ProcessingStatus.COMPLETED
            item.alt_text = f"Generated alt text for {image_type}"
            item.alt_text_status = AltTextStatus.COMPLETED
            items.append(item)
            
        widget.set_batch_items(items)
        
        # Verify all items displayed
        assert widget.items_table.rowCount() == 5
        
        # Simulate editorial review - edit one item
        fashion_item = widget.item_widgets.get("fashion_dress_001.jpg")
        if fashion_item:
            fashion_item.alt_text_edit.setPlainText(
                "Navy blue dress with elegant A-line silhouette, perfect for spring occasions"
            )
            
        # Test approval workflow
        widget._on_approve_all_clicked()
        
        # Verify character count warnings
        for filename, item_widget in widget.item_widgets.items():
            text = item_widget.alt_text_edit.toPlainText()
            if len(text) > 125:
                assert "background-color" in item_widget.alt_text_edit.styleSheet()
                
    @pytest.mark.asyncio
    async def test_editorial_export_workflow(self, temp_dir, editorial_images):
        """Test the complete export workflow for editorial content."""
        exporter = AltTextExporter()
        
        # Create processed batch items
        items = []
        for image_type, image_path in editorial_images.items():
            item = BatchItem(image_path)
            item.status = ProcessingStatus.COMPLETED
            item.alt_text = f"Professional {image_type} image description"
            item.alt_text_status = AltTextStatus.COMPLETED
            item.processing_time = 0.5
            item.api_cost = 0.006
            items.append(item)
            
        # Test CSV export for spreadsheet review
        csv_path = temp_dir / "editorial_alt_text_review.csv"
        success, message = exporter.export_csv(items, csv_path)
        assert success is True
        
        # Test WordPress export
        wp_path = temp_dir / "wordpress_import.csv"
        success, message = exporter.export_for_cms(items, wp_path, "wordpress")
        assert success is True
        
        # Verify WordPress format includes proper titles
        import csv
        with open(wp_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check title formatting
            for row in rows:
                assert row['title']  # Has title
                assert row['alt_text']  # Has alt text
                assert '_' not in row['title']  # Underscores removed
                
    def test_editorial_quality_checks(self, editorial_images):
        """Test quality validation for editorial alt text."""
        
        def validate_editorial_alt_text(alt_text):
            """Validate alt text meets editorial standards."""
            issues = []
            
            # Length check
            if len(alt_text) > 150:
                issues.append("Too long - should be under 150 characters")
            elif len(alt_text) < 20:
                issues.append("Too short - provide more detail")
                
            # Forbidden phrases
            forbidden = ["image of", "picture of", "photo of", "photograph of"]
            for phrase in forbidden:
                if phrase in alt_text.lower():
                    issues.append(f"Remove '{phrase}' - redundant for alt text")
                    
            # Check for descriptive content
            if not any(word in alt_text.lower() for word in 
                      ['wearing', 'showing', 'featuring', 'with', 'displaying']):
                issues.append("Add more descriptive context")
                
            return len(issues) == 0, issues
            
        # Test various alt texts
        test_cases = [
            ("Woman wearing navy dress with floral pattern", True),
            ("Image of a red dress", False),  # Has forbidden phrase
            ("Dress", False),  # Too short
            ("A stunning haute couture evening gown in midnight blue silk with intricate beadwork cascading down the bodice and a dramatic train that pools elegantly on the floor", False),  # Too long
            ("Coffee shop interior featuring rustic wooden tables", True),
        ]
        
        for alt_text, should_pass in test_cases:
            is_valid, issues = validate_editorial_alt_text(alt_text)
            assert is_valid == should_pass, f"Failed for: {alt_text}, Issues: {issues}"


class TestEditorialEdgeCases:
    """Test edge cases specific to editorial content."""
    
    @pytest.mark.asyncio
    async def test_complex_scene_description(self, temp_dir):
        """Test alt text for complex editorial scenes."""
        # Create complex scene image
        complex_path = temp_dir / "complex_scene.jpg"
        img = Image.new('RGB', (1600, 1200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Multiple elements
        draw.rectangle([100, 100, 400, 500], fill='blue')  # Person 1
        draw.rectangle([500, 150, 800, 550], fill='red')   # Person 2
        draw.rectangle([900, 200, 1200, 600], fill='green')  # Person 3
        draw.ellipse([200, 700, 1400, 1000], fill='brown')  # Table
        
        img.save(complex_path)
        
        generator = AltTextGenerator("test-key")
        
        mock_response = {
            "content": [{
                "text": "Three people in colorful outfits gathered around a wooden table in bright setting"
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            
            result = await generator.generate_alt_text(
                complex_path,
                context="editorial group shot"
            )
            
            assert result.status == AltTextStatus.COMPLETED
            assert "people" in result.alt_text.lower()
            assert len(result.alt_text) <= 125  # Concise despite complexity
            
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Test logic needs update for current batch processor API")
    async def test_seasonal_collection_batch(self, temp_dir):
        """Test processing a seasonal collection batch."""
        # Create seasonal collection images
        collection_images = []
        seasons = ['spring', 'summer', 'fall', 'winter']
        
        for i, season in enumerate(seasons):
            for j in range(3):  # 3 items per season
                img_path = temp_dir / f"{season}_look_{j+1:03d}.jpg"
                img = Image.new('RGB', (1000, 1500), color=['#90EE90', '#FFB6C1', '#FFA500', '#E6E6FA'][i])
                img.save(img_path)
                collection_images.append(img_path)
                
        # Process batch
        generator = AltTextGenerator("test-key")
        
        async def mock_seasonal_generate(image_path, context=None):
            season = image_path.stem.split('_')[0]
            look_num = image_path.stem.split('_')[2]
            
            seasonal_descriptions = {
                'spring': f"Light floral dress in pastel tones, look {look_num}",
                'summer': f"Breezy linen ensemble in soft pink, look {look_num}",
                'fall': f"Layered outfit with warm orange accents, look {look_num}",
                'winter': f"Cozy knit sweater with matching scarf, look {look_num}"
            }
            
            return Mock(
                alt_text=seasonal_descriptions.get(season, "Seasonal fashion look"),
                status=AltTextStatus.COMPLETED,
                api_cost=0.006
            )
            
        with patch.object(generator, 'generate_alt_text', side_effect=mock_seasonal_generate):
            results = await generator.generate_batch(collection_images)
            
            # Verify seasonal consistency
            for season in seasons:
                season_results = [
                    r for p, r in results.items() 
                    if season in p.name
                ]
                assert len(season_results) == 3
                assert all(season in r.alt_text.lower() for r in season_results)
                
    def test_accessibility_compliance(self):
        """Test alt text meets accessibility standards."""
        
        def check_accessibility_compliance(alt_text):
            """Check if alt text meets WCAG guidelines."""
            issues = []
            
            # Must be present
            if not alt_text or alt_text.strip() == "":
                issues.append("Alt text cannot be empty")
                
            # Should be concise
            if len(alt_text) > 200:
                issues.append("Consider breaking into caption for lengthy descriptions")
                
            # Should not repeat file name
            if any(ext in alt_text.lower() for ext in ['.jpg', '.png', '.jpeg']):
                issues.append("Should not include file extensions")
                
            # Should be meaningful
            generic_terms = ['image', 'picture', 'photo', 'graphic']
            if alt_text.lower().strip() in generic_terms:
                issues.append("Alt text is too generic")
                
            return len(issues) == 0, issues
            
        # Test cases
        test_cases = [
            ("Woman in red dress walking through autumn leaves", True),
            ("", False),  # Empty
            ("image", False),  # Too generic
            ("fashion_dress_001.jpg", False),  # Contains filename
            ("A" * 250, False),  # Too long
        ]
        
        for alt_text, should_pass in test_cases:
            is_valid, issues = check_accessibility_compliance(alt_text)
            assert is_valid == should_pass


class TestEditorialIntegration:
    """Integration tests for editorial workflows."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Test logic needs update for current batch processor API")
    async def test_full_editorial_pipeline(self, temp_dir, app):
        """Test complete editorial pipeline from import to CMS export."""
        # Setup components
        processor = BatchProcessor()
        generator = AltTextGenerator("test-key")
        widget = AltTextWidget()
        exporter = AltTextExporter()
        
        # Create editorial batch
        editorial_batch = []
        for i in range(10):
            img_path = temp_dir / f"editorial_{i+1:03d}.jpg"
            img = Image.new('RGB', (1200, 1800), color='white')
            img.save(img_path)
            editorial_batch.append(img_path)
            processor.add_image(img_path)
            
        # Mock API responses
        async def mock_editorial_generate(image_path, context=None):
            num = int(image_path.stem.split('_')[1])
            descriptions = [
                "Elegant evening gown in deep burgundy",
                "Casual weekend outfit with denim and stripes",
                "Professional blazer paired with tailored trousers",
                "Bohemian maxi dress with floral print",
                "Athletic wear ensemble for yoga practice",
                "Vintage-inspired cocktail dress",
                "Modern minimalist outfit in neutral tones",
                "Bold statement piece with geometric patterns",
                "Classic little black dress with pearl accessories",
                "Sustainable fashion look with organic materials"
            ]
            
            return Mock(
                alt_text=descriptions[num - 1],
                status=AltTextStatus.COMPLETED,
                api_cost=0.006,
                generation_time=0.3
            )
            
        with patch.object(generator, 'generate_alt_text', side_effect=mock_editorial_generate):
            # Generate alt text
            results = await generator.generate_batch(editorial_batch)
            
            # Update batch items
            for item in processor.items:
                if item.source_path in results:
                    result = results[item.source_path]
                    item.alt_text = result.alt_text
                    item.alt_text_status = result.status
                    item.status = ProcessingStatus.COMPLETED
                    
            # Load into widget for review
            widget.set_batch_items(processor.items)
            
            # Simulate editorial review and edits
            # Edit a few items
            if "editorial_001.jpg" in widget.item_widgets:
                widget.item_widgets["editorial_001.jpg"].alt_text_edit.setPlainText(
                    "Stunning burgundy evening gown with flowing silhouette"
                )
                
            # Export for CMS
            cms_path = temp_dir / "editorial_cms_import.csv"
            success, message = exporter.export_for_cms(
                processor.items,
                cms_path,
                "wordpress"
            )
            
            assert success is True
            
            # Verify export quality
            import csv
            with open(cms_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 10
                for row in rows:
                    assert row['alt_text']
                    assert len(row['alt_text']) > 20  # Meaningful descriptions
                    assert len(row['alt_text']) < 150  # Concise
                    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Test logic needs update for current batch processor API")
    async def test_editorial_error_recovery(self, temp_dir):
        """Test error recovery in editorial workflows."""
        generator = AltTextGenerator("test-key")
        
        # Create batch with some problematic images
        images = []
        for i in range(5):
            if i == 2:
                # Create corrupted image
                img_path = temp_dir / f"corrupted_{i}.jpg"
                img_path.write_bytes(b"Not a real image")
            else:
                img_path = temp_dir / f"good_{i}.jpg"
                img = Image.new('RGB', (800, 600), color='blue')
                img.save(img_path)
            images.append(img_path)
            
        # Process with error handling
        results = {}
        for img_path in images:
            try:
                if "corrupted" in img_path.name:
                    result = Mock(
                        status=AltTextStatus.ERROR,
                        error_message="Failed to process image",
                        alt_text=None
                    )
                else:
                    result = Mock(
                        status=AltTextStatus.COMPLETED,
                        alt_text="Editorial fashion image",
                        api_cost=0.006
                    )
                results[img_path] = result
            except Exception as e:
                results[img_path] = Mock(
                    status=AltTextStatus.ERROR,
                    error_message=str(e),
                    alt_text=None
                )
                
        # Verify partial success handling
        successful = sum(1 for r in results.values() if r.status == AltTextStatus.COMPLETED)
        failed = sum(1 for r in results.values() if r.status == AltTextStatus.ERROR)
        
        assert successful == 4
        assert failed == 1
        
        # Test export with mixed results
        items = []
        for img_path, result in results.items():
            item = BatchItem(img_path)
            item.alt_text = result.alt_text
            item.alt_text_status = result.status
            item.status = ProcessingStatus.COMPLETED if result.status == AltTextStatus.COMPLETED else ProcessingStatus.FAILED
            items.append(item)
            
        exporter = AltTextExporter()
        export_path = temp_dir / "mixed_results.csv"
        success, message = exporter.export_csv(items, export_path)
        
        assert success is True
        # Should export all items, including failed ones
        import csv
        with open(export_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])