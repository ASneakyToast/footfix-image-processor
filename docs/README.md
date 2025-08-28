# FootFix

**Image processing desktop application for editorial teams**

FootFix streamlines image optimization workflows by automating the manual process of resizing and compressing images for web content. Designed as a user-friendly alternative to complex image editing software, it enables editorial teams to efficiently process batches of images while maintaining quality standards.

## Features

### Phase 2 - Enhanced Batch Processing (NEW!)
- **Advanced Queue Management**: Add/remove images before processing starts
- **Folder Processing**: Drag entire folders to process all images inside
- **Real-time Progress**: Track current image, time elapsed, and estimated time remaining
- **Error Resilience**: Individual image failures don't stop the entire batch
- **Background Processing**: Keep working while images process in the background
- **Cancel Support**: Stop batch processing at any time without losing completed work

### Core Features
- **Batch Processing**: Process 6-30+ images simultaneously with detailed progress tracking
- **Preset Profiles**: Four optimized profiles for different use cases:
  - Editorial Web (max 2560×1440px, 0.5-1MB target)
  - Email Marketing (max 600px width, <100KB target)
  - Instagram Story (1080×1920px, 9:16 aspect ratio)
  - Instagram Feed Portrait (1080×1350px, 4:5 aspect ratio)
- **Smart Drag & Drop**: 
  - Single images open in single processing mode
  - Multiple images or folders automatically switch to batch mode
  - Visual feedback during drag operations
- **Dual Processing Modes**: Single image tab for quick edits, batch tab for bulk operations
- **Multiple Formats**: Support for JPEG, PNG, and TIFF input files
- **Smart Output**: Automatic file naming based on preset and original filename

## Requirements

### System Requirements
- macOS 10.15 or later
- 8GB RAM minimum (16GB recommended)
- 1GB free disk space

### Dependencies
- Python 3.8 or higher
- PySide6 6.5.0+
- Pillow 10.0.0+
- NumPy 1.24.0+

## Installation

### Option 1: From Source
```bash
# Clone the repository
git clone https://github.com/footfix/footfix.git
cd footfix

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Option 2: Using pip
```bash
pip install footfix
footfix
```

## Usage

### Single Image Processing
1. **Launch the application**: Run `python main.py` or `footfix` command
2. **Stay on Single Image tab**: The default tab for quick processing
3. **Add image**: Drag and drop a single image or click "Select Image"
4. **Select preset**: Choose your desired output profile
5. **Process**: Click "Process Image" to optimize
6. **Find output**: Processed image is saved to your selected folder

### Batch Processing
1. **Launch the application**: Run `python main.py` or `footfix` command
2. **Switch to Batch Processing tab**: For multiple images
3. **Add images**: Use any of these methods:
   - Click "Add Images" to select multiple files
   - Click "Add Folder" to add all images from a directory
   - Drag and drop multiple files or folders onto the window
4. **Manage queue**: Review and remove unwanted images if needed
5. **Select preset**: Choose your output profile (applies to all images)
6. **Start processing**: Click "Start Processing" and monitor progress
7. **Find outputs**: All processed images are saved to your selected folder

### Supported Input Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)

### Output Formats
- JPEG (default for most content)
- PNG (when transparency is needed)

## Development

### Setup Development Environment
```bash
# Clone and enter directory
git clone https://github.com/footfix/footfix.git
cd footfix

# Install development dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8

# Type checking
mypy footfix/
```

### Project Structure
```
footfix/
├── build/                 # Build scripts and assets
│   ├── setup_app.py       # macOS app packaging
│   ├── assets/            # App icons and build resources
│   └── *.sh              # Build automation scripts
├── docs/                  # Documentation
│   └── guides/            # User and developer documentation
├── playgrounds/           # Experimental scripts and demos
├── footfix/               # Main application package
│   ├── core/              # Image processing engine
│   ├── gui/               # PySide6 user interface
│   ├── presets/           # Processing profiles
│   ├── qml_ui/            # QML-based UI components
│   └── utils/             # Utility functions
└── tests/                 # Test suite
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

See [PROJECT_EPIC.md](PROJECT_EPIC.md) for detailed project specifications and future roadmap.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

*FootFix - Making image optimization as easy as dragging and dropping.*