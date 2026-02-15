"""
Document review dialog for manual verification of uncertain documents.
Third pass of the intelligent analysis pipeline.
"""
import logging
import re
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSplitter, QWidget,
    QLineEdit, QComboBox, QTextEdit, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

try:
    from ...core.intelligent_analyzer import AnalysisResult
    from ...core.content_extractor import ContentExtractor
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.intelligent_analyzer import AnalysisResult
    from core.content_extractor import ContentExtractor

logger = logging.getLogger(__name__)


class DocumentReviewItem(QWidget):
    """Widget for displaying a document needing review."""
    
    def __init__(self, result: AnalysisResult, parent=None):
        super().__init__(parent)
        self.result = result
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # File info
        file_label = QLabel(f"📄 {self.result.file_path.name}")
        file_label.setFont(QFont("", 11, QFont.Weight.Medium))
        layout.addWidget(file_label)
        
        # Reason for review
        reason_label = QLabel(f"⚠️ {self.result.review_reason}")
        reason_label.setStyleSheet("color: #F59E0B;")
        layout.addWidget(reason_label)
        
        # Suggested values (if any)
        if self.result.suggested_name != self.result.file_path.name:
            suggestion = QLabel(f"💡 Suggestion: {self.result.suggested_name}")
            suggestion.setStyleSheet("color: #737373;")
            layout.addWidget(suggestion)


class ReviewWorker(QThread):
    """Worker thread for loading document previews."""

    preview_ready = pyqtSignal(str, str)  # text_content, error

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path
        self.extractor = ContentExtractor()
        self._is_cancelled = False

    def cancel(self):
        """Request cancellation of the worker."""
        self._is_cancelled = True
        self.wait(500)  # Wait up to 500ms for graceful shutdown

    def run(self):
        try:
            if self._is_cancelled:
                return
            content = self.extractor.extract(self.file_path)
            if self._is_cancelled:
                return
            if content.error:
                self.preview_ready.emit("", content.error)
            else:
                self.preview_ready.emit(content.text_content, "")
        except Exception as e:
            if not self._is_cancelled:
                self.preview_ready.emit("", str(e))


class DocumentReviewDialog(QDialog):
    """
    Dialog for manually reviewing documents that couldn't be auto-classified.
    
    Features:
    - Side-by-side document list and preview
    - Quick category buttons
    - Custom filename/folder entry
    - Bulk actions (skip all, accept all suggestions)
    """
    
    # Signals
    document_reviewed = pyqtSignal(Path, str, str, str)  # file, name, folder, category
    batch_complete = pyqtSignal()
    
    def __init__(self, review_items: List[AnalysisResult], parent=None):
        super().__init__(parent)
        self.review_items = review_items
        self.current_index = 0
        self.results = []  # Store user decisions
        self.current_worker: Optional[ReviewWorker] = None
        
        self._setup_ui()
        self._load_current_document()
        
        self.setWindowTitle(f"Review Documents ({len(review_items)} need attention)")
        self.resize(1200, 800)
        
        logger.info(f"DocumentReviewDialog opened with {len(review_items)} items")
    
    def _setup_ui(self):
        """Setup the review UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("📋 Document Review Required")
        header.setObjectName("dialogHeader")
        header_font = QFont("", 16, QFont.Weight.Bold)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Progress
        self.progress_label = QLabel(f"Document 1 of {len(self.review_items)}")
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(len(self.review_items))
        self.progress_bar.setValue(1)
        layout.addWidget(self.progress_bar)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Document list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("Documents to Review:")
        left_layout.addWidget(list_label)
        
        self.doc_list = QListWidget()
        self.doc_list.setMaximumWidth(350)
        self._populate_doc_list()
        self.doc_list.currentRowChanged.connect(self._on_doc_selected)
        left_layout.addWidget(self.doc_list)
        
        # Quick stats
        self.stats_label = QLabel(f"Auto-classified: 0 | Reviewed: 0 | Remaining: {len(self.review_items)}")
        left_layout.addWidget(self.stats_label)
        
        splitter.addWidget(left_panel)
        
        # Right: Preview and editing
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview section
        preview_label = QLabel("📄 Document Preview:")
        right_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("JetBrains Mono, Consolas, monospace", 9))
        self.preview_text.setPlaceholderText("Loading document content...")
        right_layout.addWidget(self.preview_text, 1)
        
        # Classification section
        classify_label = QLabel("🏷️ Classification:")
        right_layout.addWidget(classify_label)
        
        # Quick category buttons
        category_layout = QHBoxLayout()
        
        categories = [
            ("Bank Statement", "Finance/Bank_Statements"),
            ("Credit Card", "Finance/Credit_Cards"),
            ("Utility Bill", "Finance/Utilities"),
            ("Insurance", "Finance/Insurance"),
            ("Medical", "Medical"),
            ("Tax", "Finance/Taxes"),
            ("Receipt", "Finance/Receipts"),
            ("Invoice", "Finance/Invoices"),
            ("Legal", "Legal"),
            ("Other", "Documents")
        ]
        
        for cat_name, folder in categories:
            btn = QPushButton(cat_name)
            btn.setProperty("category", cat_name)
            btn.setProperty("folder", folder)
            btn.clicked.connect(self._on_quick_category)
            btn.setMinimumHeight(32)
            category_layout.addWidget(btn)
        
        right_layout.addLayout(category_layout)
        
        # Custom fields
        fields_layout = QHBoxLayout()
        
        # Filename
        filename_layout = QVBoxLayout()
        filename_label = QLabel("Filename:")
        filename_layout.addWidget(filename_label)
        
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Descriptive_filename_YYYY-MM.pdf")
        filename_layout.addWidget(self.filename_input)
        
        fields_layout.addLayout(filename_layout, 2)
        
        # Folder
        folder_layout = QVBoxLayout()
        folder_label = QLabel("Folder:")
        folder_layout.addWidget(folder_label)
        
        self.folder_input = QComboBox()
        self.folder_input.setEditable(True)
        self.folder_input.addItems([
            "Finance/Bank_Statements",
            "Finance/Credit_Cards",
            "Finance/Utilities",
            "Finance/Insurance",
            "Finance/Taxes",
            "Finance/Receipts",
            "Finance/Invoices",
            "Medical",
            "Legal",
            "Documents",
            "Review_Later"
        ])
        folder_layout.addWidget(self.folder_input)
        
        fields_layout.addLayout(folder_layout, 2)
        
        # Category dropdown
        cat_layout = QVBoxLayout()
        cat_label = QLabel("Category:")
        cat_layout.addWidget(cat_label)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems([
            "Bank_Statement",
            "Credit_Card_Statement",
            "Utility_Bill",
            "Insurance",
            "Medical",
            "Tax_Document",
            "Receipt",
            "Invoice",
            "Legal",
            "Other"
        ])
        cat_layout.addWidget(self.category_input)
        
        fields_layout.addLayout(cat_layout, 1)
        
        right_layout.addLayout(fields_layout)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.skip_btn = QPushButton("⏭️ Skip")
        self.skip_btn.setToolTip("Skip this document for now")
        self.skip_btn.clicked.connect(self._on_skip)
        buttons_layout.addWidget(self.skip_btn)
        
        buttons_layout.addStretch()
        
        self.accept_suggestion_btn = QPushButton("✓ Accept Suggestion")
        self.accept_suggestion_btn.setToolTip("Use the AI suggestion (if available)")
        self.accept_suggestion_btn.clicked.connect(self._on_accept_suggestion)
        self.accept_suggestion_btn.setEnabled(False)
        buttons_layout.addWidget(self.accept_suggestion_btn)
        
        self.save_btn = QPushButton("✓ Save & Next")
        self.save_btn.setToolTip("Save classification and go to next document")
        self.save_btn.setDefault(True)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #22C55E;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #16A34A;
            }
        """)
        self.save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(self.save_btn)
        
        right_layout.addLayout(buttons_layout)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 850])
        
        layout.addWidget(splitter, 1)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        self.skip_all_btn = QPushButton("⏭️ Skip All Remaining")
        self.skip_all_btn.clicked.connect(self._on_skip_all)
        bottom_layout.addWidget(self.skip_all_btn)
        
        bottom_layout.addStretch()
        
        done_btn = QPushButton("Done")
        done_btn.clicked.connect(self._on_done)
        bottom_layout.addWidget(done_btn)
        
        layout.addLayout(bottom_layout)
    
    def _populate_doc_list(self):
        """Populate the document list."""
        for result in self.review_items:
            item = QListWidgetItem()
            
            # Show filename and reason
            text = f"{result.file_path.name}\n"
            if result.suggested_name != result.file_path.name:
                text += f"💡 {result.suggested_name}"
            else:
                text += f"⚠️ {result.review_reason[:50]}..."
            
            item.setText(text)
            self.doc_list.addItem(item)
    
    def _load_current_document(self):
        """Load the current document for review."""
        if self.current_index >= len(self.review_items):
            self._on_done()
            return
        
        result = self.review_items[self.current_index]
        
        # Update UI
        self.progress_label.setText(f"Document {self.current_index + 1} of {len(self.review_items)}")
        self.progress_bar.setValue(self.current_index + 1)
        self.doc_list.setCurrentRow(self.current_index)
        
        # Set suggested values
        self.filename_input.setText(result.suggested_name)
        self.folder_input.setCurrentText(result.suggested_folder.replace("_", " ").title())
        self.category_input.setCurrentText(result.category.replace("_", " ").title())
        
        # Enable accept suggestion if we have a real suggestion
        has_suggestion = result.suggested_name != result.file_path.name
        self.accept_suggestion_btn.setEnabled(has_suggestion)
        
        # Load preview in background
        self.preview_text.setPlainText("Loading document content...")
        self.preview_text.setPlaceholderText("Loading...")

        # Cancel any existing worker gracefully
        if self.current_worker:
            self.current_worker.cancel()
            self.current_worker = None

        self.current_worker = ReviewWorker(result.file_path)
        self.current_worker.preview_ready.connect(self._on_preview_ready)
        self.current_worker.start()
    
    def _on_preview_ready(self, text_content: str, error: str):
        """Handle preview load completion."""
        if error:
            self.preview_text.setPlainText(f"Error loading document:\n{error}")
        else:
            self.preview_text.setPlainText(text_content)
    
    def _on_doc_selected(self, row: int):
        """Handle document selection from list."""
        if row >= 0 and row != self.current_index:
            # Save current if modified?
            self.current_index = row
            self._load_current_document()
    
    def _on_quick_category(self):
        """Handle quick category button click."""
        btn = self.sender()
        category = btn.property("category")
        folder = btn.property("folder")
        
        self.category_input.setCurrentText(category.replace("_", " "))
        self.folder_input.setCurrentText(folder.replace("_", " ").title())
        
        # Auto-generate filename if not set
        if not self.filename_input.text() or self.filename_input.text() == self.review_items[self.current_index].file_path.name:
            result = self.review_items[self.current_index]
            ext = result.file_path.suffix
            suggested = f"{category.replace(' ', '_')}_{result.file_path.stem}{ext}"
            self.filename_input.setText(suggested)
    
    def _on_accept_suggestion(self):
        """Accept the AI suggestion."""
        result = self.review_items[self.current_index]
        self._save_result(
            result.file_path,
            result.suggested_name,
            result.suggested_folder,
            result.category
        )
        self._next_document()
    
    def _on_save(self):
        """Save current classification and move to next."""
        filename = self.filename_input.text().strip()
        folder = self.folder_input.currentText().strip()
        category = self.category_input.currentText().strip()

        if not filename:
            QMessageBox.warning(self, "Missing Filename", "Please enter a filename.")
            return

        # Clean filename - remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

        result = self.review_items[self.current_index]
        self._save_result(result.file_path, filename, folder, category)
        self._next_document()
    
    def _save_result(self, file_path: Path, filename: str, folder: str, category: str):
        """Save a review result."""
        self.results.append({
            "file_path": file_path,
            "filename": filename,
            "folder": folder,
            "category": category
        })
        
        # Emit signal
        self.document_reviewed.emit(file_path, filename, folder, category)
        
        # Update stats
        remaining = len(self.review_items) - len(self.results)
        self.stats_label.setText(f"Reviewed: {len(self.results)} | Remaining: {remaining}")
        
        logger.info(f"Reviewed: {file_path.name} → {filename}")
    
    def _on_skip(self):
        """Skip current document."""
        self._next_document()
    
    def _on_skip_all(self):
        """Skip all remaining documents."""
        reply = QMessageBox.question(
            self,
            "Skip All?",
            f"Skip all {len(self.review_items) - self.current_index} remaining documents?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._on_done()
    
    def _next_document(self):
        """Move to next document."""
        self.current_index += 1
        self._load_current_document()
    
    def _on_done(self):
        """Finish review."""
        # Clean up worker before closing
        if self.current_worker:
            self.current_worker.cancel()
            self.current_worker = None
        self.batch_complete.emit()
        self.accept()

    def closeEvent(self, event):
        """Handle dialog close - clean up worker."""
        if self.current_worker:
            self.current_worker.cancel()
            self.current_worker = None
        event.accept()

    def get_results(self) -> List[dict]:
        """Get all review results."""
        return self.results
