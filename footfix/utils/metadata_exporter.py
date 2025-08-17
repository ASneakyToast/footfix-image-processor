"""
Unified metadata export functionality for FootFix.
Provides comprehensive export capabilities for both alt text and tags in CMS-friendly formats.
"""

import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from ..core.batch_processor import BatchItem, ProcessingStatus
from ..core.alt_text_generator import AltTextStatus
from ..core.tag_manager import TagStatus

logger = logging.getLogger(__name__)


class MetadataExportFormat(Enum):
    """Supported metadata export formats."""
    CSV = "csv"
    JSON = "json"
    TSV = "tsv"
    WORDPRESS_CSV = "wordpress_csv"
    IPTC_KEYWORDS = "iptc"
    CLIPBOARD_TEXT = "clipboard"


class MetadataExportOptions(Enum):
    """Export filtering options."""
    ALL = "all"
    SELECTED = "selected"
    COMPLETED_ONLY = "completed_only"
    ALT_TEXT_ONLY = "alt_text_only"
    TAGS_ONLY = "tags_only"


class MetadataExporter:
    """
    Unified exporter for image metadata including alt text and tags.
    Supports multiple formats optimized for different CMS platforms and workflows.
    """
    
    def __init__(self):
        """Initialize the metadata exporter."""
        self.default_export_dir = Path.home() / "Downloads"
        
    def generate_filename(self, format: MetadataExportFormat, prefix: str = "metadata_export") -> str:
        """
        Generate a timestamped filename for metadata export.
        
        Args:
            format: Export format
            prefix: Filename prefix
            
        Returns:
            Generated filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        extension_map = {
            MetadataExportFormat.CSV: "csv",
            MetadataExportFormat.JSON: "json",
            MetadataExportFormat.TSV: "txt",
            MetadataExportFormat.WORDPRESS_CSV: "csv",
            MetadataExportFormat.IPTC_KEYWORDS: "txt",
            MetadataExportFormat.CLIPBOARD_TEXT: "txt"
        }
        
        extension = extension_map.get(format, "txt")
        return f"{prefix}_{timestamp}.{extension}"
        
    def export_metadata(
        self,
        batch_items: List[BatchItem],
        output_path: Path,
        format: MetadataExportFormat,
        options: MetadataExportOptions = MetadataExportOptions.ALL,
        selected_items: Optional[List[str]] = None,
        include_alt_text: bool = True,
        include_tags: bool = True
    ) -> Tuple[bool, str]:
        """
        Export metadata in the specified format.
        
        Args:
            batch_items: List of batch items to export
            output_path: Path for the output file
            format: Export format
            options: Export filtering options
            selected_items: List of selected filenames (for SELECTED option)
            include_alt_text: Whether to include alt text in export
            include_tags: Whether to include tags in export
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Filter items based on options
            items_to_export = self._filter_items(
                batch_items, options, selected_items, include_alt_text, include_tags
            )
            
            if not items_to_export:
                return False, "No items to export based on selected criteria"
                
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export based on format
            if format == MetadataExportFormat.CSV:
                return self._export_csv(items_to_export, output_path, include_alt_text, include_tags)
            elif format == MetadataExportFormat.JSON:
                return self._export_json(items_to_export, output_path, include_alt_text, include_tags)
            elif format == MetadataExportFormat.TSV:
                return self._export_tsv(items_to_export, output_path, include_alt_text, include_tags)
            elif format == MetadataExportFormat.WORDPRESS_CSV:
                return self._export_wordpress_csv(items_to_export, output_path)
            elif format == MetadataExportFormat.IPTC_KEYWORDS:
                return self._export_iptc_keywords(items_to_export, output_path)
            elif format == MetadataExportFormat.CLIPBOARD_TEXT:
                return self._export_clipboard_text(items_to_export, include_alt_text, include_tags)
            else:
                return False, f"Unsupported export format: {format}"
                
        except Exception as e:
            logger.error(f"Failed to export metadata: {e}")
            return False, f"Export failed: {str(e)}"
            
    def _filter_items(
        self,
        batch_items: List[BatchItem],
        options: MetadataExportOptions,
        selected_items: Optional[List[str]] = None,
        include_alt_text: bool = True,
        include_tags: bool = True
    ) -> List[BatchItem]:
        """Filter batch items based on export options."""
        filtered_items = []
        
        for item in batch_items:
            # Apply selection filter
            if options == MetadataExportOptions.SELECTED:
                if not selected_items or item.source_path.name not in selected_items:
                    continue
                    
            # Apply completion filter
            if options == MetadataExportOptions.COMPLETED_ONLY:
                has_completed_alt = (
                    include_alt_text and 
                    item.alt_text_status == AltTextStatus.COMPLETED and 
                    item.alt_text
                )
                has_completed_tags = (
                    include_tags and 
                    item.tag_status == TagStatus.COMPLETED and 
                    item.tags
                )
                
                if not (has_completed_alt or has_completed_tags):
                    continue
                    
            # Apply content type filters
            if options == MetadataExportOptions.ALT_TEXT_ONLY:
                if not (item.alt_text and item.alt_text_status == AltTextStatus.COMPLETED):
                    continue
                    
            if options == MetadataExportOptions.TAGS_ONLY:
                if not (item.tags and item.tag_status == TagStatus.COMPLETED):
                    continue
                    
            filtered_items.append(item)
            
        return filtered_items
        
    def _export_csv(
        self,
        items: List[BatchItem],
        output_path: Path,
        include_alt_text: bool,
        include_tags: bool
    ) -> Tuple[bool, str]:
        """Export to standard CSV format."""
        fieldnames = ["filename"]
        
        if include_alt_text:
            fieldnames.extend(["alt_text", "alt_text_status"])
            
        if include_tags:
            fieldnames.extend(["tags", "tag_count", "tag_status"])
            
        fieldnames.extend(["file_size_mb", "dimensions", "export_date"])
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in items:
                row = {"filename": item.source_path.name}
                
                if include_alt_text:
                    row["alt_text"] = item.alt_text or ""
                    row["alt_text_status"] = item.alt_text_status.value if item.alt_text_status else "none"
                    
                if include_tags:
                    tags_text = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
                    row["tags"] = tags_text
                    row["tag_count"] = len(item.tags) if item.tags else 0
                    row["tag_status"] = item.tag_status.value if item.tag_status else "none"
                    
                # Add file metadata
                try:
                    file_size_mb = item.source_path.stat().st_size / (1024 * 1024) if item.source_path.exists() else 0
                    row["file_size_mb"] = f"{file_size_mb:.2f}"
                except:
                    row["file_size_mb"] = "0.00"
                    
                row["dimensions"] = f"{getattr(item, 'width', 'unknown')}x{getattr(item, 'height', 'unknown')}"
                row["export_date"] = datetime.now().isoformat()
                
                writer.writerow(row)
                
        logger.info(f"Exported {len(items)} items to CSV: {output_path}")
        return True, f"Successfully exported {len(items)} items to CSV"
        
    def _export_json(
        self,
        items: List[BatchItem],
        output_path: Path,
        include_alt_text: bool,
        include_tags: bool
    ) -> Tuple[bool, str]:
        """Export to JSON format."""
        export_data = {
            "export_info": {
                "export_date": datetime.now().isoformat(),
                "total_items": len(items),
                "format_version": "1.0",
                "source": "FootFix Metadata Export",
                "includes_alt_text": include_alt_text,
                "includes_tags": include_tags
            },
            "items": []
        }
        
        # Calculate summary statistics
        summary = {
            "total_items": len(items),
            "items_with_alt_text": 0,
            "items_with_tags": 0,
            "unique_tags": set()
        }
        
        for item in items:
            item_data = {
                "filename": item.source_path.name,
                "file_path": str(item.source_path)
            }
            
            if include_alt_text:
                item_data["alt_text"] = {
                    "text": item.alt_text or "",
                    "status": item.alt_text_status.value if item.alt_text_status else "none"
                }
                if item.alt_text:
                    summary["items_with_alt_text"] += 1
                    
            if include_tags:
                tags_list = list(item.tags) if item.tags else []
                item_data["tags"] = {
                    "tags": tags_list,
                    "count": len(tags_list),
                    "status": item.tag_status.value if item.tag_status else "none"
                }
                if item.tags:
                    summary["items_with_tags"] += 1
                    summary["unique_tags"].update(str(tag) for tag in item.tags if tag)
                    
            # Add file metadata
            try:
                if item.source_path.exists():
                    stat = item.source_path.stat()
                    item_data["file_info"] = {
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    }
            except:
                item_data["file_info"] = {"size_bytes": 0, "size_mb": 0.0}
                
            export_data["items"].append(item_data)
            
        # Add summary
        summary["unique_tags"] = len(summary["unique_tags"])
        export_data["summary"] = summary
        
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
            
        logger.info(f"Exported {len(items)} items to JSON: {output_path}")
        return True, f"Successfully exported {len(items)} items to JSON"
        
    def _export_tsv(
        self,
        items: List[BatchItem],
        output_path: Path,
        include_alt_text: bool,
        include_tags: bool
    ) -> Tuple[bool, str]:
        """Export to tab-separated values format."""
        headers = ["Filename"]
        
        if include_alt_text:
            headers.append("Alt Text")
            
        if include_tags:
            headers.append("Tags")
            
        with open(output_path, 'w', encoding='utf-8') as tsvfile:
            # Write header
            tsvfile.write("\t".join(headers) + "\n")
            
            # Write data
            for item in items:
                row = [item.source_path.name]
                
                if include_alt_text:
                    row.append(item.alt_text or "")
                    
                if include_tags:
                    tags_text = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
                    row.append(tags_text)
                    
                tsvfile.write("\t".join(row) + "\n")
                
        logger.info(f"Exported {len(items)} items to TSV: {output_path}")
        return True, f"Successfully exported {len(items)} items to TSV"
        
    def _export_wordpress_csv(self, items: List[BatchItem], output_path: Path) -> Tuple[bool, str]:
        """Export in WordPress Media Library import format."""
        fieldnames = ["filename", "title", "alt_text", "caption", "description", "tags"]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in items:
                # Generate title from filename
                title = item.source_path.stem.replace('_', ' ').replace('-', ' ').title()
                
                # Prepare tags
                tags_text = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
                
                # Use alt text for both alt_text and description
                alt_text = item.alt_text or ""
                
                writer.writerow({
                    "filename": item.source_path.name,
                    "title": title,
                    "alt_text": alt_text,
                    "caption": "",  # Leave empty for manual entry
                    "description": alt_text,
                    "tags": tags_text
                })
                
        logger.info(f"Exported {len(items)} items to WordPress CSV: {output_path}")
        return True, f"Successfully exported {len(items)} items for WordPress"
        
    def _export_iptc_keywords(self, items: List[BatchItem], output_path: Path) -> Tuple[bool, str]:
        """Export IPTC keywords list."""
        all_tags = set()
        items_with_tags = 0
        
        for item in items:
            if item.tags:
                all_tags.update(str(tag) for tag in item.tags if tag)
                items_with_tags += 1
                
        if not all_tags:
            return False, "No tags found in selected items"
            
        sorted_tags = sorted(all_tags)
        
        with open(output_path, 'w', encoding='utf-8') as txtfile:
            txtfile.write(f"# IPTC Keywords Export\n")
            txtfile.write(f"# Generated from FootFix on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            txtfile.write(f"# Total unique keywords: {len(sorted_tags)}\n")
            txtfile.write(f"# Source images with tags: {items_with_tags} of {len(items)}\n")
            txtfile.write("\n")
            
            for tag in sorted_tags:
                txtfile.write(f"{tag}\n")
                
        logger.info(f"Exported {len(sorted_tags)} unique keywords to IPTC list: {output_path}")
        return True, f"Successfully exported {len(sorted_tags)} unique keywords"
        
    def _export_clipboard_text(
        self,
        items: List[BatchItem],
        include_alt_text: bool,
        include_tags: bool
    ) -> Tuple[bool, str]:
        """Generate clipboard-friendly text format."""
        lines = []
        
        # Header
        headers = ["Filename"]
        if include_alt_text:
            headers.append("Alt Text")
        if include_tags:
            headers.append("Tags")
            
        lines.append("\t".join(headers))
        
        # Data
        for item in items:
            row = [item.source_path.name]
            
            if include_alt_text:
                row.append(item.alt_text or "")
                
            if include_tags:
                tags_text = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
                row.append(tags_text)
                
            lines.append("\t".join(row))
            
        clipboard_text = "\n".join(lines)
        
        # For clipboard export, we'd typically copy to clipboard here
        # But we'll return the text for the caller to handle
        return True, clipboard_text
        
    def get_export_summary(self, batch_items: List[BatchItem]) -> Dict[str, Any]:
        """
        Get a summary of available metadata for export preview.
        
        Args:
            batch_items: List of batch items to analyze
            
        Returns:
            Dictionary containing export summary
        """
        total_items = len(batch_items)
        
        alt_text_stats = {
            "completed": sum(1 for item in batch_items 
                           if item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text),
            "pending": sum(1 for item in batch_items 
                          if item.alt_text_status == AltTextStatus.PENDING),
            "error": sum(1 for item in batch_items 
                        if item.alt_text_status == AltTextStatus.ERROR)
        }
        
        tag_stats = {
            "completed": sum(1 for item in batch_items 
                           if item.tag_status == TagStatus.COMPLETED and item.tags),
            "pending": sum(1 for item in batch_items 
                          if item.tag_status == TagStatus.PENDING),
            "error": sum(1 for item in batch_items 
                        if item.tag_status == TagStatus.ERROR)
        }
        
        # Collect all unique tags
        all_tags = set()
        for item in batch_items:
            if item.tags:
                all_tags.update(str(tag) for tag in item.tags if tag)
                
        return {
            "total_items": total_items,
            "alt_text_stats": alt_text_stats,
            "tag_stats": tag_stats,
            "unique_tags_count": len(all_tags),
            "unique_tags": sorted(list(all_tags)),
            "items_with_both": sum(1 for item in batch_items 
                                 if (item.alt_text and item.alt_text_status == AltTextStatus.COMPLETED and
                                     item.tags and item.tag_status == TagStatus.COMPLETED)),
            "items_ready_for_export": sum(1 for item in batch_items 
                                        if ((item.alt_text and item.alt_text_status == AltTextStatus.COMPLETED) or
                                            (item.tags and item.tag_status == TagStatus.COMPLETED)))
        }
        
    def validate_export_path(self, path: Path) -> Tuple[bool, str]:
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