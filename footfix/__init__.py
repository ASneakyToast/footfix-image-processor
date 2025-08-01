"""
FootFix - Image Processing Desktop Application for macOS
A batch image processor that automates image optimization for editorial teams.
"""

__version__ = "0.1.0"
__author__ = "FootFix Team"
__email__ = "info@footfix.app"

from .core.processor import ImageProcessor
from .presets.profiles import PresetProfile, EditorialWebPreset

__all__ = ["ImageProcessor", "PresetProfile", "EditorialWebPreset"]