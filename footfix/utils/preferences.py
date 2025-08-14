"""
Preferences management for FootFix.
Handles saving and loading application preferences.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PreferencesManager:
    """Manages application preferences with persistent storage."""
    
    # Default preferences
    DEFAULTS = {
        'output': {
            'default_folder': str(Path.home() / "Downloads"),
            'filename_template': '{original_name}_{preset}',
            'duplicate_strategy': 'rename',
            'recent_folders': [],
            'favorite_folders': [],
        },
        'interface': {
            'window_geometry': None,
            'window_state': None,
            'last_tab_index': 0,
            'show_tooltips': True,
            'confirm_batch_cancel': True,
        },
        'processing': {
            'max_concurrent_batch': 3,
            'auto_preview': False,
            'preserve_metadata': True,
            'completion_notification': True,
            'completion_sound': True,
        },
        'recent': {
            'files': [],
            'presets': [],
            'max_recent_items': 10,
        },
        'advanced': {
            'memory_limit_mb': 2048,
            'temp_directory': None,
            'log_level': 'INFO',
            'check_updates': True,
            'max_file_size_mb': 50,
        },
        'alt_text': {
            'enabled': False,
            'api_key': None,
            'default_context': 'editorial image',
            'max_concurrent_requests': 5,
            'enable_cost_tracking': True,
        }
    }
    
    def __init__(self):
        """Initialize the preferences manager."""
        self.preferences_dir = Path.home() / ".footfix"
        self.preferences_file = self.preferences_dir / "preferences.json"
        self.preferences = self.DEFAULTS.copy()
        
        # Ensure preferences directory exists
        self.preferences_dir.mkdir(exist_ok=True)
        
        # Load existing preferences
        self.load()
        
    def load(self) -> bool:
        """
        Load preferences from disk.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not self.preferences_file.exists():
            logger.info("No preferences file found, using defaults")
            return False
            
        try:
            logger.info(f"Loading preferences from: {self.preferences_file}")
            with open(self.preferences_file, 'r') as f:
                loaded_prefs = json.load(f)
                
            # Merge with defaults to handle missing keys
            self.preferences = self._merge_preferences(self.DEFAULTS, loaded_prefs)
            
            # Log the alt_text section specifically
            alt_text_prefs = self.preferences.get('alt_text', {})
            api_key = alt_text_prefs.get('api_key')
            logger.info(f"Alt text preferences loaded: api_key={'[REDACTED]' if api_key else '[EMPTY]'}, enabled={alt_text_prefs.get('enabled')}")
            
            logger.info("Preferences loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load preferences: {e}")
            return False
            
    def save(self) -> bool:
        """
        Save preferences to disk.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            logger.info(f"Saving preferences to: {self.preferences_file}")
            
            # Log the alt_text section specifically
            alt_text_prefs = self.preferences.get('alt_text', {})
            api_key = alt_text_prefs.get('api_key')
            logger.info(f"Alt text preferences being saved: api_key={'[REDACTED]' if api_key else '[EMPTY]'}, enabled={alt_text_prefs.get('enabled')}")
            
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
                
            logger.info("Preferences saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a preference value using dot notation.
        
        Args:
            key: Preference key (e.g., 'output.default_folder')
            default: Default value if key not found
            
        Returns:
            The preference value or default
        """
        keys = key.split('.')
        value = self.preferences
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set(self, key: str, value: Any) -> None:
        """
        Set a preference value using dot notation.
        
        Args:
            key: Preference key (e.g., 'output.default_folder')
            value: Value to set
        """
        keys = key.split('.')
        target = self.preferences
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
            
        # Set the value
        target[keys[-1]] = value
        
    def update_recent(self, category: str, item: str) -> None:
        """
        Update a recent items list.
        
        Args:
            category: Recent category ('files' or 'presets')
            item: Item to add to recent list
        """
        recent_list = self.get(f'recent.{category}', [])
        max_items = self.get('recent.max_recent_items', 10)
        
        # Remove if already exists
        if item in recent_list:
            recent_list.remove(item)
            
        # Add to front
        recent_list.insert(0, item)
        
        # Trim to max items
        recent_list = recent_list[:max_items]
        
        # Update preferences
        self.set(f'recent.{category}', recent_list)
        
    def _merge_preferences(self, defaults: Dict, loaded: Dict) -> Dict:
        """
        Recursively merge loaded preferences with defaults.
        
        Args:
            defaults: Default preferences dictionary
            loaded: Loaded preferences dictionary
            
        Returns:
            Merged preferences dictionary
        """
        result = defaults.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_preferences(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def reset_to_defaults(self, category: Optional[str] = None) -> None:
        """
        Reset preferences to defaults.
        
        Args:
            category: Optional category to reset (None resets all)
        """
        if category and category in self.DEFAULTS:
            self.preferences[category] = self.DEFAULTS[category].copy()
        else:
            self.preferences = self.DEFAULTS.copy()
            
    def export_preferences(self, export_path: Path) -> bool:
        """
        Export preferences to a file.
        
        Args:
            export_path: Path to export preferences to
            
        Returns:
            bool: True if exported successfully
        """
        try:
            with open(export_path, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to export preferences: {e}")
            return False
            
    def import_preferences(self, import_path: Path) -> bool:
        """
        Import preferences from a file.
        
        Args:
            import_path: Path to import preferences from
            
        Returns:
            bool: True if imported successfully
        """
        try:
            with open(import_path, 'r') as f:
                imported_prefs = json.load(f)
                
            self.preferences = self._merge_preferences(self.DEFAULTS, imported_prefs)
            return True
        except Exception as e:
            logger.error(f"Failed to import preferences: {e}")
            return False