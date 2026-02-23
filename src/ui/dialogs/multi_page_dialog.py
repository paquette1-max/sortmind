"""
Multi-page document splitting review dialog.
Allows users to review and adjust automatic document boundaries before splitting.
"""

import logging
from pathlib import Path
from typing import List, Optional, Callable

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSplitter, QWidget,
    QLineEdit, QTextEdit, QMessageBox, QProgressBar,
    QGroupBox, QSpinBox, QCheckBox, QFrame, QFileDialog,
    QScrollArea, QSizePolicy, QToolButton, QMenu, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QFont, QIcon, QAction, QKeySequence

try:
    from ...core.multi_page_analyzer import (
        MultiPageDocumentAnalyzer, MultiPageAnalysisResult,
        DocumentSegment, PageAnalysis
    )
    from ...core.content_extractor import ContentExtractor
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.multi_page_analyzer import (
        MultiPageDocumentAnalyzer, MultiPageAnalysisResult,
        DocumentSegment, PageAnalysis
    )
    from core.content_extractor import ContentExtractor

logger = logging.getLogger(__name__)


class SegmentListItem(QWidget):
    """Widget for displaying a document segment in the list."""
    
    def __init__(self, segment: DocumentSegment, segment_index: int, parent=None):
        super().__init__(parent)
        self.segment = segment
        self.segment_index = segment_index
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Header: Segment number and page range
        header_layout = QHBoxLayout()
        
        segment_label = QLabel(f"📄 Document {self.segment_index + 1}")
        segment_label.setFont(QFont("", 12, QFont.Weight.Bold))
        header_layout.addWidget(segment_label)
        
        page_range = QLabel(f"Pages {self.segment.start_page} - {self.segment.end_page}")
        page_range.setStyleSheet("color: #666;")
        header_layout.addWidget(page_range)
        
        header_layout.addStretch()
        
        # Confidence indicator
        conf_color = "#22c55e" if self.segment.confidence > 0.8 else "#f59e0b" if self.segment.confidence > 0.5 else "#ef4444"
        confidence_label = QLabel(f"Confidence: {self.segment.confidence:.0%}")
        confidence_label.setStyleSheet(f"color: {conf_color}; font-weight: bold;")
        header_layout.addWidget(confidence_label)
        
        layout.addLayout(header_layout)
        
        # Document info
        if self.segment.document_type:
            doc_type = QLabel(f"📋 Type: {self.segment.document_type.replace('_', ' ').title()}")
            layout.addWidget(doc_type)
        
        if self.segment.institution:
            institution = QLabel(f"🏦 Institution: {self.segment.institution}")
            layout.addWidget(institution)
        
        if self.segment.date_range:
            date_label = QLabel(f"📅 Date: {self.segment.date_range}")
            layout.addWidget(date_label)
        
        if self.segment.account_number:
            account = QLabel(f"🔢 Account: ...{self.segment.account_number[-4:]}")
            layout.addWidget(account)
        
        # Suggested filename
        if self.segment.suggested_filename:
            filename_layout = QHBoxLayout()
            filename_label = QLabel("💾 Suggested filename:")
            filename_layout.addWidget(filename_label)
            
            self.filename_edit = QLineEdit(self.segment.suggested_filename)
            self.filename_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #f0fdf4;
                    border: 1px solid #22c55e;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
            filename_layout.addWidget(self.filename_edit)
            layout.addLayout(filename_layout)
        
        # Split reason
        reason = QLabel(f"ℹ️ Split reason: {self.segment.split_reason}")
        reason.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(reason)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #e5e5e5;")
        layout.addWidget(line)


class MultiPageReviewDialog(QDialog):
    """
    Dialog for reviewing multi-page document splits.
    
    Features:
    - Shows proposed document segments with page ranges
    - Allows editing suggested filenames
    - Shows confidence scores for each segment
    - Allows merging or splitting segments
    - Preview of page content
    """
    
    # Signals
    segments_accepted = pyqtSignal(list, Path)  # segments, output directory
    segments_rejected = pyqtSignal()
    
    def __init__(self, analysis_result: MultiPageAnalysisResult, 
                 source_pdf_path: Path, parent=None):
        """
        Initialize the review dialog.
        
        Args:
            analysis_result: Result from multi-page analyzer
            source_pdf_path: Path to the source PDF
            parent: Parent widget
        """
        super().__init__(parent)
        self.analysis_result = analysis_result
        self.source_pdf_path = source_pdf_path
        self.segments = list(analysis_result.detected_segments)
        self.output_directory = source_pdf_path.parent
        
        self.setWindowTitle(f"Review Document Splits - {source_pdf_path.name}")
        self.resize(1400, 900)
        self._setup_ui()
        self._populate_segments()
        
        logger.info(f"MultiPageReviewDialog initialized with {len(self.segments)} segments")
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("📑 Multi-Page Document Review")
        header.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Info bar
        info_text = (f"Source: {self.source_pdf_path.name} | "
                    f"Total pages: {self.analysis_result.total_pages} | "
                    f"Detected documents: {len(self.segments)}")
        if self.analysis_result.blank_page_indices:
            info_text += f" | Blank pages: {len(self.analysis_result.blank_page_indices)}"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #666; padding: 8px 0;")
        layout.addWidget(info_label)
        
        # Warning if low confidence
        if self.analysis_result.needs_review:
            warning = QLabel("⚠️ Low confidence detection - please review carefully")
            warning.setStyleSheet("""
                background-color: #fef3c7;
                color: #92400e;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            """)
            layout.addWidget(warning)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Segments list
        left_widget = self._create_segments_panel()
        splitter.addWidget(left_widget)
        
        # Right panel: Preview
        right_widget = self._create_preview_panel()
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setSizes([500, 900])
        layout.addWidget(splitter)
        
        # Bottom: Output directory and actions
        bottom_widget = self._create_bottom_panel()
        layout.addWidget(bottom_widget)
    
    def _create_segments_panel(self) -> QWidget:
        """Create the segments list panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Split")
        add_btn.setToolTip("Add a new split point at selected page")
        add_btn.clicked.connect(self._add_split)
        toolbar.addWidget(add_btn)
        
        merge_btn = QPushButton("🔄 Merge")
        merge_btn.setToolTip("Merge selected segments")
        merge_btn.clicked.connect(self._merge_segments)
        toolbar.addWidget(merge_btn)
        
        toolbar.addStretch()
        
        refresh_btn = QPushButton("🔄 Re-analyze")
        refresh_btn.clicked.connect(self._reanalyze)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Segments list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.segments_container = QWidget()
        self.segments_layout = QVBoxLayout(self.segments_container)
        self.segments_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.segments_layout.setSpacing(8)
        
        scroll.setWidget(self.segments_container)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_preview_panel(self) -> QWidget:
        """Create the page preview panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Page selector
        selector_layout = QHBoxLayout()
        
        prev_btn = QPushButton("◀ Previous")
        prev_btn.clicked.connect(self._prev_page)
        selector_layout.addWidget(prev_btn)
        
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(self.analysis_result.total_pages)
        self.page_spinbox.valueChanged.connect(self._page_changed)
        selector_layout.addWidget(self.page_spinbox)
        
        of_label = QLabel(f"of {self.analysis_result.total_pages}")
        selector_layout.addWidget(of_label)
        
        next_btn = QPushButton("Next ▶")
        next_btn.clicked.connect(self._next_page)
        selector_layout.addWidget(next_btn)
        
        selector_layout.addStretch()
        
        # Mark as blank button
        self.blank_btn = QPushButton("⚪ Mark as Blank")
        self.blank_btn.setCheckable(True)
        self.blank_btn.clicked.connect(self._toggle_blank)
        selector_layout.addWidget(self.blank_btn)
        
        layout.addLayout(selector_layout)
        
        # Preview area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Page content will appear here...")
        layout.addWidget(self.preview_text)
        
        # Page info
        self.page_info_label = QLabel()
        self.page_info_label.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(self.page_info_label)
        
        return widget
    
    def _create_bottom_panel(self) -> QWidget:
        """Create the bottom actions panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #ccc;")
        layout.addWidget(line)
        
        # Output directory
        dir_layout = QHBoxLayout()
        dir_label = QLabel("📁 Output Directory:")
        dir_layout.addWidget(dir_label)
        
        self.dir_edit = QLineEdit(str(self.output_directory))
        self.dir_edit.setReadOnly(True)
        dir_layout.addWidget(self.dir_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(browse_btn)
        
        layout.addLayout(dir_layout)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self._reject_splits)
        actions_layout.addWidget(cancel_btn)
        
        self.accept_btn = QPushButton("✅ Accept & Split Documents")
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        self.accept_btn.clicked.connect(self._accept_splits)
        actions_layout.addWidget(self.accept_btn)
        
        layout.addLayout(actions_layout)
        
        return widget
    
    def _populate_segments(self):
        """Populate the segments list."""
        # Clear existing
        while self.segments_layout.count():
            item = self.segments_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add segment widgets
        for i, segment in enumerate(self.segments):
            segment_widget = SegmentListItem(segment, i)
            self.segments_layout.addWidget(segment_widget)
        
        # Add stretch at end
        self.segments_layout.addStretch()
    
    def _page_changed(self, page_num: int):
        """Handle page selection change."""
        # Update preview (would load actual page content in production)
        self.preview_text.setText(f"Preview of page {page_num}\n\n(Content would be extracted here)")
        
        # Find which segment this page belongs to
        for segment in self.segments:
            if segment.start_page <= page_num <= segment.end_page:
                self.page_info_label.setText(
                    f"Page {page_num} is part of: {segment.suggested_filename}"
                )
                break
    
    def _prev_page(self):
        """Go to previous page."""
        current = self.page_spinbox.value()
        if current > 1:
            self.page_spinbox.setValue(current - 1)
    
    def _next_page(self):
        """Go to next page."""
        current = self.page_spinbox.value()
        if current < self.analysis_result.total_pages:
            self.page_spinbox.setValue(current + 1)
    
    def _toggle_blank(self):
        """Toggle current page as blank."""
        page_num = self.page_spinbox.value()
        is_blank = self.blank_btn.isChecked()
        
        if is_blank:
            self.blank_btn.setText("⚪ Marked as Blank")
            self.blank_btn.setStyleSheet("background-color: #fef3c7;")
        else:
            self.blank_btn.setText("⚪ Mark as Blank")
            self.blank_btn.setStyleSheet("")
        
        # In production, this would update the analysis
        logger.info(f"Page {page_num} marked as blank: {is_blank}")
    
    def _add_split(self):
        """Add a new split point."""
        page_num = self.page_spinbox.value()
        
        # Find which segment contains this page
        for i, segment in enumerate(self.segments):
            if segment.start_page <= page_num <= segment.end_page:
                if page_num > segment.start_page and page_num <= segment.end_page:
                    # Split this segment
                    # In production, this would actually split the segment
                    QMessageBox.information(
                        self, "Add Split",
                        f"Would add split at page {page_num}\n\n"
                        f"(Full implementation would split segment {i+1})"
                    )
                    return
        
        QMessageBox.warning(
            self, "Cannot Split",
            "Cannot add split at this location."
        )
    
    def _merge_segments(self):
        """Merge selected segments."""
        QMessageBox.information(
            self, "Merge Segments",
            "Select two adjacent segments to merge them.\n\n"
            "(Full implementation would allow multi-select and merge)"
        )
    
    def _reanalyze(self):
        """Re-run analysis with current settings."""
        reply = QMessageBox.question(
            self, "Re-analyze",
            "This will discard any manual changes. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # In production, this would re-run the analyzer
            QMessageBox.information(
                self, "Re-analyze",
                "Re-analysis would run here with adjusted parameters."
            )
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", str(self.output_directory)
        )
        
        if dir_path:
            self.output_directory = Path(dir_path)
            self.dir_edit.setText(dir_path)
    
    def _accept_splits(self):
        """Accept the proposed splits."""
        # Collect filenames from edits
        updated_segments = []
        
        # In production, this would collect the actual edited filenames
        # from the segment widgets
        
        # Show confirmation
        msg = f"Will create {len(self.segments)} documents in:\n{self.output_directory}"
        
        reply = QMessageBox.question(
            self, "Confirm Split",
            msg + "\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.segments_accepted.emit(self.segments, self.output_directory)
            self.accept()
    
    def _reject_splits(self):
        """Reject the proposed splits."""
        reply = QMessageBox.question(
            self, "Cancel",
            "Discard all changes and close?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.segments_rejected.emit()
            self.reject()
    
    def get_segment_filenames(self) -> List[str]:
        """Get the (possibly edited) filenames for each segment."""
        filenames = []
        
        # In production, iterate through segment widgets and collect edited filenames
        for segment in self.segments:
            filenames.append(segment.suggested_filename)
        
        return filenames


def show_multi_page_review(analysis_result: MultiPageAnalysisResult,
                           source_pdf_path: Path,
                           parent=None) -> Optional[MultiPageReviewDialog]:
    """
    Convenience function to show the multi-page review dialog.
    
    Args:
        analysis_result: Result from multi-page analyzer
        source_pdf_path: Path to source PDF
        parent: Parent widget
        
    Returns:
        Dialog instance if shown, None otherwise
    """
    dialog = MultiPageReviewDialog(analysis_result, source_pdf_path, parent)
    
    # Connect signals
    dialog.segments_accepted.connect(
        lambda segs, out_dir: logger.info(f"Accepted {len(segs)} segments to {out_dir}")
    )
    dialog.segments_rejected.connect(
        lambda: logger.info("Segments rejected")
    )
    
    return dialog
