"""
Tag CSV export utilities for FootFix.
Handles exporting tag data to CSV format with various filtering options.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
from enum import Enum

from ..core.batch_processor import BatchItem
from ..core.tag_manager import TagStatus

logger = logging.getLogger(__name__)


class TagExportOptions(Enum):
    """Export filtering options for tag data."""
    ALL_ITEMS = "all"  # Export all items regardless of tag status
    TAGGED_ONLY = "tagged"  # Export only items with tags
    COMPLETED_ONLY = "completed"  # Export only items with completed tag status
    FAILED_ONLY = "failed"  # Export only items with failed tag status


class TagCsvExporter:
    """Utility for exporting tag data to CSV format."""
    
    def __init__(self):
        """Initialize the tag CSV exporter."""
        pass
    
    def generate_filename(self, prefix: str = "tags_export") -> str:
        """
        Generate a timestamped filename for tag export.
        
        Args:
            prefix: Prefix for the filename
            
        Returns:
            Generated filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.csv"
    
    def filter_items(self, items: List[BatchItem], options: TagExportOptions) -> List[BatchItem]:
        """
        Filter batch items based on export options.
        
        Args:
            items: List of batch items to filter
            options: Export filtering options
            
        Returns:
            Filtered list of batch items
        """
        if options == TagExportOptions.ALL_ITEMS:
            return items
        elif options == TagExportOptions.TAGGED_ONLY:
            return [item for item in items if item.tags]
        elif options == TagExportOptions.COMPLETED_ONLY:
            return [item for item in items if item.tag_status == TagStatus.COMPLETED and item.tags]
        elif options == TagExportOptions.FAILED_ONLY:
            return [item for item in items if item.tag_status == TagStatus.ERROR]
        else:
            logger.warning(f"Unknown export option: {options}, defaulting to all items")
            return items
    
    def export_csv(self, items: List[BatchItem], output_path: Path, 
                   options: TagExportOptions = TagExportOptions.TAGGED_ONLY,
                   include_metadata: bool = True) -> Tuple[bool, str]:
        """
        Export tag data to CSV file.
        
        Args:
            items: List of batch items to export
            output_path: Path to save the CSV file
            options: Export filtering options
            include_metadata: Whether to include timing and status metadata
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Filter items based on options
            filtered_items = self.filter_items(items, options)
            
            if not filtered_items:
                return False, "No items match the export criteria"
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write CSV file
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                if include_metadata:
                    header = ['Filename', 'Source Path', 'Tags', 'Tag Count', 'Status', 'Application Time (s)', 'Error Message']
                else:
                    header = ['Filename', 'Tags', 'Tag Count']
                
                writer.writerow(header)
                
                # Write data rows
                for item in filtered_items:
                    tags_str = ', '.join(item.tags) if item.tags else ''
                    
                    if include_metadata:
                        row = [
                            item.source_path.name,
                            str(item.source_path),
                            tags_str,
                            len(item.tags) if item.tags else 0,
                            item.tag_status.value,
                            f"{item.tag_application_time:.2f}",
                            item.tag_error or ''
                        ]
                    else:
                        row = [
                            item.source_path.name,
                            tags_str,
                            len(item.tags) if item.tags else 0
                        ]
                    
                    writer.writerow(row)
            
            logger.info(f"Successfully exported {len(filtered_items)} tag records to {output_path}")
            return True, f"Exported {len(filtered_items)} records successfully"
            
        except Exception as e:
            error_msg = f"Failed to export tag data: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def export_summary(self, items: List[BatchItem], output_path: Path) -> Tuple[bool, str]:
        """
        Export a summary of tag statistics to CSV.
        
        Args:
            items: List of batch items to analyze
            output_path: Path to save the summary CSV
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Calculate statistics
            total_items = len(items)
            tagged_items = [item for item in items if item.tags]
            completed_items = [item for item in items if item.tag_status == TagStatus.COMPLETED]
            failed_items = [item for item in items if item.tag_status == TagStatus.ERROR]
            
            # Count unique tags
            all_tags = []
            for item in tagged_items:
                all_tags.extend(item.tags)
            
            unique_tags = list(set(all_tags))
            tag_counts = {tag: all_tags.count(tag) for tag in unique_tags}
            
            # Calculate average application time
            application_times = [item.tag_application_time for item in completed_items if item.tag_application_time > 0]
            avg_application_time = sum(application_times) / len(application_times) if application_times else 0
            
            # Write summary CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write summary statistics
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Total Items', total_items])
                writer.writerow(['Tagged Items', len(tagged_items)])
                writer.writerow(['Completed Items', len(completed_items)])
                writer.writerow(['Failed Items', len(failed_items)])
                writer.writerow(['Unique Tags', len(unique_tags)])
                writer.writerow(['Average Application Time (s)', f"{avg_application_time:.2f}"])
                writer.writerow([])  # Empty row
                
                # Write tag frequency table
                writer.writerow(['Tag', 'Frequency'])
                for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
                    writer.writerow([tag, count])
            
            logger.info(f"Successfully exported tag summary to {output_path}")
            return True, f"Summary exported successfully"
            
        except Exception as e:
            error_msg = f"Failed to export tag summary: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_default_export_path(self, filename: Optional[str] = None) -> Path:
        """
        Get default export path for tag data.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Default export path
        """
        if filename is None:
            filename = self.generate_filename()
        
        return Path.home() / "Downloads" / filename