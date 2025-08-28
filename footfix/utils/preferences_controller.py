"""
Controller for FootFix preferences.
Coordinates between model, viewmodel, and provides unified API for the application.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from .preferences_model import PreferencesModel
from .preferences_viewmodel import PreferencesViewModel

logger = logging.getLogger(__name__)


class PreferencesController(QObject):
    """Main controller for preferences system."""
    
    # Singleton instance
    _instance = None
    _initialized = False
    
    # Signals for application-wide notifications
    preferences_loaded = Signal()
    preferences_saved = Signal()
    preferences_changed = Signal(str, object)  # key, value
    api_key_validated = Signal(bool, str)  # success, message
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the preferences controller."""
        if self._initialized:
            return
        
        super().__init__()
        
        # Create model and viewmodel
        self._model = PreferencesModel()
        self._viewmodel = PreferencesViewModel(self._model)
        
        # Connect signals
        self._setup_signals()
        
        # Load preferences on initialization
        self.load_preferences()
        
        self._initialized = True
        logger.info("PreferencesController initialized")
    
    def _setup_signals(self) -> None:
        """Set up signal connections."""
        # Forward model/viewmodel signals
        self._viewmodel.preference_updated.connect(self.preferences_changed.emit)
        self._viewmodel.load_completed.connect(lambda success: self.preferences_loaded.emit() if success else None)
        self._viewmodel.save_completed.connect(lambda success: self.preferences_saved.emit() if success else None)
        self._viewmodel.api_validation_completed.connect(self.api_key_validated.emit)
    
    @classmethod
    def get_instance(cls) -> 'PreferencesController':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = PreferencesController()
        return cls._instance
    
    # Public API methods
    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        return self._viewmodel.get_preference(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a preference value."""
        return self._viewmodel.set_preference(key, value)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all preferences."""
        return self._viewmodel.get_all_preferences()
    
    def load_preferences(self) -> bool:
        """Load preferences from disk."""
        return self._viewmodel.load_preferences()
    
    def save_preferences(self) -> bool:
        """Save preferences to disk."""
        return self._viewmodel.save_preferences()
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._viewmodel.has_unsaved_changes()
    
    # Specialized getters with business logic
    def get_output_folder(self) -> str:
        """Get validated output folder."""
        return self._viewmodel.get_output_folder()
    
    def get_filename_template(self) -> str:
        """Get validated filename template."""
        return self._viewmodel.get_filename_template()
    
    def get_concurrent_processes(self) -> int:
        """Get concurrent process limit."""
        return self._viewmodel.get_concurrent_processes()
    
    def get_memory_limit_mb(self) -> int:
        """Get memory limit."""
        return self._viewmodel.get_memory_limit_mb()
    
    def get_api_key(self) -> Optional[str]:
        """Get API key securely."""
        return self._viewmodel.get_api_key()
    
    def is_alt_text_enabled(self) -> bool:
        """Check if alt text is properly configured."""
        return self._viewmodel.is_alt_text_enabled()
    
    def get_recent_items(self, category: str) -> List[str]:
        """Get recent items for category."""
        return self._viewmodel.get_recent_items(category)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return self._viewmodel.get_usage_stats()
    
    # Specialized setters with validation
    def set_output_folder(self, folder: str) -> bool:
        """Set output folder with validation."""
        return self._viewmodel.set_output_folder(folder)
    
    def set_filename_template(self, template: str) -> bool:
        """Set filename template with validation."""
        return self._viewmodel.set_filename_template(template)
    
    def set_api_key(self, key: str) -> bool:
        """Set API key with validation."""
        return self._viewmodel.set_api_key(key)
    
    def set_memory_limit(self, limit_mb: int) -> bool:
        """Set memory limit with validation."""
        return self._viewmodel.set_memory_limit(limit_mb)
    
    def set_concurrent_processes(self, count: int) -> bool:
        """Set concurrent process count with validation."""
        return self._viewmodel.set_concurrent_processes(count)
    
    # Recent items management
    def add_recent_file(self, file_path: Union[str, Path]) -> None:
        """Add file to recent files list."""
        self._viewmodel.add_recent_item('files', str(file_path))
    
    def add_recent_preset(self, preset_name: str) -> None:
        """Add preset to recent presets list."""
        self._viewmodel.add_recent_item('presets', preset_name)
    
    def clear_recent_files(self) -> None:
        """Clear recent files list."""
        self._viewmodel.clear_recent_items('files')
    
    def clear_recent_presets(self) -> None:
        """Clear recent presets list."""
        self._viewmodel.clear_recent_items('presets')
    
    # Usage statistics
    def update_usage_stats(self, cost: float, requests: int = 1) -> None:
        """Update API usage statistics."""
        self._viewmodel.update_usage_stats(cost, requests)
    
    def reset_usage_stats(self) -> None:
        """Reset all usage statistics."""
        self._viewmodel.reset_usage_stats()
    
    # API validation
    def validate_api_key(self, api_key: str) -> None:
        """Validate API key asynchronously."""
        # Run async validation
        asyncio.create_task(self._viewmodel.validate_api_key_async(api_key))
    
    def validate_current_api_key(self) -> None:
        """Validate current API key."""
        api_key = self.get_api_key()
        if api_key:
            self.validate_api_key(api_key)
        else:
            self.api_key_validated.emit(False, "No API key configured")
    
    # Import/Export
    def export_preferences(self, file_path: Union[str, Path]) -> bool:
        """Export preferences to file."""
        return self._viewmodel.export_preferences(Path(file_path))
    
    def import_preferences(self, file_path: Union[str, Path]) -> bool:
        """Import preferences from file."""
        return self._viewmodel.import_preferences(Path(file_path))
    
    # Reset operations
    def reset_to_defaults(self, category: Optional[str] = None) -> None:
        """Reset preferences to defaults."""
        self._viewmodel.reset_to_defaults(category)
    
    def reset_window_state(self) -> None:
        """Reset window geometry and state."""
        self.set('interface.window_geometry', None)
        self.set('interface.window_state', None)
        logger.info("Window state reset")
    
    # Convenience methods for common preference patterns
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean preference."""
        return bool(self.get(key, default))
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer preference."""
        try:
            return int(self.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float preference."""
        try:
            return float(self.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_str(self, key: str, default: str = "") -> str:
        """Get string preference."""
        value = self.get(key, default)
        return str(value) if value is not None else default
    
    def get_list(self, key: str, default: List[Any] = None) -> List[Any]:
        """Get list preference."""
        if default is None:
            default = []
        value = self.get(key, default)
        return list(value) if isinstance(value, (list, tuple)) else default
    
    def get_dict(self, key: str, default: Dict[Any, Any] = None) -> Dict[Any, Any]:
        """Get dict preference."""
        if default is None:
            default = {}
        value = self.get(key, default)
        return dict(value) if isinstance(value, dict) else default
    
    # Batch operations
    def update_multiple(self, preferences: Dict[str, Any]) -> bool:
        """Update multiple preferences at once."""
        success = True
        for key, value in preferences.items():
            if not self.set(key, value):
                success = False
                logger.warning(f"Failed to set preference {key}={value}")
        return success
    
    def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple preferences at once."""
        return {key: self.get(key) for key in keys}
    
    # Category operations
    def get_category_preferences(self, category: str) -> Dict[str, Any]:
        """Get all preferences for a category (e.g., 'output', 'processing')."""
        all_prefs = self.get_all()
        return {
            key: value for key, value in all_prefs.items() 
            if key.startswith(f"{category}.")
        }
    
    def set_category_preferences(self, category: str, preferences: Dict[str, Any]) -> bool:
        """Set all preferences for a category."""
        prefixed_prefs = {
            f"{category}.{key}": value 
            for key, value in preferences.items()
        }
        return self.update_multiple(prefixed_prefs)
    
    # Debug and utility methods
    def get_schema_info(self, key: str) -> Optional[str]:
        """Get schema description for a preference."""
        return self._viewmodel.get_schema_description(key)
    
    def validate_all_preferences(self) -> tuple[bool, List[str]]:
        """Validate all current preferences."""
        return self._model.validate_all()
    
    def get_unsaved_keys(self) -> set[str]:
        """Get keys with unsaved changes."""
        return self._viewmodel.get_unsaved_keys()
    
    def force_save(self) -> bool:
        """Force save preferences (bypassing validation)."""
        return self._model.save_to_file()
    
    def reload_from_disk(self) -> bool:
        """Reload preferences from disk (discarding unsaved changes)."""
        success = self._model.load_from_file()
        if success:
            self._viewmodel.mark_saved()
        return success
    
    # Context manager support
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - auto-save if changes exist."""
        if self.has_unsaved_changes():
            self.save_preferences()
    
    def shutdown(self) -> bool:
        """Shutdown preferences system - save any unsaved changes."""
        if self.has_unsaved_changes():
            logger.info("Saving unsaved preferences on shutdown")
            return self.save_preferences()
        return True


# Module-level convenience functions for backward compatibility
_controller = None

def get_preferences_controller() -> PreferencesController:
    """Get the global preferences controller instance."""
    global _controller
    if _controller is None:
        _controller = PreferencesController.get_instance()
    return _controller

def get_preference(key: str, default: Any = None) -> Any:
    """Get a preference value (convenience function)."""
    return get_preferences_controller().get(key, default)

def set_preference(key: str, value: Any) -> bool:
    """Set a preference value (convenience function)."""
    return get_preferences_controller().set(key, value)

def save_preferences() -> bool:
    """Save preferences to disk (convenience function)."""
    return get_preferences_controller().save_preferences()

def load_preferences() -> bool:
    """Load preferences from disk (convenience function)."""
    return get_preferences_controller().load_preferences()