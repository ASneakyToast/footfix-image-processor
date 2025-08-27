"""
API key validation utilities for FootFix.
Centralizes API key validation logic that was scattered across GUI widgets.
"""

import logging
from typing import Optional, Tuple
from .preferences import PreferencesManager

logger = logging.getLogger(__name__)


class ApiKeyValidator:
    """Centralized API key validation and configuration utility."""
    
    def __init__(self, preferences_manager: Optional[PreferencesManager] = None):
        """Initialize the validator with a preferences manager."""
        self.prefs_manager = preferences_manager or PreferencesManager.get_instance()
    
    def validate_alt_text_api_key(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate alt text API key configuration.
        
        Returns:
            Tuple of (is_valid, api_key, error_message)
        """
        api_key = self.prefs_manager.get('alt_text.api_key')
        
        if not api_key or not api_key.strip():
            return False, None, "No Anthropic API key configured for alt text generation"
        
        # Basic format validation - Anthropic keys typically start with 'sk-ant-'
        if not api_key.startswith('sk-ant-'):
            logger.warning("API key may not be in expected format")
        
        return True, api_key, None
    
    def validate_ai_tag_api_key(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate AI tag generation API key configuration.
        
        Returns:
            Tuple of (is_valid, api_key, error_message)
        """
        # Check if sharing API key with alt text
        share_api_key = self.prefs_manager.get('tags.ai_share_api_key_with_alt_text', True)
        
        if share_api_key:
            # Use alt text API key
            return self.validate_alt_text_api_key()
        else:
            # Use separate API key (future implementation)
            api_key = self.prefs_manager.get('tags.ai_api_key')
            
            if not api_key or not api_key.strip():
                return False, None, "No Anthropic API key configured for AI tag generation"
            
            return True, api_key, None
    
    def get_configured_api_key(self, service_type: str) -> Optional[str]:
        """
        Get the configured API key for a specific service.
        
        Args:
            service_type: Either 'alt_text' or 'ai_tags'
            
        Returns:
            The API key if valid, None otherwise
        """
        if service_type == 'alt_text':
            is_valid, api_key, _ = self.validate_alt_text_api_key()
            return api_key if is_valid else None
        elif service_type == 'ai_tags':
            is_valid, api_key, _ = self.validate_ai_tag_api_key()
            return api_key if is_valid else None
        else:
            logger.error(f"Unknown service type: {service_type}")
            return None
    
    def is_alt_text_available(self) -> bool:
        """Check if alt text generation is available (API key configured)."""
        is_valid, _, _ = self.validate_alt_text_api_key()
        return is_valid
    
    def is_ai_tags_available(self) -> bool:
        """Check if AI tag generation is available (API key configured)."""
        is_valid, _, _ = self.validate_ai_tag_api_key()
        return is_valid
    
    def get_alt_text_error_message(self) -> str:
        """Get user-friendly error message for alt text configuration issues."""
        is_valid, _, error = self.validate_alt_text_api_key()
        
        if is_valid:
            return ""
        
        return "Configure Anthropic API key in Preferences → Alt Text to enable alt text generation"
    
    def get_ai_tags_error_message(self) -> str:
        """Get user-friendly error message for AI tags configuration issues."""
        is_valid, _, error = self.validate_ai_tag_api_key()
        
        if is_valid:
            return ""
        
        share_api_key = self.prefs_manager.get('tags.ai_share_api_key_with_alt_text', True)
        
        if share_api_key:
            return "Configure Anthropic API key in Preferences → Alt Text to enable AI tag generation"
        else:
            return "Configure Anthropic API key in Preferences → Tags to enable AI tag generation"