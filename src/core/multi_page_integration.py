"""
Integration example for multi-page document scanning in SortMind.

This shows how to add the multi-page scanning feature to the main window.
Add this to your app_controller.py or main_window.py
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import QAction, QFileDialog, QMessageBox

try:
    from ..core.multi_page_analyzer import MultiPageDocumentAnalyzer
    from ..core.document_splitter import MultiPageScanProcessor
    from ..ui.dialogs.multi_page_dialog import show_multi_page_review
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.multi_page_analyzer import MultiPageDocumentAnalyzer
    from core.document_splitter import MultiPageScanProcessor
    from ui.dialogs.multi_page_dialog import show_multi_page_review

logger = logging.getLogger(__name__)


def add_multi_page_scan_menu(main_window, menu_bar):
    """
    Add multi-page scan menu items to the main window.
    
    Args:
        main_window: The main window instance
        menu_bar: The menu bar to add items to
    """
    # Find or create Tools menu
    tools_menu = None
    for action in menu_bar.actions():
        if action.text() == "&Tools":
            tools_menu = action.menu()
            break
    
    if tools_menu is None:
        tools_menu = menu_bar.addMenu("&Tools")
    
    # Add separator if menu has items
    if tools_menu.actions():
        tools_menu.addSeparator()
    
    # Add multi-page scan action
    multi_page_action = QAction("📑 Split Multi-Page Scan...", main_window)
    multi_page_action.setShortcut("Ctrl+M")
    multi_page_action.setStatusTip("Split a multi-page scanned PDF into separate documents")
    multi_page_action.triggered.connect(lambda: on_multi_page_scan(main_window))
    tools_menu.addAction(multi_page_action)
    
    # Add to toolbar if exists
    if hasattr(main_window, 'toolbar'):
        main_window.toolbar.addSeparator()
        main_window.toolbar.addAction(multi_page_action)
    
    logger.info("Multi-page scan menu added")


def on_multi_page_scan(parent_widget):
    """
    Handle multi-page scan menu action.
    
    Args:
        parent_widget: Parent widget for dialogs
    """
    # Show file dialog
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Select Multi-Page PDF to Split",
        str(Path.home()),
        "PDF Files (*.pdf)"
    )
    
    if not file_path:
        return
    
    file_path = Path(file_path)
    
    # Check file size
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > 100:
        reply = QMessageBox.question(
            parent_widget,
            "Large File",
            f"This PDF is {size_mb:.1f} MB. Processing may take a while.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
    
    # Process the PDF
    logger.info(f"Starting multi-page processing for: {file_path}")
    
    try:
        # Create processor
        processor = MultiPageScanProcessor()
        
        # Process
        result = processor.process_pdf(file_path, parent_widget)
        
        # Show results
        if result.success:
            QMessageBox.information(
                parent_widget,
                "Success",
                f"PDF split successfully!\n\n"
                f"Created {len(result.output_files)} documents:\n" +
                "\n".join(f"  • {f.name}" for f in result.output_files[:5]) +
                ("\n  ..." if len(result.output_files) > 5 else "")
            )
        else:
            error_msg = "\n".join(result.errors) if result.errors else "Unknown error"
            QMessageBox.warning(
                parent_widget,
                "Processing Failed",
                f"Could not split PDF:\n\n{error_msg}"
            )
            
    except Exception as e:
        logger.exception("Multi-page processing failed")
        QMessageBox.critical(
            parent_widget,
            "Error",
            f"An error occurred:\n\n{str(e)}"
        )


# Example usage for testing
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = QMainWindow()
    window.setWindowTitle("Multi-Page Scan Test")
    window.resize(600, 400)
    
    central = QWidget()
    layout = QVBoxLayout(central)
    
    label = QLabel("Click the button to test multi-page PDF splitting")
    layout.addWidget(label)
    
    btn = QPushButton("📑 Split Multi-Page PDF")
    btn.clicked.connect(lambda: on_multi_page_scan(window))
    layout.addWidget(btn)
    
    window.setCentralWidget(central)
    
    # Add menu
    menu_bar = window.menuBar()
    add_multi_page_scan_menu(window, menu_bar)
    
    window.show()
    sys.exit(app.exec())
