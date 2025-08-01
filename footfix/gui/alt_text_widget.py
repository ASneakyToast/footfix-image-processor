"""
Alt text review and editing widget for FootFix.
Provides an interface for reviewing and editing generated alt text descriptions.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QTextEdit, QPushButton, QLabel,
    QHeaderView, QGroupBox, QCheckBox, QMessageBox,
    QProgressBar, QSplitter, QAbstractItemView, QMenu,
    QFileDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QTextCharFormat, QColor, QAction

from ..core.batch_processor import BatchItem, ProcessingStatus
from ..core.alt_text_generator import AltTextStatus
from ..utils.preferences import PreferencesManager
from ..utils.alt_text_exporter import AltTextExporter, ExportFormat, ExportOptions
from ..utils.notifications import NotificationManager

logger = logging.getLogger(__name__)


class AltTextEditWidget(QTextEdit):
    """Custom text edit widget with character count and validation."""
    
    text_changed_with_validation = Signal(str, bool)  # text, is_valid
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.char_limit = 125  # Recommended alt text character limit
        self.warning_threshold = 100  # Show warning color when approaching limit
        
        self.textChanged.connect(self._on_text_changed)
        self.setMaximumHeight(80)
        self.setPlaceholderText("Enter alt text description...")
        
    def _on_text_changed(self):
        """Handle text changes and apply validation."""
        text = self.toPlainText()
        char_count = len(text)
        
        # Apply text formatting based on character count
        if char_count > self.char_limit:
            self.setStyleSheet("QTextEdit { background-color: #ffeeee; }")
            is_valid = False
        elif char_count > self.warning_threshold:
            self.setStyleSheet("QTextEdit { background-color: #fff7ee; }")
            is_valid = True
        else:
            self.setStyleSheet("")
            is_valid = True
            
        self.text_changed_with_validation.emit(text, is_valid)
        
    def set_text_with_validation(self, text: str):
        """Set text and trigger validation."""
        self.setPlainText(text)
        

class AltTextItemWidget(QWidget):
    """Widget for displaying and editing a single alt text item."""
    
    alt_text_updated = Signal(str, str)  # filename, new_alt_text
    regenerate_requested = Signal(str)  # filename
    
    def __init__(self, batch_item: BatchItem, parent=None):
        super().__init__(parent)
        self.batch_item = batch_item
        self.setup_ui()
        self.update_display()
        
    def setup_ui(self):
        """Set up the UI for the item widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(80, 80)
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 2px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.thumbnail_label)
        
        # Info section
        info_layout = QVBoxLayout()
        
        # Filename and status
        header_layout = QHBoxLayout()
        self.filename_label = QLabel(self.batch_item.source_path.name)
        self.filename_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.filename_label)
        
        self.status_label = QLabel()
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        
        info_layout.addLayout(header_layout)
        
        # Alt text editor
        self.alt_text_edit = AltTextEditWidget()
        self.alt_text_edit.text_changed_with_validation.connect(self._on_alt_text_changed)
        info_layout.addWidget(self.alt_text_edit)
        
        # Character count and actions
        actions_layout = QHBoxLayout()
        
        self.char_count_label = QLabel("0/125 characters")
        self.char_count_label.setStyleSheet("color: #666; font-size: 11px;")
        actions_layout.addWidget(self.char_count_label)
        
        actions_layout.addStretch()
        
        # Regenerate button
        self.regenerate_btn = QPushButton("Regenerate")
        self.regenerate_btn.setFixedHeight(24)
        self.regenerate_btn.clicked.connect(self._on_regenerate_clicked)
        actions_layout.addWidget(self.regenerate_btn)
        
        info_layout.addLayout(actions_layout)
        layout.addLayout(info_layout, 1)
        
        # Load thumbnail
        self._load_thumbnail()
        
    def _load_thumbnail(self):
        """Load and display image thumbnail."""
        try:
            # Use output path if available, otherwise source path
            image_path = self.batch_item.output_path or self.batch_item.source_path
            if image_path.exists():
                pixmap = QPixmap(str(image_path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        80, 80,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.thumbnail_label.setPixmap(scaled)
        except Exception as e:
            logger.error(f"Failed to load thumbnail: {e}")
            
    def update_display(self):
        """Update the display based on current batch item state."""
        # Update alt text
        if self.batch_item.alt_text:
            self.alt_text_edit.set_text_with_validation(self.batch_item.alt_text)
            
        # Update status
        status_text = ""
        status_style = ""
        
        if self.batch_item.alt_text_status == AltTextStatus.COMPLETED:
            status_text = "✓ Generated"
            status_style = "color: green;"
        elif self.batch_item.alt_text_status == AltTextStatus.GENERATING:
            status_text = "⟳ Generating..."
            status_style = "color: blue;"
        elif self.batch_item.alt_text_status == AltTextStatus.ERROR:
            status_text = f"✗ Error: {self.batch_item.alt_text_error or 'Unknown'}"
            status_style = "color: red;"
        elif self.batch_item.alt_text_status == AltTextStatus.PENDING:
            status_text = "⏳ Pending"
            status_style = "color: orange;"
            
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(status_style)
        
        # Enable/disable regenerate button
        self.regenerate_btn.setEnabled(
            self.batch_item.alt_text_status in [AltTextStatus.COMPLETED, AltTextStatus.ERROR]
        )
        
    def _on_alt_text_changed(self, text: str, is_valid: bool):
        """Handle alt text changes."""
        char_count = len(text)
        self.char_count_label.setText(f"{char_count}/125 characters")
        
        if char_count > 125:
            self.char_count_label.setStyleSheet("color: red; font-size: 11px;")
        elif char_count > 100:
            self.char_count_label.setStyleSheet("color: orange; font-size: 11px;")
        else:
            self.char_count_label.setStyleSheet("color: #666; font-size: 11px;")
            
        # Update batch item
        self.batch_item.alt_text = text
        
        # Emit signal
        self.alt_text_updated.emit(self.batch_item.source_path.name, text)
        
    def _on_regenerate_clicked(self):
        """Handle regenerate button click."""
        self.regenerate_requested.emit(self.batch_item.source_path.name)


class AltTextWidget(QWidget):
    """Main widget for reviewing and editing alt text descriptions."""
    
    regenerate_requested = Signal(list)  # List of filenames to regenerate
    alt_text_updated = Signal(dict)  # Dict of filename: alt_text pairs
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.batch_items: List[BatchItem] = []
        self.item_widgets: Dict[str, AltTextItemWidget] = {}
        self.prefs_manager = PreferencesManager()
        self.exporter = AltTextExporter()
        self.notification_manager = NotificationManager()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header with actions
        header_layout = QHBoxLayout()
        
        self.status_label = QLabel("No items to review")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        # Bulk actions
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.toggled.connect(self._on_select_all_toggled)
        header_layout.addWidget(self.select_all_cb)
        
        self.approve_all_btn = QPushButton("Approve All")
        self.approve_all_btn.clicked.connect(self._on_approve_all_clicked)
        header_layout.addWidget(self.approve_all_btn)
        
        self.regenerate_selected_btn = QPushButton("Regenerate Selected")
        self.regenerate_selected_btn.clicked.connect(self._on_regenerate_selected_clicked)
        self.regenerate_selected_btn.setEnabled(False)
        header_layout.addWidget(self.regenerate_selected_btn)
        
        # Export button with dropdown menu
        self.export_btn = QPushButton("Export")
        self.export_btn.setEnabled(False)
        export_menu = QMenu(self)
        
        export_csv_action = QAction("Export to CSV...", self)
        export_csv_action.triggered.connect(lambda: self._on_export_clicked(ExportFormat.CSV))
        export_menu.addAction(export_csv_action)
        
        export_json_action = QAction("Export to JSON...", self)
        export_json_action.triggered.connect(lambda: self._on_export_clicked(ExportFormat.JSON))
        export_menu.addAction(export_json_action)
        
        export_menu.addSeparator()
        
        export_cms_action = QAction("Export for WordPress...", self)
        export_cms_action.triggered.connect(self._on_export_cms_clicked)
        export_menu.addAction(export_cms_action)
        
        self.export_btn.setMenu(export_menu)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Guidelines
        guidelines_group = QGroupBox("Alt Text Best Practices")
        guidelines_layout = QVBoxLayout()
        
        guidelines_text = (
            "• Keep descriptions concise (under 125 characters recommended)\n"
            "• Describe the content and context, not just objects\n"
            "• Include relevant details like emotions, actions, or settings\n"
            "• Avoid phrases like 'image of' or 'picture of'\n"
            "• Consider the editorial context when writing descriptions"
        )
        
        guidelines_label = QLabel(guidelines_text)
        guidelines_label.setWordWrap(True)
        guidelines_label.setStyleSheet("color: #666; padding: 5px;")
        guidelines_layout.addWidget(guidelines_label)
        
        guidelines_group.setLayout(guidelines_layout)
        layout.addWidget(guidelines_group)
        
        # Splitter for items and details
        splitter = QSplitter(Qt.Vertical)
        
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "Select", "Filename", "Status", "Alt Text", "Actions"
        ])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        splitter.addWidget(self.items_table)
        
        # Detailed view area
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        
        self.details_label = QLabel("Select an item to view details")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setStyleSheet("color: #999; padding: 20px;")
        details_layout.addWidget(self.details_label)
        
        splitter.addWidget(self.details_widget)
        splitter.setSizes([400, 200])
        
        layout.addWidget(splitter)
        
        # Progress section
        progress_group = QGroupBox("Generation Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
    def set_batch_items(self, items: List[BatchItem]):
        """Set the batch items to display."""
        self.batch_items = items
        self.item_widgets.clear()
        self.refresh_display()
        
    def refresh_display(self):
        """Refresh the display with current batch items."""
        # Clear table
        self.items_table.setRowCount(0)
        
        # Count statistics
        total_items = len(self.batch_items)
        completed_items = sum(
            1 for item in self.batch_items 
            if item.alt_text_status == AltTextStatus.COMPLETED
        )
        pending_items = sum(
            1 for item in self.batch_items
            if item.alt_text_status == AltTextStatus.PENDING
        )
        error_items = sum(
            1 for item in self.batch_items
            if item.alt_text_status == AltTextStatus.ERROR
        )
        
        # Update status
        status_parts = [f"{total_items} items"]
        if completed_items > 0:
            status_parts.append(f"{completed_items} completed")
        if pending_items > 0:
            status_parts.append(f"{pending_items} pending")
        if error_items > 0:
            status_parts.append(f"{error_items} errors")
            
        self.status_label.setText(" | ".join(status_parts))
        
        # Populate table
        self.items_table.setRowCount(total_items)
        
        for row, item in enumerate(self.batch_items):
            # Only show items that have been processed
            if item.status != ProcessingStatus.COMPLETED:
                continue
                
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setProperty("filename", item.source_path.name)
            self.items_table.setCellWidget(row, 0, checkbox)
            
            # Filename
            self.items_table.setItem(row, 1, QTableWidgetItem(item.source_path.name))
            
            # Status
            status_item = QTableWidgetItem()
            if item.alt_text_status == AltTextStatus.COMPLETED:
                status_item.setText("✓ Generated")
                status_item.setForeground(QColor("green"))
            elif item.alt_text_status == AltTextStatus.GENERATING:
                status_item.setText("⟳ Generating...")
                status_item.setForeground(QColor("blue"))
            elif item.alt_text_status == AltTextStatus.ERROR:
                status_item.setText("✗ Error")
                status_item.setForeground(QColor("red"))
            else:
                status_item.setText("⏳ Pending")
                status_item.setForeground(QColor("orange"))
                
            self.items_table.setItem(row, 2, status_item)
            
            # Alt text preview
            alt_text_preview = item.alt_text or ""
            if len(alt_text_preview) > 50:
                alt_text_preview = alt_text_preview[:50] + "..."
            self.items_table.setItem(row, 3, QTableWidgetItem(alt_text_preview))
            
            # Create item widget
            item_widget = AltTextItemWidget(item)
            item_widget.alt_text_updated.connect(self._on_item_alt_text_updated)
            item_widget.regenerate_requested.connect(self._on_item_regenerate_requested)
            
            self.item_widgets[item.source_path.name] = item_widget
            self.items_table.setCellWidget(row, 4, item_widget)
            
        # Enable/disable buttons
        self.approve_all_btn.setEnabled(total_items > 0)
        self.export_btn.setEnabled(total_items > 0)
        
    def _on_select_all_toggled(self, checked: bool):
        """Handle select all checkbox toggle."""
        for row in range(self.items_table.rowCount()):
            checkbox = self.items_table.cellWidget(row, 0)
            if checkbox and isinstance(checkbox, QCheckBox):
                checkbox.setChecked(checked)
                
        self._on_selection_changed()
        
    def _on_selection_changed(self):
        """Handle table selection changes."""
        selected_count = 0
        
        for row in range(self.items_table.rowCount()):
            checkbox = self.items_table.cellWidget(row, 0)
            if checkbox and isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                selected_count += 1
                
        self.regenerate_selected_btn.setEnabled(selected_count > 0)
        self.regenerate_selected_btn.setText(
            f"Regenerate Selected ({selected_count})" if selected_count > 0 
            else "Regenerate Selected"
        )
        
    def _on_approve_all_clicked(self):
        """Handle approve all button click."""
        # Collect all alt text updates
        updates = {}
        
        for item in self.batch_items:
            if item.alt_text:
                updates[item.source_path.name] = item.alt_text
                
        if updates:
            self.alt_text_updated.emit(updates)
            QMessageBox.information(
                self,
                "Alt Text Approved",
                f"Approved alt text for {len(updates)} images."
            )
            
    def _on_regenerate_selected_clicked(self):
        """Handle regenerate selected button click."""
        selected_files = []
        
        for row in range(self.items_table.rowCount()):
            checkbox = self.items_table.cellWidget(row, 0)
            if checkbox and isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                filename = checkbox.property("filename")
                if filename:
                    selected_files.append(filename)
                    
        if selected_files:
            reply = QMessageBox.question(
                self,
                "Regenerate Alt Text",
                f"Regenerate alt text for {len(selected_files)} selected images?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.regenerate_requested.emit(selected_files)
                
    def _on_item_alt_text_updated(self, filename: str, alt_text: str):
        """Handle individual item alt text update."""
        updates = {filename: alt_text}
        self.alt_text_updated.emit(updates)
        
    def _on_item_regenerate_requested(self, filename: str):
        """Handle individual item regenerate request."""
        reply = QMessageBox.question(
            self,
            "Regenerate Alt Text",
            f"Regenerate alt text for {filename}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.regenerate_requested.emit([filename])
            
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress display."""
        if total > 0:
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            
            percentage = (current / total) * 100
            self.progress_label.setText(
                f"{message} - {current}/{total} ({percentage:.0f}%)"
            )
        else:
            self.progress_bar.setVisible(False)
            self.progress_label.setText("Ready")
            
    def show_generation_complete(self, successful: int, failed: int):
        """Show generation completion message."""
        message = f"Alt text generation complete.\n\n"
        message += f"Successful: {successful}\n"
        
        if failed > 0:
            message += f"Failed: {failed}"
            QMessageBox.warning(self, "Generation Complete", message)
        else:
            QMessageBox.information(self, "Generation Complete", message)
            
    def _on_export_clicked(self, format: ExportFormat):
        """Handle export button click."""
        # Check if we have items to export
        if not self.batch_items:
            QMessageBox.warning(self, "No Data", "No items available to export.")
            return
            
        # Create export options dialog
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Export Options")
        dialog.setText("Select which items to export:")
        
        all_btn = dialog.addButton("All Items", QMessageBox.ActionRole)
        selected_btn = dialog.addButton("Selected Only", QMessageBox.ActionRole)
        completed_btn = dialog.addButton("Completed Only", QMessageBox.ActionRole)
        dialog.addButton(QMessageBox.Cancel)
        
        dialog.exec_()
        clicked_button = dialog.clickedButton()
        
        if clicked_button == dialog.button(QMessageBox.Cancel):
            return
            
        # Determine export options
        if clicked_button == all_btn:
            options = ExportOptions.ALL
        elif clicked_button == selected_btn:
            options = ExportOptions.SELECTED
        else:  # completed_btn
            options = ExportOptions.COMPLETED_ONLY
            
        # Get selected items if needed
        selected_items = None
        if options == ExportOptions.SELECTED:
            selected_items = self._get_selected_filenames()
            if not selected_items:
                QMessageBox.warning(self, "No Selection", "No items selected for export.")
                return
                
        # Get output file path
        default_filename = self.exporter.generate_filename(format)
        file_filter = f"{format.value.upper()} Files (*.{format.value})"
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Alt Text as {format.value.upper()}",
            str(self.exporter.default_export_dir / default_filename),
            file_filter
        )
        
        if not output_path:
            return
            
        output_path = Path(output_path)
        
        # Validate path
        is_valid, msg = self.exporter.validate_export_path(output_path)
        if not is_valid:
            QMessageBox.critical(self, "Invalid Path", msg)
            return
            
        # Perform export
        if format == ExportFormat.CSV:
            success, message = self.exporter.export_csv(
                self.batch_items, output_path, options, selected_items
            )
        else:  # JSON
            success, message = self.exporter.export_json(
                self.batch_items, output_path, options, selected_items
            )
            
        # Show result
        if success:
            QMessageBox.information(self, "Export Complete", message)
            
            # Show notification
            self.notification_manager.show_notification(
                "Export Complete",
                f"Alt text exported to {output_path.name}",
                duration=3000
            )
            
            # Open folder in finder
            reply = QMessageBox.question(
                self,
                "Open Export Location",
                "Would you like to open the export location?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                import subprocess
                subprocess.run(["open", "-R", str(output_path)])
        else:
            QMessageBox.critical(self, "Export Failed", message)
            
    def _on_export_cms_clicked(self):
        """Handle CMS export click."""
        if not self.batch_items:
            QMessageBox.warning(self, "No Data", "No items available to export.")
            return
            
        # Check for completed items
        completed_items = [
            item for item in self.batch_items 
            if item.alt_text_status == AltTextStatus.COMPLETED and item.alt_text
        ]
        
        if not completed_items:
            QMessageBox.warning(
                self, 
                "No Completed Items", 
                "No completed items with alt text available for CMS export."
            )
            return
            
        # Get output file path
        default_filename = "wordpress_alt_text_import.csv"
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export for WordPress",
            str(self.exporter.default_export_dir / default_filename),
            "CSV Files (*.csv)"
        )
        
        if not output_path:
            return
            
        output_path = Path(output_path)
        
        # Perform export
        success, message = self.exporter.export_for_cms(
            self.batch_items, output_path, "wordpress"
        )
        
        # Show result
        if success:
            QMessageBox.information(
                self,
                "Export Complete",
                f"{message}\n\nThis file can be imported into WordPress using "
                "a CSV import plugin like 'WP All Import' or similar."
            )
            
            # Open folder
            import subprocess
            subprocess.run(["open", "-R", str(output_path)])
        else:
            QMessageBox.critical(self, "Export Failed", message)
            
    def _get_selected_filenames(self) -> List[str]:
        """Get list of selected filenames from the table."""
        selected_files = []
        
        for row in range(self.items_table.rowCount()):
            checkbox = self.items_table.cellWidget(row, 0)
            if checkbox and isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                filename = checkbox.property("filename")
                if filename:
                    selected_files.append(filename)
                    
        return selected_files