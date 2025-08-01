#!/usr/bin/env python3
"""
Create application icon for FootFix
Generates all required icon sizes for macOS
"""

import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def create_base_icon(size=1024):
    """Create the base FootFix icon design"""
    # Create a new image with a gradient background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background gradient (blue to purple)
    for y in range(size):
        r = int(70 + (y / size) * 30)
        g = int(130 - (y / size) * 30)
        b = int(200 + (y / size) * 55)
        draw.rectangle([(0, y), (size, y+1)], fill=(r, g, b, 255))
    
    # Add rounded corners
    corner_radius = size // 8
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size, size)], radius=corner_radius, fill=255)
    
    # Apply mask for rounded corners
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0))
    output.putalpha(mask)
    
    # Draw the FootFix logo elements
    draw = ImageDraw.Draw(output)
    
    # Camera/lens icon in the center
    center_x, center_y = size // 2, size // 2
    lens_radius = size // 4
    
    # Outer lens circle
    draw.ellipse(
        [(center_x - lens_radius, center_y - lens_radius),
         (center_x + lens_radius, center_y + lens_radius)],
        outline=(255, 255, 255, 255),
        width=size // 20
    )
    
    # Inner lens circle
    inner_radius = lens_radius // 2
    draw.ellipse(
        [(center_x - inner_radius, center_y - inner_radius),
         (center_x + inner_radius, center_y + inner_radius)],
        outline=(255, 255, 255, 200),
        width=size // 30
    )
    
    # Aperture blades
    blade_count = 6
    blade_length = inner_radius * 0.8
    for i in range(blade_count):
        angle = (360 / blade_count) * i
        x1 = center_x + int(blade_length * 0.3 * 
                           np.cos(np.radians(angle)))
        y1 = center_y + int(blade_length * 0.3 * 
                           np.sin(np.radians(angle)))
        x2 = center_x + int(blade_length * 
                           np.cos(np.radians(angle)))
        y2 = center_y + int(blade_length * 
                           np.sin(np.radians(angle)))
        draw.line([(x1, y1), (x2, y2)], 
                 fill=(255, 255, 255, 150), 
                 width=size // 50)
    
    # Add "FF" text at the bottom
    try:
        # Try to use a system font
        font_size = size // 8
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "FF"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = center_x - text_width // 2
    text_y = center_y + lens_radius + size // 20
    
    # Text shadow
    draw.text((text_x + 3, text_y + 3), text, 
             fill=(0, 0, 0, 100), font=font)
    # Main text
    draw.text((text_x, text_y), text, 
             fill=(255, 255, 255, 255), font=font)
    
    return output


def generate_iconset():
    """Generate all required icon sizes for macOS"""
    # Required sizes for macOS iconset
    sizes = [
        (16, "16x16"),
        (32, "16x16@2x"),
        (32, "32x32"),
        (64, "32x32@2x"),
        (128, "128x128"),
        (256, "128x128@2x"),
        (256, "256x256"),
        (512, "256x256@2x"),
        (512, "512x512"),
        (1024, "512x512@2x"),
    ]
    
    # Create iconset directory
    iconset_path = Path("assets/FootFix.iconset")
    iconset_path.mkdir(parents=True, exist_ok=True)
    
    # Import numpy for the icon generation
    global np
    import numpy as np
    
    # Generate base icon
    print("Generating FootFix application icon...")
    base_icon = create_base_icon(1024)
    
    # Generate all sizes
    for size, name in sizes:
        resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)
        icon_path = iconset_path / f"icon_{name}.png"
        resized.save(icon_path, "PNG")
        print(f"  Created {name} ({size}x{size})")
    
    # Create the .icns file using iconutil
    print("\nCreating .icns file...")
    os.system(f"iconutil -c icns '{iconset_path}' -o 'assets/FootFix.icns'")
    
    # Clean up iconset directory
    import shutil
    shutil.rmtree(iconset_path)
    
    print("✅ Icon generation complete: assets/FootFix.icns")


def create_dmg_background():
    """Create a background image for the DMG installer"""
    width, height = 600, 400
    img = Image.new('RGB', (width, height), (245, 245, 247))
    draw = ImageDraw.Draw(img)
    
    # Add subtle gradient
    for y in range(height):
        gray = 245 - int((y / height) * 10)
        draw.rectangle([(0, y), (width, y+1)], fill=(gray, gray, gray+2))
    
    # Add FootFix branding
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        font_subtitle = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
    
    # Title
    draw.text((width//2 - 80, 50), "FootFix", 
             fill=(70, 130, 200), font=font_title)
    
    # Subtitle
    draw.text((width//2 - 140, 110), "Professional Image Processing", 
             fill=(100, 100, 100), font=font_subtitle)
    
    # Installation instructions
    draw.text((width//2 - 180, height - 100), 
             "Drag FootFix to your Applications folder", 
             fill=(150, 150, 150), font=font_subtitle)
    
    # Save background
    img.save("assets/dmg_background.png", "PNG")
    print("✅ DMG background created: assets/dmg_background.png")


if __name__ == "__main__":
    generate_iconset()
    create_dmg_background()