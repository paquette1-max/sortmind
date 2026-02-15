"""
Progress dialog for long-running operations.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

import logging

logger = logging.getLogger(__name__)


class ProgressDialog(QDialog):
    """Dialog showing operation progress."""
    
    cancel_requested = pyqtSignal()
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self._setup_ui()
        # Default to non-cancelable until UI is created
        self.set_cancelable(False)
        logger.info(f"Progress dialog created: {title}")
    
    def _setup_ui(self):
        """Setup progress bar, labels, cancel button."""
        layout = QVBoxLayout()
        
        # Title label
        self.title_label = QLabel("Processing...")
        self.title_label.setObjectName("progressTitle")
        layout.addWidget(self.title_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("progressStatus")
        layout.addWidget(self.status_label)
        
        # File label
        self.file_label = QLabel("")
        self.file_label.setObjectName("progressFile")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_btn)
        
        self.setLayout(layout)
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress display."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.status_label.setText(f"{current} / {total}")
        
        if message:
            self.file_label.setText(message)
    
    def set_title(self, title: str):
        """Set title label."""
        self.title_label.setText(title)
        # Also update the window title so tests observing windowTitle() see change
        self.setWindowTitle(title)
    
    def set_cancelable(self, cancelable: bool):
        """Set whether operation can be canceled."""
        self.cancel_btn.setEnabled(cancelable)
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancel_requested.emit()
        logger.info("Cancel requested by user")


class SimpleProgressDialog(QDialog):
    """Simple progress dialog with just a message."""
    
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing")
        self.setModal(True)
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def set_message(self, message: str):
        """Update message."""
        self.label.setText(message)
