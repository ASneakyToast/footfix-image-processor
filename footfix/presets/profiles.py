"""
Preset profiles for image processing.
Each preset defines specific dimensions, file size targets, and output formats.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from ..core.processor import ImageProcessor

logger = logging.getLogger(__name__)


@dataclass
class PresetConfig:
    """Configuration for a preset profile."""
    name: str
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    exact_width: Optional[int] = None
    exact_height: Optional[int] = None
    target_size_kb: Optional[int] = None
    min_size_kb: Optional[int] = None
    max_size_kb: Optional[int] = None
    format: str = 'JPEG'
    quality: int = 85
    maintain_aspect: bool = True
    

class PresetProfile(ABC):
    """Abstract base class for preset profiles."""
    
    def __init__(self):
        self.config = self.get_config()
        
    @abstractmethod
    def get_config(self) -> PresetConfig:
        """Return the configuration for this preset."""
        pass
        
    def process(self, processor: ImageProcessor) -> bool:
        """
        Process an image using this preset's configuration.
        
        Args:
            processor: ImageProcessor instance with loaded image
            
        Returns:
            bool: True if processing successful, False otherwise
        """
        if not processor.current_image:
            logger.error("No image loaded in processor")
            return False
            
        try:
            # Reset to original before processing
            processor.reset_to_original()
            
            # Apply resizing based on configuration
            if self.config.exact_width and self.config.exact_height:
                # Exact dimensions (will crop if necessary)
                processor.resize_to_exact(self.config.exact_width, self.config.exact_height)
            elif self.config.max_width and self.config.max_height:
                # Fit within max dimensions
                processor.resize_to_fit(
                    self.config.max_width, 
                    self.config.max_height,
                    self.config.maintain_aspect
                )
                
            logger.info(f"Applied {self.config.name} preset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error applying preset {self.config.name}: {e}")
            return False
            
    def get_output_config(self) -> Dict[str, Any]:
        """Get configuration for saving the processed image."""
        config = {
            'format': self.config.format,
            'quality': self.config.quality,
        }
        
        if self.config.target_size_kb:
            config['target_size_kb'] = self.config.target_size_kb
            
        return config
        
    def get_suggested_filename(self, original_path: Path) -> str:
        """
        Generate a suggested output filename based on the preset.
        
        Args:
            original_path: Path to the original image
            
        Returns:
            str: Suggested filename
        """
        stem = original_path.stem
        suffix = '.jpg' if self.config.format == 'JPEG' else f'.{self.config.format.lower()}'
        preset_suffix = self.config.name.lower().replace(' ', '_')
        return f"{stem}_{preset_suffix}{suffix}"


class EditorialWebPreset(PresetProfile):
    """Preset for editorial web usage: Max 2560×1440px, 0.5-1MB target."""
    
    def get_config(self) -> PresetConfig:
        return PresetConfig(
            name="Editorial Web",
            max_width=2560,
            max_height=1440,
            min_size_kb=500,
            max_size_kb=1024,
            target_size_kb=750,  # Aim for middle of range
            format='JPEG',
            quality=85,
            maintain_aspect=True
        )


class EmailPreset(PresetProfile):
    """Preset for email usage: Max 600px width, <100KB target."""
    
    def get_config(self) -> PresetConfig:
        return PresetConfig(
            name="Email",
            max_width=600,
            max_height=2000,  # Reasonable max height
            target_size_kb=80,  # Stay well under 100KB
            format='JPEG',
            quality=75,
            maintain_aspect=True
        )


class InstagramStoryPreset(PresetProfile):
    """Preset for Instagram Stories: 1080×1920px (9:16 aspect ratio)."""
    
    def get_config(self) -> PresetConfig:
        return PresetConfig(
            name="Instagram Story",
            exact_width=1080,
            exact_height=1920,
            format='JPEG',
            quality=90,
            maintain_aspect=False
        )


class InstagramFeedPortraitPreset(PresetProfile):
    """Preset for Instagram Feed Portrait: 1080×1350px (4:5 aspect ratio)."""
    
    def get_config(self) -> PresetConfig:
        return PresetConfig(
            name="Instagram Feed Portrait",
            exact_width=1080,
            exact_height=1350,
            format='JPEG',
            quality=90,
            maintain_aspect=False
        )


# Registry of available presets
PRESET_REGISTRY = {
    'editorial_web': EditorialWebPreset,
    'email': EmailPreset,
    'instagram_story': InstagramStoryPreset,
    'instagram_feed_portrait': InstagramFeedPortraitPreset,
}


def get_preset(preset_name: str) -> Optional[PresetProfile]:
    """
    Get a preset profile by name.
    
    Args:
        preset_name: Name of the preset (key in PRESET_REGISTRY)
        
    Returns:
        PresetProfile instance or None if not found
    """
    preset_class = PRESET_REGISTRY.get(preset_name)
    if preset_class:
        return preset_class()
    return None