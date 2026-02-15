"""
File preview panel widget for PyQt6.
Displays file content preview before organizing.
"""
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QColor

import logging

try:
    from ...core.preview import PreviewManager, FilePreview, PreviewType
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.preview import PreviewManager, FilePreview, PreviewType

logger = logging.getLogger(__name__)


class PreviewPanel(QWidget):
    """Panel for displaying file preview content."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preview_manager = PreviewManager()
        self.current_preview: Optional[FilePreview] = None
        
        self._setup_ui()
        logger.info("Preview panel initialized")
    
    def _setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header with file info
        self.header_label = QLabel("No file selected")
        self.header_label.setObjectName("previewHeader")
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)
        
        # Metadata info
        self.metadata_label = QLabel("")
        self.metadata_label.setObjectName("previewMetadata")
        self.metadata_label.setWordWrap(True)
        layout.addWidget(self.metadata_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("previewSeparator")
        layout.addWidget(separator)
        
        # Preview content area (scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("previewScrollArea")
        
        # Container for preview content
        self.preview_container = QWidget()
        self.preview_container.setObjectName("previewContainer")
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # Text preview
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setFont(QFont("JetBrains Mono, Consolas, monospace", 10))
        self.text_preview.setObjectName("previewTextEdit")
        self.preview_layout.addWidget(self.text_preview)
        
        # Image preview label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setObjectName("previewImageLabel")
        self.image_label.setVisible(False)
        self.preview_layout.addWidget(self.image_label)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setObjectName("previewErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        self.preview_layout.addWidget(self.error_label)
        
        self.scroll_area.setWidget(self.preview_container)
        layout.addWidget(self.scroll_area, 1)  # Give it stretch
        
        # Preview type indicator
        self.type_label = QLabel("")
        self.type_label.setObjectName("previewTypeLabel")
        layout.addWidget(self.type_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
    
    def preview_file(self, file_path: Optional[Path]):
        """
        Generate and display preview for a file.
        
        Args:
            file_path: Path to the file to preview
        """
        if file_path is None:
            self._show_no_selection()
            return
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            self._show_error(f"File not found: {file_path}")
            return
        
        try:
            self.current_preview = self.preview_manager.get_preview(file_path)
            self._display_preview()
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            self._show_error(f"Failed to generate preview: {e}")
    
    def _display_preview(self):
        """Display the current preview."""
        if not self.current_preview:
            self._show_no_selection()
            return
        
        preview = self.current_preview
        
        # Update header
        self.header_label.setText(f"📄 {preview.file_path.name}")
        
        # Update metadata
        metadata_text = self._format_metadata(preview.metadata)
        self.metadata_label.setText(metadata_text)
        
        # Hide all content widgets first
        self.text_preview.setVisible(False)
        self.image_label.setVisible(False)
        self.error_label.setVisible(False)
        
        # Show error if present
        if preview.error:
            self.error_label.setText(f"⚠️ {preview.error}")
            self.error_label.setVisible(True)
        
        # Display based on preview type
        if preview.preview_type == PreviewType.IMAGE:
            self._display_image_preview()
        else:
            self._display_text_preview()
        
        # Update type label
        type_names = {
            PreviewType.TEXT: "Text File",
            PreviewType.IMAGE: "Image",
            PreviewType.PDF: "PDF Document",
            PreviewType.DOCUMENT: "Document",
            PreviewType.UNKNOWN: "Unknown Type"
        }
        self.type_label.setText(f"Type: {type_names.get(preview.preview_type, 'Unknown')}")
    
    def _display_text_preview(self):
        """Display text-based preview."""
        if not self.current_preview:
            return
        
        content = self.current_preview.preview_content
        self.text_preview.setPlainText(content)
        self.text_preview.setVisible(True)
    
    def _display_image_preview(self):
        """Display image preview."""
        if not self.current_preview:
            return
        
        file_path = self.current_preview.file_path
        
        try:
            # Try to load and display the image
            pixmap = QPixmap(str(file_path))
            
            if not pixmap.isNull():
                # Scale to fit while maintaining aspect ratio
                max_width = 400
                max_height = 300
                scaled_pixmap = pixmap.scaled(
                    max_width, max_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setVisible(True)
            else:
                # Fallback to text preview if image can't be loaded
                self._display_text_preview()
                
        except Exception as e:
            logger.warning(f"Failed to display image preview: {e}")
            self._display_text_preview()
    
    def _format_metadata(self, metadata: Optional[dict]) -> str:
        """Format metadata for display."""
        if not metadata:
            return ""
        
        parts = []
        
        if 'size_human' in metadata:
            parts.append(f"Size: {metadata['size_human']}")
        
        if 'width' in metadata and 'height' in metadata:
            parts.append(f"Dimensions: {metadata['width']}×{metadata['height']}")
        
        if 'format' in metadata:
            parts.append(f"Format: {metadata['format']}")
        
        if 'page_count' in metadata:
            parts.append(f"Pages: {metadata['page_count']}")
        
        if 'line_count' in metadata:
            parts.append(f"Lines: {metadata['line_count']}")
        
        if 'date_taken' in metadata:
            parts.append(f"Taken: {metadata['date_taken']}")
        
        return " | ".join(parts) if parts else ""
    
    def _show_no_selection(self):
        """Show 'no selection' state."""
        self.header_label.setText("No file selected")
        self.metadata_label.setText("Select a file to preview its contents")
        self.text_preview.setPlainText("")
        self.text_preview.setVisible(True)
        self.image_label.setVisible(False)
        self.error_label.setVisible(False)
        self.type_label.setText("")
    
    def _show_error(self, message: str):
        """Show error state."""
        self.header_label.setText("Error")
        self.metadata_label.setText("")
        self.text_preview.setVisible(False)
        self.image_label.setVisible(False)
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        self.type_label.setText("")
    
    def clear_preview(self):
        """Clear the current preview."""
        self.current_preview = None
        self._show_no_selection()
    
    def get_current_preview(self) -> Optional[FilePreview]:
        """Get the current preview object."""
        return self.current_preview
