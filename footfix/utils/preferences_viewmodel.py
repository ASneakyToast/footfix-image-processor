"""
ViewModel for FootFix preferences.
Handles business logic, validation, and coordination between model and view.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Set
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer

from .preferences_model import PreferencesModel

logger = logging.getLogger(__name__)


class PreferencesViewModel(QObject):
    """ViewModel that manages preferences business logic and state."""
    
    # Signals for view updates
    preference_updated = Signal(str, object)  # key, value
    validation_error = Signal(str, str)  # key, error_message
    save_completed = Signal(bool)  # success
    load_completed = Signal(bool)  # success
    recent_items_updated = Signal(str, list)  # category, items
    usage_stats_updated = Signal(dict)  # stats
    api_validation_completed = Signal(bool, str)  # success, message
    
    def __init__(self, model: PreferencesModel):
        super().__init__()
        self._model = model
        self._unsaved_changes = set()
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.setSingleShot(True)
        
        # Connect to model signals
        self._model.preference_changed.connect(self._on_model_changed)
        self._model.preferences_loaded.connect(self._on_model_loaded)
        self._model.preferences_saved.connect(self._on_model_saved)
    
    def _on_model_changed(self, key: str, value: Any) -> None:
        """Handle model data changes."""
        self._unsaved_changes.add(key)
        self.preference_updated.emit(key, value)
        
        # Trigger auto-save after delay
        self._auto_save_timer.start(1000)  # 1 second delay
    
    def _on_model_loaded(self) -> None:
        """Handle model load completion."""
        self._unsaved_changes.clear()
        self.load_completed.emit(True)
    
    def _on_model_saved(self) -> None:
        """Handle model save completion."""
        self._unsaved_changes.clear()
        self.save_completed.emit(True)
    
    def _auto_save(self) -> None:
        """Auto-save preferences if there are unsaved changes."""
        if self._unsaved_changes:
            self.save_preferences()
    
    # Preference getters with business logic
    def get_output_folder(self) -> str:
        """Get default output folder with validation."""
        folder = self._model.get('output.default_folder', str(Path.home() / "Downloads"))
        # Ensure folder exists or create it
        folder_path = Path(folder)
        if not folder_path.exists():
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create output folder {folder}: {e}")
                # Fall back to Downloads
                folder = str(Path.home() / "Downloads")
        return folder
    
    def get_filename_template(self) -> str:
        """Get filename template with validation."""
        template = self._model.get('output.filename_template', '{original_name}_{preset}')
        if not self._validate_filename_template(template):
            logger.warning(f"Invalid filename template: {template}")
            return '{original_name}_{preset}'  # Safe default
        return template
    
    def get_concurrent_processes(self) -> int:
        """Get concurrent process limit with bounds checking."""
        value = self._model.get('processing.max_concurrent_batch', 3)
        return max(1, min(20, value))  # Ensure valid range
    
    def get_memory_limit_mb(self) -> int:
        """Get memory limit with bounds checking."""
        value = self._model.get('advanced.memory_limit_mb', 2048)
        return max(512, min(16384, value))  # Ensure valid range
    
    def get_api_key(self) -> Optional[str]:
        """Get API key securely."""
        key = self._model.get('alt_text.api_key')
        return key.strip() if key else None
    
    def is_alt_text_enabled(self) -> bool:
        """Check if alt text is enabled and properly configured."""
        enabled = self._model.get('alt_text.enabled', False)
        has_key = bool(self.get_api_key())
        return enabled and has_key
    
    def get_recent_items(self, category: str) -> List[str]:
        """Get recent items for a category."""
        max_items = self._model.get('recent.max_recent_items', 10)
        items = self._model.get(f'recent.{category}', [])
        return items[:max_items]  # Ensure we don't exceed limit
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics with calculations."""
        stats = self._model.get('alt_text.usage_stats', {})
        
        # Calculate current month stats
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")
        monthly_stats = stats.get('monthly', {})
        current_stats = monthly_stats.get(current_month, {'requests': 0, 'cost': 0.0})
        
        # Calculate averages
        avg_cost_per_request = 0.0
        if current_stats.get('requests', 0) > 0:
            avg_cost_per_request = current_stats.get('cost', 0) / current_stats['requests']
        
        total_stats = stats.get('total', {'requests': 0, 'cost': 0.0})
        
        return {
            'current_month': current_stats,
            'total': total_stats,
            'avg_cost_per_request': avg_cost_per_request
        }
    
    # Preference setters with validation
    def set_output_folder(self, folder: str) -> bool:
        """Set output folder with validation."""
        folder_path = Path(folder)
        if not folder_path.exists():
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.validation_error.emit('output.default_folder', f"Cannot create folder: {e}")
                return False
        
        return self._model.set('output.default_folder', str(folder_path))
    
    def set_filename_template(self, template: str) -> bool:
        """Set filename template with validation."""
        if not self._validate_filename_template(template):
            self.validation_error.emit('output.filename_template', "Invalid template format")
            return False
        
        return self._model.set('output.filename_template', template)
    
    def set_api_key(self, key: str) -> bool:
        """Set API key with validation."""
        key = key.strip() if key else None
        if key and len(key) < 10:  # Basic length check
            self.validation_error.emit('alt_text.api_key', "API key seems too short")
            return False
        
        return self._model.set('alt_text.api_key', key)
    
    def set_memory_limit(self, limit_mb: int) -> bool:
        """Set memory limit with validation."""
        if not (512 <= limit_mb <= 16384):
            self.validation_error.emit('advanced.memory_limit_mb', 
                                     "Memory limit must be between 512 and 16384 MB")
            return False
        
        return self._model.set('advanced.memory_limit_mb', limit_mb)
    
    def set_concurrent_processes(self, count: int) -> bool:
        """Set concurrent process count with validation."""
        if not (1 <= count <= 20):
            self.validation_error.emit('processing.max_concurrent_batch',
                                     "Concurrent processes must be between 1 and 20")
            return False
        
        return self._model.set('processing.max_concurrent_batch', count)
    
    # Composite operations
    def add_recent_item(self, category: str, item: str) -> None:
        """Add item to recent list with automatic management."""
        current_items = self.get_recent_items(category)
        max_items = self._model.get('recent.max_recent_items', 10)
        
        # Remove if already exists
        if item in current_items:
            current_items.remove(item)
        
        # Add to front
        current_items.insert(0, item)
        
        # Trim to max items
        current_items = current_items[:max_items]
        
        self._model.set(f'recent.{category}', current_items)
        self.recent_items_updated.emit(category, current_items)
    
    def clear_recent_items(self, category: str) -> None:
        """Clear all recent items for a category."""
        self._model.set(f'recent.{category}', [])
        self.recent_items_updated.emit(category, [])
    
    def update_usage_stats(self, cost: float, requests: int = 1) -> None:
        """Update API usage statistics."""
        from datetime import datetime
        
        current_stats = self._model.get('alt_text.usage_stats', {})
        current_month = datetime.now().strftime("%Y-%m")
        
        # Initialize structure if needed
        if 'monthly' not in current_stats:
            current_stats['monthly'] = {}
        if 'total' not in current_stats:
            current_stats['total'] = {'requests': 0, 'cost': 0.0}
        
        # Update monthly stats
        if current_month not in current_stats['monthly']:
            current_stats['monthly'][current_month] = {'requests': 0, 'cost': 0.0}
        
        month_stats = current_stats['monthly'][current_month]
        month_stats['requests'] += requests
        month_stats['cost'] += cost
        
        # Update total stats
        current_stats['total']['requests'] += requests
        current_stats['total']['cost'] += cost
        
        self._model.set('alt_text.usage_stats', current_stats)
        self.usage_stats_updated.emit(self.get_usage_stats())
    
    def reset_usage_stats(self) -> None:
        """Reset all usage statistics."""
        self._model.set('alt_text.usage_stats', {})
        self.usage_stats_updated.emit(self.get_usage_stats())
    
    async def validate_api_key_async(self, api_key: str) -> None:
        """Validate API key asynchronously."""
        if not api_key.strip():
            self.api_validation_completed.emit(False, "API key cannot be empty")
            return
        
        try:
            # Import here to avoid circular dependency
            from ..core.alt_text_generator import AltTextGenerator
            
            generator = AltTextGenerator(api_key.strip())
            is_valid, message = await generator.validate_api_key()
            self.api_validation_completed.emit(is_valid, message)
            
        except Exception as e:
            self.api_validation_completed.emit(False, f"Validation error: {str(e)}")
    
    # File operations
    def load_preferences(self) -> bool:
        """Load preferences from disk."""
        success = self._model.load_from_file()
        if not success:
            # Initialize with defaults if load failed
            self._model.reset_to_defaults()
        return success
    
    def save_preferences(self) -> bool:
        """Save preferences to disk."""
        # Validate all preferences before saving
        is_valid, errors = self._model.validate_all()
        if not is_valid:
            logger.warning(f"Validation errors before save: {errors}")
            # Still try to save, but log warnings
        
        success = self._model.save_to_file()
        if success:
            logger.info("Preferences saved successfully")
        else:
            logger.error("Failed to save preferences")
        
        return success
    
    def export_preferences(self, file_path: Path) -> bool:
        """Export preferences to file."""
        return self._model.export_to_file(file_path)
    
    def import_preferences(self, file_path: Path) -> bool:
        """Import preferences from file."""
        return self._model.import_from_file(file_path)
    
    def reset_to_defaults(self, category: Optional[str] = None) -> None:
        """Reset preferences to defaults."""
        if category:
            # Reset specific category
            category_keys = [key for key in self._model.get_all_schema_keys() 
                           if key.startswith(f"{category}.")]
            for key in category_keys:
                schema = self._model.get_schema_info(key)
                if schema:
                    self._model.set(key, schema.default)
        else:
            # Reset all
            self._model.reset_to_defaults()
    
    # Validation helpers
    def _validate_filename_template(self, template: str) -> bool:
        """Validate filename template format."""
        if not template or not isinstance(template, str):
            return False
        
        # Check for basic template variables
        valid_vars = {
            'original_name', 'preset', 'date', 'time', 
            'dimensions', 'width', 'height', 'counter'
        }
        
        # Simple validation - just check it's not empty and contains some valid chars
        import re
        
        # Check for invalid filename characters
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, template):
            return False
        
        # Must contain at least one variable placeholder
        var_pattern = r'\{(\w+)(?::[^}]*)?\}'
        matches = re.findall(var_pattern, template)
        
        if not matches:
            return False
        
        # All variables should be known (warn but don't fail)
        unknown_vars = set(matches) - valid_vars
        if unknown_vars:
            logger.warning(f"Unknown template variables: {unknown_vars}")
        
        return True
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return bool(self._unsaved_changes)
    
    def get_unsaved_keys(self) -> Set[str]:
        """Get keys with unsaved changes."""
        return self._unsaved_changes.copy()
    
    def mark_saved(self) -> None:
        """Mark all changes as saved."""
        self._unsaved_changes.clear()
    
    # Convenience methods for common operations
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get any preference value."""
        return self._model.get(key, default)
    
    def set_preference(self, key: str, value: Any) -> bool:
        """Set any preference value with validation."""
        return self._model.set(key, value)
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all preference values."""
        return self._model.get_all()
    
    def get_schema_description(self, key: str) -> Optional[str]:
        """Get description for a preference key."""
        schema = self._model.get_schema_info(key)
        return schema.description if schema else None