"""
Tag management and review widget for FootFix.
Provides an interface for reviewing and editing image tags.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QLineEdit, QPushButton, QLabel,
    QHeaderView, QGroupBox, QCheckBox, QMessageBox,
    QProgressBar, QSplitter, QAbstractItemView, QMenu,
    QFileDialog, QCompleter
)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel
from PySide6.QtGui import QPixmap, QColor, QAction, QPalette

from ..core.batch_processor import BatchItem, ProcessingStatus
from ..core.tag_manager import TagStatus, TagManager, TagCategory
from ..utils.preferences import PreferencesManager
from ..utils.notifications import NotificationManager

logger = logging.getLogger(__name__)


class TagEditWidget(QLineEdit):
    """Custom line edit widget with autocomplete for tag input."""
    
    tags_changed = Signal(list)  # List of tags
    
    def __init__(self, available_tags: List[str] = None, parent=None):
        super().__init__(parent)
        self.available_tags = available_tags or []
        self.current_tags: List[str] = []
        self.max_tags = 10
        
        self.setPlaceholderText("Type tags separated by commas...")
        self.textChanged.connect(self._on_text_changed)
        self.returnPressed.connect(self._on_return_pressed)
        
        # Set up autocompleter
        self._setup_autocompleter()
        
    def _setup_autocompleter(self):
        """Set up autocomplete functionality."""
        if self.available_tags:
            completer = QCompleter(self.available_tags, self)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.setCompleter(completer)
    
    def _on_text_changed(self):
        """Handle text changes and validate tags."""
        text = self.text().strip()
        if text.endswith(',') or text.endswith(' '):
            self._process_tags()
    
    def _on_return_pressed(self):
        """Handle return key press."""
        self._process_tags()
    
    def _process_tags(self):
        """Process the current text into tags."""
        text = self.text().strip()
        if not text:
            return
            
        # Split by comma and clean up
        raw_tags = [tag.strip().lower() for tag in text.split(',') if tag.strip()]
        
        # Remove duplicates and limit
        unique_tags = []
        for tag in raw_tags:
            if tag and tag not in unique_tags:
                unique_tags.append(tag)
        
        if len(unique_tags) > self.max_tags:
            unique_tags = unique_tags[:self.max_tags]
            QMessageBox.warning(
                self,
                "Too Many Tags",
                f"Maximum {self.max_tags} tags allowed. Extra tags were removed."
            )
        
        self.current_tags = unique_tags
        self.tags_changed.emit(self.current_tags)
        
        # Update display
        self.setText(', '.join(self.current_tags))
        
    def set_tags(self, tags: List[str]):
        """Set the current tags."""
        self.current_tags = tags[:self.max_tags]  # Enforce limit
        self.setText(', '.join(self.current_tags))
        
    def get_tags(self) -> List[str]:
        """Get the current tags."""
        self._process_tags()  # Ensure latest text is processed
        return self.current_tags.copy()
    
    def update_available_tags(self, tags: List[str]):
        """Update the available tags for autocomplete."""
        self.available_tags = tags
        self._setup_autocompleter()



class TagWidget(QWidget):
    """Main widget for reviewing and editing image tags."""
    
    tag_assignment_requested = Signal(list, list)  # tags, filenames 
    tag_updated = Signal(dict)  # Dict of filename: tags pairs
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.batch_items: List[BatchItem] = []
        self.tag_manager = TagManager()
        self.prefs_manager = PreferencesManager.get_instance()
        self.notification_manager = NotificationManager()
        
        # Load tag preferences
        self._load_tag_preferences()
        
        self.setup_ui()
        
    def _load_tag_preferences(self):
        """Load tag preferences and configure tag manager."""
        tag_prefs = self.prefs_manager.get('tags', {})
        
        # Configure tag manager
        self.tag_manager.auto_suggest = tag_prefs.get('auto_suggest', True)
        self.tag_manager.max_tags_per_image = tag_prefs.get('max_tags_per_image', 10)
        self.tag_manager.require_tags = tag_prefs.get('require_tags', False)
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header with actions
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Tag Management")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Tag assignment section
        self.assign_tags_btn = QPushButton("Assign Tags to Selected")
        self.assign_tags_btn.clicked.connect(self._on_assign_tags_clicked)
        self.assign_tags_btn.setEnabled(False)
        header_layout.addWidget(self.assign_tags_btn)
        
        self.clear_tags_btn = QPushButton("Clear All Tags")
        self.clear_tags_btn.clicked.connect(self._on_clear_tags_clicked)
        self.clear_tags_btn.setEnabled(False)
        header_layout.addWidget(self.clear_tags_btn)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Images table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Quick tag input
        tag_input_group = QGroupBox("Quick Tag Assignment")
        tag_input_layout = QVBoxLayout(tag_input_group)
        
        self.tag_input = TagEditWidget(self.tag_manager.get_all_tags())
        self.tag_input.tags_changed.connect(self._on_quick_tags_changed)
        tag_input_layout.addWidget(self.tag_input)
        
        # Suggested tags
        suggestion_layout = QHBoxLayout()
        suggestion_layout.addWidget(QLabel("Suggested:"))
        
        self.suggestion_buttons = []
        for tag in self.tag_manager.get_suggested_tags()[:5]:
            btn = QPushButton(tag)
            btn.setMaximumHeight(25)
            btn.clicked.connect(lambda checked, t=tag: self._add_suggested_tag(t))
            self.suggestion_buttons.append(btn)
            suggestion_layout.addWidget(btn)
        
        suggestion_layout.addStretch()
        tag_input_layout.addLayout(suggestion_layout)
        
        left_layout.addWidget(tag_input_group)
        
        # Images table
        self.images_table = QTableWidget()
        self.images_table.setColumnCount(4)
        self.images_table.setHorizontalHeaderLabels([
            "Select", "Filename", "Status", "Tags"
        ])
        
        # Configure table
        header = self.images_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select checkbox
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Filename
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # Status  
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Tags
        
        self.images_table.setColumnWidth(0, 60)
        self.images_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.images_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        left_layout.addWidget(self.images_table)
        
        splitter.addWidget(left_widget)
        
        splitter.setSizes([1000])
        
        # Status bar
        self.status_label = QLabel("No images loaded")
        layout.addWidget(self.status_label)
        
    
    def set_batch_items(self, items: List[BatchItem]):
        """Set the batch items to display."""
        self.batch_items = items
        self.refresh_display()
        
    def refresh_display(self):
        """Refresh the display with current batch items."""
        # Clear table
        self.images_table.setRowCount(0)
        
        if not self.batch_items:
            self.status_label.setText("No images loaded")
            self.assign_tags_btn.setEnabled(False)
            self.clear_tags_btn.setEnabled(False)
            return
            
        # Populate table
        self.images_table.setRowCount(len(self.batch_items))
        
        for row, item in enumerate(self.batch_items):
            # Checkbox
            checkbox = QCheckBox()
            self.images_table.setCellWidget(row, 0, checkbox)
            
            # Filename
            self.images_table.setItem(row, 1, QTableWidgetItem(item.source_path.name))
            
            # Status
            status_map = {
                TagStatus.PENDING: "Pending",
                TagStatus.APPLYING: "Applying",
                TagStatus.COMPLETED: "Tagged",
                TagStatus.ERROR: "Error"
            }
            status_text = status_map.get(item.tag_status, "Unknown")
            status_item = QTableWidgetItem(status_text)
            
            # Color code status
            if item.tag_status == TagStatus.COMPLETED:
                status_item.setBackground(QColor("#d4edda"))
            elif item.tag_status == TagStatus.ERROR:
                status_item.setBackground(QColor("#f8d7da"))
            elif item.tag_status == TagStatus.APPLYING:
                status_item.setBackground(QColor("#fff3cd"))
                
            self.images_table.setItem(row, 2, status_item)
            
            # Tags - ensure proper string conversion
            if item.tags:
                # Convert each tag to string and filter out any None values
                tag_strings = [str(tag) for tag in item.tags if tag is not None]
                tags_text = ', '.join(tag_strings) if tag_strings else "No tags"
            else:
                tags_text = "No tags"
            self.images_table.setItem(row, 3, QTableWidgetItem(tags_text))
        
        # Update status
        total_items = len(self.batch_items)
        tagged_items = sum(1 for item in self.batch_items if item.tags)
        self.status_label.setText(f"Total: {total_items} images, Tagged: {tagged_items}")
        
        # Enable buttons
        self.assign_tags_btn.setEnabled(True)
        self.clear_tags_btn.setEnabled(True)
    
    def _on_selection_changed(self):
        """Handle table selection changes."""
        selected_rows = set()
        for i in range(self.images_table.rowCount()):
            checkbox = self.images_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                selected_rows.add(i)
        
        self.assign_tags_btn.setEnabled(len(selected_rows) > 0)
        
    def _on_quick_tags_changed(self, tags: List[str]):
        """Handle changes to quick tag input."""
        pass  # Tags are ready for assignment
        
    def _add_suggested_tag(self, tag: str):
        """Add a suggested tag to the input."""
        current_tags = self.tag_input.get_tags()
        if tag not in current_tags:
            current_tags.append(tag)
            self.tag_input.set_tags(current_tags)
    
    def _on_assign_tags_clicked(self):
        """Handle assign tags button click."""
        tags = self.tag_input.get_tags()
        if not tags:
            QMessageBox.warning(self, "No Tags", "Please enter tags to assign.")
            return
        
        selected_filenames = []
        for i in range(self.images_table.rowCount()):
            checkbox = self.images_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                filename = self.images_table.item(i, 1).text()
                selected_filenames.append(filename)
        
        if not selected_filenames:
            QMessageBox.warning(self, "No Selection", "Please select images to tag.")
            return
        
        # Emit signal for tag assignment
        self.tag_assignment_requested.emit(tags, selected_filenames)
        
        # Update local data
        tag_updates = {}
        for item in self.batch_items:
            if item.source_path.name in selected_filenames:
                item.tags = tags.copy()
                item.tag_status = TagStatus.COMPLETED
                tag_updates[item.source_path.name] = tags
        
        # Refresh display and emit update signal
        self.refresh_display()
        self.tag_updated.emit(tag_updates)
        
        # Clear input
        self.tag_input.setText("")
        self.tag_input.current_tags = []
        
        # Show notification
        self.notification_manager.show_notification(
            "Tags Assigned",
            f"Tags assigned to {len(selected_filenames)} images"
        )
    
    def _on_clear_tags_clicked(self):
        """Handle clear tags button click."""
        reply = QMessageBox.question(
            self,
            "Clear All Tags",
            "Are you sure you want to clear all tags from all images?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear tags from all items
            tag_updates = {}
            for item in self.batch_items:
                item.tags = []
                item.tag_status = TagStatus.PENDING
                item.tag_error = None
                tag_updates[item.source_path.name] = []
            
            # Refresh display and emit update signal
            self.refresh_display()
            self.tag_updated.emit(tag_updates)
            
            # Show notification
            self.notification_manager.show_notification(
                "Tags Cleared",
                "All tags have been cleared from all images"
            )