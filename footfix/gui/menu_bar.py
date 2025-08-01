"""
Menu bar implementation for FootFix application.
Provides standard macOS menus with keyboard shortcuts.
"""

from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Signal, QObject
import webbrowser
from pathlib import Path


class MenuBarManager(QObject):
    """Manages the application menu bar and its actions."""
    
    # Signals for menu actions
    open_file = Signal()
    open_folder = Signal()
    save_as = Signal()
    show_preferences = Signal()
    quit_app = Signal()
    
    show_preview = Signal()
    toggle_fullscreen = Signal()
    
    show_help = Signal()
    show_shortcuts = Signal()
    show_about = Signal()
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.menu_bar = parent_window.menuBar()
        self.setup_menus()
        
    def setup_menus(self):
        """Set up all application menus."""
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_window_menu()
        self._create_help_menu()
        
    def _create_file_menu(self):
        """Create the File menu."""
        file_menu = self.menu_bar.addMenu("File")
        
        # Open Image
        open_action = QAction("Open Image...", self.parent_window)
        open_action.setShortcut(QKeySequence.Open)  # Cmd+O
        open_action.setStatusTip("Open an image file for processing")
        open_action.triggered.connect(self.open_file.emit)
        file_menu.addAction(open_action)
        
        # Open Folder
        open_folder_action = QAction("Open Folder...", self.parent_window)
        open_folder_action.setShortcut(QKeySequence("Cmd+Shift+O"))
        open_folder_action.setStatusTip("Open a folder of images for batch processing")
        open_folder_action.triggered.connect(self.open_folder.emit)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # Save As
        save_as_action = QAction("Save As...", self.parent_window)
        save_as_action.setShortcut(QKeySequence.SaveAs)  # Cmd+Shift+S
        save_as_action.setStatusTip("Save the processed image with a custom name")
        save_as_action.triggered.connect(self.save_as.emit)
        save_as_action.setEnabled(False)  # Enable when image is loaded
        self.save_as_action = save_as_action
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Recent Files submenu
        self.recent_menu = file_menu.addMenu("Open Recent")
        self.recent_menu.setEnabled(False)  # Enable when we have recent files
        self._update_recent_files([])  # Initialize empty
        
        file_menu.addSeparator()
        
        # Quit
        quit_action = QAction("Quit FootFix", self.parent_window)
        quit_action.setShortcut(QKeySequence.Quit)  # Cmd+Q
        quit_action.setStatusTip("Quit the application")
        quit_action.triggered.connect(self.quit_app.emit)
        file_menu.addAction(quit_action)
        
    def _create_edit_menu(self):
        """Create the Edit menu."""
        edit_menu = self.menu_bar.addMenu("Edit")
        
        # Undo (placeholder for future implementation)
        undo_action = QAction("Undo", self.parent_window)
        undo_action.setShortcut(QKeySequence.Undo)  # Cmd+Z
        undo_action.setEnabled(False)
        edit_menu.addAction(undo_action)
        
        # Redo (placeholder for future implementation)
        redo_action = QAction("Redo", self.parent_window)
        redo_action.setShortcut(QKeySequence.Redo)  # Cmd+Shift+Z
        redo_action.setEnabled(False)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Cut/Copy/Paste (for text fields)
        cut_action = QAction("Cut", self.parent_window)
        cut_action.setShortcut(QKeySequence.Cut)  # Cmd+X
        cut_action.triggered.connect(lambda: self._text_operation("cut"))
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("Copy", self.parent_window)
        copy_action.setShortcut(QKeySequence.Copy)  # Cmd+C
        copy_action.triggered.connect(lambda: self._text_operation("copy"))
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self.parent_window)
        paste_action.setShortcut(QKeySequence.Paste)  # Cmd+V
        paste_action.triggered.connect(lambda: self._text_operation("paste"))
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        # Select All
        select_all_action = QAction("Select All", self.parent_window)
        select_all_action.setShortcut(QKeySequence.SelectAll)  # Cmd+A
        select_all_action.triggered.connect(lambda: self._text_operation("selectAll"))
        edit_menu.addAction(select_all_action)
        
        edit_menu.addSeparator()
        
        # Preferences
        prefs_action = QAction("Preferences...", self.parent_window)
        prefs_action.setShortcut(QKeySequence("Cmd+,"))
        prefs_action.setStatusTip("Open application preferences")
        prefs_action.triggered.connect(self.show_preferences.emit)
        edit_menu.addAction(prefs_action)
        
    def _create_view_menu(self):
        """Create the View menu."""
        view_menu = self.menu_bar.addMenu("View")
        
        # Show Preview
        preview_action = QAction("Show Preview", self.parent_window)
        preview_action.setShortcut(QKeySequence("Space"))
        preview_action.setStatusTip("Show before/after preview")
        preview_action.triggered.connect(self.show_preview.emit)
        preview_action.setEnabled(False)  # Enable when image is loaded
        self.preview_action = preview_action
        view_menu.addAction(preview_action)
        
        view_menu.addSeparator()
        
        # Enter Full Screen
        fullscreen_action = QAction("Enter Full Screen", self.parent_window)
        fullscreen_action.setShortcut(QKeySequence("Cmd+Ctrl+F"))
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen.emit)
        view_menu.addAction(fullscreen_action)
        self.fullscreen_action = fullscreen_action
        
    def _create_window_menu(self):
        """Create the Window menu."""
        window_menu = self.menu_bar.addMenu("Window")
        
        # Minimize
        minimize_action = QAction("Minimize", self.parent_window)
        minimize_action.setShortcut(QKeySequence("Cmd+M"))
        minimize_action.triggered.connect(self.parent_window.showMinimized)
        window_menu.addAction(minimize_action)
        
        # Zoom
        zoom_action = QAction("Zoom", self.parent_window)
        zoom_action.triggered.connect(self._toggle_maximized)
        window_menu.addAction(zoom_action)
        
        window_menu.addSeparator()
        
        # Bring All to Front
        bring_all_action = QAction("Bring All to Front", self.parent_window)
        bring_all_action.triggered.connect(self._bring_all_to_front)
        window_menu.addAction(bring_all_action)
        
    def _create_help_menu(self):
        """Create the Help menu."""
        help_menu = self.menu_bar.addMenu("Help")
        
        # FootFix Help
        help_action = QAction("FootFix Help", self.parent_window)
        help_action.setShortcut(QKeySequence.HelpContents)  # Cmd+?
        help_action.setStatusTip("Show application help")
        help_action.triggered.connect(self.show_help.emit)
        help_menu.addAction(help_action)
        
        # Keyboard Shortcuts
        shortcuts_action = QAction("Keyboard Shortcuts", self.parent_window)
        shortcuts_action.setStatusTip("Show keyboard shortcuts reference")
        shortcuts_action.triggered.connect(self.show_shortcuts.emit)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        # Report an Issue
        report_action = QAction("Report an Issue...", self.parent_window)
        report_action.triggered.connect(self._report_issue)
        help_menu.addAction(report_action)
        
        help_menu.addSeparator()
        
        # About FootFix
        about_action = QAction("About FootFix", self.parent_window)
        about_action.setStatusTip("Show information about FootFix")
        about_action.triggered.connect(self.show_about.emit)
        help_menu.addAction(about_action)
        
    def _text_operation(self, operation):
        """Perform text operation on focused widget."""
        focused_widget = self.parent_window.focusWidget()
        if hasattr(focused_widget, operation):
            getattr(focused_widget, operation)()
            
    def _toggle_maximized(self):
        """Toggle window maximized state."""
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()
            
    def _bring_all_to_front(self):
        """Bring all application windows to front."""
        self.parent_window.raise_()
        self.parent_window.activateWindow()
        
    def _report_issue(self):
        """Open issue reporting page."""
        # For now, just show a message. In production, this would open a web page
        QMessageBox.information(
            self.parent_window,
            "Report an Issue",
            "To report an issue, please email:\nsupport@footfix.app\n\n"
            "Include:\n- Description of the issue\n- Steps to reproduce\n- Your macOS version"
        )
        
    def _update_recent_files(self, recent_files):
        """Update the recent files menu."""
        self.recent_menu.clear()
        
        if not recent_files:
            action = QAction("No Recent Files", self.parent_window)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
            return
            
        for i, file_path in enumerate(recent_files[:10]):  # Show max 10 recent files
            path = Path(file_path)
            action = QAction(f"{i+1}. {path.name}", self.parent_window)
            action.setStatusTip(str(path))
            action.triggered.connect(lambda checked, p=str(path): self._open_recent_file(p))
            
            # Add keyboard shortcut for first 9 items
            if i < 9:
                action.setShortcut(QKeySequence(f"Cmd+{i+1}"))
                
            self.recent_menu.addAction(action)
            
        self.recent_menu.addSeparator()
        
        # Clear Recent
        clear_action = QAction("Clear Menu", self.parent_window)
        clear_action.triggered.connect(self._clear_recent_files)
        self.recent_menu.addAction(clear_action)
        
        self.recent_menu.setEnabled(True)
        
    def _open_recent_file(self, file_path):
        """Open a recent file."""
        # This will be connected to the main window's load_image method
        self.parent_window.load_image(file_path)
        
    def _clear_recent_files(self):
        """Clear the recent files list."""
        # This will be implemented when we add preferences
        self._update_recent_files([])
        
    def update_fullscreen_text(self, is_fullscreen):
        """Update the fullscreen menu item text."""
        if is_fullscreen:
            self.fullscreen_action.setText("Exit Full Screen")
        else:
            self.fullscreen_action.setText("Enter Full Screen")
            
    def enable_image_actions(self, enabled=True):
        """Enable/disable actions that require an image."""
        self.save_as_action.setEnabled(enabled)
        self.preview_action.setEnabled(enabled)