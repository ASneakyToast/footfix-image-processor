"""
Metadata export widget for FootFix.
Provides a unified interface for reviewing and exporting both alt text and tags for CMS integration.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QGroupBox, QComboBox, QCheckBox, QMessageBox,
    QAbstractItemView, QMenu, QFileDialog, QApplication,
    QSplitter, QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QAction, QFont, QClipboard

from ..core.batch_processor import BatchItem, ProcessingStatus
from ..core.alt_text_generator import AltTextStatus
from ..core.tag_manager import TagStatus
from ..utils.preferences import PreferencesManager
from ..utils.notifications import NotificationManager

logger = logging.getLogger(__name__)


class MetadataExportWidget(QWidget):
    """Widget for unified metadata export focusing on CMS integration."""
    
    # Signals
    export_requested = Signal(str, dict)  # format, options
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.batch_items: List[BatchItem] = []
        self.prefs_manager = PreferencesManager.get_instance()
        self.notification_manager = NotificationManager()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        self.setup_header(layout)
        
        # Main content area
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Metadata table
        self.setup_metadata_table(splitter)
        
        # Right side - Export options and preview
        self.setup_export_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([700, 300])
        
        # Status bar
        self.status_label = QLabel("No images loaded")
        layout.addWidget(self.status_label)
        
    def setup_header(self, layout):
        """Set up the header section."""
        header_group = QGroupBox("Metadata Export for CMS")
        header_layout = QVBoxLayout(header_group)
        
        # Title and description
        title_label = QLabel("Review and Export Image Metadata")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        description_label = QLabel(
            "Review alt text and tags for your images, then export in CMS-friendly formats. "
            "Click individual copy buttons or select multiple items for bulk export."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        header_layout.addWidget(description_label)
        
        # Quick action buttons
        action_layout = QHBoxLayout()
        
        self.copy_all_btn = QPushButton("Copy All to Clipboard")
        self.copy_all_btn.setToolTip("Copy all metadata in a tab-separated format for easy pasting")
        self.copy_all_btn.clicked.connect(self.copy_all_metadata)
        self.copy_all_btn.setEnabled(False)
        action_layout.addWidget(self.copy_all_btn)
        
        self.copy_selected_btn = QPushButton("Copy Selected")
        self.copy_selected_btn.setToolTip("Copy selected rows to clipboard")
        self.copy_selected_btn.clicked.connect(self.copy_selected_metadata)
        self.copy_selected_btn.setEnabled(False)
        action_layout.addWidget(self.copy_selected_btn)
        
        action_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.setToolTip("Refresh metadata from current batch")
        self.refresh_btn.clicked.connect(self.refresh_display)
        action_layout.addWidget(self.refresh_btn)
        
        header_layout.addLayout(action_layout)
        layout.addWidget(header_group)
        
    def setup_metadata_table(self, parent):
        """Set up the main metadata table."""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        # Table
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(6)
        self.metadata_table.setHorizontalHeaderLabels([
            "Select", "Filename", "Alt Text", "Tags", "Status", "Actions"
        ])
        
        # Configure table
        header = self.metadata_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Filename
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Alt Text
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Tags
        header.setSectionResizeMode(4, QHeaderView.Interactive)  # Status
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # Actions
        
        self.metadata_table.setColumnWidth(0, 60)  # Select checkbox
        self.metadata_table.setColumnWidth(1, 200)  # Filename
        self.metadata_table.setColumnWidth(4, 120)  # Status
        self.metadata_table.setColumnWidth(5, 200)  # Actions
        
        self.metadata_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.metadata_table.setAlternatingRowColors(True)
        self.metadata_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        table_layout.addWidget(self.metadata_table)
        parent.addWidget(table_widget)
        
    def setup_export_panel(self, parent):
        """Set up the export options panel."""
        export_widget = QWidget()
        export_layout = QVBoxLayout(export_widget)
        
        # Export format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItem("CSV for Spreadsheets", "csv")
        self.format_combo.addItem("WordPress Media Import", "wordpress_csv")
        self.format_combo.addItem("JSON for APIs", "json")
        self.format_combo.addItem("Tab-separated (Clipboard)", "tsv")
        self.format_combo.addItem("IPTC Keywords Only", "iptc")
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        
        export_layout.addWidget(format_group)
        
        # Filter options
        filter_group = QGroupBox("Filter Options")
        filter_layout = QVBoxLayout(filter_group)
        
        self.include_alt_text_cb = QCheckBox("Include Alt Text")
        self.include_alt_text_cb.setChecked(True)
        filter_layout.addWidget(self.include_alt_text_cb)
        
        self.include_tags_cb = QCheckBox("Include Tags")
        self.include_tags_cb.setChecked(True)
        filter_layout.addWidget(self.include_tags_cb)
        
        self.completed_only_cb = QCheckBox("Completed Items Only")
        self.completed_only_cb.setChecked(True)
        self.completed_only_cb.setToolTip("Only include items with successfully generated metadata")
        filter_layout.addWidget(self.completed_only_cb)
        
        export_layout.addWidget(filter_group)
        
        # Preview area
        preview_group = QGroupBox("Export Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setPlainText("Select a format to see preview...")
        preview_layout.addWidget(self.preview_text)
        
        export_layout.addWidget(preview_group)
        
        # Export buttons
        button_layout = QVBoxLayout()
        
        self.export_file_btn = QPushButton("Export to File")
        self.export_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.export_file_btn.clicked.connect(self.export_to_file)
        self.export_file_btn.setEnabled(False)
        button_layout.addWidget(self.export_file_btn)
        
        self.copy_preview_btn = QPushButton("Copy Preview to Clipboard")
        self.copy_preview_btn.clicked.connect(self.copy_preview_to_clipboard)
        self.copy_preview_btn.setEnabled(False)
        button_layout.addWidget(self.copy_preview_btn)
        
        export_layout.addLayout(button_layout)
        export_layout.addStretch()
        
        parent.addWidget(export_widget)
        
    def set_batch_items(self, items: List[BatchItem]):
        """Set the batch items to display."""
        self.batch_items = items
        self.refresh_display()
        
    def refresh_display(self):
        """Refresh the display with current batch items."""
        # Clear table
        self.metadata_table.setRowCount(0)
        
        if not self.batch_items:
            self.status_label.setText("No images loaded")
            self.copy_all_btn.setEnabled(False)
            self.export_file_btn.setEnabled(False)
            self.update_preview()
            return
            
        # Filter items based on current filter settings
        items_to_show = self.get_filtered_items()
        
        # Populate table
        self.metadata_table.setRowCount(len(items_to_show))
        
        for row, item in enumerate(items_to_show):
            self.populate_table_row(row, item)
        
        # Update status
        total_items = len(self.batch_items)
        shown_items = len(items_to_show)
        alt_text_count = sum(1 for item in items_to_show if item.alt_text)
        tag_count = sum(1 for item in items_to_show if item.tags)
        
        self.status_label.setText(
            f"Showing {shown_items} of {total_items} images | "
            f"Alt Text: {alt_text_count} | Tags: {tag_count}"
        )
        
        # Enable buttons
        self.copy_all_btn.setEnabled(len(items_to_show) > 0)
        self.export_file_btn.setEnabled(len(items_to_show) > 0)
        self.copy_preview_btn.setEnabled(len(items_to_show) > 0)
        
        # Update preview
        self.update_preview()
        
    def populate_table_row(self, row: int, item: BatchItem):
        """Populate a single table row with item data."""
        # Checkbox
        checkbox = QCheckBox()
        self.metadata_table.setCellWidget(row, 0, checkbox)
        checkbox.stateChanged.connect(self.on_selection_changed)
        
        # Filename
        filename_item = QTableWidgetItem(item.source_path.name)
        filename_item.setToolTip(str(item.source_path))
        self.metadata_table.setItem(row, 1, filename_item)
        
        # Alt Text
        alt_text = item.alt_text or "No alt text"
        alt_text_item = QTableWidgetItem(alt_text)
        alt_text_item.setToolTip(alt_text)
        
        # Color code based on status
        if item.alt_text and item.alt_text_status == AltTextStatus.COMPLETED:
            alt_text_item.setBackground(QColor("#d4edda"))
        elif item.alt_text_status == AltTextStatus.ERROR:
            alt_text_item.setBackground(QColor("#f8d7da"))
        
        self.metadata_table.setItem(row, 2, alt_text_item)
        
        # Tags
        if item.tags:
            tags_text = ", ".join(str(tag) for tag in item.tags if tag)
            tags_item = QTableWidgetItem(tags_text)
            tags_item.setToolTip(tags_text)
            
            if item.tag_status == TagStatus.COMPLETED:
                tags_item.setBackground(QColor("#d4edda"))
            elif item.tag_status == TagStatus.ERROR:
                tags_item.setBackground(QColor("#f8d7da"))
        else:
            tags_item = QTableWidgetItem("No tags")
            
        self.metadata_table.setItem(row, 3, tags_item)
        
        # Status
        status_parts = []
        if item.alt_text_status == AltTextStatus.COMPLETED:
            status_parts.append("Alt✓")
        elif item.alt_text_status == AltTextStatus.ERROR:
            status_parts.append("Alt✗")
            
        if item.tag_status == TagStatus.COMPLETED:
            status_parts.append("Tags✓")
        elif item.tag_status == TagStatus.ERROR:
            status_parts.append("Tags✗")
            
        status_text = " | ".join(status_parts) if status_parts else "Pending"
        status_item = QTableWidgetItem(status_text)
        self.metadata_table.setItem(row, 4, status_item)
        
        # Actions - Copy buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 5, 5, 5)
        
        # Copy alt text button
        copy_alt_btn = QPushButton("Alt")
        copy_alt_btn.setMaximumWidth(35)
        copy_alt_btn.setToolTip("Copy alt text to clipboard")
        copy_alt_btn.clicked.connect(lambda: self.copy_field_to_clipboard(item.alt_text or ""))
        copy_alt_btn.setEnabled(bool(item.alt_text))
        actions_layout.addWidget(copy_alt_btn)
        
        # Copy tags button
        copy_tags_btn = QPushButton("Tags")
        copy_tags_btn.setMaximumWidth(40)
        copy_tags_btn.setToolTip("Copy tags to clipboard")
        tags_for_copy = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
        copy_tags_btn.clicked.connect(lambda: self.copy_field_to_clipboard(tags_for_copy))
        copy_tags_btn.setEnabled(bool(item.tags))
        actions_layout.addWidget(copy_tags_btn)
        
        # Copy both button
        copy_both_btn = QPushButton("Both")
        copy_both_btn.setMaximumWidth(40)
        copy_both_btn.setToolTip("Copy both alt text and tags")
        both_text = f"Alt: {item.alt_text or 'N/A'}\nTags: {tags_for_copy or 'N/A'}"
        copy_both_btn.clicked.connect(lambda: self.copy_field_to_clipboard(both_text))
        copy_both_btn.setEnabled(bool(item.alt_text or item.tags))
        actions_layout.addWidget(copy_both_btn)
        
        self.metadata_table.setCellWidget(row, 5, actions_widget)
        
    def get_filtered_items(self) -> List[BatchItem]:
        """Get filtered list of items based on current filter settings."""
        filtered_items = []
        
        for item in self.batch_items:
            # Apply completed only filter
            if self.completed_only_cb.isChecked():
                has_completed_alt = (item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text)
                has_completed_tags = (item.tag_status == TagStatus.COMPLETED and item.tags)
                
                if not (has_completed_alt or has_completed_tags):
                    continue
                    
            filtered_items.append(item)
            
        return filtered_items
        
    def on_selection_changed(self):
        """Handle selection changes in the table."""
        selected_count = 0
        for row in range(self.metadata_table.rowCount()):
            checkbox = self.metadata_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
                
        self.copy_selected_btn.setEnabled(selected_count > 0)
        
    def on_format_changed(self):
        """Handle format selection changes."""
        self.update_preview()
        
    def update_preview(self):
        """Update the export preview based on current format and filters."""
        if not self.batch_items:
            self.preview_text.setPlainText("No data to preview")
            return
            
        format_type = self.format_combo.currentData()
        items_to_export = self.get_filtered_items()
        
        if not items_to_export:
            self.preview_text.setPlainText("No items match current filters")
            return
            
        preview_text = self.generate_export_preview(items_to_export, format_type)
        self.preview_text.setPlainText(preview_text)
        
    def generate_export_preview(self, items: List[BatchItem], format_type: str) -> str:
        """Generate preview text for the given format."""
        if format_type == "csv":
            return self.generate_csv_preview(items)
        elif format_type == "wordpress_csv":
            return self.generate_wordpress_preview(items)
        elif format_type == "json":
            return self.generate_json_preview(items)
        elif format_type == "tsv":
            return self.generate_tsv_preview(items)
        elif format_type == "iptc":
            return self.generate_iptc_preview(items)
        else:
            return "Preview not available for this format"
            
    def generate_csv_preview(self, items: List[BatchItem]) -> str:
        """Generate CSV preview."""
        lines = ["Filename,Alt Text,Tags,Status"]
        
        for item in items[:5]:  # Show first 5 items
            filename = item.source_path.name
            alt_text = (item.alt_text or "").replace('"', '""')
            tags = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
            tags = tags.replace('"', '""')
            status = "Complete" if (item.alt_text or item.tags) else "Incomplete"
            
            lines.append(f'"{filename}","{alt_text}","{tags}","{status}"')
            
        if len(items) > 5:
            lines.append(f"... and {len(items) - 5} more rows")
            
        return "\n".join(lines)
        
    def generate_wordpress_preview(self, items: List[BatchItem]) -> str:
        """Generate WordPress CSV preview."""
        lines = ["filename,title,alt_text,caption,description,tags"]
        
        for item in items[:5]:
            filename = item.source_path.name
            title = item.source_path.stem.replace('_', ' ').title()
            alt_text = (item.alt_text or "").replace('"', '""')
            tags = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
            
            lines.append(f'"{filename}","{title}","{alt_text}","","{alt_text}","{tags}"')
            
        if len(items) > 5:
            lines.append(f"... and {len(items) - 5} more rows")
            
        return "\n".join(lines)
        
    def generate_json_preview(self, items: List[BatchItem]) -> str:
        """Generate JSON preview."""
        import json
        
        preview_data = {
            "export_date": datetime.now().isoformat(),
            "total_items": len(items),
            "items": []
        }
        
        for item in items[:3]:  # Show first 3 items for JSON
            item_data = {
                "filename": item.source_path.name,
                "alt_text": item.alt_text or "",
                "tags": list(item.tags) if item.tags else [],
                "metadata": {
                    "alt_text_status": item.alt_text_status.value if item.alt_text_status else "none",
                    "tag_status": item.tag_status.value if item.tag_status else "none"
                }
            }
            preview_data["items"].append(item_data)
            
        if len(items) > 3:
            preview_data["note"] = f"Preview showing 3 of {len(items)} items"
            
        return json.dumps(preview_data, indent=2)
        
    def generate_tsv_preview(self, items: List[BatchItem]) -> str:
        """Generate tab-separated preview."""
        lines = ["Filename\tAlt Text\tTags"]
        
        for item in items[:5]:
            filename = item.source_path.name
            alt_text = item.alt_text or ""
            tags = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
            
            lines.append(f"{filename}\t{alt_text}\t{tags}")
            
        if len(items) > 5:
            lines.append(f"... and {len(items) - 5} more rows")
            
        return "\n".join(lines)
        
    def generate_iptc_preview(self, items: List[BatchItem]) -> str:
        """Generate IPTC keywords preview."""
        all_tags = set()
        for item in items:
            if item.tags:
                all_tags.update(str(tag) for tag in item.tags if tag)
                
        if not all_tags:
            return "No tags found in selected items"
            
        sorted_tags = sorted(all_tags)
        lines = [
            "# IPTC Keywords Export",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Total keywords: {len(sorted_tags)}",
            ""
        ]
        
        lines.extend(sorted_tags[:10])  # Show first 10
        
        if len(sorted_tags) > 10:
            lines.append(f"... and {len(sorted_tags) - 10} more keywords")
            
        return "\n".join(lines)
        
    def copy_field_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.notification_manager.show_notification("Copied", f"Text copied to clipboard")
        
    def copy_all_metadata(self):
        """Copy all metadata to clipboard in tab-separated format."""
        items = self.get_filtered_items()
        if not items:
            return
            
        lines = ["Filename\tAlt Text\tTags"]
        for item in items:
            filename = item.source_path.name
            alt_text = item.alt_text or ""
            tags = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
            lines.append(f"{filename}\t{alt_text}\t{tags}")
            
        clipboard_text = "\n".join(lines)
        clipboard = QApplication.clipboard()
        clipboard.setText(clipboard_text)
        
        self.notification_manager.show_notification(
            "Copied All", 
            f"Metadata for {len(items)} images copied to clipboard"
        )
        
    def copy_selected_metadata(self):
        """Copy selected metadata to clipboard."""
        selected_items = []
        items = self.get_filtered_items()
        
        for row in range(self.metadata_table.rowCount()):
            checkbox = self.metadata_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked() and row < len(items):
                selected_items.append(items[row])
                
        if not selected_items:
            return
            
        lines = ["Filename\tAlt Text\tTags"]
        for item in selected_items:
            filename = item.source_path.name
            alt_text = item.alt_text or ""
            tags = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
            lines.append(f"{filename}\t{alt_text}\t{tags}")
            
        clipboard_text = "\n".join(lines)
        clipboard = QApplication.clipboard()
        clipboard.setText(clipboard_text)
        
        self.notification_manager.show_notification(
            "Copied Selected", 
            f"Metadata for {len(selected_items)} images copied to clipboard"
        )
        
    def copy_preview_to_clipboard(self):
        """Copy the current preview to clipboard."""
        preview_text = self.preview_text.toPlainText()
        if preview_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(preview_text)
            self.notification_manager.show_notification("Copied", "Preview copied to clipboard")
            
    def export_to_file(self):
        """Export metadata to file."""
        format_type = self.format_combo.currentData()
        items = self.get_filtered_items()
        
        if not items:
            QMessageBox.warning(self, "No Data", "No items to export with current filters.")
            return
            
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        format_extensions = {
            "csv": "csv",
            "wordpress_csv": "csv", 
            "json": "json",
            "tsv": "txt",
            "iptc": "txt"
        }
        
        extension = format_extensions.get(format_type, "txt")
        default_filename = f"metadata_export_{timestamp}.{extension}"
        
        # Get save location
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Metadata",
            str(Path.home() / "Downloads" / default_filename),
            f"{extension.upper()} Files (*.{extension});;All Files (*.*)"
        )
        
        if not output_path:
            return
            
        try:
            self.write_export_file(Path(output_path), items, format_type)
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Metadata exported to:\n{Path(output_path).name}\n\n"
                f"Exported {len(items)} items"
            )
            
            # Open in finder
            import subprocess
            subprocess.run(["open", "-R", str(output_path)])
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export metadata:\n{str(e)}"
            )
            
    def write_export_file(self, output_path: Path, items: List[BatchItem], format_type: str):
        """Write export file in the specified format."""
        if format_type in ["csv", "wordpress_csv", "tsv"]:
            self.write_text_export(output_path, items, format_type)
        elif format_type == "json":
            self.write_json_export(output_path, items)
        elif format_type == "iptc":
            self.write_iptc_export(output_path, items)
            
    def write_text_export(self, output_path: Path, items: List[BatchItem], format_type: str):
        """Write text-based export (CSV, TSV, WordPress)."""
        import csv
        
        delimiter = "," if format_type != "tsv" else "\t"
        
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            if format_type == "wordpress_csv":
                fieldnames = ["filename", "title", "alt_text", "caption", "description", "tags"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in items:
                    title = item.source_path.stem.replace('_', ' ').title()
                    tags = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
                    alt_text = item.alt_text or ""
                    
                    writer.writerow({
                        "filename": item.source_path.name,
                        "title": title,
                        "alt_text": alt_text,
                        "caption": "",
                        "description": alt_text,
                        "tags": tags
                    })
            else:
                # Standard CSV or TSV
                fieldnames = ["filename", "alt_text", "tags", "status"]
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                
                for item in items:
                    tags = ", ".join(str(tag) for tag in item.tags if tag) if item.tags else ""
                    status = "Complete" if (item.alt_text or item.tags) else "Incomplete"
                    
                    writer.writerow({
                        "filename": item.source_path.name,
                        "alt_text": item.alt_text or "",
                        "tags": tags,
                        "status": status
                    })
                    
    def write_json_export(self, output_path: Path, items: List[BatchItem]):
        """Write JSON export."""
        import json
        
        export_data = {
            "export_info": {
                "export_date": datetime.now().isoformat(),
                "total_items": len(items),
                "format_version": "1.0",
                "source": "FootFix Metadata Export"
            },
            "items": []
        }
        
        for item in items:
            item_data = {
                "filename": item.source_path.name,
                "alt_text": item.alt_text or "",
                "tags": list(item.tags) if item.tags else [],
                "metadata": {
                    "alt_text_status": item.alt_text_status.value if item.alt_text_status else "none",
                    "tag_status": item.tag_status.value if item.tag_status else "none",
                    "file_path": str(item.source_path)
                }
            }
            export_data["items"].append(item_data)
            
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(export_data, file, indent=2, ensure_ascii=False)
            
    def write_iptc_export(self, output_path: Path, items: List[BatchItem]):
        """Write IPTC keywords export."""
        all_tags = set()
        for item in items:
            if item.tags:
                all_tags.update(str(tag) for tag in item.tags if tag)
                
        sorted_tags = sorted(all_tags)
        
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(f"# IPTC Keywords Export\n")
            file.write(f"# Generated from FootFix on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"# Total unique keywords: {len(sorted_tags)}\n")
            file.write(f"# Source images: {len(items)}\n")
            file.write("\n")
            
            for tag in sorted_tags:
                file.write(f"{tag}\n")