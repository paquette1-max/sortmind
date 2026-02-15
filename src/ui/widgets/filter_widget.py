"""
Filter widget for ResultsTable with smart filtering capabilities.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QComboBox, 
    QPushButton, QLabel, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

import fnmatch
import logging

logger = logging.getLogger(__name__)


class SmartFilterWidget(QWidget):
    """
    Smart filter widget for filtering results table.
    
    Features:
    - Wildcard pattern matching (*.pdf, *report*)
    - File type filtering
    - Confidence level filtering
    - Category filtering
    """
    
    filter_changed = pyqtSignal()  # Emitted when filter changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        logger.info("SmartFilterWidget initialized")
    
    def _setup_ui(self):
        """Setup filter UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Search/Pattern filter
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("🔍 Filter files... (*.pdf, *report*, etc.)")
        self.pattern_input.setToolTip(
            "Filter files by name pattern:\n"
            "- *.pdf - all PDF files\n"
            "- *report* - files with 'report' in name\n"
            "- 2024* - files starting with '2024'\n"
            "Leave empty to show all files"
        )
        self.pattern_input.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self.pattern_input, 2)
        
        # File type filter
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types", "")
        self.type_filter.addItem("📄 Documents (.pdf, .doc, .txt)", "document")
        self.type_filter.addItem("🖼️ Images (.jpg, .png, .gif)", "image")
        self.type_filter.addItem("💻 Code (.py, .js, .html)", "code")
        self.type_filter.addItem("📊 Data (.csv, .json, .xlsx)", "data")
        self.type_filter.addItem("🎵 Audio (.mp3, .wav)", "audio")
        self.type_filter.addItem("🎬 Video (.mp4, .avi)", "video")
        self.type_filter.addItem("📦 Archives (.zip, .rar)", "archive")
        self.type_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.type_filter, 1)
        
        # Confidence filter
        self.confidence_filter = QComboBox()
        self.confidence_filter.addItem("All Confidence", 0.0)
        self.confidence_filter.addItem("✓ High (85%+)", 0.85)
        self.confidence_filter.addItem("⚠ Medium+ (70%+)", 0.70)
        self.confidence_filter.addItem("❓ All Review (<85%)", -1.0)
        self.confidence_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.confidence_filter, 1)
        
        # Sort by
        self.sort_by = QComboBox()
        self.sort_by.addItem("Sort by: Name", "name")
        self.sort_by.addItem("Sort by: Type", "type")
        self.sort_by.addItem("Sort by: Confidence", "confidence")
        self.sort_by.addItem("Sort by: Category", "category")
        self.sort_by.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.sort_by, 1)
        
        # Clear filters button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear all filters")
        self.clear_btn.clicked.connect(self.clear_filters)
        layout.addWidget(self.clear_btn)
        
        # Selection actions
        self.select_menu = QPushButton("Select ▼")
        self.select_menu.setToolTip("Selection actions")
        
        select_menu = QMenu(self)
        select_all = QAction("Select All Visible", self)
        select_all.triggered.connect(lambda: self._select_action.emit("all_visible"))
        select_menu.addAction(select_all)
        
        select_none = QAction("Clear Selection", self)
        select_none.triggered.connect(lambda: self._select_action.emit("none"))
        select_menu.addAction(select_none)
        
        select_menu.addSeparator()
        
        select_high_conf = QAction("Select High Confidence (85%+)", self)
        select_high_conf.triggered.connect(lambda: self._select_action.emit("high_conf"))
        select_menu.addAction(select_high_conf)
        
        select_by_type = QAction("Select by Type...", self)
        select_by_type.triggered.connect(lambda: self._select_action.emit("by_type"))
        select_menu.addAction(select_by_type)
        
        self.select_menu.setMenu(select_menu)
        layout.addWidget(self.select_menu)
    
    def _on_filter_changed(self):
        """Handle filter change."""
        self.filter_changed.emit()
        logger.debug(f"Filter changed: pattern='{self.pattern_input.text()}', "
                    f"type={self.type_filter.currentData()}, "
                    f"confidence={self.confidence_filter.currentData()}")
    
    def clear_filters(self):
        """Clear all filters."""
        self.pattern_input.clear()
        self.type_filter.setCurrentIndex(0)
        self.confidence_filter.setCurrentIndex(0)
        self.sort_by.setCurrentIndex(0)
        self.filter_changed.emit()
        logger.info("Filters cleared")
    
    def matches_filter(self, result: dict) -> bool:
        """
        Check if a result matches the current filter.
        
        Args:
            result: File analysis result dict
            
        Returns:
            True if result matches filter, False otherwise
        """
        file_path = result.get("file_path", "")
        category = result.get("category", "")
        confidence = result.get("confidence", 0.0)
        
        # Pattern filter
        pattern = self.pattern_input.text().strip()
        if pattern:
            # Convert file path to filename for matching
            filename = file_path.split("/")[-1] if "/" in file_path else file_path
            if not fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return False
        
        # Type filter
        type_filter = self.type_filter.currentData()
        if type_filter:
            ext = file_path.split(".")[-1].lower() if "." in file_path else ""
            type_mapping = {
                "document": ["pdf", "doc", "docx", "txt", "rtf", "odt"],
                "image": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp"],
                "code": ["py", "js", "html", "css", "java", "cpp", "c", "h", "go", "rs"],
                "data": ["csv", "json", "xml", "xlsx", "xls", "db", "sqlite"],
                "audio": ["mp3", "wav", "flac", "aac", "ogg", "m4a"],
                "video": ["mp4", "avi", "mkv", "mov", "wmv", "flv"],
                "archive": ["zip", "rar", "7z", "tar", "gz", "bz2"],
            }
            if ext not in type_mapping.get(type_filter, []):
                return False
        
        # Confidence filter
        conf_filter = self.confidence_filter.currentData()
        if conf_filter > 0:  # Minimum confidence
            if confidence < conf_filter:
                return False
        elif conf_filter < 0:  # Review mode (show low confidence)
            if confidence >= 0.85:
                return False
        
        return True
    
    def get_sort_key(self):
        """Get the current sort key function."""
        sort_by = self.sort_by.currentData()
        
        def sort_key(result):
            file_path = result.get("file_path", "")
            filename = file_path.split("/")[-1] if "/" in file_path else file_path
            
            if sort_by == "name":
                return filename.lower()
            elif sort_by == "type":
                ext = filename.split(".")[-1].lower() if "." in filename else ""
                return (ext, filename.lower())
            elif sort_by == "confidence":
                return -result.get("confidence", 0.0)  # Descending
            elif sort_by == "category":
                return (result.get("category", "").lower(), filename.lower())
            return filename.lower()
        
        return sort_key
    
    # Signal for selection actions
    _select_action = pyqtSignal(str)
    select_action = property(lambda self: self._select_action)
