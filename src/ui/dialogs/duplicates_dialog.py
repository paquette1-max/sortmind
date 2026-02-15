"""
Duplicate Files Dialog for managing and removing duplicate files.
"""
from pathlib import Path
from typing import List, Optional, Dict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QGroupBox,
    QMessageBox, QProgressBar, QSplitter, QCheckBox, QHeaderView,
    QAbstractItemView, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFont

import logging

try:
    from ...core.duplicate_detector import (
        DuplicateDetector, DuplicateGroup, DuplicateType, DuplicateDetectionResult
    )
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.duplicate_detector import (
        DuplicateDetector, DuplicateGroup, DuplicateType, DuplicateDetectionResult
    )

logger = logging.getLogger(__name__)


class DuplicateScanWorker(QThread):
    """Worker thread for duplicate detection."""
    
    progress = pyqtSignal(int, int)  # current, total
    finished_signal = pyqtSignal(DuplicateDetectionResult)
    error = pyqtSignal(str)
    
    def __init__(self, file_paths: List[Path], detector: DuplicateDetector):
        super().__init__()
        self.file_paths = file_paths
        self.detector = detector
    
    def run(self):
        try:
            result = self.detector.find_duplicates(
                self.file_paths,
                progress_callback=lambda c, t: self.progress.emit(c, t)
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class DuplicateItemWidget(QWidget):
    """Widget for displaying a duplicate file item with checkbox."""
    
    selection_changed = pyqtSignal(Path, bool)
    
    def __init__(self, file_path: Path, is_original: bool = False, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(not is_original)  # Check duplicates by default
        self.checkbox.stateChanged.connect(self._on_state_changed)
        layout.addWidget(self.checkbox)
        
        # File icon/indicator
        indicator = "⭐" if is_original else "📄"
        indicator_label = QLabel(indicator)
        layout.addWidget(indicator_label)
        
        # File path
        path_label = QLabel(str(file_path))
        path_label.setWordWrap(True)
        if is_original:
            path_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(path_label, 1)
        
        # File size
        try:
            size = file_path.stat().st_size
            size_label = QLabel(self._format_size(size))
            size_label.setStyleSheet("color: #666; font-size: 10px;")
            layout.addWidget(size_label)
        except:
            pass
    
    def _on_state_changed(self, state):
        """Handle checkbox state change."""
        self.selection_changed.emit(self.file_path, state == Qt.CheckState.Checked.value)
    
    def is_checked(self) -> bool:
        """Check if item is selected for deletion."""
        return self.checkbox.isChecked()
    
    def set_checked(self, checked: bool):
        """Set checkbox state."""
        self.checkbox.setChecked(checked)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


class DuplicatesDialog(QDialog):
    """Dialog for managing duplicate files."""
    
    duplicates_removed = pyqtSignal(int, int)  # count, space_freed
    
    def __init__(self, file_paths: Optional[List[Path]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate File Manager")
        self.setModal(False)
        self.resize(1000, 700)
        
        self.file_paths = file_paths or []
        self.detector = DuplicateDetector()
        self.detection_result: Optional[DuplicateDetectionResult] = None
        self.scan_worker: Optional[DuplicateScanWorker] = None
        
        # Track which files are selected for deletion
        self.selected_for_deletion: Dict[str, List[Path]] = {}  # group_id -> paths
        
        self._setup_ui()
        
        if self.file_paths:
            self._start_scan()
        
        logger.info("Duplicates dialog initialized")
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("🔍 Duplicate File Detection")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Stats
        self.stats_label = QLabel("No scan performed yet")
        self.stats_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Duplicate groups list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("Duplicate Groups:"))
        
        self.groups_tree = QTreeWidget()
        self.groups_tree.setHeaderLabels(["Group", "Files", "Wasted Space", "Type"])
        self.groups_tree.setColumnWidth(0, 200)
        self.groups_tree.setColumnWidth(1, 80)
        self.groups_tree.setColumnWidth(2, 120)
        self.groups_tree.setColumnWidth(3, 80)
        self.groups_tree.currentItemChanged.connect(self._on_group_selected)
        self.groups_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        left_layout.addWidget(self.groups_tree)
        
        # Group actions
        group_actions = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Select All Duplicates")
        self.select_all_btn.clicked.connect(self._select_all_duplicates)
        group_actions.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        group_actions.addWidget(self.deselect_all_btn)
        
        group_actions.addStretch()
        
        self.rescan_btn = QPushButton("🔄 Rescan")
        self.rescan_btn.clicked.connect(self._start_scan)
        group_actions.addWidget(self.rescan_btn)
        
        left_layout.addLayout(group_actions)
        
        splitter.addWidget(left_widget)
        
        # Right: Files in selected group
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        right_layout.addWidget(QLabel("Files in Group (⭐ = Original, 📄 = Duplicate):"))
        
        # Files list
        self.files_list = QListWidget()
        self.files_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 2px;
            }
        """)
        right_layout.addWidget(self.files_list)
        
        # Group info
        self.group_info = QLabel("Select a group to view details")
        self.group_info.setStyleSheet("""
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 4px;
        """)
        self.group_info.setWordWrap(True)
        right_layout.addWidget(self.group_info)
        
        # Action buttons
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout(action_group)
        
        self.delete_btn = QPushButton("🗑️ Delete Selected Duplicates")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.delete_btn.clicked.connect(self._delete_selected)
        action_layout.addWidget(self.delete_btn)
        
        self.smart_select_btn = QPushButton("🧠 Smart Select (Keep First in Each Folder)")
        self.smart_select_btn.clicked.connect(self._smart_select)
        action_layout.addWidget(self.smart_select_btn)
        
        right_layout.addWidget(action_group)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter, 1)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(self.close_btn)
        
        bottom_layout.addStretch()
        
        self.export_btn = QPushButton("📄 Export Report")
        self.export_btn.clicked.connect(self._export_report)
        bottom_layout.addWidget(self.export_btn)
        
        layout.addLayout(bottom_layout)
        
        self.setLayout(layout)
    
    def set_files(self, file_paths: List[Path]):
        """Set the list of files to scan."""
        self.file_paths = file_paths
        self._start_scan()
    
    def _start_scan(self):
        """Start duplicate detection scan."""
        if not self.file_paths:
            QMessageBox.information(self, "No Files", "No files to scan")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.rescan_btn.setEnabled(False)
        self.title_label.setText("🔍 Scanning for Duplicates...")
        
        self.scan_worker = DuplicateScanWorker(self.file_paths, self.detector)
        self.scan_worker.progress.connect(self._on_scan_progress)
        self.scan_worker.finished_signal.connect(self._on_scan_finished)
        self.scan_worker.error.connect(self._on_scan_error)
        self.scan_worker.start()
    
    def _on_scan_progress(self, current: int, total: int):
        """Update scan progress."""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
    
    def _on_scan_finished(self, result: DuplicateDetectionResult):
        """Handle scan completion."""
        self.detection_result = result
        self.progress_bar.setVisible(False)
        self.rescan_btn.setEnabled(True)
        self.title_label.setText("🔍 Duplicate File Detection")
        
        # Update stats
        wasted_mb = result.total_wasted_space / (1024 * 1024)
        self.stats_label.setText(
            f"Found {result.group_count} groups | "
            f"{result.total_duplicates} duplicates | "
            f"{wasted_mb:.1f} MB wasted"
        )
        
        # Populate groups tree
        self._populate_groups_tree()
        
        # Initialize selected_for_deletion
        self.selected_for_deletion = {}
        for group in result.exact_duplicates:
            self.selected_for_deletion[group.group_id] = group.files[1:].copy()
        for group in result.similar_images:
            self.selected_for_deletion[group.group_id] = group.files[1:].copy()
    
    def _on_scan_error(self, error: str):
        """Handle scan error."""
        self.progress_bar.setVisible(False)
        self.rescan_btn.setEnabled(True)
        self.title_label.setText("🔍 Duplicate File Detection")
        QMessageBox.critical(self, "Scan Error", f"Failed to scan for duplicates: {error}")
    
    def _populate_groups_tree(self):
        """Populate the groups tree with results."""
        self.groups_tree.clear()
        
        if not self.detection_result:
            return
        
        # Add exact duplicates
        for group in self.detection_result.exact_duplicates:
            wasted = group.get_wasted_space()
            item = QTreeWidgetItem([
                f"Exact: {group.files[0].name[:30]}..." if len(group.files[0].name) > 30 
                    else f"Exact: {group.files[0].name}",
                str(len(group.files)),
                self._format_size(wasted),
                "Exact"
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, group.group_id)
            item.setForeground(0, QColor("#1976d2"))
            self.groups_tree.addTopLevelItem(item)
        
        # Add similar images
        for group in self.detection_result.similar_images:
            wasted = group.get_wasted_space()
            item = QTreeWidgetItem([
                f"Similar: {group.files[0].name[:30]}..." if len(group.files[0].name) > 30 
                    else f"Similar: {group.files[0].name}",
                str(len(group.files)),
                self._format_size(wasted),
                "Similar"
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, group.group_id)
            item.setForeground(0, QColor("#f57c00"))
            self.groups_tree.addTopLevelItem(item)
        
        # Expand first item
        if self.groups_tree.topLevelItemCount() > 0:
            self.groups_tree.setCurrentItem(self.groups_tree.topLevelItem(0))
    
    def _on_group_selected(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        """Handle group selection."""
        if not current or not self.detection_result:
            self.files_list.clear()
            return
        
        group_id = current.data(0, Qt.ItemDataRole.UserRole)
        group = self._find_group(group_id)
        
        if not group:
            return
        
        # Update group info
        group_type = "Exact Duplicate" if group.duplicate_type == DuplicateType.EXACT else "Similar Image"
        info_text = f"Type: {group_type}\n"
        info_text += f"Files: {len(group.files)}\n"
        info_text += f"Wasted Space: {self._format_size(group.get_wasted_space())}\n"
        if group.hash_value:
            info_text += f"Hash: {group.hash_value[:16]}..."
        
        self.group_info.setText(info_text)
        
        # Populate files list
        self.files_list.clear()
        
        for i, file_path in enumerate(group.files):
            is_original = i == 0
            
            item = QListWidgetItem()
            widget = DuplicateItemWidget(file_path, is_original)
            
            # Restore checkbox state from selected_for_deletion
            if group_id in self.selected_for_deletion:
                widget.set_checked(file_path in self.selected_for_deletion[group_id])
            
            widget.selection_changed.connect(
                lambda path, checked, gid=group_id: self._on_file_selection_changed(gid, path, checked)
            )
            
            item.setSizeHint(widget.sizeHint())
            self.files_list.addItem(item)
            self.files_list.setItemWidget(item, widget)
    
    def _on_file_selection_changed(self, group_id: str, file_path: Path, checked: bool):
        """Handle file selection change."""
        if group_id not in self.selected_for_deletion:
            self.selected_for_deletion[group_id] = []
        
        if checked:
            if file_path not in self.selected_for_deletion[group_id]:
                self.selected_for_deletion[group_id].append(file_path)
        else:
            if file_path in self.selected_for_deletion[group_id]:
                self.selected_for_deletion[group_id].remove(file_path)
    
    def _find_group(self, group_id: str) -> Optional[DuplicateGroup]:
        """Find a group by ID."""
        if not self.detection_result:
            return None
        
        for group in self.detection_result.exact_duplicates:
            if group.group_id == group_id:
                return group
        
        for group in self.detection_result.similar_images:
            if group.group_id == group_id:
                return group
        
        return None
    
    def _select_all_duplicates(self):
        """Select all duplicate files (not originals)."""
        if not self.detection_result:
            return
        
        for group in self.detection_result.exact_duplicates:
            self.selected_for_deletion[group.group_id] = group.files[1:].copy()
        
        for group in self.detection_result.similar_images:
            self.selected_for_deletion[group.group_id] = group.files[1:].copy()
        
        # Refresh current view
        self._refresh_current_files_list()
    
    def _deselect_all(self):
        """Deselect all files."""
        self.selected_for_deletion = {}
        self._refresh_current_files_list()
    
    def _refresh_current_files_list(self):
        """Refresh the files list for the current group."""
        current_item = self.groups_tree.currentItem()
        if current_item:
            self._on_group_selected(current_item, None)
    
    def _smart_select(self):
        """Smart selection - keep one file from each folder."""
        if not self.detection_result:
            return
        
        self.selected_for_deletion = {}
        
        all_groups = (self.detection_result.exact_duplicates + 
                     self.detection_result.similar_images)
        
        for group in all_groups:
            # Group files by parent directory
            by_folder: Dict[Path, List[Path]] = {}
            for file_path in group.files:
                folder = file_path.parent
                if folder not in by_folder:
                    by_folder[folder] = []
                by_folder[folder].append(file_path)
            
            # Select all but first from each folder
            to_delete = []
            for folder, files in by_folder.items():
                to_delete.extend(files[1:])  # Keep first in each folder
            
            self.selected_for_deletion[group.group_id] = to_delete
        
        self._refresh_current_files_list()
    
    def _delete_selected(self):
        """Delete selected duplicate files."""
        # Count selected files
        total_selected = sum(len(paths) for paths in self.selected_for_deletion.values())
        
        if total_selected == 0:
            QMessageBox.information(self, "No Selection", "No files selected for deletion")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete {total_selected} duplicate files?\n\n"
            "This action cannot be undone. Files will be permanently deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Perform deletion
        deleted_count = 0
        space_freed = 0
        errors = []
        
        for group_id, paths in self.selected_for_deletion.items():
            for file_path in paths:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    space_freed += file_size
                except Exception as e:
                    errors.append(f"{file_path}: {e}")
        
        # Emit signal
        self.duplicates_removed.emit(deleted_count, space_freed)
        
        # Show result
        if errors:
            QMessageBox.warning(
                self,
                "Partial Success",
                f"Deleted {deleted_count} files ({self._format_size(space_freed)} freed)\n\n"
                f"Errors:\n" + "\n".join(errors[:10])
            )
        else:
            QMessageBox.information(
                self,
                "Success",
                f"Deleted {deleted_count} files\n"
                f"Space freed: {self._format_size(space_freed)}"
            )
        
        # Rescan
        self._start_scan()
    
    def _export_report(self):
        """Export duplicate report to file."""
        from PyQt6.QtWidgets import QFileDialog
        
        if not self.detection_result:
            QMessageBox.information(self, "No Results", "No scan results to export")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            "duplicate_report.txt",
            "Text Files (*.txt)"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w') as f:
                f.write("DUPLICATE FILE REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Scanned Files: {self.detection_result.scanned_files}\n")
                f.write(f"Duplicate Groups: {self.detection_result.group_count}\n")
                f.write(f"Total Duplicates: {self.detection_result.total_duplicates}\n")
                f.write(f"Total Wasted Space: {self._format_size(self.detection_result.total_wasted_space)}\n")
                f.write(f"Scan Duration: {self.detection_result.scan_duration:.1f}s\n\n")
                
                f.write("EXACT DUPLICATES\n")
                f.write("-" * 80 + "\n")
                for group in self.detection_result.exact_duplicates:
                    f.write(f"\nGroup: {group.group_id}\n")
                    f.write(f"Hash: {group.hash_value}\n")
                    for file_path in group.files:
                        f.write(f"  - {file_path}\n")
                
                f.write("\n\nSIMILAR IMAGES\n")
                f.write("-" * 80 + "\n")
                for group in self.detection_result.similar_images:
                    f.write(f"\nGroup: {group.group_id}\n")
                    for file_path in group.files:
                        f.write(f"  - {file_path}\n")
            
            QMessageBox.information(self, "Success", f"Report exported to {filepath}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export report: {e}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
