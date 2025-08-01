"""
Demonstration of alt text generation integration in FootFix.
This shows how the alt text feature can be used programmatically.
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from footfix.core import BatchProcessor, AltTextGenerator
from footfix.utils.preferences import PreferencesManager


async def demo_alt_text_generation():
    """Demonstrate alt text generation workflow."""
    
    print("FootFix Alt Text Generation Demo")
    print("=" * 50)
    
    # Initialize preferences and check for API key
    prefs = PreferencesManager()
    api_key = prefs.get('alt_text.api_key')
    
    if not api_key:
        print("\n⚠️  No API key found in preferences.")
        print("To use alt text generation:")
        print("1. Get an API key from https://console.anthropic.com/")
        print("2. Set it in preferences: prefs.set('alt_text.api_key', 'your-key')")
        print("3. Save preferences: prefs.save()")
        return
    
    # Create batch processor
    processor = BatchProcessor()
    
    # Enable alt text generation
    processor.set_alt_text_generation(True, api_key)
    processor.set_alt_text_context("editorial fashion photography")
    
    print("\n✓ Alt text generation enabled")
    print(f"✓ Context: {processor.alt_text_context}")
    
    # Example: Add images to queue
    image_folder = Path.home() / "Pictures"  # Change to your image folder
    print(f"\nLooking for images in: {image_folder}")
    
    # Add some sample images (adjust paths as needed)
    sample_images = [
        image_folder / "sample1.jpg",
        image_folder / "sample2.jpg",
        image_folder / "sample3.jpg",
    ]
    
    added_count = 0
    for img_path in sample_images:
        if img_path.exists():
            if processor.add_image(img_path):
                added_count += 1
                print(f"✓ Added: {img_path.name}")
        else:
            print(f"✗ Not found: {img_path.name}")
    
    if added_count == 0:
        print("\n⚠️  No images found. Please adjust the sample_images paths.")
        return
    
    print(f"\n📸 Processing {added_count} images...")
    
    # Process batch with alt text
    output_folder = Path.home() / "Downloads" / "footfix_with_alt"
    results = processor.process_batch_with_alt_text("web_optimized", output_folder)
    
    # Display results
    print("\n" + "=" * 50)
    print("Processing Results:")
    print(f"✓ Images processed: {results['successful']}")
    print(f"✗ Failed: {results.get('failed', 0)}")
    
    if 'alt_text_generated' in results:
        print(f"\n📝 Alt text generated: {results['alt_text_generated']}")
        print(f"✗ Alt text failed: {results.get('alt_text_failed', 0)}")
    
    # Display generated alt text
    print("\n" + "=" * 50)
    print("Generated Alt Text:")
    for item in processor.queue:
        if item.alt_text:
            print(f"\n📸 {item.source_path.name}:")
            print(f"   {item.alt_text}")
    
    # Cost estimation
    if added_count > 0:
        cost_info = processor.alt_text_generator.estimate_batch_cost(added_count)
        print("\n" + "=" * 50)
        print("Cost Estimation:")
        print(f"💰 This batch: ${cost_info['total']:.3f}")
        print(f"💰 Per image: ${cost_info['per_image']:.3f}")
        print(f"💰 Monthly estimate (20 batches): ${cost_info['monthly_estimate']:.2f}")


def main():
    """Run the demo."""
    # Check if running in async context
    try:
        asyncio.run(demo_alt_text_generation())
    except RuntimeError:
        # Already in async context
        loop = asyncio.get_event_loop()
        loop.run_until_complete(demo_alt_text_generation())


if __name__ == "__main__":
    main()