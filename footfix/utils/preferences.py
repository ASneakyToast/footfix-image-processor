"""
Preferences management for FootFix.
Handles saving and loading application preferences.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class PreferencesManager(QObject):
    """Manages application preferences with persistent storage using singleton pattern."""
    
    # Class-level singleton instance and lock
    _instance = None
    _lock = threading.Lock()
    
    # Signals for preference changes
    preferences_changed = Signal(str)  # Emits the key that changed
    preferences_reloaded = Signal()    # Emits when preferences are reloaded from disk
    
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
        },
        'tags': {
            'enabled': True,
            'auto_suggest': True,
            'max_tags_per_image': 10,
            'require_tags': False,
            'ai_generation_enabled': False,
            'ai_confidence_threshold': 0.7,
            'ai_max_tags_per_category': 3,
            'ai_fallback_to_patterns': True,
            'ai_share_api_key_with_alt_text': True,
            'semantic_extraction_enabled': True,
            'semantic_confidence_threshold': 0.4,
            'semantic_max_tags': 10
        }
    }
    
    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the preferences manager (only called once due to singleton)."""
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        self.preferences_dir = Path.home() / ".footfix"
        self.preferences_file = self.preferences_dir / "preferences.json"
        self.preferences = self.DEFAULTS.copy()
        self._data_lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Ensure preferences directory exists
        self.preferences_dir.mkdir(exist_ok=True)
        
        # Initialize backup file path
        self.backup_file = self.preferences_dir / "preferences.backup.json"
        
        # Load existing preferences
        self.load()
        self._initialized = True
        
    def load(self) -> bool:
        """
        Load preferences from disk with thread safety.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        with self._data_lock:
            if not self.preferences_file.exists():
                logger.info("No preferences file found, using defaults")
                return False
                
            try:
                logger.info(f"Loading preferences from: {self.preferences_file}")
                with open(self.preferences_file, 'r') as f:
                    loaded_prefs = json.load(f)
                
                # Validate loaded preferences
                is_valid, error_msg = self.validate_preferences(loaded_prefs)
                if not is_valid:
                    logger.warning(f"Invalid preferences detected: {error_msg}")
                    # Try to restore from backup
                    if hasattr(self, 'backup_file') and self.backup_file.exists():
                        logger.info("Attempting to restore from backup...")
                        try:
                            with open(self.backup_file, 'r') as f:
                                backup_prefs = json.load(f)
                            backup_valid, backup_error = self.validate_preferences(backup_prefs)
                            if backup_valid:
                                loaded_prefs = backup_prefs
                                logger.info("Successfully restored preferences from backup")
                            else:
                                logger.warning(f"Backup is also invalid: {backup_error}. Using defaults.")
                                loaded_prefs = self.DEFAULTS.copy()
                        except Exception as backup_e:
                            logger.error(f"Failed to load backup: {backup_e}. Using defaults.")
                            loaded_prefs = self.DEFAULTS.copy()
                    else:
                        logger.warning("No valid backup found. Using defaults.")
                        loaded_prefs = self.DEFAULTS.copy()
                    
                # Merge with defaults to handle missing keys
                old_preferences = self.preferences.copy()
                self.preferences = self._merge_preferences(self.DEFAULTS, loaded_prefs)
                
                # Log the alt_text section specifically
                alt_text_prefs = self.preferences.get('alt_text', {})
                api_key = alt_text_prefs.get('api_key')
                logger.info(f"Alt text preferences loaded: api_key={'[REDACTED]' if api_key else '[EMPTY]'}, enabled={alt_text_prefs.get('enabled')}")
                
                logger.info("Preferences loaded successfully")
                
                # Emit signal if preferences have changed (only if this isn't initial load)
                if hasattr(self, '_initialized') and old_preferences != self.preferences:
                    self.preferences_reloaded.emit()
                    
                return True
                
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
                # Try to restore from backup as a last resort
                if hasattr(self, 'backup_file') and self.backup_file.exists():
                    logger.info("Main preferences file corrupted, attempting backup restore...")
                    return self.restore_from_backup()
                return False
            
    def save(self) -> bool:
        """
        Save preferences to disk with thread safety and backup.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        with self._data_lock:
            try:
                logger.info(f"Saving preferences to: {self.preferences_file}")
                
                # Validate preferences before saving
                is_valid, error_msg = self.validate_preferences(self.preferences)
                if not is_valid:
                    logger.error(f"Cannot save invalid preferences: {error_msg}")
                    return False
                
                # Create backup before saving (if file exists)
                if hasattr(self, 'backup_file') and self.preferences_file.exists():
                    self.create_backup()
                
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
        Get a preference value using dot notation with thread safety.
        
        Args:
            key: Preference key (e.g., 'output.default_folder')
            default: Default value if key not found
            
        Returns:
            The preference value or default
        """
        with self._data_lock:
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
        Set a preference value using dot notation with thread safety and change notifications.
        
        Args:
            key: Preference key (e.g., 'output.default_folder')
            value: Value to set
        """
        with self._data_lock:
            # Get old value for comparison
            old_value = self.get(key, None)
            
            keys = key.split('.')
            target = self.preferences
            
            # Navigate to the parent dictionary
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
                
            # Set the value
            target[keys[-1]] = value
            
            # Emit signal if value actually changed
            if old_value != value:
                logger.debug(f"Preference changed: {key} = {value}")
                self.preferences_changed.emit(key)
        
    def update_recent(self, category: str, item: str) -> None:
        """
        Update a recent items list with thread safety.
        
        Args:
            category: Recent category ('files' or 'presets')
            item: Item to add to recent list
        """
        with self._data_lock:
            recent_list = self.get(f'recent.{category}', []).copy()  # Make a copy to avoid mutation issues
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
    
    @classmethod
    def get_instance(cls) -> 'PreferencesManager':
        """
        Get the singleton instance of PreferencesManager.
        
        Returns:
            PreferencesManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = PreferencesManager()
        return cls._instance
    
    def reload_from_disk(self) -> bool:
        """
        Reload preferences from disk and emit signals if changed.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        logger.info("Reloading preferences from disk")
        return self.load()
        
    def reset_to_defaults(self, category: Optional[str] = None) -> None:
        """
        Reset preferences to defaults with thread safety.
        
        Args:
            category: Optional category to reset (None resets all)
        """
        with self._data_lock:
            if category and category in self.DEFAULTS:
                old_value = self.preferences.get(category, {}).copy()
                self.preferences[category] = self.DEFAULTS[category].copy()
                # Emit signal for category change
                if old_value != self.preferences[category]:
                    self.preferences_changed.emit(category)
            else:
                self.preferences = self.DEFAULTS.copy()
                # Emit reload signal for complete reset
                self.preferences_reloaded.emit()
            
    def export_preferences(self, export_path: Path) -> bool:
        """
        Export preferences to a file with thread safety.
        
        Args:
            export_path: Path to export preferences to
            
        Returns:
            bool: True if exported successfully
        """
        with self._data_lock:
            try:
                with open(export_path, 'w') as f:
                    json.dump(self.preferences, f, indent=2)
                return True
            except Exception as e:
                logger.error(f"Failed to export preferences: {e}")
                return False
            
    def import_preferences(self, import_path: Path) -> bool:
        """
        Import preferences from a file with thread safety.
        
        Args:
            import_path: Path to import preferences from
            
        Returns:
            bool: True if imported successfully
        """
        with self._data_lock:
            try:
                with open(import_path, 'r') as f:
                    imported_prefs = json.load(f)
                    
                self.preferences = self._merge_preferences(self.DEFAULTS, imported_prefs)
                # Emit reload signal for import
                self.preferences_reloaded.emit()
                return True
            except Exception as e:
                logger.error(f"Failed to import preferences: {e}")
                return False
    
    def validate_preferences(self, prefs: Dict) -> tuple[bool, str]:
        """
        Validate preferences structure and values.
        
        Args:
            prefs: Preferences dictionary to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check that all required top-level keys exist
            required_keys = set(self.DEFAULTS.keys())
            provided_keys = set(prefs.keys())
            
            missing_keys = required_keys - provided_keys
            if missing_keys:
                return False, f"Missing required preference sections: {missing_keys}"
            
            # Validate specific preference values
            # Check memory limit
            memory_limit = prefs.get('advanced', {}).get('memory_limit_mb')
            if memory_limit is not None and (not isinstance(memory_limit, int) or memory_limit < 512 or memory_limit > 16384):
                return False, "Memory limit must be between 512 and 16384 MB"
            
            # Check max concurrent batch
            max_concurrent = prefs.get('processing', {}).get('max_concurrent_batch')
            if max_concurrent is not None and (not isinstance(max_concurrent, int) or max_concurrent < 1 or max_concurrent > 20):
                return False, "Max concurrent batch must be between 1 and 20"
            
            # Check max recent items
            max_recent = prefs.get('recent', {}).get('max_recent_items')
            if max_recent is not None and (not isinstance(max_recent, int) or max_recent < 1 or max_recent > 100):
                return False, "Max recent items must be between 1 and 100"
            
            # Check file size limit
            max_file_size = prefs.get('advanced', {}).get('max_file_size_mb')
            if max_file_size is not None and (not isinstance(max_file_size, int) or max_file_size < 1 or max_file_size > 500):
                return False, "Max file size must be between 1 and 500 MB"
            
            return True, "Preferences are valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def create_backup(self) -> bool:
        """
        Create a backup of current preferences.
        
        Returns:
            bool: True if backup created successfully
        """
        try:
            if self.preferences_file.exists():
                import shutil
                shutil.copy2(self.preferences_file, self.backup_file)
                logger.info(f"Preferences backup created: {self.backup_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to create preferences backup: {e}")
            return False
    
    def restore_from_backup(self) -> bool:
        """
        Restore preferences from backup file.
        
        Returns:
            bool: True if restored successfully
        """
        try:
            if not self.backup_file.exists():
                logger.warning("No backup file found to restore from")
                return False
                
            with open(self.backup_file, 'r') as f:
                backup_prefs = json.load(f)
                
            # Validate backup before restoring
            is_valid, error_msg = self.validate_preferences(backup_prefs)
            if not is_valid:
                logger.error(f"Backup file is invalid: {error_msg}")
                return False
                
            with self._data_lock:
                self.preferences = self._merge_preferences(self.DEFAULTS, backup_prefs)
                success = self.save()
                if success:
                    self.preferences_reloaded.emit()
                    logger.info("Preferences restored from backup successfully")
                return success
                
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False