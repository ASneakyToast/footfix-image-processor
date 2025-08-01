"""
Preview widget for before/after image comparison.
Provides side-by-side comparison with zoom and file size information.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import io

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QGroupBox, QSplitter, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint, QRect
from PySide6.QtGui import QPixmap, QPainter, QWheelEvent, QMouseEvent, QResizeEvent
from PIL import Image

from ..core.processor import ImageProcessor
from ..presets.profiles import PresetProfile

logger = logging.getLogger(__name__)


class ZoomableImageLabel(QLabel):
    """Custom QLabel that supports zoom and pan functionality."""
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setScaledContents(False)
        self._zoom = 1.0
        self._empty = True
        self._pixmap = None
        self._pan_start = None
        self._pan_offset = QPoint(0, 0)
        
    def setPixmap(self, pixmap: QPixmap):
        """Set the pixmap and reset zoom/pan."""
        self._pixmap = pixmap
        self._empty = False
        self._zoom = 1.0
        self._pan_offset = QPoint(0, 0)
        self.update()
        
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        if self._empty or not self._pixmap:
            return
            
        # Get the position of the mouse relative to the widget
        pos = event.position().toPoint()
        
        # Calculate zoom factor
        delta = event.angleDelta().y()
        zoom_in = delta > 0
        zoom_factor = 1.1 if zoom_in else 0.9
        
        # Limit zoom range
        new_zoom = self._zoom * zoom_factor
        if 0.1 <= new_zoom <= 5.0:
            self._zoom = new_zoom
            self.update()
            
    def mousePressEvent(self, event: QMouseEvent):
        """Start panning on mouse press."""
        if event.button() == Qt.LeftButton and self._pixmap:
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle panning while mouse is pressed."""
        if self._pan_start is not None:
            delta = event.pos() - self._pan_start
            self._pan_offset += delta
            self._pan_start = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop panning on mouse release."""
        if event.button() == Qt.LeftButton:
            self._pan_start = None
            self.setCursor(Qt.ArrowCursor)
            
    def paintEvent(self, event):
        """Custom paint event to handle zoom and pan."""
        if self._empty or not self._pixmap:
            super().paintEvent(event)
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Calculate scaled size
        scaled_size = self._pixmap.size() * self._zoom
        
        # Calculate position (centered with pan offset)
        x = (self.width() - scaled_size.width()) / 2 + self._pan_offset.x()
        y = (self.height() - scaled_size.height()) / 2 + self._pan_offset.y()
        
        # Draw the scaled pixmap
        target_rect = QRect(int(x), int(y), int(scaled_size.width()), int(scaled_size.height()))
        painter.drawPixmap(target_rect, self._pixmap)
        
    def reset_view(self):
        """Reset zoom and pan to default."""
        self._zoom = 1.0
        self._pan_offset = QPoint(0, 0)
        self.update()
        
    def fit_to_window(self):
        """Fit the image to the window size."""
        if not self._pixmap:
            return
            
        # Calculate zoom to fit
        widget_size = self.size()
        pixmap_size = self._pixmap.size()
        
        zoom_x = widget_size.width() / pixmap_size.width()
        zoom_y = widget_size.height() / pixmap_size.height()
        
        self._zoom = min(zoom_x, zoom_y) * 0.95  # 95% to leave some margin
        self._pan_offset = QPoint(0, 0)
        self.update()


class PreviewWidget(QWidget):
    """Widget for displaying before/after image comparison."""
    
    # Signals
    apply_settings = Signal()  # User wants to apply current settings
    adjust_settings = Signal()  # User wants to adjust settings
    
    def __init__(self):
        super().__init__()
        self.processor = None
        self.current_preset = None
        self.original_pixmap = None
        self.preview_pixmap = None
        self.original_file_size = 0
        self.estimated_file_size = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Before/After Preview")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.addStretch()
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)  # 10% to 500%
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setTickInterval(50)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        
        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("100%")
        zoom_layout.addWidget(self.zoom_label)
        
        self.fit_button = QPushButton("Fit to Window")
        self.fit_button.clicked.connect(self.fit_to_window)
        zoom_layout.addWidget(self.fit_button)
        
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.reset_view)
        zoom_layout.addWidget(self.reset_button)
        
        zoom_layout.addStretch()
        layout.addLayout(zoom_layout)
        
        # Image comparison area
        splitter = QSplitter(Qt.Horizontal)
        
        # Before (Original) side
        before_group = QGroupBox("Original")
        before_layout = QVBoxLayout()
        
        self.before_scroll = QScrollArea()
        self.before_image = ZoomableImageLabel()
        self.before_image.setAlignment(Qt.AlignCenter)
        self.before_image.setMinimumSize(400, 300)
        self.before_scroll.setWidget(self.before_image)
        self.before_scroll.setWidgetResizable(True)
        before_layout.addWidget(self.before_scroll)
        
        self.before_info = QLabel("No image loaded")
        self.before_info.setAlignment(Qt.AlignCenter)
        before_layout.addWidget(self.before_info)
        
        before_group.setLayout(before_layout)
        splitter.addWidget(before_group)
        
        # After (Preview) side
        after_group = QGroupBox("Preview")
        after_layout = QVBoxLayout()
        
        self.after_scroll = QScrollArea()
        self.after_image = ZoomableImageLabel()
        self.after_image.setAlignment(Qt.AlignCenter)
        self.after_image.setMinimumSize(400, 300)
        self.after_scroll.setWidget(self.after_image)
        self.after_scroll.setWidgetResizable(True)
        after_layout.addWidget(self.after_scroll)
        
        self.after_info = QLabel("No preview generated")
        self.after_info.setAlignment(Qt.AlignCenter)
        after_layout.addWidget(self.after_info)
        
        after_group.setLayout(after_layout)
        splitter.addWidget(after_group)
        
        layout.addWidget(splitter)
        
        # Comparison info
        info_group = QGroupBox("Comparison")
        info_layout = QHBoxLayout()
        
        self.size_reduction_label = QLabel("Size Reduction: N/A")
        info_layout.addWidget(self.size_reduction_label)
        
        info_layout.addStretch()
        
        self.dimension_change_label = QLabel("Dimension Change: N/A")
        info_layout.addWidget(self.dimension_change_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.adjust_button = QPushButton("Adjust Settings")
        self.adjust_button.clicked.connect(self.adjust_settings.emit)
        self.adjust_button.setEnabled(False)
        button_layout.addWidget(self.adjust_button)
        
        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.clicked.connect(self.apply_settings.emit)
        self.apply_button.setEnabled(False)
        self.apply_button.setStyleSheet("""
            QPushButton:enabled {
                background-color: #007AFF;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
        """)
        button_layout.addWidget(self.apply_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
    def load_image(self, processor: ImageProcessor, preset: PresetProfile):
        """Load an image for preview comparison."""
        self.processor = processor
        self.current_preset = preset
        
        if not processor.current_image:
            return
            
        # Get original image info
        original_info = processor.get_image_info()
        
        # Convert PIL image to QPixmap for display
        self.original_pixmap = self._pil_to_pixmap(processor.current_image)
        self.before_image.setPixmap(self.original_pixmap)
        
        # Get file size if source path exists
        if processor.source_path and processor.source_path.exists():
            self.original_file_size = processor.source_path.stat().st_size
            size_mb = self.original_file_size / (1024 * 1024)
            self.before_info.setText(
                f"Dimensions: {original_info['width']}×{original_info['height']}px\n"
                f"File Size: {size_mb:.2f} MB"
            )
        else:
            self.before_info.setText(
                f"Dimensions: {original_info['width']}×{original_info['height']}px"
            )
            
        # Generate preview
        self.generate_preview()
        
        # Enable buttons
        self.adjust_button.setEnabled(True)
        self.apply_button.setEnabled(True)
        
    def generate_preview(self):
        """Generate a preview of the processed image without saving."""
        if not self.processor or not self.current_preset:
            return
            
        try:
            # Create a copy of the processor to avoid modifying the original
            preview_processor = ImageProcessor()
            preview_processor.current_image = self.processor.current_image.copy()
            preview_processor.original_image = self.processor.original_image.copy()
            
            # Apply preset to the copy
            self.current_preset.process(preview_processor)
            
            # Get preview info
            preview_info = preview_processor.get_image_info()
            
            # Convert to pixmap
            self.preview_pixmap = self._pil_to_pixmap(preview_processor.current_image)
            self.after_image.setPixmap(self.preview_pixmap)
            
            # Estimate file size
            buffer = io.BytesIO()
            output_config = self.current_preset.get_output_config()
            
            if output_config.get('format', 'JPEG').upper() == 'JPEG':
                preview_processor.current_image.save(
                    buffer, 
                    format='JPEG', 
                    quality=output_config.get('quality', 85),
                    optimize=True
                )
            else:
                preview_processor.current_image.save(
                    buffer,
                    format=output_config.get('format', 'JPEG'),
                    optimize=True
                )
                
            self.estimated_file_size = buffer.tell()
            size_mb = self.estimated_file_size / (1024 * 1024)
            
            # Update preview info
            self.after_info.setText(
                f"Dimensions: {preview_info['width']}×{preview_info['height']}px\n"
                f"Estimated Size: {size_mb:.2f} MB"
            )
            
            # Update comparison info
            if self.original_file_size > 0:
                reduction = (1 - self.estimated_file_size / self.original_file_size) * 100
                self.size_reduction_label.setText(f"Size Reduction: {reduction:.1f}%")
            
            original_info = self.processor.get_image_info()
            width_change = preview_info['width'] / original_info['width'] * 100
            height_change = preview_info['height'] / original_info['height'] * 100
            
            self.dimension_change_label.setText(
                f"Dimensions: {width_change:.0f}% × {height_change:.0f}%"
            )
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            self.after_info.setText(f"Error generating preview: {str(e)}")
            
    def _pil_to_pixmap(self, pil_image: Image.Image) -> QPixmap:
        """Convert PIL Image to QPixmap."""
        # Convert PIL image to bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Create QPixmap from bytes
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return pixmap
        
    def on_zoom_changed(self, value: int):
        """Handle zoom slider changes."""
        zoom = value / 100.0
        self.zoom_label.setText(f"{value}%")
        
        # Apply zoom to both images
        if self.before_image._pixmap:
            self.before_image._zoom = zoom
            self.before_image.update()
            
        if self.after_image._pixmap:
            self.after_image._zoom = zoom
            self.after_image.update()
            
    def fit_to_window(self):
        """Fit both images to their respective windows."""
        self.before_image.fit_to_window()
        self.after_image.fit_to_window()
        
        # Update slider to match
        if self.before_image._pixmap:
            self.zoom_slider.setValue(int(self.before_image._zoom * 100))
            
    def reset_view(self):
        """Reset zoom and pan for both images."""
        self.before_image.reset_view()
        self.after_image.reset_view()
        self.zoom_slider.setValue(100)
        
    def clear_preview(self):
        """Clear the preview display."""
        self.before_image.clear()
        self.after_image.clear()
        self.before_info.setText("No image loaded")
        self.after_info.setText("No preview generated")
        self.size_reduction_label.setText("Size Reduction: N/A")
        self.dimension_change_label.setText("Dimension Change: N/A")
        self.adjust_button.setEnabled(False)
        self.apply_button.setEnabled(False)