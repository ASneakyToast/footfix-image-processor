"""
Migration utility for FootFix preferences.
Handles migration from old PreferencesManager to new MVVM system.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .preferences import PreferencesManager as OldPreferencesManager
from .preferences_controller import PreferencesController

logger = logging.getLogger(__name__)


class PreferencesMigrator:
    """Handles migration from old to new preferences system."""
    
    def __init__(self):
        self.old_prefs_path = Path.home() / ".footfix" / "preferences.json"
        self.migration_complete_flag = Path.home() / ".footfix" / ".migrated_to_mvvm"
    
    def needs_migration(self) -> bool:
        """Check if migration is needed."""
        # Migration needed if old prefs exist and migration not completed
        return (
            self.old_prefs_path.exists() 
            and not self.migration_complete_flag.exists()
        )
    
    def migrate(self) -> bool:
        """Perform migration from old to new system."""
        if not self.needs_migration():
            logger.info("No migration needed")
            return True
        
        logger.info("Starting preferences migration from old system")
        
        try:
            # Load old preferences
            old_data = self._load_old_preferences()
            if not old_data:
                logger.warning("No old preferences found to migrate")
                self._mark_migration_complete()
                return True
            
            # Get new controller
            new_controller = PreferencesController.get_instance()
            
            # Map old structure to new structure
            mapped_data = self._map_old_to_new(old_data)
            
            # Apply mapped preferences
            success_count = 0
            total_count = len(mapped_data)
            
            for key, value in mapped_data.items():
                if new_controller.set(key, value):
                    success_count += 1
                else:
                    logger.warning(f"Failed to migrate preference: {key}={value}")
            
            # Save migrated preferences
            if new_controller.save_preferences():
                logger.info(f"Migration completed: {success_count}/{total_count} preferences migrated")
                self._mark_migration_complete()
                return True
            else:
                logger.error("Failed to save migrated preferences")
                return False
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def _load_old_preferences(self) -> Optional[Dict[str, Any]]:
        """Load old preferences from disk."""
        try:
            if not self.old_prefs_path.exists():
                return None
            
            with open(self.old_prefs_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load old preferences: {e}")
            return None
    
    def _map_old_to_new(self, old_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map old nested structure to new flat key structure."""
        mapped = {}
        
        # Recursively flatten nested dictionary
        def flatten_dict(data: Dict[str, Any], prefix: str = "") -> None:
            for key, value in data.items():
                new_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    flatten_dict(value, new_key)
                else:
                    mapped[new_key] = value
        
        flatten_dict(old_data)
        
        # Apply specific migrations for changed keys or values
        mapped = self._apply_specific_migrations(mapped)
        
        return mapped
    
    def _apply_specific_migrations(self, mapped: Dict[str, Any]) -> Dict[str, Any]:
        """Apply specific migrations for changed keys or values."""
        migrations = {}
        
        # Handle any key renames or value transformations
        for old_key, new_key in self._get_key_migrations().items():
            if old_key in mapped:
                migrations[new_key] = mapped[old_key]
                del mapped[old_key]
        
        # Handle value transformations
        for key in list(mapped.keys()):
            value = mapped[key]
            transformed = self._transform_value(key, value)
            if transformed != value:
                mapped[key] = transformed
        
        # Add migrations
        mapped.update(migrations)
        
        return mapped
    
    def _get_key_migrations(self) -> Dict[str, str]:
        """Get mapping of old keys to new keys."""
        return {
            # Add any key renames here
            # 'old.key.name': 'new.key.name'
        }
    
    def _transform_value(self, key: str, value: Any) -> Any:
        """Transform values if needed for specific keys."""
        # Handle specific value transformations
        
        # Ensure boolean values are proper booleans
        if key in [
            'interface.show_tooltips',
            'interface.confirm_batch_cancel',
            'processing.auto_preview',
            'processing.preserve_metadata',
            'processing.completion_notification',
            'processing.completion_sound',
            'alt_text.enabled',
            'alt_text.enable_cost_tracking',
            'tags.enabled',
            'tags.auto_suggest',
            'tags.require_tags',
            'tags.ai_generation_enabled',
            'tags.ai_fallback_to_patterns',
            'tags.ai_share_api_key_with_alt_text',
            'tags.semantic_extraction_enabled',
            'advanced.check_updates'
        ]:
            return bool(value)
        
        # Ensure integer values are proper integers
        if key in [
            'processing.max_concurrent_batch',
            'recent.max_recent_items',
            'advanced.memory_limit_mb',
            'advanced.max_file_size_mb',
            'alt_text.max_concurrent_requests',
            'tags.max_tags_per_image',
            'tags.ai_max_tags_per_category',
            'tags.semantic_max_tags',
            'interface.last_tab_index'
        ]:
            try:
                return int(value)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert {key}={value} to int")
                return value
        
        # Ensure float values are proper floats
        if key in [
            'tags.ai_confidence_threshold',
            'tags.semantic_confidence_threshold'
        ]:
            try:
                return float(value)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert {key}={value} to float")
                return value
        
        # Ensure list values are proper lists
        if key in [
            'output.recent_folders',
            'output.favorite_folders',
            'recent.files',
            'recent.presets'
        ]:
            if not isinstance(value, list):
                logger.warning(f"Converting non-list value for {key}: {value}")
                return []
            return value
        
        # Clean up API key
        if key == 'alt_text.api_key':
            if value:
                cleaned = str(value).strip()
                return cleaned if cleaned else None
            return None
        
        # Clean up paths
        if key in ['output.default_folder', 'advanced.temp_directory']:
            if value:
                return str(value).strip()
            return None
        
        return value
    
    def _mark_migration_complete(self) -> None:
        """Mark migration as complete."""
        try:
            # Create flag file
            self.migration_complete_flag.parent.mkdir(exist_ok=True, parents=True)
            self.migration_complete_flag.touch()
            
            # Also create backup of old preferences
            if self.old_prefs_path.exists():
                backup_path = self.old_prefs_path.with_suffix('.json.pre_mvvm_backup')
                import shutil
                shutil.copy2(self.old_prefs_path, backup_path)
                logger.info(f"Old preferences backed up to: {backup_path}")
                
        except Exception as e:
            logger.error(f"Failed to mark migration complete: {e}")
    
    def rollback_migration(self) -> bool:
        """Rollback migration if something went wrong."""
        try:
            if self.migration_complete_flag.exists():
                self.migration_complete_flag.unlink()
                logger.info("Migration rollback completed")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to rollback migration: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        return {
            'needs_migration': self.needs_migration(),
            'migration_complete': self.migration_complete_flag.exists(),
            'old_prefs_exist': self.old_prefs_path.exists(),
            'old_prefs_path': str(self.old_prefs_path),
            'migration_flag_path': str(self.migration_complete_flag)
        }


def ensure_preferences_migrated() -> bool:
    """
    Ensure preferences are migrated to new system.
    Call this early in application startup.
    """
    migrator = PreferencesMigrator()
    
    if migrator.needs_migration():
        logger.info("Migrating preferences to new MVVM system...")
        return migrator.migrate()
    else:
        logger.debug("Preferences already migrated or no old preferences found")
        return True


def get_migration_status() -> Dict[str, Any]:
    """Get current migration status (utility function)."""
    migrator = PreferencesMigrator()
    return migrator.get_migration_status()


# Backward compatibility layer
class PreferencesManagerCompatibility:
    """
    Compatibility wrapper to help transition from old PreferencesManager.
    Provides the same interface but uses new system underneath.
    """
    
    def __init__(self):
        self._controller = PreferencesController.get_instance()
        
        # Ensure migration is done
        ensure_preferences_migrated()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get preference value (old interface)."""
        return self._controller.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set preference value (old interface)."""
        self._controller.set(key, value)
    
    def save(self) -> bool:
        """Save preferences (old interface)."""
        return self._controller.save_preferences()
    
    def load(self) -> bool:
        """Load preferences (old interface)."""
        return self._controller.load_preferences()
    
    def update_recent(self, category: str, item: str) -> None:
        """Update recent items (old interface)."""
        if category == 'files':
            self._controller.add_recent_file(item)
        elif category == 'presets':
            self._controller.add_recent_preset(item)
    
    def reset_to_defaults(self, category: Optional[str] = None) -> None:
        """Reset to defaults (old interface)."""
        self._controller.reset_to_defaults(category)
    
    def export_preferences(self, export_path: Path) -> bool:
        """Export preferences (old interface)."""
        return self._controller.export_preferences(export_path)
    
    def import_preferences(self, import_path: Path) -> bool:
        """Import preferences (old interface)."""
        return self._controller.import_preferences(import_path)
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance (old interface)."""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance
    
    # Signal compatibility
    @property
    def preferences_changed(self):
        """Preferences changed signal."""
        return self._controller.preferences_changed
    
    @property
    def preferences_reloaded(self):
        """Preferences reloaded signal."""
        return self._controller.preferences_loaded