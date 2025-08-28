# FootFix User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Single Image Processing](#single-image-processing)
6. [Batch Processing](#batch-processing)
7. [AI Alt Text Generation](#ai-alt-text-generation)
8. [Advanced Features](#advanced-features)
9. [Presets](#presets)
10. [Keyboard Shortcuts](#keyboard-shortcuts)
11. [Troubleshooting](#troubleshooting)
12. [FAQ](#faq)

## Introduction

FootFix is a professional image processing application designed specifically for editorial teams. It provides powerful batch processing capabilities with an intuitive macOS interface, allowing you to quickly resize, optimize, and enhance multiple images while maintaining consistent quality.

### Key Features
- **Batch Processing**: Process multiple images simultaneously with progress tracking
- **Smart Resizing**: Maintain aspect ratios with percentage-based scaling
- **Quality Optimization**: Fine-tune JPEG quality for optimal file sizes
- **Image Enhancement**: Built-in sharpening and color optimization
- **AI Alt Text Generation**: Create professional image descriptions using Claude Vision API
- **Preset Management**: Save and reuse your favorite settings
- **Before/After Preview**: Compare original and processed images side-by-side
- **Native macOS Integration**: Menu bar, keyboard shortcuts, and drag-and-drop support

## System Requirements

- **Operating System**: macOS 10.15 (Catalina) or later
- **Processor**: Intel or Apple Silicon (M1/M2/M3)
- **Memory**: 4GB RAM minimum (8GB recommended for large batches)
- **Storage**: 100MB for application, plus space for processed images
- **Display**: Retina display supported

## Installation

### Installing from DMG

1. **Download** FootFix-1.0.0.dmg from the provided location
2. **Double-click** the DMG file to mount it
3. **Drag** the FootFix application to your Applications folder
4. **Eject** the DMG by clicking the eject button in Finder
5. **Launch** FootFix from your Applications folder or Spotlight

### First Launch

On first launch, macOS may show a security warning:
1. Click **OK** on the warning dialog
2. Go to **System Preferences** > **Security & Privacy**
3. Click **Open Anyway** next to the FootFix message
4. Click **Open** in the confirmation dialog

## Getting Started

### Main Interface Overview

When you launch FootFix, you'll see the main window with three tabs:

1. **Single Image** - Process one image at a time with live preview
2. **Batch Processing** - Process multiple images with the same settings
3. **Alt Text** - Generate and review AI-powered image descriptions

### Quick Start

1. **Choose a tab** based on your needs (Single or Batch)
2. **Load images** using drag-and-drop or the "Browse" button
3. **Select a preset** or adjust settings manually
4. **Choose output location** and filename options
5. **Click Process** to start

## Single Image Processing

### Loading an Image

Three ways to load an image:
1. **Drag and drop** an image file onto the preview area
2. Click **Browse** and select an image
3. Use **File > Open** from the menu bar (⌘O)

### Adjusting Settings

#### Basic Settings
- **Resize**: Set percentage (10-200%) to scale the image
- **Quality**: JPEG compression level (1-100, higher = better quality)
- **Format**: Choose output format (JPEG, PNG, BMP, TIFF)

#### Advanced Settings
- **Enable Sharpening**: Enhance image clarity
- **Sharpen Amount**: Intensity of sharpening (0.5-3.0)
- **Auto Color Balance**: Automatically adjust colors
- **Auto Contrast**: Optimize image contrast

### Preview Options

- **Zoom**: Click the zoom buttons or use scroll wheel
- **Compare**: Toggle between original and preview
- **Split View**: See before/after side-by-side
- **Fit to Window**: Auto-scale preview to window size

### Processing

1. Review your settings in the preview
2. Choose output location (defaults to source folder)
3. Set filename template (e.g., "{name}_edited")
4. Click **Process Image**
5. View the result in your file browser

## Batch Processing

### Adding Images

Multiple ways to add images for batch processing:
1. **Drag and drop** multiple files onto the file list
2. Click **Add Images** to browse and select multiple files
3. Drag a **folder** to add all images inside

### Managing the Queue

- **Remove**: Select images and press Delete or click Remove
- **Clear All**: Remove all images from the queue
- **Sort**: Click column headers to sort by name, size, or status
- **Select All**: ⌘A to select all images

### Batch Settings

Settings apply to all images in the batch:
- Use the same controls as single image processing
- Preview shows the first selected image
- All images use identical settings

### Processing Options

- **Output Directory**: Choose where to save processed images
  - Same as source: Each image saved in its original folder
  - Custom folder: All images saved to one location
- **Filename Pattern**: Set naming for all output files
- **Overwrite Protection**: Automatically rename if file exists

### Progress Tracking

During batch processing:
- **Progress Bar**: Shows overall completion
- **Current Image**: Displays which image is processing
- **Time Estimate**: Shows remaining time
- **Cancel**: Stop processing at any time
- **Status Icons**: ✓ = Complete, ⚠️ = Warning, ✗ = Failed

## AI Alt Text Generation

FootFix includes powerful AI-driven alt text generation using Anthropic's Claude Vision API. This feature helps create professional, accessibility-compliant image descriptions for editorial content.

### Setting Up Alt Text

1. **Configure API Key**:
   - Open Preferences (⌘,)
   - Go to Alt Text tab
   - Enter your Anthropic API key
   - Click "Validate Key"

2. **First Time Setup**:
   - Get an API key from [console.anthropic.com](https://console.anthropic.com)
   - Enable cost tracking (optional)
   - Set monthly budget alerts

### Generating Alt Text

#### For Processed Images

1. Process your images normally
2. Switch to the **Alt Text** tab
3. Click **Generate Alt Text**
4. Review generated descriptions
5. Edit as needed for brand voice

#### Batch Generation

1. Select multiple images
2. Click **Generate for All**
3. Monitor progress bar
4. Costs approximately $0.006 per image

### Reviewing and Editing

The Alt Text tab shows:
- Image thumbnails
- Generated descriptions
- Character count (optimal: 50-125)
- Status indicators
- Edit capabilities

**Best Practices**:
- Keep under 125 characters
- Be descriptive yet concise
- Avoid "image of" or "picture of"
- Include relevant context

### Exporting Alt Text

#### Export Formats

1. **CSV**: For spreadsheet review
   - Includes all metadata
   - Easy bulk editing
   - Excel compatible

2. **JSON**: For developers
   - Structured data
   - API integration ready
   - Includes statistics

3. **WordPress**: CMS-ready format
   - Proper column mapping
   - Import-ready CSV
   - Title generation

#### Export Workflow

1. Click **Export** dropdown
2. Choose format
3. Select scope:
   - All items
   - Selected only
   - Completed only
4. Save to location

### Cost Management

**Current Pricing**: ~$0.006 per image

**Monthly Estimates**:
- 100 images: $0.60
- 1,000 images: $6.00
- 5,000 images: $30.00

**Tracking Usage**:
- View in Preferences
- Monthly summaries
- Cost per session

## Advanced Features

### Custom Filename Templates

Create sophisticated naming patterns:

- `{name}` - Original filename (without extension)
- `{date}` - Current date (YYYY-MM-DD)
- `{time}` - Current time (HH-MM-SS)
- `{counter}` - Sequential number
- `{counter:03d}` - Padded counter (001, 002, etc.)
- `{width}` - Image width in pixels
- `{height}` - Image height in pixels
- `{preset}` - Name of preset used

**Examples:**
- `{name}_resized_{date}` → `photo_resized_2024-03-15.jpg`
- `IMG_{counter:04d}` → `IMG_0001.jpg`
- `{name}_{width}x{height}` → `photo_1920x1080.jpg`

### Preferences

Access via **FootFix > Preferences** (⌘,):

#### General
- Default output directory
- Default filename template
- Startup behavior
- Update checking

#### Processing
- Default resize percentage
- Default quality setting
- Auto-enhancement options
- Memory usage limits

#### Alt Text
- API key configuration
- Cost tracking settings
- Usage statistics
- Export preferences

#### Interface
- Theme (Light/Dark/Auto)
- Preview quality
- Thumbnail size
- Show tooltips

### Menu Bar Actions

#### File Menu
- New Window (⌘N)
- Open Image (⌘O)
- Open Recent
- Close Window (⌘W)

#### Edit Menu
- Copy Settings (⌘C)
- Paste Settings (⌘V)
- Reset Settings

#### View Menu
- Show/Hide Sidebar
- Zoom In/Out
- Actual Size (⌘0)
- Fit to Window (⌘9)

#### Window Menu
- Minimize (⌘M)
- Bring All to Front
- Show Previous/Next Tab

## Presets

### Using Built-in Presets

FootFix includes several presets for common tasks:

- **Default**: Balanced settings for general use
- **High Quality**: Maximum quality, larger files
- **Web Optimized**: Smaller files for web use
- **Email Attachment**: Very small files for emailing
- **Print Ready**: High resolution for printing
- **Social Media**: Optimized for social platforms

### Creating Custom Presets

1. Adjust settings to your preference
2. Click the **Save Preset** button (+ icon)
3. Enter a descriptive name
4. Click Save

### Managing Presets

- **Edit**: Select preset and click edit icon
- **Delete**: Select preset and click trash icon
- **Export**: Share presets with team members
- **Import**: Load presets from colleagues

## Keyboard Shortcuts

### Essential Shortcuts
- **⌘O** - Open image
- **⌘S** - Process current image
- **⌘,** - Open preferences
- **⌘Q** - Quit FootFix
- **Space** - Toggle preview
- **⌘Z** - Undo last change

### Navigation
- **⌘1** - Single image tab
- **⌘2** - Batch processing tab
- **⌘3** - Alt text tab
- **⌘[** - Previous image (in batch)
- **⌘]** - Next image (in batch)

### Alt Text Shortcuts
- **⌘G** - Generate alt text
- **⌘R** - Regenerate selected
- **⌘E** - Export alt text

### View Controls
- **⌘+** - Zoom in
- **⌘-** - Zoom out
- **⌘0** - Actual size
- **⌘9** - Fit to window

## Troubleshooting

### Common Issues

#### "Can't open FootFix" on first launch
- Right-click FootFix and choose "Open"
- Go to System Preferences > Security & Privacy
- Click "Open Anyway"

#### Images look blurry after processing
- Check your resize percentage (may be too low)
- Enable sharpening in advanced settings
- Increase sharpen amount (try 1.2-1.5)

#### Batch processing is slow
- Process fewer images at once
- Close other applications
- Check available disk space
- Reduce output quality slightly

#### "Failed to process image" error
- Check file permissions
- Ensure output directory is writable
- Try a different output format
- Image may be corrupted

#### Alt text generation issues
- **"Invalid API key"**: Verify key in Preferences
- **"Rate limited"**: Wait 60 seconds or upgrade plan
- **"Network error"**: Check internet connection
- **"No alt text generated"**: Try regenerating

### Performance Tips

1. **For large batches** (50+ images):
   - Process in smaller groups
   - Use lower quality settings
   - Close preview during processing

2. **For large files** (RAW, TIFF):
   - Allow extra processing time
   - Ensure adequate free disk space
   - Consider converting to JPEG first

3. **Memory management**:
   - Restart FootFix after processing 200+ images
   - Clear recent files list periodically
   - Monitor Activity Monitor if needed

## FAQ

**Q: Can FootFix process RAW files?**
A: Yes, FootFix supports most RAW formats and will convert them to your chosen output format.

**Q: How do I process images from different folders?**
A: Use batch processing and add images from multiple locations. They'll all be processed with the same settings.

**Q: Can I stop batch processing partway through?**
A: Yes, click the Cancel button. Already processed images will be kept.

**Q: Where are my presets stored?**
A: Presets are saved in `~/Library/Application Support/FootFix/presets/`

**Q: Can I use FootFix from the command line?**
A: Not currently, but this feature is planned for a future update.

**Q: How do I reset all settings?**
A: Hold Option while launching FootFix, or delete `~/Library/Preferences/com.footfix.imageprocessor.plist`

**Q: Is there a Windows version?**
A: FootFix is currently macOS only, optimized for the Mac experience.

**Q: How much does alt text generation cost?**
A: Approximately $0.006 per image. 1,000 images cost about $6.00.

**Q: Can I use my own AI service for alt text?**
A: Currently FootFix only supports Anthropic's Claude Vision API.

**Q: Are alt texts saved with the images?**
A: Alt texts are stored in FootFix and can be exported in various formats.

**Q: Can I edit alt text after generation?**
A: Yes, all generated alt text can be reviewed and edited before export.

## Support

For additional help:
- Check for updates via FootFix > Check for Updates
- Review the changelog for new features
- Contact your IT administrator for site-specific settings

---

*FootFix Version 1.1.0 - Professional Image Processing with AI Alt Text for Editorial Teams*