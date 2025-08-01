#!/usr/bin/env python3
"""
Test script to verify the Alt Text API fix.
Run this to test if the 404 error is resolved.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from footfix.core.alt_text_generator import AltTextGenerator

async def test_api_validation():
    """Test API key validation with the new model."""
    print("Testing Alt Text API Fix...")
    print("=" * 50)
    
    # Test without API key
    print("1. Testing without API key:")
    generator = AltTextGenerator()
    is_valid, message = await generator.validate_api_key()
    print(f"   Result: {is_valid}")
    print(f"   Message: {message}")
    print()
    
    # Test with placeholder API key (will fail but show proper error)
    print("2. Testing with placeholder API key:")
    generator = AltTextGenerator("test-key-12345")
    is_valid, message = await generator.validate_api_key()
    print(f"   Result: {is_valid}")
    print(f"   Message: {message}")
    print()
    
    # Show current model being used
    print("3. Current configuration:")
    print(f"   Model: {generator.MODEL}")
    print(f"   API URL: {generator.API_BASE_URL}")
    print(f"   API Version: {generator.API_VERSION}")
    print()
    
    print("API fix verification complete!")
    print("If you have a valid Anthropic API key, set it in Preferences → Alt Text")
    print("and test again. The 404 error should now be resolved!")

if __name__ == "__main__":
    asyncio.run(test_api_validation())