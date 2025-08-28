"""
Comprehensive tests for the new MVVM preferences system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from footfix.utils.preferences_model import PreferencesModel, PreferenceSchema
from footfix.utils.preferences_viewmodel import PreferencesViewModel
from footfix.utils.preferences_controller import PreferencesController
from footfix.utils.preferences_migration import PreferencesMigrator


class TestPreferencesModel:
    """Test the preferences data model."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock the preferences directory
        with patch('footfix.utils.preferences_model.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            self.model = PreferencesModel()
    
    def test_default_values_loaded(self):
        """Test that default values are loaded correctly."""
        assert self.model.get('output.default_folder') is not None
        assert self.model.get('processing.max_concurrent_batch') == 3
        assert self.model.get('alt_text.enabled') == False
        assert self.model.get('tags.enabled') == True
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        # Test setting valid value
        assert self.model.set('processing.max_concurrent_batch', 5)
        assert self.model.get('processing.max_concurrent_batch') == 5
        
        # Test setting invalid value (should fail validation)
        assert not self.model.set('processing.max_concurrent_batch', 25)  # Out of range
        assert self.model.get('processing.max_concurrent_batch') == 5  # Unchanged
    
    def test_validation(self):
        """Test preference validation."""
        # Test valid values
        assert self.model.set('alt_text.enabled', True)
        assert self.model.set('advanced.memory_limit_mb', 1024)
        assert self.model.set('output.duplicate_strategy', 'rename')
        
        # Test invalid values
        assert not self.model.set('advanced.memory_limit_mb', 100)  # Too low
        assert not self.model.set('output.duplicate_strategy', 'invalid')  # Invalid option
        assert not self.model.set('processing.max_concurrent_batch', -1)  # Negative
    
    def test_schema_validation(self):
        """Test schema-based validation."""
        # Test valid boolean
        assert self.model.set('alt_text.enabled', True)
        assert not self.model.set('alt_text.enabled', "yes")  # String not boolean
        
        # Test valid integer range
        assert self.model.set('recent.max_recent_items', 15)
        assert not self.model.set('recent.max_recent_items', 0)  # Below minimum
        assert not self.model.set('recent.max_recent_items', 150)  # Above maximum
    
    def test_signal_emission(self):
        """Test that signals are emitted on changes."""
        signal_received = Mock()
        self.model.preference_changed.connect(signal_received)
        
        # Change value should emit signal
        self.model.set('alt_text.enabled', True)
        signal_received.emit.assert_called_once_with('alt_text.enabled', True)
        
        # Setting same value should not emit signal
        signal_received.reset_mock()
        self.model.set('alt_text.enabled', True)
        signal_received.emit.assert_not_called()
    
    def test_file_operations(self):
        """Test loading and saving to file."""
        # Set some values
        self.model.set('alt_text.enabled', True)
        self.model.set('processing.max_concurrent_batch', 7)
        
        # Save to file
        assert self.model.save_to_file()
        assert self.model.preferences_file.exists()
        
        # Create new model and load
        with patch('footfix.utils.preferences_model.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            new_model = PreferencesModel()
            assert new_model.load_from_file()
            
            # Check values were loaded
            assert new_model.get('alt_text.enabled') == True
            assert new_model.get('processing.max_concurrent_batch') == 7
    
    def test_backup_and_restore(self):
        """Test backup and restore functionality."""
        # Set initial values and save
        self.model.set('alt_text.enabled', True)
        self.model.save_to_file()
        
        # Modify and save (should create backup)
        self.model.set('alt_text.enabled', False)
        self.model.save_to_file()
        
        # Check backup exists
        assert self.model.backup_file.exists()
        
        # Simulate corruption and restore
        self.model.preferences_file.write_text("invalid json")
        
        with patch('footfix.utils.preferences_model.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            new_model = PreferencesModel()
            # Should restore from backup
            assert new_model.load_from_file()
    
    def test_validation_all(self):
        """Test validation of all preferences."""
        # All defaults should be valid
        is_valid, errors = self.model.validate_all()
        assert is_valid
        assert len(errors) == 0
        
        # Set invalid value and test
        self.model._data['processing.max_concurrent_batch'] = -1  # Bypass setter validation
        is_valid, errors = self.model.validate_all()
        assert not is_valid
        assert len(errors) > 0


class TestPreferencesViewModel:
    """Test the preferences view model."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        with patch('footfix.utils.preferences_model.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            self.model = PreferencesModel()
            self.viewmodel = PreferencesViewModel(self.model)
    
    def test_business_logic_getters(self):
        """Test business logic in getters."""
        # Test output folder with fallback
        folder = self.viewmodel.get_output_folder()
        assert folder is not None
        assert Path(folder).exists() or folder == str(Path.home() / "Downloads")
        
        # Test filename template validation
        template = self.viewmodel.get_filename_template()
        assert template is not None
        assert len(template) > 0
        
        # Test concurrent processes bounds
        processes = self.viewmodel.get_concurrent_processes()
        assert 1 <= processes <= 20
    
    def test_validation_setters(self):
        """Test validation in setters."""
        # Test valid values
        assert self.viewmodel.set_concurrent_processes(5)
        assert self.viewmodel.set_memory_limit(1024)
        assert self.viewmodel.set_api_key("sk-test-key-12345")
        
        # Test invalid values
        assert not self.viewmodel.set_concurrent_processes(25)  # Too high
        assert not self.viewmodel.set_memory_limit(100)  # Too low
        assert not self.viewmodel.set_api_key("short")  # Too short
    
    def test_recent_items_management(self):
        """Test recent items management."""
        # Add items
        self.viewmodel.add_recent_item('files', '/path/to/image1.jpg')
        self.viewmodel.add_recent_item('files', '/path/to/image2.jpg')
        self.viewmodel.add_recent_item('files', '/path/to/image1.jpg')  # Duplicate
        
        recent_files = self.viewmodel.get_recent_items('files')
        assert len(recent_files) == 2
        assert recent_files[0] == '/path/to/image1.jpg'  # Most recent first
        assert recent_files[1] == '/path/to/image2.jpg'
        
        # Clear items
        self.viewmodel.clear_recent_items('files')
        assert len(self.viewmodel.get_recent_items('files')) == 0
    
    def test_usage_stats(self):
        """Test usage statistics tracking."""
        # Initially empty
        stats = self.viewmodel.get_usage_stats()
        assert stats['total']['requests'] == 0
        assert stats['total']['cost'] == 0.0
        
        # Add some usage
        self.viewmodel.update_usage_stats(0.05, 1)
        self.viewmodel.update_usage_stats(0.03, 1)
        
        stats = self.viewmodel.get_usage_stats()
        assert stats['total']['requests'] == 2
        assert stats['total']['cost'] == 0.08
        assert stats['avg_cost_per_request'] > 0
        
        # Reset stats
        self.viewmodel.reset_usage_stats()
        stats = self.viewmodel.get_usage_stats()
        assert stats['total']['requests'] == 0
    
    def test_auto_save(self):
        """Test auto-save functionality."""
        # Mock the timer to trigger immediately
        with patch.object(self.viewmodel._auto_save_timer, 'start') as mock_start:
            self.viewmodel.set_preference('alt_text.enabled', True)
            mock_start.assert_called_once_with(1000)  # 1 second delay
    
    def test_unsaved_changes_tracking(self):
        """Test tracking of unsaved changes."""
        assert not self.viewmodel.has_unsaved_changes()
        
        # Make a change
        self.viewmodel.set_preference('alt_text.enabled', True)
        assert self.viewmodel.has_unsaved_changes()
        assert 'alt_text.enabled' in self.viewmodel.get_unsaved_keys()
        
        # Save changes
        self.viewmodel.save_preferences()
        assert not self.viewmodel.has_unsaved_changes()
    
    @pytest.mark.asyncio
    async def test_api_key_validation(self):
        """Test async API key validation."""
        # Mock the alt text generator
        with patch('footfix.utils.preferences_viewmodel.AltTextGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_api_key.return_value = (True, "Valid API key")
            
            # Create a signal mock
            signal_mock = Mock()
            self.viewmodel.api_validation_completed.connect(signal_mock)
            
            # Test validation
            await self.viewmodel.validate_api_key_async("test-key")
            
            # Check that validation was called
            mock_generator.assert_called_once_with("test-key")
            mock_instance.validate_api_key.assert_called_once()


class TestPreferencesController:
    """Test the preferences controller."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Reset singleton for testing
        PreferencesController._instance = None
        PreferencesController._initialized = False
        
        with patch('footfix.utils.preferences_model.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            self.controller = PreferencesController.get_instance()
    
    def test_singleton_behavior(self):
        """Test singleton pattern."""
        controller2 = PreferencesController.get_instance()
        assert self.controller is controller2
    
    def test_convenience_methods(self):
        """Test convenience getter methods."""
        # Test type-specific getters
        assert isinstance(self.controller.get_bool('alt_text.enabled'), bool)
        assert isinstance(self.controller.get_int('processing.max_concurrent_batch'), int)
        assert isinstance(self.controller.get_str('output.filename_template'), str)
        assert isinstance(self.controller.get_list('recent.files'), list)
        assert isinstance(self.controller.get_dict('alt_text.usage_stats'), dict)
    
    def test_specialized_getters(self):
        """Test specialized business logic getters."""
        # Test output folder
        folder = self.controller.get_output_folder()
        assert folder is not None
        assert isinstance(folder, str)
        
        # Test filename template
        template = self.controller.get_filename_template()
        assert template is not None
        assert '{' in template  # Should contain template variables
        
        # Test memory limit
        memory = self.controller.get_memory_limit_mb()
        assert 512 <= memory <= 16384
    
    def test_batch_operations(self):
        """Test batch preference operations."""
        # Test multiple update
        prefs = {
            'alt_text.enabled': True,
            'processing.max_concurrent_batch': 7,
            'interface.show_tooltips': False
        }
        assert self.controller.update_multiple(prefs)
        
        # Verify values
        assert self.controller.get_bool('alt_text.enabled') == True
        assert self.controller.get_int('processing.max_concurrent_batch') == 7
        assert self.controller.get_bool('interface.show_tooltips') == False
        
        # Test multiple get
        keys = ['alt_text.enabled', 'processing.max_concurrent_batch']
        result = self.controller.get_multiple(keys)
        assert len(result) == 2
        assert result['alt_text.enabled'] == True
        assert result['processing.max_concurrent_batch'] == 7
    
    def test_category_operations(self):
        """Test category-based operations."""
        # Set category preferences
        processing_prefs = {
            'max_concurrent_batch': 5,
            'preserve_metadata': False,
            'auto_preview': True
        }
        assert self.controller.set_category_preferences('processing', processing_prefs)
        
        # Get category preferences
        result = self.controller.get_category_preferences('processing')
        assert 'processing.max_concurrent_batch' in result
        assert result['processing.max_concurrent_batch'] == 5
        assert result['processing.preserve_metadata'] == False
    
    def test_recent_items_management(self):
        """Test recent items management."""
        # Add recent files
        self.controller.add_recent_file('/path/to/image1.jpg')
        self.controller.add_recent_file('/path/to/image2.jpg')
        
        recent_files = self.controller.get_recent_items('files')
        assert len(recent_files) >= 2
        assert '/path/to/image2.jpg' in recent_files
        
        # Add recent presets
        self.controller.add_recent_preset('web-optimized')
        recent_presets = self.controller.get_recent_items('presets')
        assert 'web-optimized' in recent_presets
        
        # Clear recent items
        self.controller.clear_recent_files()
        assert len(self.controller.get_recent_items('files')) == 0
    
    def test_usage_statistics(self):
        """Test usage statistics tracking."""
        # Update stats
        self.controller.update_usage_stats(0.05, 1)
        self.controller.update_usage_stats(0.03, 1)
        
        stats = self.controller.get_usage_stats()
        assert stats['total']['requests'] == 2
        assert stats['total']['cost'] == 0.08
        
        # Reset stats
        self.controller.reset_usage_stats()
        stats = self.controller.get_usage_stats()
        assert stats['total']['requests'] == 0
    
    def test_export_import(self):
        """Test export and import functionality."""
        # Set some preferences
        self.controller.set('alt_text.enabled', True)
        self.controller.set('processing.max_concurrent_batch', 8)
        
        # Export to file
        export_file = self.temp_dir / "export_test.json"
        assert self.controller.export_preferences(export_file)
        assert export_file.exists()
        
        # Modify preferences
        self.controller.set('alt_text.enabled', False)
        assert self.controller.get_bool('alt_text.enabled') == False
        
        # Import from file
        assert self.controller.import_preferences(export_file)
        assert self.controller.get_bool('alt_text.enabled') == True
        assert self.controller.get_int('processing.max_concurrent_batch') == 8
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with self.controller as prefs:
            prefs.set('alt_text.enabled', True)
            assert prefs.has_unsaved_changes()
        
        # Changes should be auto-saved on exit
        # Note: This might require mocking or actual file operations


class TestPreferencesMigrator:
    """Test preferences migration functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.old_prefs_path = self.temp_dir / ".footfix" / "preferences.json"
        self.old_prefs_path.parent.mkdir(parents=True, exist_ok=True)
        
        with patch('footfix.utils.preferences_migration.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            self.migrator = PreferencesMigrator()
    
    def test_needs_migration_detection(self):
        """Test migration need detection."""
        # Initially no migration needed
        assert not self.migrator.needs_migration()
        
        # Create old preferences file
        old_prefs = {
            'output': {
                'default_folder': '/old/path',
                'filename_template': '{name}_{preset}'
            },
            'processing': {
                'max_concurrent_batch': 5
            }
        }
        
        with open(self.old_prefs_path, 'w') as f:
            json.dump(old_prefs, f)
        
        # Now migration should be needed
        assert self.migrator.needs_migration()
    
    def test_successful_migration(self):
        """Test successful migration process."""
        # Create old preferences
        old_prefs = {
            'output': {
                'default_folder': str(self.temp_dir / "output"),
                'filename_template': '{original_name}_{preset}',
                'duplicate_strategy': 'rename'
            },
            'processing': {
                'max_concurrent_batch': 5,
                'preserve_metadata': True
            },
            'alt_text': {
                'enabled': True,
                'api_key': 'test-key-12345'
            }
        }
        
        with open(self.old_prefs_path, 'w') as f:
            json.dump(old_prefs, f)
        
        # Mock the controller
        with patch('footfix.utils.preferences_migration.PreferencesController.get_instance') as mock_controller:
            mock_instance = Mock()
            mock_controller.return_value = mock_instance
            mock_instance.set.return_value = True
            mock_instance.save_preferences.return_value = True
            
            # Perform migration
            assert self.migrator.migrate()
            
            # Check that preferences were set
            assert mock_instance.set.call_count > 0
            mock_instance.save_preferences.assert_called_once()
    
    def test_migration_status(self):
        """Test migration status reporting."""
        status = self.migrator.get_migration_status()
        assert 'needs_migration' in status
        assert 'migration_complete' in status
        assert 'old_prefs_exist' in status
    
    def test_migration_rollback(self):
        """Test migration rollback."""
        # Mark migration as complete
        self.migrator._mark_migration_complete()
        assert self.migrator.migration_complete_flag.exists()
        
        # Rollback
        assert self.migrator.rollback_migration()
        assert not self.migrator.migration_complete_flag.exists()


class TestPreferencesIntegration:
    """Integration tests for the complete preferences system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Reset singleton
        PreferencesController._instance = None
        PreferencesController._initialized = False
    
    @patch('footfix.utils.preferences_model.Path.home')
    @patch('footfix.utils.preferences_migration.Path.home')
    def test_end_to_end_workflow(self, mock_migration_home, mock_model_home):
        """Test complete end-to-end workflow."""
        mock_migration_home.return_value = self.temp_dir
        mock_model_home.return_value = self.temp_dir
        
        # Create old preferences to migrate
        old_prefs_path = self.temp_dir / ".footfix" / "preferences.json"
        old_prefs_path.parent.mkdir(parents=True, exist_ok=True)
        
        old_prefs = {
            'output': {'default_folder': str(self.temp_dir)},
            'alt_text': {'enabled': True, 'api_key': 'test-key'}
        }
        
        with open(old_prefs_path, 'w') as f:
            json.dump(old_prefs, f)
        
        # Initialize controller (should trigger migration)
        controller = PreferencesController.get_instance()
        
        # Verify migration worked
        assert controller.get('output.default_folder') == str(self.temp_dir)
        assert controller.get_bool('alt_text.enabled') == True
        assert controller.get('alt_text.api_key') == 'test-key'
        
        # Make some changes
        controller.set('processing.max_concurrent_batch', 7)
        controller.add_recent_file('/test/image.jpg')
        
        # Save and reload
        assert controller.save_preferences()
        controller.reload_from_disk()
        
        # Verify persistence
        assert controller.get_int('processing.max_concurrent_batch') == 7
        recent_files = controller.get_recent_items('files')
        assert '/test/image.jpg' in recent_files
    
    def test_signal_propagation(self):
        """Test that signals propagate correctly through the system."""
        with patch('footfix.utils.preferences_model.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            
            controller = PreferencesController.get_instance()
            
            # Connect to signals
            changed_signal = Mock()
            loaded_signal = Mock()
            controller.preferences_changed.connect(changed_signal)
            controller.preferences_loaded.connect(loaded_signal)
            
            # Make a change
            controller.set('alt_text.enabled', True)
            
            # Verify signal was emitted
            changed_signal.emit.assert_called_with('alt_text.enabled', True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])