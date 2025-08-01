# FootFix

**Image processing desktop application for editorial teams**

FootFix streamlines image optimization workflows by automating the manual process of resizing and compressing images for web content. Designed as a user-friendly alternative to complex image editing software, it enables editorial teams to efficiently process batches of images while maintaining quality standards.

## Features

- **Batch Processing**: Process 6-30 images simultaneously with progress tracking
- **Preset Profiles**: Three optimized profiles for different use cases:
  - Editorial Web (max 2560×1440px, 0.5-1MB target)
  - Social Media (Instagram Story/Feed optimized)
  - Email Marketing (max 600px width, <100KB target)
- **Drag & Drop Interface**: Simply drag images into the application to start processing
- **Before/After Preview**: Compare original and optimized images before final processing
- **Multiple Formats**: Support for JPEG, PNG, and TIFF input files
- **Custom Settings**: Advanced options for power users with manual overrides
- **Smart Output**: Automatic file naming and organization

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

1. **Launch the application**: Run `python main.py` or `footfix` command
2. **Add images**: Drag and drop images or folders into the application window
3. **Select preset**: Choose from Editorial Web, Social Media, or Email profiles
4. **Preview results**: Use the before/after preview to check quality
5. **Process**: Click process to optimize your images
6. **Find outputs**: Processed images are saved to your Downloads folder by default

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
├── core/           # Image processing engine
├── gui/            # PySide6 user interface
├── presets/        # Processing profiles
├── utils/          # Utility functions
└── tests/          # Test suite
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