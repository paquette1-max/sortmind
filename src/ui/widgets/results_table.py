"""
Results table widget for displaying analysis results.
Enhanced with world-class UX: checkboxes, file type icons, smart filtering.
"""
from pathlib import Path
from typing import List, Dict, Optional, Set
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu, QWidget, QVBoxLayout, QLabel, QStyledItemDelegate, QStyle,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QAction, QIcon

import logging

logger = logging.getLogger(__name__)


class NoFocusDelegate(QStyledItemDelegate):
    """Delegate that removes the focus rectangle from table items."""
    
    def paint(self, painter, option, index):
        if option.state & QStyle.StateFlag.State_HasFocus:
            option.state &= ~QStyle.StateFlag.State_HasFocus
        super().paint(painter, option, index)


# File type icon mapping (emoji-based for now)
FILE_TYPE_ICONS = {
    # Documents
    "pdf": "📄", "doc": "📄", "docx": "📄", "txt": "📄", "rtf": "📄",
    "odt": "📄", "md": "📝", "tex": "📝",
    
    # Images
    "jpg": "🖼️", "jpeg": "🖼️", "png": "🖼️", "gif": "🖼️", "bmp": "🖼️",
    "svg": "🎨", "webp": "🖼️", "ico": "🖼️", "tiff": "🖼️",
    
    # Code
    "py": "🐍", "js": "📜", "ts": "📘", "html": "🌐", "css": "🎨",
    "java": "☕", "cpp": "⚙️", "c": "⚙️", "h": "⚙️", "go": "🐹",
    "rs": "🦀", "rb": "💎", "php": "🐘", "swift": "🦉",
    
    # Data
    "csv": "📊", "json": "📋", "xml": "📋", "xlsx": "📊", "xls": "📊",
    "db": "🗄️", "sqlite": "🗄️", "sql": "🗄️",
    
    # Audio
    "mp3": "🎵", "wav": "🎵", "flac": "🎵", "aac": "🎵", "ogg": "🎵",
    "m4a": "🎵", "wma": "🎵",
    
    # Video
    "mp4": "🎬", "avi": "🎬", "mkv": "🎬", "mov": "🎬", "wmv": "🎬",
    "flv": "🎬", "webm": "🎬",
    
    # Archives
    "zip": "📦", "rar": "📦", "7z": "📦", "tar": "📦", "gz": "📦",
    "bz2": "📦", "xz": "📦",
    
    # Executables
    "exe": "⚙️", "dmg": "🍎", "pkg": "📦", "app": "🍎", "deb": "📦",
    "rpm": "📦",
    
    # Config
    "yml": "⚙️", "yaml": "⚙️", "toml": "⚙️", "ini": "⚙️", "cfg": "⚙️",
    "conf": "⚙️", "env": "🔐",
    
    # Default
    "default": "📎"
}


def get_file_icon(file_path: str) -> str:
    """Get the appropriate icon for a file based on its extension."""
    ext = Path(file_path).suffix.lower().lstrip(".")
    return FILE_TYPE_ICONS.get(ext, FILE_TYPE_ICONS["default"])


class CheckboxHeader(QHeaderView):
    """Custom header with checkbox for select all/none."""
    
    check_state_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._checkbox = QCheckBox(self)
        self._checkbox.setStyleSheet("QCheckBox { margin-left: 6px; }")
        self._checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.sectionResized.connect(self._update_checkbox_position)
    
    def _on_checkbox_changed(self, state):
        self.check_state_changed.emit(state == Qt.CheckState.Checked.value)
    
    def _update_checkbox_position(self):
        # Position checkbox in first column
        x = self.sectionPosition(0) + 6
        y = (self.height() - self._checkbox.height()) // 2
        self._checkbox.move(x, y)
    
    def setCheckState(self, state: Qt.CheckState):
        self._checkbox.setCheckState(state)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_checkbox_position()


class ResultsTable(QTableWidget):
    """
    Table widget displaying analysis results with world-class UX.
    
    Features:
    - Checkbox column for bulk selection
    - File type icons for visual identification
    - Smart multi-selection (Ctrl, Shift, checkboxes)
    - Keyboard navigation
    - Context menu for actions
    """
    
    selection_changed = pyqtSignal(list)
    current_file_changed = pyqtSignal(object)
    files_organized = pyqtSignal()
    selection_count_changed = pyqtSignal(int)  # Emits count when selection changes
    
    def __init__(self):
        super().__init__()
        self.results = []
        self._selected_rows: Set[int] = set()  # Persistent selection
        self._filtered_rows: Set[int] = set()  # Currently visible rows
        self._setup_table()
        logger.info("Results table initialized")
    
    def _setup_table(self):
        """Setup table with checkbox column and file type icons."""
        # Columns: Checkbox, Icon, Filename, Category, New Name, Confidence, Reason
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels([
            "",           # 0: Checkbox
            "",           # 1: Icon
            "File",       # 2: Filename
            "Folder",     # 3: Suggested folder
            "New Name",   # 4: Proposed rename
            "Conf",       # 5: Confidence
            "Reason"      # 6: Why
        ])
        
        # Configure columns
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        
        # Set column widths
        self.setColumnWidth(0, 30)   # Checkbox
        self.setColumnWidth(1, 30)   # Icon
        self.setColumnWidth(5, 70)   # Confidence
        
        # Selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        
        # Remove focus rectangle
        self.setItemDelegate(NoFocusDelegate(self))
        
        # Connect signals
        self.itemClicked.connect(self._on_item_clicked)
        self.itemChanged.connect(self._on_item_changed)
        
        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def add_result(self, result: Dict):
        """Add a result row with checkbox and icon."""
        row = self.rowCount()
        self.insertRow(row)
        
        file_path = result.get("file_path", "Unknown")
        category = result.get("category", "uncategorized")
        suggested_name = result.get("suggested_name", "")
        confidence = result.get("confidence", 0.0)
        reasoning = result.get("reasoning", "")
        
        # Column 0: Checkbox
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        checkbox_item.setCheckState(Qt.CheckState.Unchecked)
        checkbox_item.setData(Qt.ItemDataRole.UserRole, row)  # Store row index
        self.setItem(row, 0, checkbox_item)
        
        # Column 1: File type icon
        icon_item = QTableWidgetItem(get_file_icon(file_path))
        icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not selectable
        self.setItem(row, 1, icon_item)
        
        # Column 2: Filename
        filename = Path(file_path).name
        path_item = QTableWidgetItem(filename)
        path_item.setToolTip(f"Full path: {file_path}")
        path_item.setData(Qt.ItemDataRole.UserRole, file_path)
        self.setItem(row, 2, path_item)
        
        # Column 3: Category
        cat_item = QTableWidgetItem(category)
        cat_item.setToolTip(f"Suggested folder: {category}")
        self.setItem(row, 3, cat_item)
        
        # Column 4: New name
        name_item = QTableWidgetItem(suggested_name if suggested_name else "(no change)")
        if suggested_name:
            name_item.setToolTip(f"Will be renamed to: {suggested_name}")
        else:
            name_item.setToolTip("Filename will not be changed")
            name_item.setForeground(QColor("#737373"))
        self.setItem(row, 4, name_item)
        
        # Column 5: Confidence
        conf_text = f"{confidence:.0%}"
        conf_item = QTableWidgetItem(conf_text)
        conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if confidence >= 0.85:
            conf_item.setForeground(QColor("#22C55E"))
            conf_item.setToolTip("High confidence (85%+)")
        elif confidence >= 0.70:
            conf_item.setForeground(QColor("#F59E0B"))
            conf_item.setToolTip("Medium confidence (70%+)")
        else:
            conf_item.setForeground(QColor("#EF4444"))
            conf_item.setToolTip("Low confidence - review carefully")
        self.setItem(row, 5, conf_item)
        
        # Column 6: Reason
        reason_item = QTableWidgetItem(reasoning[:50] + "..." if len(reasoning) > 50 else reasoning)
        reason_item.setToolTip(reasoning if reasoning else "No explanation provided")
        self.setItem(row, 6, reason_item)
        
        self.results.append(result)
        self._filtered_rows.add(row)
    
    def _on_item_clicked(self, item: QTableWidgetItem):
        """Handle item click."""
        row = item.row()
        col = item.column()
        
        if col == 0:  # Checkbox column
            # Checkbox was clicked
            is_checked = item.checkState() == Qt.CheckState.Checked
            if is_checked:
                self._selected_rows.add(row)
            else:
                self._selected_rows.discard(row)
            self._emit_selection_changed()
        
        # Show preview for ANY column click (not just filename)
        # This ensures preview updates when user clicks anywhere on a row
        if 0 <= row < len(self.results) and row in self._filtered_rows:
            file_path = self.results[row].get("file_path")
            if file_path:
                self.current_file_changed.emit(Path(file_path))
    
    def _on_item_changed(self, item: QTableWidgetItem):
        """Handle checkbox state changes."""
        if item.column() == 0:  # Checkbox column
            row = item.row()
            is_checked = item.checkState() == Qt.CheckState.Checked
            if is_checked:
                self._selected_rows.add(row)
            else:
                self._selected_rows.discard(row)
            self._emit_selection_changed()
    
    def _emit_selection_changed(self):
        """Emit selection changed signal."""
        selected = self.get_selected_results()
        self.selection_changed.emit(selected)
        self.selection_count_changed.emit(len(selected))
    
    def get_selected_results(self) -> List[Dict]:
        """Get selected results (from checkboxes)."""
        return [self.results[row] for row in sorted(self._selected_rows) 
                if row < len(self.results) and row in self._filtered_rows]
    
    def select_all_visible(self):
        """Select all currently visible (filtered) rows."""
        for row in self._filtered_rows:
            if row < self.rowCount():
                item = self.item(row, 0)
                if item:
                    item.setCheckState(Qt.CheckState.Checked)
        self._emit_selection_changed()
    
    def clear_selection(self):
        """Clear all selections."""
        self._selected_rows.clear()
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
        self._emit_selection_changed()
    
    def select_by_pattern(self, pattern: str):
        """Select files matching a wildcard pattern."""
        import fnmatch
        for row, result in enumerate(self.results):
            if row not in self._filtered_rows:
                continue
            file_path = result.get("file_path", "")
            filename = Path(file_path).name
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                item = self.item(row, 0)
                if item:
                    item.setCheckState(Qt.CheckState.Checked)
        self._emit_selection_changed()
    
    def select_by_type(self, extensions: List[str]):
        """Select files by extension(s)."""
        for row, result in enumerate(self.results):
            if row not in self._filtered_rows:
                continue
            file_path = result.get("file_path", "")
            ext = Path(file_path).suffix.lower().lstrip(".")
            if ext in extensions:
                item = self.item(row, 0)
                if item:
                    item.setCheckState(Qt.CheckState.Checked)
        self._emit_selection_changed()
    
    def filter_results(self, visible_rows: Set[int]):
        """Show only specific rows (filtering)."""
        self._filtered_rows = visible_rows
        for row in range(self.rowCount()):
            self.setRowHidden(row, row not in visible_rows)
    
    def clear_results(self):
        """Clear all results."""
        self.setRowCount(0)
        self.results.clear()
        self._selected_rows.clear()
        self._filtered_rows.clear()
    
    def _show_context_menu(self, position):
        """Show context menu."""
        selected = self.get_selected_results()
        if not selected:
            return
        
        menu = QMenu(self)
        
        organize_action = QAction(f"📁 Organize {len(selected)} file(s)", self)
        organize_action.triggered.connect(self.files_organized.emit)
        menu.addAction(organize_action)
        
        menu.addSeparator()
        
        # Selection actions
        highlighted = self._get_highlighted_rows()
        if highlighted:
            check_selected = QAction(f"✓ Check {len(highlighted)} Highlighted", self)
            check_selected.triggered.connect(lambda: self.check_highlighted_rows(True))
            menu.addAction(check_selected)
            
            uncheck_selected = QAction(f"☐ Uncheck {len(highlighted)} Highlighted", self)
            uncheck_selected.triggered.connect(lambda: self.check_highlighted_rows(False))
            menu.addAction(uncheck_selected)
            
            menu.addSeparator()
        
        select_all = QAction("☑️ Select All Visible", self)
        select_all.triggered.connect(self.select_all_visible)
        menu.addAction(select_all)
        
        clear_sel = QAction("Clear All Checks", self)
        clear_sel.triggered.connect(self.clear_selection)
        menu.addAction(clear_sel)
        
        menu.addSeparator()
        
        # Quick filters
        pdf_action = QAction("📄 Select PDFs", self)
        pdf_action.triggered.connect(lambda: self.select_by_type(["pdf"]))
        menu.addAction(pdf_action)
        
        img_action = QAction("🖼️ Select Images", self)
        img_action.triggered.connect(lambda: self.select_by_type(["jpg", "jpeg", "png", "gif"]))
        menu.addAction(img_action)
        
        doc_action = QAction("📄 Select Documents", self)
        doc_action.triggered.connect(lambda: self.select_by_type(["doc", "docx", "txt", "pdf"]))
        menu.addAction(doc_action)
        
        menu.exec(self.viewport().mapToGlobal(position))
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()
        
        if key == Qt.Key.Key_Space:
            # Space toggles ALL highlighted rows
            highlighted = self._get_highlighted_rows()
            if highlighted:
                # Check if majority are checked or unchecked
                checked_count = sum(1 for row in highlighted 
                                   if self.item(row, 0) and self.item(row, 0).checkState() == Qt.CheckState.Checked)
                # If more than half are checked, uncheck all. Otherwise, check all.
                new_state = Qt.CheckState.Unchecked if checked_count > len(highlighted) / 2 else Qt.CheckState.Checked
                
                for row in highlighted:
                    item = self.item(row, 0)
                    if item:
                        item.setCheckState(new_state)
                        if new_state == Qt.CheckState.Checked:
                            self._selected_rows.add(row)
                        else:
                            self._selected_rows.discard(row)
                self._emit_selection_changed()
            event.accept()
            return
        
        elif key == Qt.Key.Key_A and modifiers == Qt.KeyboardModifier.ControlModifier:
            self.select_all_visible()
            event.accept()
            return
        
        elif key == Qt.Key.Key_Return and len(self.get_selected_results()) > 0:
            self.files_organized.emit()
            event.accept()
            return
        
        # Update preview when navigating with arrow keys
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Home, Qt.Key.Key_End):
            super().keyPressEvent(event)
            # After navigation, update preview for current row
            current_row = self.currentRow()
            if 0 <= current_row < len(self.results) and current_row in self._filtered_rows:
                file_path = self.results[current_row].get("file_path")
                if file_path:
                    self.current_file_changed.emit(Path(file_path))
            event.accept()
            return
        
        super().keyPressEvent(event)
    
    def _get_highlighted_rows(self) -> Set[int]:
        """Get rows that are highlighted (selected via click/shift/ctrl)."""
        highlighted = set()
        for item in self.selectedItems():
            highlighted.add(item.row())
        return highlighted
    
    def check_highlighted_rows(self, checked: bool = True):
        """Check or uncheck all highlighted rows."""
        highlighted = self._get_highlighted_rows()
        if not highlighted:
            return
        
        new_state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for row in highlighted:
            item = self.item(row, 0)
            if item and row in self._filtered_rows:
                item.setCheckState(new_state)
                if checked:
                    self._selected_rows.add(row)
                else:
                    self._selected_rows.discard(row)
        self._emit_selection_changed()
    
    def get_statistics(self) -> Dict:
        """Get statistics about results."""
        visible = [self.results[r] for r in self._filtered_rows if r < len(self.results)]
        selected = self.get_selected_results()
        
        return {
            "total": len(self.results),
            "visible": len(visible),
            "selected": len(selected),
            "by_type": self._count_by_type(),
            "by_category": self._count_by_category()
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count files by type."""
        counts = {}
        for result in self.results:
            ext = Path(result.get("file_path", "")).suffix.lower().lstrip(".") or "unknown"
            counts[ext] = counts.get(ext, 0) + 1
        return counts
    
    def _count_by_category(self) -> Dict[str, int]:
        """Count files by suggested category."""
        counts = {}
        for result in self.results:
            cat = result.get("category", "uncategorized")
            counts[cat] = counts.get(cat, 0) + 1
        return counts
