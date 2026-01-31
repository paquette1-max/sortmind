"""
Results table widget for displaying analysis results.
"""
from pathlib import Path
from typing import List, Dict
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

import logging

logger = logging.getLogger(__name__)


class ResultsTable(QTableWidget):
    """Table widget displaying analysis results."""
    
    selection_changed = pyqtSignal(list)  # Emits list of selected rows
    
    def __init__(self):
        super().__init__()
        self.results = []  # Store results data
        self._setup_table()
        logger.info("Results table initialized")
    
    def _setup_table(self):
        """Setup table columns and behavior."""
        # Set columns
        columns = [
            "Original Path",
            "New Category",
            "New Name",
            "Confidence",
            "Reasoning"
        ]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # Configure header
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        # Configure behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        
        # Connect signals
        self.itemSelectionChanged.connect(self._on_selection_changed)
    
    def add_result(self, result: Dict):
        """Add a result row to the table."""
        row = self.rowCount()
        self.insertRow(row)
        
        # Extract result data
        file_path = result.get("file_path", "Unknown")
        category = result.get("category", "uncategorized")
        suggested_name = result.get("suggested_name", "")
        confidence = result.get("confidence", 0.0)
        reasoning = result.get("reasoning", "")
        
        # Create items
        path_item = QTableWidgetItem(Path(file_path).name)
        category_item = QTableWidgetItem(category)
        name_item = QTableWidgetItem(suggested_name)
        
        # Confidence with color coding
        confidence_text = f"{confidence:.1%}"
        confidence_item = QTableWidgetItem(confidence_text)
        
        # Color code confidence
        if confidence >= 0.85:
            confidence_item.setBackground(QColor("#90EE90"))  # Light green
            confidence_item.setForeground(QColor("#006400"))  # Dark green
        elif confidence >= 0.70:
            confidence_item.setBackground(QColor("#FFD700"))  # Gold
            confidence_item.setForeground(QColor("#8B6914"))  # Dark goldenrod
        else:
            confidence_item.setBackground(QColor("#FFB6C6"))  # Light red
            confidence_item.setForeground(QColor("#8B0000"))  # Dark red
        
        reasoning_item = QTableWidgetItem(reasoning)
        
        # Add items to row
        self.setItem(row, 0, path_item)
        self.setItem(row, 1, category_item)
        self.setItem(row, 2, name_item)
        self.setItem(row, 3, confidence_item)
        self.setItem(row, 4, reasoning_item)
        
        # Store result data
        self.results.append(result)
    
    def clear_results(self):
        """Clear all results from table."""
        self.setRowCount(0)
        self.results = []
        logger.info("Results table cleared")
    
    def get_selected_results(self) -> List[Dict]:
        """Get results that are selected."""
        selected_rows = set()
        for item in self.selectedItems():
            selected_rows.add(item.row())
        
        return [self.results[row] for row in sorted(selected_rows)]
    
    def get_all_results(self) -> List[Dict]:
        """Get all results from table."""
        return self.results.copy()
    
    def update_row_status(self, row: int, status: str):
        """Update status column for a row."""
        if 0 <= row < self.rowCount():
            # Can be extended to show operation status
            logger.debug(f"Row {row} status: {status}")
    
    def _on_selection_changed(self):
        """Handle selection change."""
        selected = self.get_selected_results()
        self.selection_changed.emit(selected)
    
    def select_all(self):
        """Select all results."""
        self.selectAll()
    
    def deselect_all(self):
        """Deselect all results."""
        self.clearSelection()
    
    def get_result_count(self) -> int:
        """Get total number of results."""
        return len(self.results)
    
    def get_selected_count(self) -> int:
        """Get number of selected results."""
        return len(self.get_selected_results())
