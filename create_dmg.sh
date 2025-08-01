#!/bin/bash
# Create DMG installer for FootFix

APP_NAME="FootFix"
VERSION="1.0.0"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
VOLUME_NAME="${APP_NAME} ${VERSION}"
SOURCE_DIR="dmg_source"

echo "📀 Creating DMG installer for ${APP_NAME}..."

# Check if app exists
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo "❌ Error: dist/${APP_NAME}.app not found. Run build_app.sh first."
    exit 1
fi

# Clean up any existing files
echo "🧹 Cleaning up..."
rm -rf "${SOURCE_DIR}" "${DMG_NAME}" temp.dmg

# Create source directory
echo "📁 Setting up DMG contents..."
mkdir -p "${SOURCE_DIR}"

# Copy app to source directory
cp -R "dist/${APP_NAME}.app" "${SOURCE_DIR}/"

# Create Applications symlink
ln -s /Applications "${SOURCE_DIR}/Applications"

# Copy background image if it exists
if [ -f "assets/dmg_background.png" ]; then
    mkdir -p "${SOURCE_DIR}/.background"
    cp "assets/dmg_background.png" "${SOURCE_DIR}/.background/background.png"
fi

# Create temporary DMG
echo "🔨 Creating temporary DMG..."
hdiutil create -srcfolder "${SOURCE_DIR}" -volname "${VOLUME_NAME}" -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" -format UDRW -size 200mb temp.dmg

# Mount the DMG
echo "📎 Mounting DMG..."
device=$(hdiutil attach -readwrite -noverify temp.dmg | \
    egrep '^/dev/' | sed 1q | awk '{print $1}')
mount_point="/Volumes/${VOLUME_NAME}"

# Wait for mount
sleep 2

# Set up the DMG window properties
echo "🎨 Configuring DMG appearance..."
echo '
   tell application "Finder"
     tell disk "'${VOLUME_NAME}'"
           open
           set current view of container window to icon view
           set toolbar visible of container window to false
           set statusbar visible of container window to false
           set the bounds of container window to {100, 100, 700, 500}
           set viewOptions to the icon view options of container window
           set arrangement of viewOptions to not arranged
           set icon size of viewOptions to 128
           set background picture of viewOptions to file ".background:background.png"
           set position of item "'${APP_NAME}'.app" of container window to {150, 200}
           set position of item "Applications" of container window to {450, 200}
           close
           open
           update without registering applications
           delay 2
     end tell
   end tell
' | osascript

# Set window properties that osascript missed
SetFile -a C "${mount_point}"

# Unmount the DMG
echo "📤 Finalizing DMG..."
hdiutil detach "${device}"

# Convert to compressed DMG
echo "🗜️  Compressing DMG..."
hdiutil convert temp.dmg -format UDZO -imagekey zlib-level=9 -o "${DMG_NAME}"

# Clean up
echo "🧹 Cleaning up..."
rm -rf "${SOURCE_DIR}" temp.dmg

# Sign the DMG if code signing identity is available
if security find-identity -p codesigning -v | grep -q "Developer ID"; then
    echo "🔏 Code signing DMG..."
    codesign --force --sign "Developer ID Application" "${DMG_NAME}"
else
    echo "ℹ️  No code signing identity found. DMG will not be signed."
fi

# Show final info
echo ""
echo "✅ DMG created successfully!"
echo "📍 Location: ${DMG_NAME}"
echo "📊 Size: $(du -h ${DMG_NAME} | cut -f1)"
echo ""
echo "🚀 The DMG is ready for distribution!"