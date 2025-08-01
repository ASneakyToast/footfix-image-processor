"""
Filename template system for FootFix.
Supports variable substitution for dynamic filename generation.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import os

from PySide6.QtWidgets import QWidget


class FilenameTemplate:
    """Handles filename template parsing and variable substitution."""
    
    # Available template variables
    VARIABLES = {
        '{original_name}': 'Original filename without extension',
        '{original_ext}': 'Original file extension',
        '{preset}': 'Name of the preset used',
        '{date}': 'Current date (YYYY-MM-DD)',
        '{time}': 'Current time (HH-MM-SS)',
        '{year}': 'Current year (YYYY)',
        '{month}': 'Current month (MM)',
        '{day}': 'Current day (DD)',
        '{dimensions}': 'Image dimensions (WIDTHxHEIGHT)',
        '{width}': 'Image width in pixels',
        '{height}': 'Image height in pixels',
        '{size}': 'File size (e.g., 1.2MB)',
        '{counter}': 'Auto-incrementing number',
        '{counter:03}': 'Zero-padded counter (3 digits)',
    }
    
    # Default templates for different use cases
    DEFAULT_TEMPLATES = {
        'simple': '{original_name}_{preset}',
        'dated': '{original_name}_{date}_{preset}',
        'timestamped': '{original_name}_{date}_{time}_{preset}',
        'dimensions': '{original_name}_{dimensions}_{preset}',
        'sequential': '{original_name}_{counter:03}_{preset}',
    }
    
    def __init__(self):
        self.counter = 0
        self.counter_start = 1
        
    def reset_counter(self, start: int = 1):
        """Reset the counter to a specific starting value."""
        self.counter = 0
        self.counter_start = start
        
    def parse_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Parse a filename template and substitute variables.
        
        Args:
            template: The template string with variables
            context: Dictionary containing variable values
            
        Returns:
            The parsed filename string
        """
        result = template
        
        # Get current datetime values
        now = datetime.now()
        date_values = {
            '{date}': now.strftime('%Y-%m-%d'),
            '{time}': now.strftime('%H-%M-%S'),
            '{year}': now.strftime('%Y'),
            '{month}': now.strftime('%m'),
            '{day}': now.strftime('%d'),
        }
        
        # Handle counter with different padding formats
        counter_pattern = r'\{counter(?::(\d+))?\}'
        counter_matches = re.findall(counter_pattern, result)
        
        for match in counter_matches:
            padding = int(match) if match else 0
            self.counter += 1
            counter_value = self.counter + self.counter_start - 1
            
            if padding > 0:
                replacement = str(counter_value).zfill(padding)
                result = result.replace(f'{{counter:{match}}}', replacement)
            else:
                result = result.replace('{counter}', str(counter_value))
        
        # Substitute date/time values
        for var, value in date_values.items():
            result = result.replace(var, value)
        
        # Substitute context values
        for var, value in context.items():
            result = result.replace(f'{{{var}}}', str(value))
        
        # Clean up any invalid filename characters
        result = self._sanitize_filename(result)
        
        return result
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove or replace invalid filename characters."""
        # Replace invalid characters with underscores
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        
        # Ensure filename is not empty
        if not filename:
            filename = 'unnamed'
        
        return filename
    
    def generate_filename(self, 
                         original_path: Path,
                         template: str,
                         preset_name: str,
                         image_info: Optional[Dict[str, Any]] = None,
                         output_format: str = None) -> str:
        """
        Generate a filename based on template and context.
        
        Args:
            original_path: Path to the original image file
            template: Filename template string
            preset_name: Name of the preset being used
            image_info: Optional dictionary with image information
            output_format: Output format (defaults to original extension)
            
        Returns:
            Generated filename with extension
        """
        # Build context dictionary
        context = {
            'original_name': original_path.stem,
            'original_ext': original_path.suffix.lstrip('.'),
            'preset': self._sanitize_filename(preset_name),
        }
        
        # Add image info if provided
        if image_info:
            if 'width' in image_info and 'height' in image_info:
                context['dimensions'] = f"{image_info['width']}x{image_info['height']}"
                context['width'] = image_info['width']
                context['height'] = image_info['height']
            
            if 'size_bytes' in image_info:
                size_mb = image_info['size_bytes'] / (1024 * 1024)
                if size_mb < 1:
                    size_kb = image_info['size_bytes'] / 1024
                    context['size'] = f"{size_kb:.0f}KB"
                else:
                    context['size'] = f"{size_mb:.1f}MB"
        
        # Parse the template
        filename = self.parse_template(template, context)
        
        # Add extension
        if output_format:
            extension = output_format.lower()
            if not extension.startswith('.'):
                extension = f'.{extension}'
        else:
            extension = original_path.suffix.lower()
        
        return f"{filename}{extension}"
    
    def check_duplicate(self, output_path: Path, strategy: str = 'rename') -> Path:
        """
        Check for duplicate files and handle according to strategy.
        
        Args:
            output_path: Proposed output path
            strategy: How to handle duplicates ('rename', 'overwrite', 'skip')
            
        Returns:
            Final output path (may be modified if strategy is 'rename')
        """
        if strategy == 'overwrite' or not output_path.exists():
            return output_path
        
        if strategy == 'skip':
            return output_path if not output_path.exists() else None
        
        if strategy == 'rename':
            # Find a unique filename by appending numbers
            base = output_path.stem
            extension = output_path.suffix
            directory = output_path.parent
            
            counter = 1
            while output_path.exists():
                new_name = f"{base}_{counter}{extension}"
                output_path = directory / new_name
                counter += 1
            
            return output_path
        
        return output_path


class FilenameTemplateWidget(QWidget):
    """Widget for configuring filename templates."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.template_engine = FilenameTemplate()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the widget UI."""
        from PySide6.QtWidgets import (
            QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
            QComboBox, QPushButton, QTextEdit, QGroupBox
        )
        
        layout = QVBoxLayout(self)
        
        # Template selection
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template:"))
        
        self.template_combo = QComboBox()
        self.template_combo.addItem("Simple", FilenameTemplate.DEFAULT_TEMPLATES['simple'])
        self.template_combo.addItem("With Date", FilenameTemplate.DEFAULT_TEMPLATES['dated'])
        self.template_combo.addItem("With Timestamp", FilenameTemplate.DEFAULT_TEMPLATES['timestamped'])
        self.template_combo.addItem("With Dimensions", FilenameTemplate.DEFAULT_TEMPLATES['dimensions'])
        self.template_combo.addItem("Sequential", FilenameTemplate.DEFAULT_TEMPLATES['sequential'])
        self.template_combo.addItem("Custom", "")
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        template_layout.addWidget(self.template_combo, 1)
        
        layout.addLayout(template_layout)
        
        # Custom template input
        self.custom_template = QLineEdit()
        self.custom_template.setPlaceholderText("Enter custom template...")
        self.custom_template.textChanged.connect(self.on_custom_template_changed)
        self.custom_template.setEnabled(False)
        layout.addWidget(self.custom_template)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("filename_preview.jpg")
        self.preview_label.setStyleSheet("font-family: monospace; padding: 5px;")
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Variables help
        help_group = QGroupBox("Available Variables")
        help_layout = QVBoxLayout()
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(150)
        
        help_content = []
        for var, desc in FilenameTemplate.VARIABLES.items():
            help_content.append(f"<b>{var}</b> - {desc}")
        
        help_text.setHtml("<br>".join(help_content))
        help_layout.addWidget(help_text)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        # Initialize with default template
        self.update_preview()
        
    def on_template_changed(self, index):
        """Handle template selection change."""
        if self.template_combo.currentText() == "Custom":
            self.custom_template.setEnabled(True)
            self.custom_template.setFocus()
        else:
            self.custom_template.setEnabled(False)
            self.custom_template.clear()
            self.update_preview()
            
    def on_custom_template_changed(self, text):
        """Handle custom template text change."""
        if self.template_combo.currentText() == "Custom":
            self.update_preview()
            
    def get_template(self) -> str:
        """Get the current template string."""
        if self.template_combo.currentText() == "Custom":
            return self.custom_template.text() or "{original_name}_{preset}"
        else:
            return self.template_combo.currentData()
            
    def update_preview(self):
        """Update the filename preview."""
        template = self.get_template()
        
        # Sample context for preview
        sample_context = {
            'original_name': 'example_image',
            'preset': 'editorial_web',
            'dimensions': '1920x1080',
            'width': '1920',
            'height': '1080',
            'size': '1.2MB'
        }
        
        try:
            preview = self.template_engine.parse_template(template, sample_context)
            self.preview_label.setText(f"{preview}.jpg")
            self.preview_label.setStyleSheet("font-family: monospace; padding: 5px; color: black;")
        except Exception as e:
            self.preview_label.setText(f"Error: {str(e)}")
            self.preview_label.setStyleSheet("font-family: monospace; padding: 5px; color: red;")