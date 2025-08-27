"""
Queue Management Widget for FootFix.
Extracted from UnifiedProcessingWidget to handle queue display and interactions.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QFileDialog, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from ...core.batch_processor import BatchItem, ProcessingStatus
from ...core.processor import ImageProcessor

logger = logging.getLogger(__name__)


class QueueManagementWidget(QWidget):
    """
    Dedicated widget for managing the image processing queue.
    Handles queue display, drag/drop, and queue manipulation.
    """
    
    # Signals
    add_images_requested = Signal()
    add_folder_requested = Signal()
    clear_queue_requested = Signal()
    remove_item_requested = Signal(int)
    selection_changed = Signal(list)  # List of selected row indices
    files_dropped = Signal(list)  # List of file paths
    
    def __init__(self, parent=None):
        """Initialize the queue management widget."""
        super().__init__(parent)
        self.queue_items: List[Dict[str, Any]] = []
        self.is_processing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the queue management UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the queue group
        self.queue_group = QGroupBox("Image Queue")
        queue_layout = QVBoxLayout(self.queue_group)
        
        # Queue controls toolbar
        self.setup_toolbar(queue_layout)
        
        # Queue display area
        self.setup_queue_display(queue_layout)
        
        main_layout.addWidget(self.queue_group)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
    def setup_toolbar(self, parent_layout):
        """Set up the queue controls toolbar."""
        toolbar_layout = QHBoxLayout()
        
        self.add_images_btn = QPushButton("Add Images")
        self.add_images_btn.clicked.connect(self.add_images_requested.emit)
        toolbar_layout.addWidget(self.add_images_btn)
        
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder_requested.emit)
        toolbar_layout.addWidget(self.add_folder_btn)
        
        self.clear_queue_btn = QPushButton("Clear All")
        self.clear_queue_btn.clicked.connect(self.clear_queue_requested.emit)
        toolbar_layout.addWidget(self.clear_queue_btn)
        
        toolbar_layout.addStretch()
        
        self.queue_count_label = QLabel("0 images")
        toolbar_layout.addWidget(self.queue_count_label)
        
        parent_layout.addLayout(toolbar_layout)
        
    def setup_queue_display(self, parent_layout):
        """Set up the adaptive queue display (drop zone / table)."""
        # Container for switching between drop zone and queue table
        self.queue_container = QWidget()
        container_layout = QVBoxLayout(self.queue_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Drop zone for empty state
        self.drop_zone = QLabel("Drag images here or use buttons above to add images")
        self.drop_zone.setAlignment(Qt.AlignCenter)
        self.drop_zone.setMinimumHeight(150)
        self.drop_zone.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f8f8f8;
                color: #666;
                font-size: 14px;
            }
        """)
        container_layout.addWidget(self.drop_zone)
        
        # Queue table for when we have images
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(5)
        self.queue_table.setHorizontalHeaderLabels(["Filename", "Size", "Status", "Error", "Actions"])
        self.queue_table.horizontalHeader().setStretchLastSection(True)
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.queue_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.queue_table.setVisible(False)  # Hidden initially
        container_layout.addWidget(self.queue_table)
        
        parent_layout.addWidget(self.queue_container)
        
    def update_queue_display(self, queue_items: List[Dict[str, Any]]):
        """
        Update the queue display with current queue data.
        
        Args:
            queue_items: List of queue item dictionaries from batch processor
        """
        self.queue_items = queue_items
        queue_size = len(queue_items)
        
        # Update queue count label
        if queue_size == 0:
            self.queue_count_label.setText("0 images")
        elif queue_size == 1:
            self.queue_count_label.setText("1 image")
        else:
            self.queue_count_label.setText(f"{queue_size} images")
        
        # Smart UI adaptation based on queue size
        if queue_size == 0:
            # Show drop zone, hide table
            self.drop_zone.setVisible(True)
            self.queue_table.setVisible(False)
        else:
            # Show table, hide drop zone
            self.drop_zone.setVisible(False)
            self.queue_table.setVisible(True)
            
            # Update table content
            self.update_queue_table(queue_items)
            
    def update_queue_table(self, queue_items: List[Dict[str, Any]]):
        """Update the queue table with current queue information."""
        self.queue_table.setRowCount(len(queue_items))
        
        for row, item_info in enumerate(queue_items):
            # Filename
            self.queue_table.setItem(row, 0, QTableWidgetItem(item_info['filename']))
            
            # Size
            size_mb = item_info['size'] / (1024 * 1024)
            self.queue_table.setItem(row, 1, QTableWidgetItem(f"{size_mb:.1f} MB"))
            
            # Status
            status_item = QTableWidgetItem(item_info['status'])
            if item_info['status'] == 'completed':
                status_item.setForeground(Qt.green)
            elif item_info['status'] == 'failed':
                status_item.setForeground(Qt.red)
            elif item_info['status'] == 'processing':
                status_item.setForeground(Qt.blue)
            self.queue_table.setItem(row, 2, status_item)
            
            # Error
            error_text = item_info['error'] or ""
            self.queue_table.setItem(row, 3, QTableWidgetItem(error_text))
            
            # Remove button (only for pending items when not processing)
            if not self.is_processing and item_info['status'] == 'pending':
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, idx=row: self.remove_item_requested.emit(idx))
                self.queue_table.setCellWidget(row, 4, remove_btn)
            else:
                self.queue_table.setCellWidget(row, 4, None)
                
    def set_processing_state(self, is_processing: bool):
        """
        Update the widget state based on processing status.
        
        Args:
            is_processing: Whether processing is currently active
        """
        self.is_processing = is_processing
        self.add_images_btn.setEnabled(not is_processing)
        self.add_folder_btn.setEnabled(not is_processing)
        self.clear_queue_btn.setEnabled(not is_processing)
        
        # Update remove buttons if we have items
        if self.queue_items:
            self.update_queue_table(self.queue_items)
            
    def get_selected_indices(self) -> List[int]:
        """Get the indices of selected rows."""
        selected_rows = self.queue_table.selectionModel().selectedRows()
        return [row.row() for row in selected_rows]
        
    def on_selection_changed(self):
        """Handle table selection changes."""
        selected_indices = self.get_selected_indices()
        self.selection_changed.emit(selected_indices)
        
    # Drag and Drop Support
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any URL is a valid image or directory
            for url in event.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.is_dir() or path.suffix.lower() in ImageProcessor.SUPPORTED_FORMATS:
                    event.acceptProposedAction()
                    # Visual feedback
                    self.drop_zone.setStyleSheet("""
                        QLabel {
                            border: 2px solid #007AFF;
                            border-radius: 10px;
                            padding: 20px;
                            background-color: #e6f2ff;
                            color: #007AFF;
                            font-size: 14px;
                        }
                    """)
                    return
                    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        # Reset visual feedback
        self.drop_zone.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f8f8f8;
                color: #666;
                font-size: 14px;
            }
        """)
        
        urls = event.mimeData().urls()
        if not urls:
            return
            
        # Collect all valid image paths
        image_paths = []
        
        for url in urls:
            path = Path(url.toLocalFile())
            
            if path.is_file() and path.suffix.lower() in ImageProcessor.SUPPORTED_FORMATS:
                image_paths.append(path)
            elif path.is_dir():
                # Add all images from directory
                for img_path in path.rglob('*'):
                    if img_path.is_file() and img_path.suffix.lower() in ImageProcessor.SUPPORTED_FORMATS:
                        image_paths.append(img_path)
                        
        if not image_paths:
            QMessageBox.warning(
                self,
                "No Valid Images",
                "No valid image files were found in the dropped items."
            )
            return
            
        # Emit signal with discovered image paths
        self.files_dropped.emit(image_paths)
            
    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        # Reset visual feedback
        self.drop_zone.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f8f8f8;
                color: #666;
                font-size: 14px;
            }
        """)
        
    def set_enabled(self, enabled: bool):
        """Enable or disable the queue management controls."""
        self.add_images_btn.setEnabled(enabled)
        self.add_folder_btn.setEnabled(enabled)
        self.clear_queue_btn.setEnabled(enabled)
        self.queue_table.setEnabled(enabled)