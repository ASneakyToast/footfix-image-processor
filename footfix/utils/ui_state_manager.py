"""
UI State management service for FootFix.
Coordinates state synchronization between UI components and handles preference changes.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from .preferences import PreferencesManager
from .api_validator import ApiKeyValidator
from ..core.batch_processor import BatchProcessor
from ..core.alt_text_generator import AltTextStatus
from ..core.tag_manager import TagStatus, TagManager

logger = logging.getLogger(__name__)


@dataclass
class UIState:
    """Represents the current UI state."""
    # Queue state
    queue_size: int = 0
    selected_count: int = 0
    has_items_with_alt_text: bool = False
    has_items_with_tags: bool = False
    
    # Processing state
    is_processing: bool = False
    is_cancelling: bool = False
    
    # Feature states
    alt_text_enabled: bool = False
    alt_text_available: bool = False
    tagging_enabled: bool = False
    ai_tagging_enabled: bool = False
    ai_tagging_available: bool = False
    
    # Settings
    output_folder: Optional[Path] = None
    selected_preset: str = "Default"
    filename_template: Optional[str] = None


class UIStateManager(QObject):
    """
    Manages UI state synchronization across components.
    Handles preference changes and coordinates widget updates.
    """
    
    # Signals
    state_changed = Signal(UIState)
    alt_text_availability_changed = Signal(bool)
    ai_tagging_availability_changed = Signal(bool)
    output_settings_changed = Signal(dict)
    preset_changed = Signal(str)
    
    def __init__(self, batch_processor: BatchProcessor, tag_manager: TagManager):
        """
        Initialize the UI state manager.
        
        Args:
            batch_processor: The batch processor instance
            tag_manager: The tag manager instance
        """
        super().__init__()
        self.batch_processor = batch_processor
        self.tag_manager = tag_manager
        self.prefs_manager = PreferencesManager.get_instance()
        self.api_validator = ApiKeyValidator(self.prefs_manager)
        
        # Initialize state
        self.state = UIState()
        self._load_initial_state()
        
        # Connect to preference changes
        self.prefs_manager.preferences_changed.connect(self.on_preference_changed)
        
    def _load_initial_state(self):
        """Load initial state from preferences."""
        # Load output settings
        self.state.output_folder = Path(self.prefs_manager.get(
            'output.default_folder', 
            Path.home() / "Pictures" / "FootFix"
        ))
        self.state.filename_template = self.prefs_manager.get(
            'output.filename_template', 
            "{original_name}_optimized"
        )
        
        # Load feature states
        self.state.alt_text_enabled = self.prefs_manager.get('alt_text.enabled', False)
        self.state.tagging_enabled = self.prefs_manager.get('tags.enabled', True)
        self.state.ai_tagging_enabled = self.prefs_manager.get('tags.ai_generation_enabled', False)
        
        # Check API availability
        self.refresh_api_availability()
        
        logger.info("Loaded initial UI state from preferences")
        
    def refresh_api_availability(self):
        """Refresh API key availability for features."""
        # Check alt text availability
        old_alt_text_available = self.state.alt_text_available
        self.state.alt_text_available = self.api_validator.is_alt_text_available()
        
        if old_alt_text_available != self.state.alt_text_available:
            self.alt_text_availability_changed.emit(self.state.alt_text_available)
            logger.info(f"Alt text availability changed to: {self.state.alt_text_available}")
            
        # Check AI tagging availability
        old_ai_tagging_available = self.state.ai_tagging_available
        self.state.ai_tagging_available = self.api_validator.is_ai_tags_available()
        
        if old_ai_tagging_available != self.state.ai_tagging_available:
            self.ai_tagging_availability_changed.emit(self.state.ai_tagging_available)
            logger.info(f"AI tagging availability changed to: {self.state.ai_tagging_available}")
            
        # Disable features if API not available
        if not self.state.alt_text_available:
            self.state.alt_text_enabled = False
            
        if not self.state.ai_tagging_available:
            self.state.ai_tagging_enabled = False
            
        self.state_changed.emit(self.state)
        
    def update_queue_state(self, queue_size: int, selected_count: int = 0):
        """
        Update queue-related state.
        
        Args:
            queue_size: Number of items in queue
            selected_count: Number of selected items
        """
        self.state.queue_size = queue_size
        self.state.selected_count = selected_count
        
        # Check for alt text and tags
        self.state.has_items_with_alt_text = any(
            item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text
            for item in self.batch_processor.queue
        )
        
        self.state.has_items_with_tags = any(
            item.tag_status == TagStatus.COMPLETED and item.tags
            for item in self.batch_processor.queue
        )
        
        self.state_changed.emit(self.state)
        logger.debug(f"Queue state updated: size={queue_size}, selected={selected_count}")
        
    def set_processing_state(self, is_processing: bool):
        """
        Set the processing state.
        
        Args:
            is_processing: Whether processing is active
        """
        self.state.is_processing = is_processing
        if not is_processing:
            self.state.is_cancelling = False
            
        self.state_changed.emit(self.state)
        logger.debug(f"Processing state set to: {is_processing}")
        
    def set_cancelling_state(self, is_cancelling: bool):
        """
        Set the cancelling state.
        
        Args:
            is_cancelling: Whether cancellation is in progress
        """
        self.state.is_cancelling = is_cancelling
        self.state_changed.emit(self.state)
        logger.debug(f"Cancelling state set to: {is_cancelling}")
        
    def set_alt_text_enabled(self, enabled: bool):
        """
        Set alt text generation enabled state.
        
        Args:
            enabled: Whether alt text generation is enabled
        """
        if enabled and not self.state.alt_text_available:
            logger.warning("Cannot enable alt text without valid API key")
            return
            
        self.state.alt_text_enabled = enabled
        self.prefs_manager.set('alt_text.enabled', enabled)
        self.prefs_manager.save()
        
        # Configure batch processor
        if enabled:
            is_valid, api_key, _ = self.api_validator.validate_alt_text_api_key()
            if is_valid:
                self.batch_processor.set_alt_text_generation(True, api_key)
                context = self.prefs_manager.get('alt_text.default_context', 'editorial image')
                self.batch_processor.set_alt_text_context(context)
        else:
            self.batch_processor.set_alt_text_generation(False)
            
        self.state_changed.emit(self.state)
        logger.info(f"Alt text generation set to: {enabled}")
        
    def set_tagging_enabled(self, enabled: bool):
        """
        Set tagging enabled state.
        
        Args:
            enabled: Whether tagging is enabled
        """
        self.state.tagging_enabled = enabled
        self.prefs_manager.set('tags.enabled', enabled)
        self.prefs_manager.save()
        
        self.state_changed.emit(self.state)
        logger.info(f"Tagging set to: {enabled}")
        
    def set_ai_tagging_enabled(self, enabled: bool):
        """
        Set AI tagging enabled state.
        
        Args:
            enabled: Whether AI tagging is enabled
        """
        if enabled and not self.state.ai_tagging_available:
            logger.warning("Cannot enable AI tagging without valid API key")
            return
            
        self.state.ai_tagging_enabled = enabled
        self.prefs_manager.set('tags.ai_generation_enabled', enabled)
        self.prefs_manager.save()
        
        # Configure tag manager
        if enabled:
            is_valid, api_key, _ = self.api_validator.validate_ai_tag_api_key()
            if is_valid:
                self.tag_manager.enable_ai_generation(api_key)
        else:
            self.tag_manager.disable_ai_generation()
            
        self.state_changed.emit(self.state)
        logger.info(f"AI tagging set to: {enabled}")
        
    def set_output_folder(self, folder: Path):
        """
        Set the output folder.
        
        Args:
            folder: Output folder path
        """
        self.state.output_folder = folder
        self.output_settings_changed.emit({
            'output_folder': folder,
            'filename_template': self.state.filename_template
        })
        logger.info(f"Output folder set to: {folder}")
        
    def set_preset(self, preset_name: str):
        """
        Set the selected preset.
        
        Args:
            preset_name: Name of the preset
        """
        self.state.selected_preset = preset_name
        self.preset_changed.emit(preset_name)
        logger.info(f"Preset set to: {preset_name}")
        
    def on_preference_changed(self, key: str):
        """
        Handle preference changes.
        
        Args:
            key: The preference key that changed
        """
        logger.debug(f"Handling preference change: {key}")
        
        # Handle output settings
        if key.startswith('output.'):
            if key == 'output.default_folder':
                folder = self.prefs_manager.get(key, self.state.output_folder)
                if folder:
                    self.state.output_folder = Path(folder)
                    
            elif key == 'output.filename_template':
                self.state.filename_template = self.prefs_manager.get(key, self.state.filename_template)
                
            self.output_settings_changed.emit({
                'output_folder': self.state.output_folder,
                'filename_template': self.state.filename_template
            })
            
        # Handle alt text settings
        elif key.startswith('alt_text.'):
            if key == 'alt_text.api_key':
                self.refresh_api_availability()
                
            elif key == 'alt_text.enabled':
                enabled = self.prefs_manager.get(key, False)
                if self.state.alt_text_available:
                    self.state.alt_text_enabled = enabled
                    
            elif key == 'alt_text.default_context':
                if self.state.alt_text_enabled:
                    context = self.prefs_manager.get(key, 'editorial image')
                    self.batch_processor.set_alt_text_context(context)
                    
        # Handle tag settings
        elif key.startswith('tags.'):
            if key == 'tags.enabled':
                self.state.tagging_enabled = self.prefs_manager.get(key, True)
                
            elif key == 'tags.ai_generation_enabled':
                enabled = self.prefs_manager.get(key, False)
                if self.state.ai_tagging_available:
                    self.state.ai_tagging_enabled = enabled
                    
            elif key == 'tags.api_key':
                self.refresh_api_availability()
                
        # Handle API settings
        elif key == 'api.anthropic_key':
            self.refresh_api_availability()
            
        self.state_changed.emit(self.state)
        
    def get_processing_config(self) -> Dict[str, Any]:
        """
        Get the current processing configuration.
        
        Returns:
            Dictionary with processing configuration
        """
        return {
            'preset_name': self.state.selected_preset,
            'output_folder': self.state.output_folder,
            'generate_alt_text': self.state.alt_text_enabled,
            'enable_tagging': self.state.tagging_enabled,
            'enable_ai_tagging': self.state.ai_tagging_enabled,
            'filename_template': self.state.filename_template
        }
        
    def get_feature_status(self) -> Dict[str, Any]:
        """
        Get the current feature status.
        
        Returns:
            Dictionary with feature status information
        """
        return {
            'alt_text': {
                'available': self.state.alt_text_available,
                'enabled': self.state.alt_text_enabled,
                'has_results': self.state.has_items_with_alt_text
            },
            'tagging': {
                'enabled': self.state.tagging_enabled,
                'has_results': self.state.has_items_with_tags
            },
            'ai_tagging': {
                'available': self.state.ai_tagging_available,
                'enabled': self.state.ai_tagging_enabled
            }
        }
        
    def sync_components(self, components: Dict[str, Any]):
        """
        Synchronize state across UI components.
        
        Args:
            components: Dictionary of UI components to synchronize
        """
        # Sync queue widget
        if 'queue_widget' in components:
            queue_widget = components['queue_widget']
            queue_widget.set_processing_state(self.state.is_processing)
            
        # Sync controls widget  
        if 'controls_widget' in components:
            controls_widget = components['controls_widget']
            controls_widget.set_processing_state(self.state.is_processing)
            controls_widget.set_cancel_state(self.state.is_cancelling)
            controls_widget.update_queue_state(
                self.state.queue_size, 
                self.state.selected_count
            )
            if self.state.output_folder:
                controls_widget.set_output_folder(self.state.output_folder)
                
        # Sync progress widget
        if 'progress_widget' in components:
            progress_widget = components['progress_widget']
            if self.state.is_processing:
                progress_widget.show_progress()
            else:
                progress_widget.hide_progress()
                
        logger.debug(f"Synchronized {len(components)} UI components")