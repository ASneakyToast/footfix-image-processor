"""
Pure data model for FootFix preferences.
Handles data storage and retrieval without business logic.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


@dataclass
class PreferenceSchema:
    """Schema definition for a preference value."""
    default: Any
    validator: Optional[callable] = None
    description: Optional[str] = None


class PreferencesModel(QObject):
    """Pure data model for preferences with schema validation."""
    
    # Signals for data changes
    preference_changed = Signal(str, object)  # key, value
    preferences_loaded = Signal()
    preferences_saved = Signal()
    
    # Schema definition
    SCHEMA = {
        'output.default_folder': PreferenceSchema(
            default=str(Path.home() / "Downloads"),
            validator=lambda x: isinstance(x, str),
            description="Default output folder path"
        ),
        'output.filename_template': PreferenceSchema(
            default='{original_name}_{preset}',
            validator=lambda x: isinstance(x, str) and len(x) > 0,
            description="Default filename template"
        ),
        'output.duplicate_strategy': PreferenceSchema(
            default='rename',
            validator=lambda x: x in ['rename', 'overwrite', 'skip'],
            description="How to handle duplicate files"
        ),
        'output.recent_folders': PreferenceSchema(
            default=[],
            validator=lambda x: isinstance(x, list),
            description="Recently used folders"
        ),
        'output.favorite_folders': PreferenceSchema(
            default=[],
            validator=lambda x: isinstance(x, list),
            description="Favorite folders"
        ),
        
        'interface.window_geometry': PreferenceSchema(
            default=None,
            description="Main window geometry"
        ),
        'interface.window_state': PreferenceSchema(
            default=None,
            description="Main window state"
        ),
        'interface.last_tab_index': PreferenceSchema(
            default=0,
            validator=lambda x: isinstance(x, int) and x >= 0,
            description="Last active tab index"
        ),
        'interface.show_tooltips': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Show tooltips in interface"
        ),
        'interface.confirm_batch_cancel': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Confirm when canceling batch processing"
        ),
        
        'processing.max_concurrent_batch': PreferenceSchema(
            default=3,
            validator=lambda x: isinstance(x, int) and 1 <= x <= 20,
            description="Maximum concurrent batch processes"
        ),
        'processing.auto_preview': PreferenceSchema(
            default=False,
            validator=lambda x: isinstance(x, bool),
            description="Automatically show preview for single images"
        ),
        'processing.preserve_metadata': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Preserve image metadata (EXIF)"
        ),
        'processing.completion_notification': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Show notification when batch completes"
        ),
        'processing.completion_sound': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Play sound when batch completes"
        ),
        
        'recent.files': PreferenceSchema(
            default=[],
            validator=lambda x: isinstance(x, list),
            description="Recently processed files"
        ),
        'recent.presets': PreferenceSchema(
            default=[],
            validator=lambda x: isinstance(x, list),
            description="Recently used presets"
        ),
        'recent.max_recent_items': PreferenceSchema(
            default=10,
            validator=lambda x: isinstance(x, int) and 1 <= x <= 100,
            description="Maximum number of recent items to track"
        ),
        
        'advanced.memory_limit_mb': PreferenceSchema(
            default=2048,
            validator=lambda x: isinstance(x, int) and 512 <= x <= 16384,
            description="Memory limit for processing (MB)"
        ),
        'advanced.temp_directory': PreferenceSchema(
            default=None,
            validator=lambda x: x is None or isinstance(x, str),
            description="Temporary directory path"
        ),
        'advanced.log_level': PreferenceSchema(
            default='INFO',
            validator=lambda x: x in ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            description="Logging level"
        ),
        'advanced.check_updates': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Check for updates automatically"
        ),
        'advanced.max_file_size_mb': PreferenceSchema(
            default=50,
            validator=lambda x: isinstance(x, int) and 1 <= x <= 500,
            description="Maximum file size to process (MB)"
        ),
        
        'alt_text.enabled': PreferenceSchema(
            default=False,
            validator=lambda x: isinstance(x, bool),
            description="Enable alt text generation by default"
        ),
        'alt_text.api_key': PreferenceSchema(
            default=None,
            validator=lambda x: x is None or (isinstance(x, str) and len(x.strip()) > 0),
            description="Anthropic API key"
        ),
        'alt_text.default_context': PreferenceSchema(
            default='editorial image',
            validator=lambda x: isinstance(x, str) and len(x) > 0,
            description="Default context for alt text generation"
        ),
        'alt_text.max_concurrent_requests': PreferenceSchema(
            default=5,
            validator=lambda x: isinstance(x, int) and 1 <= x <= 10,
            description="Maximum concurrent API requests"
        ),
        'alt_text.enable_cost_tracking': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Track API usage and costs"
        ),
        'alt_text.usage_stats': PreferenceSchema(
            default={},
            validator=lambda x: isinstance(x, dict),
            description="API usage statistics"
        ),
        
        'tags.enabled': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Enable tag management"
        ),
        'tags.auto_suggest': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Auto-suggest tags"
        ),
        'tags.max_tags_per_image': PreferenceSchema(
            default=10,
            validator=lambda x: isinstance(x, int) and x > 0,
            description="Maximum tags per image"
        ),
        'tags.require_tags': PreferenceSchema(
            default=False,
            validator=lambda x: isinstance(x, bool),
            description="Require tags before processing"
        ),
        'tags.ai_generation_enabled': PreferenceSchema(
            default=False,
            validator=lambda x: isinstance(x, bool),
            description="Enable AI tag generation"
        ),
        'tags.ai_confidence_threshold': PreferenceSchema(
            default=0.7,
            validator=lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            description="AI tag confidence threshold"
        ),
        'tags.ai_max_tags_per_category': PreferenceSchema(
            default=3,
            validator=lambda x: isinstance(x, int) and x > 0,
            description="Maximum AI tags per category"
        ),
        'tags.ai_fallback_to_patterns': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Fallback to pattern matching"
        ),
        'tags.ai_share_api_key_with_alt_text': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Share API key with alt text service"
        ),
        'tags.semantic_extraction_enabled': PreferenceSchema(
            default=True,
            validator=lambda x: isinstance(x, bool),
            description="Enable semantic tag extraction"
        ),
        'tags.semantic_confidence_threshold': PreferenceSchema(
            default=0.4,
            validator=lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            description="Semantic extraction confidence threshold"
        ),
        'tags.semantic_max_tags': PreferenceSchema(
            default=10,
            validator=lambda x: isinstance(x, int) and x > 0,
            description="Maximum semantic tags"
        ),
    }
    
    def __init__(self):
        super().__init__()
        self.preferences_dir = Path.home() / ".footfix"
        self.preferences_file = self.preferences_dir / "preferences.json"
        self.backup_file = self.preferences_dir / "preferences.backup.json"
        
        self._data = {}
        self._lock = threading.RLock()
        
        # Ensure preferences directory exists
        self.preferences_dir.mkdir(exist_ok=True)
        
        # Initialize with defaults
        self._load_defaults()
    
    def _load_defaults(self) -> None:
        """Load default values from schema."""
        with self._lock:
            for key, schema in self.SCHEMA.items():
                self._data[key] = schema.default
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        with self._lock:
            if key in self._data:
                return self._data[key]
            elif key in self.SCHEMA:
                return self.SCHEMA[key].default
            else:
                return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set a preference value with validation."""
        with self._lock:
            # Validate against schema if exists
            if key in self.SCHEMA:
                schema = self.SCHEMA[key]
                if schema.validator and not schema.validator(value):
                    logger.warning(f"Invalid value for preference {key}: {value}")
                    return False
            
            old_value = self._data.get(key)
            self._data[key] = value
            
            # Emit signal if value changed
            if old_value != value:
                logger.debug(f"Preference changed: {key} = {value}")
                self.preference_changed.emit(key, value)
            
            return True
    
    def get_all(self) -> Dict[str, Any]:
        """Get all preference values."""
        with self._lock:
            return self._data.copy()
    
    def set_all(self, preferences: Dict[str, Any]) -> bool:
        """Set multiple preferences at once."""
        with self._lock:
            success = True
            for key, value in preferences.items():
                if not self.set(key, value):
                    success = False
            return success
    
    def reset_to_defaults(self, key: Optional[str] = None) -> None:
        """Reset preferences to defaults."""
        with self._lock:
            if key:
                if key in self.SCHEMA:
                    old_value = self._data.get(key)
                    self._data[key] = self.SCHEMA[key].default
                    if old_value != self._data[key]:
                        self.preference_changed.emit(key, self._data[key])
            else:
                self._load_defaults()
                self.preferences_loaded.emit()
    
    def load_from_file(self) -> bool:
        """Load preferences from disk."""
        with self._lock:
            if not self.preferences_file.exists():
                logger.info("No preferences file found, using defaults")
                return False
            
            try:
                with open(self.preferences_file, 'r') as f:
                    loaded_data = json.load(f)
                
                # Validate loaded data
                valid_data = {}
                for key, value in loaded_data.items():
                    if key in self.SCHEMA:
                        schema = self.SCHEMA[key]
                        if not schema.validator or schema.validator(value):
                            valid_data[key] = value
                        else:
                            logger.warning(f"Invalid value for {key}, using default")
                            valid_data[key] = schema.default
                    else:
                        # Keep unknown keys for backward compatibility
                        valid_data[key] = value
                
                # Merge with defaults
                self._load_defaults()
                self._data.update(valid_data)
                
                self.preferences_loaded.emit()
                logger.info("Preferences loaded successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
                return self._try_restore_from_backup()
    
    def save_to_file(self) -> bool:
        """Save preferences to disk."""
        with self._lock:
            try:
                # Create backup before saving
                if self.preferences_file.exists():
                    self._create_backup()
                
                with open(self.preferences_file, 'w') as f:
                    json.dump(self._data, f, indent=2)
                
                self.preferences_saved.emit()
                logger.info("Preferences saved successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save preferences: {e}")
                return False
    
    def _create_backup(self) -> bool:
        """Create backup of current preferences file."""
        try:
            import shutil
            shutil.copy2(self.preferences_file, self.backup_file)
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def _try_restore_from_backup(self) -> bool:
        """Try to restore from backup file."""
        if not self.backup_file.exists():
            logger.warning("No backup file found")
            return False
        
        try:
            with open(self.backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Validate backup data
            valid_data = {}
            for key, value in backup_data.items():
                if key in self.SCHEMA:
                    schema = self.SCHEMA[key]
                    if not schema.validator or schema.validator(value):
                        valid_data[key] = value
                    else:
                        valid_data[key] = schema.default
                else:
                    valid_data[key] = value
            
            self._load_defaults()
            self._data.update(valid_data)
            
            # Save restored data
            self.save_to_file()
            self.preferences_loaded.emit()
            
            logger.info("Preferences restored from backup")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False
    
    def export_to_file(self, file_path: Path) -> bool:
        """Export preferences to external file."""
        with self._lock:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self._data, f, indent=2)
                logger.info(f"Preferences exported to {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to export preferences: {e}")
                return False
    
    def import_from_file(self, file_path: Path) -> bool:
        """Import preferences from external file."""
        try:
            with open(file_path, 'r') as f:
                imported_data = json.load(f)
            
            # Validate imported data
            valid_data = {}
            for key, value in imported_data.items():
                if key in self.SCHEMA:
                    schema = self.SCHEMA[key]
                    if not schema.validator or schema.validator(value):
                        valid_data[key] = value
                    else:
                        logger.warning(f"Invalid imported value for {key}, using default")
                        valid_data[key] = schema.default
                else:
                    valid_data[key] = value
            
            with self._lock:
                self._load_defaults()
                self._data.update(valid_data)
            
            self.preferences_loaded.emit()
            logger.info(f"Preferences imported from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import preferences: {e}")
            return False
    
    def validate_all(self) -> tuple[bool, list[str]]:
        """Validate all current preferences."""
        errors = []
        
        with self._lock:
            for key, value in self._data.items():
                if key in self.SCHEMA:
                    schema = self.SCHEMA[key]
                    if schema.validator and not schema.validator(value):
                        errors.append(f"Invalid value for {key}: {value}")
        
        return len(errors) == 0, errors
    
    def get_schema_info(self, key: str) -> Optional[PreferenceSchema]:
        """Get schema information for a preference key."""
        return self.SCHEMA.get(key)
    
    def get_all_schema_keys(self) -> list[str]:
        """Get all defined schema keys."""
        return list(self.SCHEMA.keys())