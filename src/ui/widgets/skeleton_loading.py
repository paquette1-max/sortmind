"""
Skeleton loading widget for displaying placeholder content during loading.
Provides a better perceived performance experience than traditional spinners.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QBrush

import logging

logger = logging.getLogger(__name__)


class SkeletonLine(QFrame):
    """A single skeleton loading line with shimmer effect."""
    
    def __init__(self, width_percent=100, height=12, parent=None):
        super().__init__(parent)
        self.width_percent = width_percent
        self.line_height = height
        self.shimmer_offset = 0
        self.animation_active = False
        
        self.setObjectName("skeletonLine")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
        
        # Setup shimmer animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_shimmer)
    
    def start_animation(self):
        """Start the shimmer animation."""
        self.animation_active = True
        self.timer.start(30)  # ~33fps
        logger.debug("Skeleton animation started")
    
    def stop_animation(self):
        """Stop the shimmer animation."""
        self.animation_active = False
        self.timer.stop()
        logger.debug("Skeleton animation stopped")
    
    def _update_shimmer(self):
        """Update shimmer offset for animation."""
        self.shimmer_offset += 5
        if self.shimmer_offset > self.width() + 100:
            self.shimmer_offset = -100
        self.update()
    
    def paintEvent(self, event):
        """Custom paint with shimmer gradient."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate actual width based on percentage
        actual_width = int(self.width() * self.width_percent / 100)
        
        # Base background color
        base_color = QColor("#262626")
        painter.fillRect(0, 0, actual_width, self.height(), base_color)
        
        # Shimmer gradient
        if self.animation_active:
            gradient = QLinearGradient(
                self.shimmer_offset, 0,
                self.shimmer_offset + 100, 0
            )
            gradient.setColorAt(0, QColor("#262626"))
            gradient.setColorAt(0.5, QColor("#333333"))
            gradient.setColorAt(1, QColor("#262626"))
            
            brush = QBrush(gradient)
            painter.fillRect(0, 0, actual_width, self.height(), brush)
        
        painter.end()


class SkeletonBlock(QWidget):
    """A block of skeleton lines representing content."""
    
    def __init__(self, line_count=3, line_heights=None, 
                 line_widths=None, spacing=8, parent=None):
        super().__init__(parent)
        self.line_count = line_count
        self.line_heights = line_heights or [12] * line_count
        self.line_widths = line_widths or [100] * line_count
        self.line_spacing = spacing
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup skeleton lines."""
        layout = QVBoxLayout(self)
        layout.setSpacing(self.line_spacing)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.lines = []
        for i in range(self.line_count):
            height = self.line_heights[i] if i < len(self.line_heights) else 12
            width = self.line_widths[i] if i < len(self.line_widths) else 100
            
            line = SkeletonLine(width_percent=width, height=height)
            layout.addWidget(line)
            self.lines.append(line)
        
        self.setLayout(layout)
    
    def start_animation(self):
        """Start shimmer animation for all lines."""
        for line in self.lines:
            line.start_animation()
    
    def stop_animation(self):
        """Stop shimmer animation for all lines."""
        for line in self.lines:
            line.stop_animation()


class SkeletonTableRow(QWidget):
    """A skeleton row resembling a table row."""
    
    def __init__(self, column_widths=None, parent=None):
        super().__init__(parent)
        self.column_widths = column_widths or [30, 25, 25, 10, 10]
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup row with columns."""
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 8, 12, 8)
        
        self.lines = []
        for width in self.column_widths:
            line = SkeletonLine(width_percent=width, height=12)
            layout.addWidget(line, width)
            self.lines.append(line)
        
        self.setLayout(layout)
        self.setMinimumHeight(40)
    
    def start_animation(self):
        """Start shimmer animation."""
        for line in self.lines:
            line.start_animation()
    
    def stop_animation(self):
        """Stop shimmer animation."""
        for line in self.lines:
            line.stop_animation()


class SkeletonLoadingWidget(QWidget):
    """
    Full skeleton loading widget for showing loading states.
    
    Features:
    - Multiple layout presets (table, form, card)
    - Animated shimmer effect
    - Accessible loading announcements
    - Configurable row/column counts
    """
    
    finished = pyqtSignal()
    
    # Preset configurations
    PRESETS = {
        'table': {
            'header': True,
            'row_count': 6,
            'columns': [30, 20, 25, 10, 15]
        },
        'form': {
            'header': False,
            'blocks': [
                {'lines': 2, 'heights': [16, 40], 'widths': [100, 100]},
                {'lines': 2, 'heights': [16, 40], 'widths': [100, 100]},
                {'lines': 2, 'heights': [16, 40], 'widths': [100, 100]},
            ]
        },
        'card': {
            'header': True,
            'blocks': [
                {'lines': 3, 'heights': [20, 12, 12], 'widths': [60, 100, 80]},
            ]
        },
        'list': {
            'header': False,
            'row_count': 8,
            'columns': [100]
        }
    }
    
    def __init__(self, preset='table', parent=None):
        super().__init__(parent)
        self.preset = preset
        self.animation_active = False
        
        self._setup_ui()
        logger.debug(f"SkeletonLoadingWidget initialized with preset: {preset}")
    
    def _setup_ui(self):
        """Setup skeleton UI based on preset."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        
        config = self.PRESETS.get(self.preset, self.PRESETS['table'])
        
        # Add header if configured
        if config.get('header', False):
            header = SkeletonBlock(
                line_count=1,
                line_heights=[16],
                line_widths=[40]
            )
            layout.addWidget(header)
            layout.addSpacing(16)
        
        # Add rows for table/list presets
        if 'row_count' in config:
            self.rows = []
            for i in range(config['row_count']):
                if self.preset == 'table':
                    row = SkeletonTableRow(column_widths=config['columns'])
                else:
                    row = SkeletonBlock(
                        line_count=1,
                        line_heights=[12],
                        line_widths=[90]
                    )
                layout.addWidget(row)
                self.rows.append(row)
                
                # Add separator
                if i < config['row_count'] - 1:
                    separator = QFrame()
                    separator.setFrameShape(QFrame.Shape.HLine)
                    separator.setStyleSheet("background-color: #262626;")
                    separator.setMaximumHeight(1)
                    layout.addWidget(separator)
        
        # Add blocks for form/card presets
        elif 'blocks' in config:
            self.blocks = []
            for block_config in config['blocks']:
                block = SkeletonBlock(
                    line_count=block_config['lines'],
                    line_heights=block_config.get('heights'),
                    line_widths=block_config.get('widths'),
                    spacing=8
                )
                layout.addWidget(block)
                self.blocks.append(block)
                layout.addSpacing(24)
        
        # Loading text
        self.status_label = QLabel("Loading...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("skeletonStatusLabel")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Set accessible description for screen readers
        self.setAccessibleName("Loading content")
        self.setAccessibleDescription("Please wait while content is loading")
    
    def start(self, message: str = "Loading..."):
        """
        Start the skeleton loading animation.
        
        Args:
            message: Status message to display
        """
        self.status_label.setText(message)
        self.animation_active = True
        
        # Start animation on all child widgets
        for child in self.findChildren(SkeletonLine):
            child.start_animation()
        
        self.setVisible(True)
        logger.debug(f"Skeleton loading started: {message}")
    
    def stop(self):
        """Stop the skeleton loading animation."""
        self.animation_active = False
        
        # Stop animation on all child widgets
        for child in self.findChildren(SkeletonLine):
            child.stop_animation()
        
        self.setVisible(False)
        self.finished.emit()
        logger.debug("Skeleton loading stopped")
    
    def set_message(self, message: str):
        """Update the loading message."""
        self.status_label.setText(message)
        # Update accessible description for screen readers
        self.setAccessibleDescription(message)
    
    def is_animating(self) -> bool:
        """Check if animation is currently active."""
        return self.animation_active


class SkeletonOverlay(QWidget):
    """
    An overlay that shows skeleton loading on top of existing content.
    Useful for refresh operations on already-loaded data.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("skeletonOverlay")
        
        # Make it fill the parent
        if parent:
            self.setGeometry(parent.rect())
        
        # Semi-transparent background
        self.setStyleSheet("""
            #skeletonOverlay {
                background-color: rgba(15, 15, 15, 0.8);
            }
        """)
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add skeleton widget
        self.skeleton = SkeletonLoadingWidget(preset='table')
        layout.addWidget(self.skeleton)
        
        self.setLayout(layout)
        self.hide()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.skeleton.start()
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        self.skeleton.stop()
    
    def set_message(self, message: str):
        """Update loading message."""
        self.skeleton.set_message(message)
