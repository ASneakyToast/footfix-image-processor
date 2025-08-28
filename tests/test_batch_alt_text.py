#!/usr/bin/env python3
"""
Test script for batch processing with alt text generation.
Verifies the complete Week 2 integration.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from footfix.gui.main_window import MainWindow
from footfix.utils.preferences import PreferencesManager


def setup_test_preferences():
    """Set up test preferences with API key prompt."""
    prefs = PreferencesManager()
    
    # Check if API key is already configured
    api_key = prefs.get('alt_text.api_key')
    if not api_key:
        print("\n=== Alt Text API Configuration ===")
        print("To test alt text generation, you need an Anthropic API key.")
        print("Get one from: https://console.anthropic.com/")
        print("\nYou can also configure this in Preferences > Alt Text")
        print("For now, alt text generation will be disabled.\n")
    else:
        print("\n=== Alt Text API Configured ===")
        print("API key found in preferences.")
        print("Alt text generation will be available.\n")
    
    return api_key is not None


def main():
    """Run the FootFix application with alt text features."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("FootFix")
    app.setOrganizationName("FootFix")
    
    # Check API configuration
    has_api_key = setup_test_preferences()
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Show instructions
    print("\n=== Testing Week 2 Alt Text Features ===")
    print("\n1. Go to 'Batch Processing' tab")
    print("2. Add some images to the queue")
    print("3. Look for 'Generate Alt Text' checkbox at the bottom")
    
    if has_api_key:
        print("4. Enable 'Generate Alt Text' before processing")
        print("5. After processing, check the 'Alt Text' tab")
        print("6. Review and edit generated descriptions")
    else:
        print("4. Configure API key in Preferences > Alt Text")
        print("5. Restart to enable alt text generation")
    
    print("\n=== New Features ===")
    print("- Alt Text tab in batch processing")
    print("- API key configuration in preferences")
    print("- Character count validation (125 char limit)")
    print("- Bulk operations (approve all, regenerate)")
    print("- Progress tracking for API calls")
    print("- Best practices guidelines")
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()