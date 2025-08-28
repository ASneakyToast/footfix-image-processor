# Building FootFix DMG Package

This guide covers how to create the FootFix DMG installer package for distribution. This is the process for IT administrators to generate the `FootFix-1.0.0.dmg` file referenced in the installation documentation.

## Prerequisites

- macOS development environment
- Xcode Command Line Tools installed
- FootFix.app already built in `build/dist/`

## Quick Start

To create the DMG package:

```bash
cd build/
./create_dmg.sh
```

This creates `FootFix-1.0.0.dmg` ready for distribution.

## Detailed Process

### 1. Verify App Build

First, ensure FootFix.app exists:

```bash
ls -la build/dist/FootFix.app
```

If the app doesn't exist, build it first:

```bash
cd build/
./build_app.sh
```

### 2. Create DMG Package

Run the DMG creation script:

```bash
cd build/
./create_dmg.sh
```

The script will:
- ✅ Verify FootFix.app exists
- 🧹 Clean up any existing DMG files
- 📁 Set up DMG contents with Applications symlink
- 🎨 Configure professional DMG appearance
- 🗜️ Create compressed DMG package
- 🔏 Code sign (if Developer ID certificate available)

### 3. Verify DMG Creation

After successful completion, you'll have:

```
build/FootFix-1.0.0.dmg
```

Test the DMG by mounting it:

```bash
open FootFix-1.0.0.dmg
```

You should see a window with FootFix.app and Applications folder for drag-and-drop installation.

## DMG Contents

The created DMG includes:

- **FootFix.app** - The main application bundle
- **Applications symlink** - For drag-and-drop installation
- **Background image** - Professional installer appearance
- **Window styling** - Proper icon layout and sizing

## Code Signing

### With Developer ID Certificate

If you have a "Developer ID Application" certificate installed:

```bash
# Check for certificates
security find-identity -p codesigning -v
```

The script automatically signs the DMG if a certificate is found.

### Without Certificate

The DMG will be created unsigned. Users will see security warnings requiring:
- Right-click → Open, or
- System Preferences → Security & Privacy → "Open Anyway"

### Manual Signing

To manually sign an existing DMG:

```bash
codesign --force --sign "Developer ID Application: Your Name" FootFix-1.0.0.dmg
```

## Distribution

Once created, distribute `FootFix-1.0.0.dmg` to users via:

- Email attachment
- Network file share
- USB drive
- Internal software repository
- MDM systems (Jamf, Munki, etc.)

## Troubleshooting

### "No such file or directory" Error

```
❌ Error: dist/FootFix.app not found. Run build_app.sh first.
```

**Solution:** Build the app first:
```bash
./build_app.sh
```

### Permission Denied

```
Permission denied: ./create_dmg.sh
```

**Solution:** Make script executable:
```bash
chmod +x create_dmg.sh
```

### DMG Mount Issues

If the created DMG won't mount:

1. Delete and recreate:
   ```bash
   rm FootFix-1.0.0.dmg
   ./create_dmg.sh
   ```

2. Check disk space (script needs ~200MB temporary space)

### Code Signing Failures

If signing fails:

1. Verify certificate:
   ```bash
   security find-identity -p codesigning -v
   ```

2. Use unsigned DMG (users can still install with extra security steps)

## Customization

### Change Version Number

Edit `create_dmg.sh`:

```bash
VERSION="1.1.0"  # Change this line
```

### Modify DMG Appearance

- **Background image:** Replace `assets/dmg_background.png`
- **Window size:** Modify bounds in AppleScript section
- **Icon positions:** Adjust coordinates in script

### DMG Size

For larger apps, increase DMG size:

```bash
# In create_dmg.sh, change:
-format UDRW -size 200mb temp.dmg
# to:
-format UDRW -size 400mb temp.dmg
```

## Integration with CI/CD

### Automated Building

For automated builds, ensure:

1. Build server has Xcode Command Line Tools
2. Code signing certificate installed (for signed builds)
3. Sufficient disk space for temporary files

### Build Pipeline Example

```bash
#!/bin/bash
# Build pipeline script

# Build the app
cd build/
./build_app.sh

# Create DMG
./create_dmg.sh

# Upload to distribution server
scp FootFix-1.0.0.dmg user@server:/path/to/releases/
```

## Security Considerations

### Developer ID Signing

For enterprise distribution:
- Obtain Developer ID Application certificate from Apple
- Sign both the .app and .dmg
- Consider notarization for macOS 10.15+

### Internal Distribution

For internal-only distribution:
- Document security warning bypass steps
- Consider enterprise code signing policies
- Train users on security dialog handling

## File Locations

After running the script:

- **DMG file:** `build/FootFix-1.0.0.dmg`
- **Build log:** `build/build.log`
- **Source app:** `build/dist/FootFix.app`

## Next Steps

After creating the DMG:

1. Test installation on clean macOS system
2. Document any security warnings for end users  
3. Distribute via your preferred method
4. Update installation documentation if needed

---

*FootFix DMG Package Creation Guide*