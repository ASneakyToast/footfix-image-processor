# FootFix Build Documentation

## Overview

This document describes how to build FootFix from source, create distribution packages, and manage releases.

## Prerequisites

### Development Environment
- macOS 10.15 (Catalina) or later
- Python 3.8 or later
- Xcode Command Line Tools
- Git

### Required Tools
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Python (if not already installed)
# Recommended: Use Homebrew
brew install python@3.11

# Verify installations
python3 --version
git --version
```

## Setting Up Development Environment

### 1. Clone the Repository
```bash
git clone <repository-url>
cd image-processor-footfix
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies
```bash
# Install all requirements
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-qt black flake8 mypy
```

### 4. Verify Installation
```bash
# Run the application in development mode
python main.py

# Run tests
pytest footfix/tests/ -v

# Run linting
flake8 footfix/
black --check footfix/
```

## Building the Application

### Quick Build
```bash
# Use the provided build script
./build_app.sh
```

### Manual Build Process

#### 1. Clean Previous Builds
```bash
rm -rf build dist *.egg-info
rm -rf FootFix.app
```

#### 2. Run Tests
```bash
# Unit tests
pytest footfix/tests/ -v

# Integration tests
python test_phase4_features.py

# Performance tests (optional)
python test_performance.py
```

#### 3. Generate Application Icon
```bash
# Create icon if not exists
python create_app_icon.py
```

#### 4. Build with py2app
```bash
# Build the application bundle
python setup_app.py py2app

# The app will be in dist/FootFix.app
```

#### 5. Verify Build
```bash
# Check app structure
ls -la dist/FootFix.app/Contents/

# Test the built app
open dist/FootFix.app
```

## Creating Distribution Package

### DMG Creation

#### Automated Method
```bash
./create_dmg.sh
```

#### Manual DMG Creation
```bash
# Create DMG source directory
mkdir dmg_source
cp -R dist/FootFix.app dmg_source/
ln -s /Applications dmg_source/Applications

# Create DMG
hdiutil create -srcfolder dmg_source -volname "FootFix 1.0.0" \
    -fs HFS+ -format UDZO FootFix-1.0.0.dmg

# Clean up
rm -rf dmg_source
```

### Code Signing (Optional but Recommended)

#### 1. Check for Signing Identity
```bash
security find-identity -p codesigning -v
```

#### 2. Sign the Application
```bash
# Sign the app bundle
codesign --force --deep --sign "Developer ID Application: Your Name" \
    dist/FootFix.app

# Verify signature
codesign --verify --verbose dist/FootFix.app
```

#### 3. Sign the DMG
```bash
codesign --force --sign "Developer ID Application: Your Name" \
    FootFix-1.0.0.dmg
```

### Notarization (For Distribution Outside App Store)

```bash
# Submit for notarization
xcrun altool --notarize-app \
    --primary-bundle-id "com.footfix.imageprocessor" \
    --username "your-apple-id@example.com" \
    --password "@keychain:AC_PASSWORD" \
    --file FootFix-1.0.0.dmg

# Check notarization status
xcrun altool --notarization-history 0 \
    --username "your-apple-id@example.com" \
    --password "@keychain:AC_PASSWORD"

# Staple the notarization
xcrun stapler staple FootFix-1.0.0.dmg
```

## Release Process

### 1. Update Version Number

Update version in these files:
- `setup.py` - version parameter
- `setup_app.py` - APP_VERSION
- `footfix/__init__.py` - __version__
- `create_dmg.sh` - VERSION variable

### 2. Update Documentation
- Update USER_GUIDE.md with new features
- Update CHANGELOG.md
- Review and update README.md

### 3. Run Full Test Suite
```bash
# Run all tests
pytest footfix/tests/ -v
python test_comprehensive_qa.py
python test_performance.py

# Manual testing checklist
- [ ] Single image processing
- [ ] Batch processing
- [ ] All presets work
- [ ] Preferences save/load
- [ ] Keyboard shortcuts
- [ ] Menu items
- [ ] Error handling
```

### 4. Create Release Build
```bash
# Clean everything
git clean -fdx

# Create fresh build
./build_app.sh

# Create DMG
./create_dmg.sh
```

### 5. Tag Release
```bash
# Create git tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag
git push origin v1.0.0
```

### 6. Create GitHub Release
1. Go to GitHub repository
2. Click "Releases" → "Create a new release"
3. Select the tag
4. Upload the DMG file
5. Add release notes from CHANGELOG.md

## Troubleshooting Build Issues

### Common Problems

#### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

#### py2app errors
```bash
# Clear py2app cache
rm -rf ~/Library/Caches/py2app

# Try building in alias mode first
python setup_app.py py2app -A
```

#### Icon generation fails
```bash
# Install required packages
pip install Pillow numpy

# Check for iconutil
which iconutil  # Should be /usr/bin/iconutil
```

#### DMG creation fails
- Ensure you have enough disk space
- Check for existing mounted volumes with same name
- Try increasing DMG size in create_dmg.sh

### Debug Build
```bash
# Build with more verbose output
python setup_app.py py2app --debug

# Check console logs
open /Applications/Utilities/Console.app
# Filter for FootFix
```

## Continuous Integration

### GitHub Actions Workflow (Optional)
Create `.github/workflows/build.yml`:

```yaml
name: Build FootFix

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Run tests
      run: |
        pytest footfix/tests/ -v
        
    - name: Build application
      run: |
        ./build_app.sh
        
    - name: Create DMG
      run: |
        ./create_dmg.sh
        
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: FootFix-DMG
        path: FootFix-*.dmg
```

## Development Tips

### Performance Profiling
```bash
# Profile the application
python -m cProfile -o profile.stats main.py

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('time').print_stats(20)"
```

### Memory Profiling
```bash
# Install memory profiler
pip install memory_profiler

# Run with memory profiling
python -m memory_profiler main.py
```

### Creating Test Builds
```bash
# Quick test build (alias mode)
python setup_app.py py2app -A

# This creates a fast build that references your development files
# Good for testing packaging without full build time
```

---

*FootFix Build Documentation - Version 1.0.0*