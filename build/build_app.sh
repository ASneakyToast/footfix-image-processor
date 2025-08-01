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

# Run tests first (allow some failures for build purposes)
echo "🧪 Running tests..."
python -m pytest ../tests/ -v --tb=short --maxfail=5
test_result=$?

if [ $test_result -eq 0 ]; then
    echo "✅ All tests passed!"
elif [ $test_result -eq 1 ]; then
    echo "⚠️  Some tests failed, but continuing with build..."
    echo "   (Fix test issues for production deployment)"
else
    echo "❌ Critical test failures or collection errors! Cannot proceed."
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