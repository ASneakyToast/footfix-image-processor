"""
Tag export functionality for FootFix.
Provides CSV, JSON, and IPTC export capabilities for tag data with metadata.
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
from ..core.tag_manager import TagStatus
from .alt_text_exporter import ExportFormat, ExportOptions  # Reuse existing enums

logger = logging.getLogger(__name__)


class TagExportFormat(Enum):
    """Supported tag export formats."""
    CSV = "csv"
    JSON = "json"
    IPTC = "txt"  # IPTC keyword list format


class TagExporter:
    """
    Handles exporting tag data in various formats.
    Supports CSV, JSON, and IPTC keyword lists with comprehensive metadata.
    """
    
    def __init__(self):
        """Initialize the tag exporter."""
        self.default_export_dir = Path.home() / "Downloads"
        
    def generate_filename(self, format: TagExportFormat) -> str:
        """
        Generate a timestamped filename for tag export.
        
        Args:
            format: Export format (CSV, JSON, or IPTC)
            
        Returns:
            Generated filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        extension = format.value
        return f"tags_export_{timestamp}.{extension}"
        
    def _gather_tag_metadata(self, batch_item: BatchItem) -> Dict[str, Any]:
        """
        Gather comprehensive tag metadata for a batch item.
        
        Args:
            batch_item: The batch item to extract tag metadata from
            
        Returns:
            Dictionary containing tag metadata
        """
        metadata = {
            "filename": batch_item.source_path.name,
            "tags": batch_item.tags.copy() if batch_item.tags else [],
            "tag_count": len(batch_item.tags) if batch_item.tags else 0,
            "tag_status": batch_item.tag_status.value if batch_item.tag_status else "none",
            "tag_error": batch_item.tag_error or "",
            "tag_application_time": getattr(batch_item, 'tag_application_time', 0),
            "tag_categories": batch_item.tag_categories.copy() if batch_item.tag_categories else {},
            "width": 0,
            "height": 0,
            "original_size": 0,
            "processed_size": 0,
            "file_format": "",
            "processing_status": batch_item.status.value if batch_item.status else "unknown",
            "processing_time": getattr(batch_item, 'processing_time', 0),
            "created_date": "",
            "export_date": datetime.now().isoformat()
        }
        
        # Get original file info
        if batch_item.source_path.exists():
            file_stat = batch_item.source_path.stat()
            metadata["original_size"] = file_stat.st_size
            metadata["file_format"] = batch_item.source_path.suffix.lstrip('.')
            metadata["created_date"] = datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            
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
    
    def export_csv(self, batch_items: List[BatchItem], output_path: Path, 
                   export_options: ExportOptions = ExportOptions.ALL) -> tuple[bool, str]:
        """
        Export tag data to CSV format.
        
        Args:
            batch_items: List of batch items to export
            output_path: Path to save the CSV file
            export_options: Filtering options for export
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Filter items based on export options
            filtered_items = self._filter_items(batch_items, export_options)
            
            if not filtered_items:
                return False, "No items match the export criteria"
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                # CSV headers
                fieldnames = [
                    'filename', 'tags', 'tag_count', 'tag_status', 'tag_error',
                    'tag_application_time', 'categories', 'width', 'height',
                    'original_size', 'processed_size', 'file_format',
                    'processing_status', 'processing_time', 'created_date', 'export_date'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in filtered_items:
                    metadata = self._gather_tag_metadata(item)
                    
                    # Format tags and categories for CSV
                    csv_row = {
                        'filename': metadata['filename'],
                        'tags': ', '.join(metadata['tags']),
                        'tag_count': metadata['tag_count'],
                        'tag_status': metadata['tag_status'],
                        'tag_error': metadata['tag_error'],
                        'tag_application_time': f"{metadata['tag_application_time']:.3f}s",
                        'categories': '; '.join([
                            f"{cat}: {', '.join(tags)}" 
                            for cat, tags in metadata['tag_categories'].items()
                        ]),
                        'width': metadata['width'],
                        'height': metadata['height'],
                        'original_size': metadata['original_size'],
                        'processed_size': metadata['processed_size'],
                        'file_format': metadata['file_format'],
                        'processing_status': metadata['processing_status'],
                        'processing_time': f"{metadata['processing_time']:.3f}s",
                        'created_date': metadata['created_date'],
                        'export_date': metadata['export_date']
                    }
                    
                    writer.writerow(csv_row)
            
            logger.info(f"Exported {len(filtered_items)} tag records to CSV: {output_path}")
            return True, f"Successfully exported {len(filtered_items)} items to CSV"
            
        except Exception as e:
            error_msg = f"CSV export failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def export_json(self, batch_items: List[BatchItem], output_path: Path,
                    export_options: ExportOptions = ExportOptions.ALL) -> tuple[bool, str]:
        """
        Export tag data to JSON format.
        
        Args:
            batch_items: List of batch items to export
            output_path: Path to save the JSON file
            export_options: Filtering options for export
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Filter items based on export options
            filtered_items = self._filter_items(batch_items, export_options)
            
            if not filtered_items:
                return False, "No items match the export criteria"
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build JSON structure
            export_data = {
                "export_info": {
                    "export_date": datetime.now().isoformat(),
                    "total_items": len(filtered_items),
                    "export_options": export_options.value,
                    "format_version": "1.0"
                },
                "items": []
            }
            
            for item in filtered_items:
                metadata = self._gather_tag_metadata(item)
                export_data["items"].append(metadata)
            
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(filtered_items)} tag records to JSON: {output_path}")
            return True, f"Successfully exported {len(filtered_items)} items to JSON"
            
        except Exception as e:
            error_msg = f"JSON export failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def export_iptc_keywords(self, batch_items: List[BatchItem], output_path: Path,
                            export_options: ExportOptions = ExportOptions.ALL) -> tuple[bool, str]:
        """
        Export tag data to IPTC keyword list format.
        This creates a simple text file with all unique tags for import into DAM systems.
        
        Args:
            batch_items: List of batch items to export
            output_path: Path to save the keyword list file
            export_options: Filtering options for export
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Filter items based on export options
            filtered_items = self._filter_items(batch_items, export_options)
            
            if not filtered_items:
                return False, "No items match the export criteria"
            
            # Collect all unique tags
            all_tags = set()
            for item in filtered_items:
                if item.tags:
                    all_tags.update(item.tags)
            
            if not all_tags:
                return False, "No tags found in selected items"
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Sort tags alphabetically
            sorted_tags = sorted(all_tags)
            
            with open(output_path, 'w', encoding='utf-8') as txtfile:
                txtfile.write(f"# IPTC Keyword List\\n")
                txtfile.write(f"# Exported from FootFix on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
                txtfile.write(f"# Total unique keywords: {len(sorted_tags)}\\n")
                txtfile.write(f"# Source images: {len(filtered_items)}\\n")
                txtfile.write("\\n")
                
                for tag in sorted_tags:
                    txtfile.write(f"{tag}\\n")
            
            logger.info(f"Exported {len(sorted_tags)} unique keywords to IPTC list: {output_path}")
            return True, f"Successfully exported {len(sorted_tags)} unique keywords to IPTC keyword list"
            
        except Exception as e:
            error_msg = f"IPTC keyword export failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _filter_items(self, batch_items: List[BatchItem], export_options: ExportOptions) -> List[BatchItem]:
        """
        Filter batch items based on export options.
        
        Args:
            batch_items: List of all batch items
            export_options: Filtering criteria
            
        Returns:
            Filtered list of batch items
        """
        if export_options == ExportOptions.ALL:
            return batch_items
        elif export_options == ExportOptions.COMPLETED_ONLY:
            return [
                item for item in batch_items 
                if item.tag_status == TagStatus.COMPLETED and item.tags
            ]
        elif export_options == ExportOptions.SELECTED:
            # This would require additional selection logic - for now, treat as ALL
            return batch_items
        else:
            return batch_items
    
    def get_export_summary(self, batch_items: List[BatchItem]) -> Dict[str, Any]:
        """
        Get a summary of tag data for export preview.
        
        Args:
            batch_items: List of batch items to analyze
            
        Returns:
            Dictionary containing export summary
        """
        total_items = len(batch_items)
        tagged_items = sum(1 for item in batch_items if item.tags)
        completed_items = sum(1 for item in batch_items if item.tag_status == TagStatus.COMPLETED)
        error_items = sum(1 for item in batch_items if item.tag_status == TagStatus.ERROR)
        
        # Collect all unique tags and categories
        all_tags = set()
        all_categories = set()
        
        for item in batch_items:
            if item.tags:
                all_tags.update(item.tags)
            if item.tag_categories:
                all_categories.update(item.tag_categories.keys())
        
        return {
            "total_items": total_items,
            "tagged_items": tagged_items,
            "completed_items": completed_items,
            "error_items": error_items,
            "unique_tags": len(all_tags),
            "unique_categories": len(all_categories),
            "tag_list": sorted(list(all_tags)),
            "category_list": sorted(list(all_categories))
        }