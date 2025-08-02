#!/usr/bin/env python3
"""
Test script for the hacker-style QML interface prototype.
Run this to test the movie hacker aesthetic UI.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the hacker interface
from footfix.qml_ui.hacker_main import main

if __name__ == "__main__":
    print("Starting FootFix Hacker UI Prototype...")
    print("Features demonstrated:")
    print("- Matrix-style animated background")
    print("- Irregular hexagonal and diamond buttons")
    print("- Circuit-board style settings panel")
    print("- Terminal-style status display")
    print("- Glitch effects and animations")
    print("- Integration with existing image processing backend")
    print()
    main()