"""
py2app build script for FootFix
Creates a standalone macOS application bundle
"""

import sys
import os
from setuptools import setup
from pathlib import Path

# Ensure we're on macOS
if sys.platform != 'darwin':
    print("This script is for macOS only!")
    sys.exit(1)

# Application metadata
APP_NAME = 'FootFix'
APP_VERSION = '1.0.0'
APP_BUNDLE_ID = 'com.footfix.imageprocessor'

# Main script
APP = ['main.py']

# Data files to include
DATA_FILES = []

# Add default presets directory
presets_dir = Path('footfix/presets/defaults')
if presets_dir.exists():
    DATA_FILES.append(('footfix/presets/defaults', [str(p) for p in presets_dir.glob('*.json')]))

# py2app options
OPTIONS = {
    'argv_emulation': False,  # Don't use argv emulation (causes issues)
    'iconfile': 'assets/FootFix.icns',  # App icon (we'll create this)
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleIdentifier': APP_BUNDLE_ID,
        'CFBundleVersion': APP_VERSION,
        'CFBundleShortVersionString': APP_VERSION,
        'NSHumanReadableCopyright': 'Copyright © 2024 FootFix Team',
        'NSHighResolutionCapable': True,  # Retina display support
        'NSRequiresAquaSystemAppearance': False,  # Support Dark Mode
        'LSMinimumSystemVersion': '10.15',  # macOS Catalina minimum
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Image Files',
                'CFBundleTypeRole': 'Editor',
                'LSItemContentTypes': [
                    'public.jpeg',
                    'public.png',
                    'public.tiff',
                    'com.compuserve.gif',
                    'com.microsoft.bmp'
                ],
                'LSHandlerRank': 'Default'
            }
        ],
        'UTExportedTypeDeclarations': [],
        'NSAppleEventsUsageDescription': 'FootFix needs to process images.',
        'NSPhotoLibraryUsageDescription': 'FootFix needs access to your photos to process them.',
    },
    'packages': [
        'PIL',
        'PySide6',
        'numpy',
        'footfix'
    ],
    'includes': [
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    'excludes': [
        'matplotlib',  # Not needed for production
        'pytest',      # Testing framework
        'black',       # Code formatter
        'flake8',      # Linter
        'mypy',        # Type checker
        'tkinter',     # Not using tkinter
    ],
    'resources': [],
    'frameworks': [],
    'dylib_excludes': [],
    'optimize': 2,  # Optimize bytecode
    'compressed': True,  # Compress the app
    'semi_standalone': False,  # Fully standalone app
}

# Setup configuration
setup(
    name=APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)