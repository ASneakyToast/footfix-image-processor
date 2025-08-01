#!/bin/bash
# Build script for FootFix macOS application

echo "🔨 Building FootFix for macOS..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.egg-info
rm -rf FootFix.app FootFix.dmg

# Install requirements
echo "📦 Installing requirements..."
pip install -r ../requirements.txt

# Run tests first
echo "🧪 Running tests..."
python -m pytest ../tests/ -v
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Fix issues before building."
    exit 1
fi

# Build the app
echo "🏗️  Building application bundle..."
python setup_app.py py2app

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "📍 Application location: dist/FootFix.app"
    
    # Show app info
    echo ""
    echo "📊 App bundle info:"
    du -sh dist/FootFix.app
    echo ""
    
    # Offer to create DMG
    read -p "Create DMG installer? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./create_dmg.sh
    fi
else
    echo "❌ Build failed!"
    exit 1
fi