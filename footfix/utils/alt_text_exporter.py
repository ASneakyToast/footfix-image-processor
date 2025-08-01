"""
Alt text export functionality for FootFix.
Provides CSV and JSON export capabilities for alt text data with metadata.
"""

import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from PIL import Image

from ..core.batch_processor import BatchItem, ProcessingStatus
from ..core.alt_text_generator import AltTextStatus

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"


class ExportOptions(Enum):
    """Export filtering options."""
    ALL = "all"
    SELECTED = "selected"
    COMPLETED_ONLY = "completed_only"


class AltTextExporter:
    """
    Handles exporting alt text data in various formats.
    Supports CSV and JSON with comprehensive metadata.
    """
    
    def __init__(self):
        """Initialize the exporter."""
        self.default_export_dir = Path.home() / "Downloads"
        
    def generate_filename(self, format: ExportFormat) -> str:
        """
        Generate a timestamped filename for export.
        
        Args:
            format: Export format (CSV or JSON)
            
        Returns:
            Generated filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        extension = format.value
        return f"alttext_export_{timestamp}.{extension}"
        
    def _gather_metadata(self, batch_item: BatchItem) -> Dict[str, Any]:
        """
        Gather comprehensive metadata for a batch item.
        
        Args:
            batch_item: The batch item to extract metadata from
            
        Returns:
            Dictionary containing metadata
        """
        metadata = {
            "filename": batch_item.source_path.name,
            "alt_text": batch_item.alt_text or "",
            "status": batch_item.alt_text_status.value if batch_item.alt_text_status else "none",
            "width": 0,
            "height": 0,
            "original_size": 0,
            "processed_size": 0,
            "file_format": "",
            "processing_time": getattr(batch_item, 'processing_time', 0),
            "api_cost": getattr(batch_item, 'api_cost', 0.0)
        }
        
        # Get original file info
        if batch_item.source_path.exists():
            metadata["original_size"] = batch_item.source_path.stat().st_size
            metadata["file_format"] = batch_item.source_path.suffix.lstrip('.')
            
            try:
                with Image.open(batch_item.source_path) as img:
                    metadata["width"], metadata["height"] = img.size
            except Exception as e:
                logger.warning(f"Failed to read image dimensions for {batch_item.source_path}: {e}")
                
        # Get processed file info if available
        if batch_item.output_path and batch_item.output_path.exists():
            metadata["processed_size"] = batch_item.output_path.stat().st_size
            metadata["processed_filename"] = batch_item.output_path.name
        else:
            metadata["processed_filename"] = ""
            
        return metadata
        
    def export_csv(
        self,
        batch_items: List[BatchItem],
        output_path: Path,
        options: ExportOptions = ExportOptions.ALL,
        selected_items: Optional[List[str]] = None
    ) -> tuple[bool, str]:
        """
        Export alt text data to CSV format.
        
        Args:
            batch_items: List of batch items to export
            output_path: Path for the output CSV file
            options: Export filtering options
            selected_items: List of selected filenames (for SELECTED option)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Filter items based on options
            items_to_export = self._filter_items(batch_items, options, selected_items)
            
            if not items_to_export:
                return False, "No items to export based on selected criteria"
                
            # CSV columns
            fieldnames = [
                'filename',
                'alt_text',
                'status',
                'width',
                'height',
                'original_size',
                'processed_size',
                'processed_filename',
                'file_format',
                'processing_time',
                'api_cost'
            ]
            
            # Write CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in items_to_export:
                    metadata = self._gather_metadata(item)
                    writer.writerow(metadata)
                    
            logger.info(f"Exported {len(items_to_export)} items to CSV: {output_path}")
            return True, f"Successfully exported {len(items_to_export)} items to {output_path.name}"
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False, f"Export failed: {str(e)}"
            
    def export_json(
        self,
        batch_items: List[BatchItem],
        output_path: Path,
        options: ExportOptions = ExportOptions.ALL,
        selected_items: Optional[List[str]] = None,
        pretty_print: bool = True
    ) -> tuple[bool, str]:
        """
        Export alt text data to JSON format.
        
        Args:
            batch_items: List of batch items to export
            output_path: Path for the output JSON file
            options: Export filtering options
            selected_items: List of selected filenames (for SELECTED option)
            pretty_print: Whether to format JSON for readability
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Filter items based on options
            items_to_export = self._filter_items(batch_items, options, selected_items)
            
            if not items_to_export:
                return False, "No items to export based on selected criteria"
                
            # Build JSON structure
            export_data = {
                "export_date": datetime.now().isoformat(),
                "export_version": "1.0",
                "total_items": len(items_to_export),
                "items": []
            }
            
            # Calculate totals
            total_cost = 0.0
            completed_count = 0
            
            for item in items_to_export:
                metadata = self._gather_metadata(item)
                export_data["items"].append(metadata)
                
                total_cost += metadata.get("api_cost", 0.0)
                if item.alt_text_status == AltTextStatus.COMPLETED:
                    completed_count += 1
                    
            # Add summary
            export_data["summary"] = {
                "completed_items": completed_count,
                "total_api_cost": round(total_cost, 4),
                "average_cost_per_item": round(total_cost / len(items_to_export), 4) if items_to_export else 0
            }
            
            # Write JSON
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                if pretty_print:
                    json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
                else:
                    json.dump(export_data, jsonfile, ensure_ascii=False)
                    
            logger.info(f"Exported {len(items_to_export)} items to JSON: {output_path}")
            return True, f"Successfully exported {len(items_to_export)} items to {output_path.name}"
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            return False, f"Export failed: {str(e)}"
            
    def _filter_items(
        self,
        batch_items: List[BatchItem],
        options: ExportOptions,
        selected_items: Optional[List[str]] = None
    ) -> List[BatchItem]:
        """
        Filter batch items based on export options.
        
        Args:
            batch_items: List of all batch items
            options: Export filtering options
            selected_items: List of selected filenames (for SELECTED option)
            
        Returns:
            Filtered list of batch items
        """
        filtered_items = []
        
        for item in batch_items:
            # Skip if not processed
            if item.status != ProcessingStatus.COMPLETED:
                continue
                
            # Apply filtering based on options
            if options == ExportOptions.ALL:
                filtered_items.append(item)
            elif options == ExportOptions.SELECTED:
                if selected_items and item.source_path.name in selected_items:
                    filtered_items.append(item)
            elif options == ExportOptions.COMPLETED_ONLY:
                if item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text:
                    filtered_items.append(item)
                    
        return filtered_items
        
    def export_for_cms(
        self,
        batch_items: List[BatchItem],
        output_path: Path,
        cms_type: str = "wordpress"
    ) -> tuple[bool, str]:
        """
        Export alt text data in a format optimized for CMS import.
        
        Args:
            batch_items: List of batch items to export
            output_path: Path for the output file
            cms_type: Type of CMS (wordpress, drupal, etc.)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Filter for completed items only
            items_to_export = self._filter_items(
                batch_items, 
                ExportOptions.COMPLETED_ONLY
            )
            
            if not items_to_export:
                return False, "No completed items with alt text to export"
                
            if cms_type.lower() == "wordpress":
                # WordPress-optimized CSV format
                with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['filename', 'title', 'alt_text', 'caption', 'description'])
                    
                    for item in items_to_export:
                        # Use filename without extension as title
                        title = item.source_path.stem.replace('_', ' ').title()
                        writer.writerow([
                            item.source_path.name,
                            title,
                            item.alt_text or "",
                            "",  # Empty caption
                            item.alt_text or ""  # Use alt text as description too
                        ])
                        
            else:
                # Generic JSON format for other CMS
                export_data = {
                    "images": []
                }
                
                for item in items_to_export:
                    export_data["images"].append({
                        "filename": item.source_path.name,
                        "alt_text": item.alt_text or "",
                        "metadata": {
                            "width": 0,
                            "height": 0,
                            "format": item.source_path.suffix.lstrip('.')
                        }
                    })
                    
                with open(output_path, 'w', encoding='utf-8') as jsonfile:
                    json.dump(export_data, jsonfile, indent=2)
                    
            logger.info(f"Exported {len(items_to_export)} items for {cms_type} CMS")
            return True, f"Successfully exported {len(items_to_export)} items for {cms_type}"
            
        except Exception as e:
            logger.error(f"Failed to export for CMS: {e}")
            return False, f"Export failed: {str(e)}"
            
    def validate_export_path(self, path: Path) -> tuple[bool, str]:
        """
        Validate the export path and ensure directory exists.
        
        Args:
            path: Path to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if we can write to the location
            if path.exists() and not path.is_file():
                return False, "Path exists but is not a file"
                
            # Try to create/write a test file
            test_path = path.parent / f".test_{path.name}"
            try:
                test_path.touch()
                test_path.unlink()
                return True, "Path is valid"
            except:
                return False, "Cannot write to the specified location"
                
        except Exception as e:
            return False, f"Invalid path: {str(e)}"