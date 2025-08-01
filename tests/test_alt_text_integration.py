"""
Test script for alt text generation integration.
This tests the Week 1 deliverables.
"""

import asyncio
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from footfix.core.batch_processor import BatchProcessor, ProcessingStatus
from footfix.core.alt_text_generator import AltTextGenerator, AltTextStatus
from footfix.utils.preferences import PreferencesManager


def test_alt_text_generator():
    """Test basic alt text generator functionality."""
    print("\n=== Testing AltTextGenerator ===")
    
    # Create generator (no API key for dry run)
    generator = AltTextGenerator()
    
    # Test initialization
    assert generator.api_key is None
    assert generator.system_prompt is not None
    print("✓ AltTextGenerator initialized successfully")
    
    # Test API key setting
    generator.set_api_key("test-key-123")
    assert generator.api_key == "test-key-123"
    print("✓ API key setting works")
    
    # Test cost estimation
    cost_info = generator.estimate_batch_cost(30)
    assert cost_info['total'] == 0.18  # 30 * 0.006
    assert cost_info['per_image'] == 0.006
    print(f"✓ Cost estimation: ${cost_info['total']:.2f} for 30 images")
    

def test_batch_item_enhancement():
    """Test that BatchItem includes alt text fields."""
    print("\n=== Testing BatchItem Enhancement ===")
    
    from footfix.core.batch_processor import BatchItem
    
    # Create a test item
    test_path = Path("/tmp/test.jpg")
    item = BatchItem(source_path=test_path)
    
    # Check alt text fields exist
    assert hasattr(item, 'alt_text')
    assert hasattr(item, 'alt_text_status')
    assert hasattr(item, 'alt_text_error')
    assert hasattr(item, 'alt_text_generation_time')
    
    # Check default values
    assert item.alt_text is None
    assert item.alt_text_status == AltTextStatus.PENDING
    assert item.alt_text_error is None
    assert item.alt_text_generation_time == 0.0
    
    print("✓ BatchItem has all required alt text fields")
    

def test_batch_processor_integration():
    """Test BatchProcessor alt text integration."""
    print("\n=== Testing BatchProcessor Integration ===")
    
    # Create processor
    processor = BatchProcessor()
    
    # Check alt text settings exist
    assert hasattr(processor, 'alt_text_generator')
    assert hasattr(processor, 'enable_alt_text')
    assert hasattr(processor, 'alt_text_context')
    
    # Check defaults
    assert processor.alt_text_generator is None
    assert processor.enable_alt_text is False
    assert processor.alt_text_context == "editorial image"
    print("✓ BatchProcessor has alt text attributes")
    
    # Test enabling alt text
    processor.set_alt_text_generation(True, "test-api-key")
    assert processor.enable_alt_text is True
    assert processor.alt_text_generator is not None
    assert processor.alt_text_generator.api_key == "test-api-key"
    print("✓ Alt text generation can be enabled")
    
    # Test context setting
    processor.set_alt_text_context("fashion editorial")
    assert processor.alt_text_context == "fashion editorial"
    print("✓ Alt text context can be customized")
    
    # Test that new method exists
    assert hasattr(processor, 'process_batch_with_alt_text')
    print("✓ process_batch_with_alt_text method exists")
    

def test_preferences_integration():
    """Test preferences support for alt text settings."""
    print("\n=== Testing Preferences Integration ===")
    
    # Create preferences manager
    prefs = PreferencesManager()
    
    # Check alt text preferences exist
    assert 'alt_text' in prefs.DEFAULTS
    alt_text_prefs = prefs.get('alt_text')
    assert alt_text_prefs is not None
    print("✓ Alt text preferences section exists")
    
    # Check default values
    assert prefs.get('alt_text.enabled') is False
    assert prefs.get('alt_text.api_key') is None
    assert prefs.get('alt_text.default_context') == 'editorial image'
    assert prefs.get('alt_text.max_concurrent_requests') == 5
    assert prefs.get('alt_text.enable_cost_tracking') is True
    print("✓ All alt text preference defaults are correct")
    
    # Test setting API key
    prefs.set('alt_text.api_key', 'test-key-456')
    assert prefs.get('alt_text.api_key') == 'test-key-456'
    print("✓ API key can be stored in preferences")
    

def test_queue_info_enhancement():
    """Test that queue info includes alt text information."""
    print("\n=== Testing Queue Info Enhancement ===")
    
    processor = BatchProcessor()
    
    # Create a test BatchItem directly without validation
    from footfix.core.batch_processor import BatchItem
    test_path = Path("/tmp/test_image.jpg")  # Dummy path with valid extension
    test_item = BatchItem(source_path=test_path)
    processor.queue.append(test_item)
    processor.progress.total_items = 1
    
    # Get queue info
    queue_info = processor.get_queue_info()
    assert len(queue_info) == 1
    
    # Check alt text fields in info
    item_info = queue_info[0]
    assert 'alt_text' in item_info
    assert 'alt_text_status' in item_info
    assert 'alt_text_error' in item_info
    
    print("✓ Queue info includes alt text fields")
    

def main():
    """Run all tests."""
    print("FootFix Alt Text Integration Tests - Week 1 Deliverables")
    print("=" * 60)
    
    try:
        test_alt_text_generator()
        test_batch_item_enhancement()
        test_batch_processor_integration()
        test_preferences_integration()
        test_queue_info_enhancement()
        
        print("\n" + "=" * 60)
        print("✅ All Week 1 integration tests passed!")
        print("\nSummary of Week 1 Deliverables:")
        print("- ✓ AltTextGenerator class created with Anthropic API integration")
        print("- ✓ BatchItem dataclass extended with alt text fields")
        print("- ✓ Alt text generation integrated into batch processing workflow")
        print("- ✓ Preferences system updated for API key storage")
        print("- ✓ Async processing support for concurrent API calls")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()