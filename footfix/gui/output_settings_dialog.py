"""
Output settings dialog for FootFix.
Provides advanced output configuration including filename templates.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QLineEdit,
    QCheckBox, QListWidget, QListWidgetItem,
    QDialogButtonBox, QRadioButton, QButtonGroup,
    QTabWidget, QWidget
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path

from ..utils.filename_template import FilenameTemplateWidget


class OutputSettingsDialog(QDialog):
    """Dialog for configuring output settings."""
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.current_settings = current_settings or {}
        self.recent_folders = []
        self.favorite_folders = []
        
        self.setWindowTitle("Output Settings")
        self.setMinimumWidth(600)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Output folder selection
        folder_group = QGroupBox("Output Folder")
        folder_layout = QVBoxLayout()
        
        # Current folder
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current:"))
        
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        current_layout.addWidget(self.folder_edit, 1)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_folder)
        current_layout.addWidget(self.browse_button)
        
        folder_layout.addLayout(current_layout)
        
        # Recent and favorite folders
        folders_tabs = QTabWidget()
        
        # Recent folders tab
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self.select_recent_folder)
        folders_tabs.addTab(self.recent_list, "Recent")
        
        # Favorite folders tab
        self.favorites_list = QListWidget()
        self.favorites_list.itemDoubleClicked.connect(self.select_favorite_folder)
        
        fav_layout = QVBoxLayout()
        fav_layout.addWidget(self.favorites_list)
        
        fav_buttons = QHBoxLayout()
        self.add_favorite_btn = QPushButton("Add Current")
        self.add_favorite_btn.clicked.connect(self.add_favorite)
        self.remove_favorite_btn = QPushButton("Remove")
        self.remove_favorite_btn.clicked.connect(self.remove_favorite)
        fav_buttons.addWidget(self.add_favorite_btn)
        fav_buttons.addWidget(self.remove_favorite_btn)
        fav_layout.addLayout(fav_buttons)
        
        fav_widget = QWidget()
        fav_widget.setLayout(fav_layout)
        folders_tabs.addTab(fav_widget, "Favorites")
        
        folder_layout.addWidget(folders_tabs)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # Filename template
        template_group = QGroupBox("Filename Template")
        template_layout = QVBoxLayout()
        
        self.template_widget = FilenameTemplateWidget()
        template_layout.addWidget(self.template_widget)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # Duplicate handling
        duplicate_group = QGroupBox("Duplicate File Handling")
        duplicate_layout = QVBoxLayout()
        
        self.duplicate_group = QButtonGroup()
        
        self.rename_radio = QRadioButton("Rename (add number suffix)")
        self.rename_radio.setChecked(True)
        self.duplicate_group.addButton(self.rename_radio, 0)
        duplicate_layout.addWidget(self.rename_radio)
        
        self.overwrite_radio = QRadioButton("Overwrite existing file")
        self.duplicate_group.addButton(self.overwrite_radio, 1)
        duplicate_layout.addWidget(self.overwrite_radio)
        
        self.skip_radio = QRadioButton("Skip (don't process)")
        self.duplicate_group.addButton(self.skip_radio, 2)
        duplicate_layout.addWidget(self.skip_radio)
        
        duplicate_group.setLayout(duplicate_layout)
        layout.addWidget(duplicate_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def load_settings(self):
        """Load current settings into the dialog."""
        # Set current folder
        folder = self.current_settings.get('output_folder', Path.home() / "Downloads")
        self.folder_edit.setText(str(folder))
        
        # Load recent folders (placeholder - would load from preferences)
        self.recent_folders = self.current_settings.get('recent_folders', [])
        self.update_recent_list()
        
        # Load favorite folders (placeholder - would load from preferences)
        self.favorite_folders = self.current_settings.get('favorite_folders', [])
        self.update_favorites_list()
        
        # Set duplicate handling
        duplicate_strategy = self.current_settings.get('duplicate_strategy', 'rename')
        if duplicate_strategy == 'overwrite':
            self.overwrite_radio.setChecked(True)
        elif duplicate_strategy == 'skip':
            self.skip_radio.setChecked(True)
        else:
            self.rename_radio.setChecked(True)
            
    def browse_folder(self):
        """Browse for output folder."""
        from PySide6.QtWidgets import QFileDialog
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self.folder_edit.text()
        )
        
        if folder:
            self.folder_edit.setText(folder)
            self.add_to_recent(folder)
            
    def add_to_recent(self, folder: str):
        """Add folder to recent list."""
        if folder in self.recent_folders:
            self.recent_folders.remove(folder)
        self.recent_folders.insert(0, folder)
        self.recent_folders = self.recent_folders[:10]  # Keep only 10 recent
        self.update_recent_list()
        
    def update_recent_list(self):
        """Update the recent folders list widget."""
        self.recent_list.clear()
        for folder in self.recent_folders:
            item = QListWidgetItem(folder)
            item.setData(Qt.UserRole, folder)
            self.recent_list.addItem(item)
            
    def update_favorites_list(self):
        """Update the favorite folders list widget."""
        self.favorites_list.clear()
        for folder in self.favorite_folders:
            item = QListWidgetItem(folder)
            item.setData(Qt.UserRole, folder)
            self.favorites_list.addItem(item)
            
    def select_recent_folder(self, item):
        """Select a folder from recent list."""
        folder = item.data(Qt.UserRole)
        self.folder_edit.setText(folder)
        
    def select_favorite_folder(self, item):
        """Select a folder from favorites list."""
        folder = item.data(Qt.UserRole)
        self.folder_edit.setText(folder)
        self.add_to_recent(folder)
        
    def add_favorite(self):
        """Add current folder to favorites."""
        folder = self.folder_edit.text()
        if folder and folder not in self.favorite_folders:
            self.favorite_folders.append(folder)
            self.update_favorites_list()
            
    def remove_favorite(self):
        """Remove selected folder from favorites."""
        current_item = self.favorites_list.currentItem()
        if current_item:
            folder = current_item.data(Qt.UserRole)
            self.favorite_folders.remove(folder)
            self.update_favorites_list()
            
    def get_settings(self) -> dict:
        """Get the configured settings."""
        duplicate_strategies = ['rename', 'overwrite', 'skip']
        
        return {
            'output_folder': Path(self.folder_edit.text()),
            'filename_template': self.template_widget.get_template(),
            'duplicate_strategy': duplicate_strategies[self.duplicate_group.checkedId()],
            'recent_folders': self.recent_folders,
            'favorite_folders': self.favorite_folders,
        }