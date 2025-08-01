"""
Core image processing functionality for FootFix.
Handles image loading, processing, and saving with various presets.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageOps
import io

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Core image processor that handles loading, processing, and saving images.
    Supports various image formats and preset profiles.
    """
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB in bytes
    MIN_FILE_SIZE = 1024  # 1KB in bytes
    
    def __init__(self):
        """Initialize the image processor."""
        self.current_image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.source_path: Optional[Path] = None
        
    def load_image(self, image_path: str | Path) -> bool:
        """
        Load an image from the specified path.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            bool: True if image loaded successfully, False otherwise
        """
        try:
            path = Path(image_path)
            
            # Validate file exists
            if not path.exists():
                logger.error(f"File does not exist: {path}")
                return False
                
            # Validate file extension
            if path.suffix.lower() not in self.SUPPORTED_FORMATS:
                logger.error(f"Unsupported file format: {path.suffix}")
                return False
                
            # Validate file size
            file_size = path.stat().st_size
            if file_size < self.MIN_FILE_SIZE or file_size > self.MAX_FILE_SIZE:
                logger.error(f"File size {file_size} bytes is outside valid range")
                return False
                
            # Load the image
            self.original_image = Image.open(path)
            self.current_image = self.original_image.copy()
            self.source_path = path
            
            # Convert RGBA to RGB if necessary
            if self.current_image.mode == 'RGBA':
                # Create a white background
                background = Image.new('RGB', self.current_image.size, (255, 255, 255))
                background.paste(self.current_image, mask=self.current_image.split()[3])
                self.current_image = background
                self.original_image = self.current_image.copy()
            elif self.current_image.mode not in ['RGB', 'L']:
                self.current_image = self.current_image.convert('RGB')
                self.original_image = self.current_image.copy()
                
            logger.info(f"Successfully loaded image: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return False
            
    def resize_to_fit(self, max_width: int, max_height: int, maintain_aspect: bool = True) -> None:
        """
        Resize the current image to fit within the specified dimensions.
        
        Args:
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            maintain_aspect: Whether to maintain aspect ratio
        """
        if not self.current_image:
            raise ValueError("No image loaded")
            
        if maintain_aspect:
            self.current_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        else:
            self.current_image = self.current_image.resize((max_width, max_height), Image.Resampling.LANCZOS)
            
    def resize_to_exact(self, width: int, height: int) -> None:
        """
        Resize the image to exact dimensions, cropping if necessary to maintain aspect ratio.
        
        Args:
            width: Target width in pixels
            height: Target height in pixels
        """
        if not self.current_image:
            raise ValueError("No image loaded")
            
        # Use ImageOps.fit to resize and crop to exact dimensions
        self.current_image = ImageOps.fit(
            self.current_image, 
            (width, height), 
            Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        )
        
    def optimize_file_size(self, target_size_kb: int, format: str = 'JPEG') -> bytes:
        """
        Optimize the image to reach a target file size.
        
        Args:
            target_size_kb: Target file size in kilobytes
            format: Output format (JPEG or PNG)
            
        Returns:
            bytes: Optimized image data
        """
        if not self.current_image:
            raise ValueError("No image loaded")
            
        target_size_bytes = target_size_kb * 1024
        
        # Start with high quality
        quality = 95
        min_quality = 10
        
        while quality >= min_quality:
            buffer = io.BytesIO()
            
            if format.upper() == 'JPEG':
                self.current_image.save(buffer, format='JPEG', quality=quality, optimize=True)
            else:
                self.current_image.save(buffer, format=format, optimize=True)
                
            size = buffer.tell()
            
            if size <= target_size_bytes:
                buffer.seek(0)
                return buffer.getvalue()
                
            # Reduce quality
            quality -= 5
            
        # If we couldn't reach target size, return with minimum quality
        buffer = io.BytesIO()
        if format.upper() == 'JPEG':
            self.current_image.save(buffer, format='JPEG', quality=min_quality, optimize=True)
        else:
            self.current_image.save(buffer, format=format, optimize=True)
        buffer.seek(0)
        return buffer.getvalue()
        
    def save_image(self, output_path: str | Path, preset_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save the processed image to the specified path.
        
        Args:
            output_path: Path where the image should be saved
            preset_config: Optional configuration for output format and quality
            
        Returns:
            bool: True if save successful, False otherwise
        """
        if not self.current_image:
            logger.error("No image to save")
            return False
            
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if preset_config and preset_config.get('target_size_kb'):
                # Optimize for file size
                image_data = self.optimize_file_size(
                    preset_config['target_size_kb'],
                    format=preset_config.get('format', 'JPEG')
                )
                with open(path, 'wb') as f:
                    f.write(image_data)
            else:
                # Standard save
                save_kwargs = {
                    'optimize': True,
                    'quality': preset_config.get('quality', 85) if preset_config else 85
                }
                
                if path.suffix.lower() in ['.jpg', '.jpeg']:
                    self.current_image.save(path, 'JPEG', **save_kwargs)
                elif path.suffix.lower() == '.png':
                    self.current_image.save(path, 'PNG', optimize=True)
                else:
                    self.current_image.save(path)
                    
            logger.info(f"Successfully saved image to: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return False
            
    def get_image_info(self) -> Dict[str, Any]:
        """
        Get information about the current image.
        
        Returns:
            Dict containing image information
        """
        if not self.current_image:
            return {}
            
        return {
            'width': self.current_image.width,
            'height': self.current_image.height,
            'mode': self.current_image.mode,
            'format': self.current_image.format,
            'size_pixels': f"{self.current_image.width}x{self.current_image.height}",
        }
        
    def reset_to_original(self) -> None:
        """Reset the current image to the original loaded image."""
        if self.original_image:
            self.current_image = self.original_image.copy()