# FootFix macOS App Installation

This guide covers installing the FootFix macOS application from the .dmg package. **No Python installation required** - this is a standalone app bundle.

## System Requirements
- macOS 10.15 (Catalina) or later
- Intel or Apple Silicon processor  
- 100MB free disk space

## Installation Steps

1. **Download FootFix**
   - Obtain `FootFix-1.0.0.dmg` from your IT department or designated source

2. **Install the Application**
   - Double-click the downloaded DMG file
   - In the window that opens, drag FootFix to the Applications folder
   - Wait for the copy to complete
   - Eject the DMG by clicking the eject button in Finder

3. **First Launch**
   - Open FootFix from Applications folder or Spotlight (⌘ Space)
   - If you see a security warning:
     - Click "OK" on the warning
     - Open System Preferences > Security & Privacy
     - Click "Open Anyway" next to the FootFix message
     - Click "Open" in the confirmation dialog

4. **Verify Installation**
   - FootFix should launch and show the main window
   - Check Help > About to confirm version 1.0.0

## Troubleshooting Installation

### "FootFix can't be opened because it is from an unidentified developer"

This is macOS security protection. To resolve:

1. **Method 1 (Recommended):**
   - Right-click (or Control-click) on FootFix in Applications
   - Select "Open" from the menu
   - Click "Open" in the dialog

2. **Method 2:**
   - Go to System Preferences > Security & Privacy > General
   - Click "Open Anyway" next to the FootFix message
   - Return to Applications and open FootFix

### "FootFix is damaged and can't be opened"

This usually means the download was corrupted:
1. Delete FootFix from Applications
2. Empty the Trash
3. Re-download the DMG file
4. Try installing again

If the issue persists:
- The DMG may need to be re-signed
- Contact your IT administrator

### Apple Silicon (M1/M2/M3) Compatibility

FootFix runs natively on Apple Silicon. If you experience issues:
1. Ensure you have the latest version of macOS
2. Try running in Rosetta mode:
   - Right-click FootFix in Applications
   - Select "Get Info"
   - Check "Open using Rosetta"
   - Try launching again

## Advanced Installation Options

### Installing via Command Line

For IT administrators or automated deployment:

```bash
# Mount the DMG
hdiutil attach FootFix-1.0.0.dmg

# Copy to Applications
cp -R /Volumes/FootFix/FootFix.app /Applications/

# Unmount
hdiutil detach /Volumes/FootFix

# Remove quarantine attribute
xattr -d com.apple.quarantine /Applications/FootFix.app
```

### Installing for All Users

To install FootFix for all users on the system:

1. Copy FootFix.app to `/Applications` (requires admin privileges)
2. Set appropriate permissions:
   ```bash
   sudo chmod -R 755 /Applications/FootFix.app
   sudo chown -R root:wheel /Applications/FootFix.app
   ```

### Network Installation

For organizations deploying via network:

1. Place FootFix.dmg on a network share
2. Users can mount and install following standard steps
3. Or use management tools like Jamf, Munki, or ARD

## Uninstallation

To completely remove FootFix:

1. **Remove the Application:**
   - Drag FootFix from Applications to Trash
   - Empty the Trash

2. **Remove User Data (Optional):**
   ```bash
   # Remove preferences
   rm ~/Library/Preferences/com.footfix.imageprocessor.plist
   
   # Remove application support files
   rm -rf ~/Library/Application\ Support/FootFix
   
   # Remove caches
   rm -rf ~/Library/Caches/com.footfix.imageprocessor
   ```

## Updating FootFix

### Automatic Updates
- FootFix checks for updates on launch
- Follow prompts to download and install

### Manual Updates
1. Download the latest DMG
2. Quit FootFix if running
3. Install over the existing version
4. Your settings and presets will be preserved

## Configuration for IT Administrators

### Pre-configuring Settings

Create a preference file at `/Library/Preferences/com.footfix.imageprocessor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>DefaultQuality</key>
    <integer>85</integer>
    <key>DefaultResizePercent</key>
    <integer>75</integer>
    <key>DefaultOutputDirectory</key>
    <string>/Users/Shared/FootFix Output</string>
</dict>
</plist>
```

### Deployment Best Practices

1. **Test First**: Always test on a representative Mac before wide deployment
2. **Sign/Notarize**: For easier deployment, have the app signed with a Developer ID
3. **Document Settings**: Create a standard configuration for your organization
4. **Train Users**: Provide the User Guide and conduct training sessions

## Security Considerations

### Code Signing
- FootFix should be signed with a valid Developer ID certificate
- Unsigned versions will trigger Gatekeeper warnings

### Permissions
FootFix requires these permissions:
- Read access to image files
- Write access to output directories
- No admin privileges needed for normal operation

### Privacy
FootFix does not:
- Collect user data
- Send images to external servers
- Require internet connection
- Access system files

## Getting Help

If you encounter installation issues:

1. Check the system requirements
2. Ensure you have sufficient disk space
3. Try downloading the DMG again
4. Contact your IT administrator
5. Check for known issues in the release notes

---

*FootFix Version 1.0.0 Installation Guide*