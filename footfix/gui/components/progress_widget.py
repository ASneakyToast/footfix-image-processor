"""
Progress Display Widget for FootFix.
Extracted from UnifiedProcessingWidget to handle progress tracking and time estimation.
"""

import logging
from datetime import timedelta
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QProgressBar, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, Signal, QTimer

from ...core.batch_processor import BatchProgress

logger = logging.getLogger(__name__)


class ProgressDisplayWidget(QWidget):
    """
    Dedicated widget for displaying processing progress.
    Handles progress bars, time estimation, and status updates.
    """
    
    # Signals
    progress_visibility_changed = Signal(bool)  # Whether progress area is visible
    
    def __init__(self, parent=None):
        """Initialize the progress display widget."""
        super().__init__(parent)
        self.is_processing = False
        self.start_time = 0.0
        
        # Timer for UI updates during processing
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_display)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the progress display UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Progress group (initially hidden)
        self.progress_group = QGroupBox("Processing Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        # Overall progress
        self.overall_progress_label = QLabel("Ready to process")
        progress_layout.addWidget(self.overall_progress_label)
        
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setTextVisible(True)
        self.overall_progress_bar.setMinimum(0)
        self.overall_progress_bar.setMaximum(100)
        self.overall_progress_bar.setValue(0)
        progress_layout.addWidget(self.overall_progress_bar)
        
        # Current item progress
        self.current_item_label = QLabel("")
        self.current_item_label.setVisible(False)
        progress_layout.addWidget(self.current_item_label)
        
        # Time estimation
        time_layout = QHBoxLayout()
        self.elapsed_label = QLabel("Elapsed: --:--")
        time_layout.addWidget(self.elapsed_label)
        
        time_layout.addStretch()
        
        self.remaining_label = QLabel("Remaining: --:--")
        time_layout.addWidget(self.remaining_label)
        
        progress_layout.addLayout(time_layout)
        
        # Initially hidden
        self.progress_group.setVisible(False)
        main_layout.addWidget(self.progress_group)
        
    def show_progress(self):
        """Show the progress area and start processing display."""
        self.is_processing = True
        self.progress_group.setVisible(True)
        self.overall_progress_bar.setValue(0)
        self.current_item_label.setVisible(True)
        self.update_timer.start(100)  # Update every 100ms
        
        # Reset labels
        self.overall_progress_label.setText("Starting processing...")
        self.current_item_label.setText("")
        self.elapsed_label.setText("Elapsed: 00:00")
        self.remaining_label.setText("Remaining: --:--")
        
        self.progress_visibility_changed.emit(True)
        logger.info("Progress display shown")
        
    def hide_progress(self):
        """Hide the progress area and stop processing display."""
        self.is_processing = False
        self.progress_group.setVisible(False)
        self.current_item_label.setVisible(False)
        self.update_timer.stop()
        
        self.progress_visibility_changed.emit(False)
        logger.info("Progress display hidden")
        
    def update_progress(self, progress: BatchProgress):
        """
        Update the progress display with current batch progress.
        
        Args:
            progress: BatchProgress object with current processing state
        """
        if not self.is_processing:
            return
            
        # Update progress bar
        if progress.total_items > 0:
            completed_count = progress.completed_items + progress.failed_items
            percentage = (completed_count / progress.total_items) * 100
            self.overall_progress_bar.setValue(int(percentage))
            
            # Update progress bar text to show actual numbers
            self.overall_progress_bar.setFormat(f"{completed_count}/{progress.total_items} (%p%)")
        
        # Update overall progress label
        status_parts = []
        if progress.is_cancelled:
            status_parts.append("Cancelling...")
        else:
            status_parts.append(f"Processing {progress.current_item_index + 1} of {progress.total_items}")
            
        if progress.completed_items > 0:
            status_parts.append(f"{progress.completed_items} completed")
            
        if progress.failed_items > 0:
            status_parts.append(f"{progress.failed_items} failed")
            
        self.overall_progress_label.setText(" - ".join(status_parts))
        
        # Update current item label
        if progress.current_item_name and not progress.is_cancelled:
            self.current_item_label.setText(f"Current: {progress.current_item_name}")
        elif progress.is_cancelled:
            self.current_item_label.setText("Cancelling processing...")
        else:
            self.current_item_label.setText("")
            
        # Update time displays
        if progress.elapsed_time > 0:
            self.elapsed_label.setText(f"Elapsed: {self._format_time(progress.elapsed_time)}")
            
        if progress.estimated_time_remaining > 0:
            self.remaining_label.setText(f"Remaining: {self._format_time(progress.estimated_time_remaining)}")
        else:
            self.remaining_label.setText("Remaining: Calculating...")
            
    def update_time_display(self):
        """Update time display during processing (called by timer)."""
        # This method can be used for real-time time updates if needed
        # Currently the main updates come from update_progress()
        pass
        
    def set_completion_state(self, success: bool, cancelled: bool = False):
        """
        Set the progress display to show completion state.
        
        Args:
            success: Whether processing completed successfully
            cancelled: Whether processing was cancelled
        """
        self.update_timer.stop()
        
        if cancelled:
            self.overall_progress_label.setText("Processing cancelled")
            self.current_item_label.setText("Operation was cancelled by user")
        elif success:
            self.overall_progress_label.setText("Processing completed successfully")
            self.current_item_label.setText("All items processed")
            self.overall_progress_bar.setValue(100)
        else:
            self.overall_progress_label.setText("Processing completed with errors")
            self.current_item_label.setText("Some items failed to process")
            
        logger.info(f"Progress completion state set: success={success}, cancelled={cancelled}")
        
    def set_error_state(self, error_message: str):
        """
        Set the progress display to show an error state.
        
        Args:
            error_message: Error message to display
        """
        self.update_timer.stop()
        self.overall_progress_label.setText("Processing failed")
        self.current_item_label.setText(f"Error: {error_message}")
        
        logger.error(f"Progress error state set: {error_message}")
        
    def reset(self):
        """Reset the progress display to initial state."""
        self.update_timer.stop()
        self.is_processing = False
        
        self.overall_progress_bar.setValue(0)
        self.overall_progress_bar.setFormat("%p%")  # Reset to default format
        self.overall_progress_label.setText("Ready to process")
        self.current_item_label.setText("")
        self.elapsed_label.setText("Elapsed: --:--")
        self.remaining_label.setText("Remaining: --:--")
        
        self.current_item_label.setVisible(False)
        self.progress_group.setVisible(False)
        
        self.progress_visibility_changed.emit(False)
        logger.info("Progress display reset")
        
    def is_visible(self) -> bool:
        """Check if the progress area is currently visible."""
        return self.progress_group.isVisible()
        
    def get_progress_summary(self) -> str:
        """Get a text summary of current progress."""
        if not self.is_processing:
            return "Not processing"
            
        return self.overall_progress_label.text()
        
    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to human-readable string.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string (e.g., "1:30", "0:05", "1:23:45")
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        else:
            td = timedelta(seconds=int(seconds))
            # Format as H:MM:SS or M:SS
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            
            if hours > 0:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes}:{secs:02d}"
                
    def set_enabled(self, enabled: bool):
        """Enable or disable the progress display."""
        self.progress_group.setEnabled(enabled)