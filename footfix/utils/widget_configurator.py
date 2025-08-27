"""
Widget configuration utilities for FootFix.
Separates business logic configuration from GUI setup.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .preferences import PreferencesManager
from .api_validator import ApiKeyValidator
from ..core.batch_processor import BatchProcessor
from ..core.tag_manager import TagManager

logger = logging.getLogger(__name__)


class WidgetConfigurator:
    """Utility class for configuring widget business logic and settings."""
    
    def __init__(self, preferences_manager: Optional[PreferencesManager] = None):
        """Initialize the configurator with a preferences manager."""
        self.prefs_manager = preferences_manager or PreferencesManager.get_instance()
        self.api_validator = ApiKeyValidator(self.prefs_manager)
    
    def configure_batch_processor(self, batch_processor: BatchProcessor, 
                                  tag_manager: Optional[TagManager] = None) -> None:
        """
        Configure batch processor with preferences-based settings.
        
        Args:
            batch_processor: The batch processor to configure
            tag_manager: Optional tag manager to associate with the processor
        """
        logger.info("Configuring batch processor with preferences")
        
        # Apply memory optimization settings
        memory_limit = self.prefs_manager.get('advanced.memory_limit_mb', 2048)
        batch_processor.set_memory_limit(memory_limit)
        batch_processor.set_memory_optimization(True)
        
        # Configure tag manager if provided
        if tag_manager:
            batch_processor.set_tag_manager(tag_manager)
            logger.info("Tag manager associated with batch processor")
        
        logger.info(f"Batch processor configured with {memory_limit}MB memory limit")
    
    def configure_alt_text_settings(self, widget: Any) -> Dict[str, Any]:
        """
        Configure alt text settings and return configuration state.
        
        Args:
            widget: The widget being configured (should have alt text UI elements)
            
        Returns:
            Dictionary with alt text configuration state
        """
        config = {
            'api_available': False,
            'enabled_by_default': False,
            'tooltip_message': '',
            'status_message': ''
        }
        
        # Check API availability
        config['api_available'] = self.api_validator.is_alt_text_available()
        
        if config['api_available']:
            config['enabled_by_default'] = self.prefs_manager.get('alt_text.enabled', False)
            config['tooltip_message'] = "Enable automatic alt text generation using AI after image processing"
            config['status_message'] = "Alt text available"
            logger.info("Alt text configuration: API available")
        else:
            config['tooltip_message'] = self.api_validator.get_alt_text_error_message()
            config['status_message'] = "Alt text unavailable"
            logger.info("Alt text configuration: API not available")
        
        return config
    
    def configure_tag_settings(self, widget: Any) -> Dict[str, Any]:
        """
        Configure tag settings and return configuration state.
        
        Args:
            widget: The widget being configured (should have tag UI elements)
            
        Returns:
            Dictionary with tag configuration state
        """
        config = {
            'tags_enabled': False,
            'ai_tags_available': False,
            'ai_tags_enabled': False,
            'tags_tooltip': '',
            'ai_tags_tooltip': '',
            'status_message': ''
        }
        
        # Basic tagging is always available
        config['tags_enabled'] = self.prefs_manager.get('tags.enabled', True)
        config['tags_tooltip'] = "Enable tag assignment to images during processing"
        
        # AI tag availability depends on API key
        config['ai_tags_available'] = self.api_validator.is_ai_tags_available()
        
        if config['ai_tags_available']:
            config['ai_tags_enabled'] = self.prefs_manager.get('tags.ai_generation_enabled', False)
            config['ai_tags_tooltip'] = "Enable automatic AI-powered tag generation based on image content"
        else:
            config['ai_tags_tooltip'] = self.api_validator.get_ai_tags_error_message()
        
        # Generate status message
        if config['tags_enabled'] and config['ai_tags_available'] and config['ai_tags_enabled']:
            config['status_message'] = "Tagging + AI enabled"
        elif config['tags_enabled']:
            config['status_message'] = "Tagging enabled"
        elif config['ai_tags_available'] and config['ai_tags_enabled']:
            config['status_message'] = "AI tagging only"
        else:
            config['status_message'] = "Tagging disabled"
        
        logger.info(f"Tag configuration: basic={config['tags_enabled']}, AI={config['ai_tags_enabled']}")
        
        return config
    
    def load_output_settings(self) -> Dict[str, Any]:
        """
        Load output settings from preferences.
        
        Returns:
            Dictionary with output configuration
        """
        output_folder = Path(self.prefs_manager.get('output.default_folder', Path.home() / "Downloads"))
        
        settings = {
            'output_folder': output_folder,
            'filename_template': self.prefs_manager.get('output.filename_template', '{original_name}_{preset}'),
            'duplicate_strategy': self.prefs_manager.get('output.duplicate_strategy', 'rename'),
            'recent_folders': self.prefs_manager.get('output.recent_folders', []),
            'favorite_folders': self.prefs_manager.get('output.favorite_folders', [])
        }
        
        logger.info(f"Output settings loaded: folder={output_folder}")
        return settings
    
    def configure_widget_components(self, widget: Any, batch_processor: BatchProcessor, 
                                    tag_manager: TagManager) -> Dict[str, Any]:
        """
        Perform complete widget configuration for all business logic components.
        
        Args:
            widget: The widget to configure
            batch_processor: The batch processor instance
            tag_manager: The tag manager instance
            
        Returns:
            Dictionary with all configuration states
        """
        logger.info("Starting complete widget configuration")
        
        # Configure batch processor
        self.configure_batch_processor(batch_processor, tag_manager)
        
        # Load configuration states
        config = {
            'alt_text': self.configure_alt_text_settings(widget),
            'tags': self.configure_tag_settings(widget),
            'output': self.load_output_settings()
        }
        
        logger.info("Widget configuration completed")
        return config
    
    def handle_preference_change(self, key: str, widget: Any) -> Dict[str, Any]:
        """
        Handle preference changes and return updated configuration.
        
        Args:
            key: The preference key that changed
            widget: The widget to update
            
        Returns:
            Dictionary with updated configuration for the changed category
        """
        logger.info(f"Handling preference change: {key}")
        
        if key.startswith('output.'):
            return {'output': self.load_output_settings()}
        elif key.startswith('alt_text.'):
            return {'alt_text': self.configure_alt_text_settings(widget)}
        elif key.startswith('tags.'):
            return {'tags': self.configure_tag_settings(widget)}
        else:
            # Return all configurations for other changes
            return {
                'alt_text': self.configure_alt_text_settings(widget),
                'tags': self.configure_tag_settings(widget),
                'output': self.load_output_settings()
            }