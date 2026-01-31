"""
Main application window for AI File Organizer.
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QLabel, QStatusBar,
    QMenuBar, QMenu, QToolBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    directory_selected = pyqtSignal(Path)
    analyze_requested = pyqtSignal()
    organize_requested = pyqtSignal()
    undo_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI File Organizer")
        self.resize(1400, 900)
        
        # Store references to UI components
        self.current_directory = None
        self.status_label = None
        self.file_count_label = None
        
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        
        logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Directory selection and file info
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("Directory:"))
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("No directory selected")
        self.dir_label.setStyleSheet("background-color: #f0f0f0; padding: 8px; border-radius: 4px;")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_directory)
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(browse_btn)
        left_layout.addLayout(dir_layout)
        
        left_layout.addWidget(QLabel("Recent Directories:"))
        self.recent_list = QWidget()  # Placeholder for recent dirs
        left_layout.addWidget(self.recent_list)
        
        left_layout.addStretch()
        
        # Center panel: Results table (will be set by controller)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.addWidget(QLabel("Analysis Results:"))
        self.results_container = QWidget()  # Placeholder for results table
        center_layout.addWidget(self.results_container)
        
        # Add action buttons
        actions_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.analyze_btn.clicked.connect(self.analyze_requested.emit)
        
        self.organize_btn = QPushButton("Organize")
        self.organize_btn.setEnabled(False)
        self.organize_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-weight: bold;")
        self.organize_btn.clicked.connect(self.organize_requested.emit)
        
        actions_layout.addWidget(self.analyze_btn)
        actions_layout.addWidget(self.organize_btn)
        center_layout.addLayout(actions_layout)
        
        # Add panels to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
    
    def _setup_menu_bar(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Directory", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._browse_directory)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo Last Operation", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_requested.emit)
        edit_menu.addAction(undo_action)
        
        edit_menu.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.settings_requested.emit)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        
        open_action = QAction("Open Directory", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._browse_directory)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        analyze_action = QAction("Analyze", self)
        analyze_action.triggered.connect(self.analyze_requested.emit)
        toolbar.addAction(analyze_action)
        
        organize_action = QAction("Organize", self)
        organize_action.triggered.connect(self.organize_requested.emit)
        toolbar.addAction(organize_action)
        
        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.undo_requested.emit)
        toolbar.addAction(undo_action)
        
        toolbar.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        toolbar.addAction(settings_action)
    
    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_label = QLabel("Ready")
        self.file_count_label = QLabel("Files: 0")
        
        statusbar = self.statusBar()
        statusbar.addWidget(self.status_label, 1)
        statusbar.addPermanentWidget(self.file_count_label)
    
    def _browse_directory(self):
        """Open directory browser dialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Organize",
            str(Path.home())
        )
        
        if directory:
            path = Path(directory)
            self.current_directory = path
            self.dir_label.setText(str(path))
            self.directory_selected.emit(path)
            logger.info(f"Directory selected: {path}")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About AI File Organizer",
            "AI File Organizer v1.0\n\n"
            "Intelligently organize your files using AI-powered analysis.\n\n"
            "© 2026"
        )
    
    def set_status(self, message: str):
        """Update status bar message."""
        if self.status_label:
            self.status_label.setText(message)
        # Also display message in the statusBar so tests can read currentMessage()
        self.statusBar().showMessage(message)
    
    def set_file_count(self, count: int):
        """Update file count display."""
        if self.file_count_label:
            self.file_count_label.setText(f"Files: {count}")
        # Reflect in statusBar for tests that read currentMessage()
        self.statusBar().showMessage(f"Files: {count}")
    
    def enable_analyze(self, enabled: bool = True):
        """Enable/disable analyze button."""
        self.analyze_btn.setEnabled(enabled)
    
    def enable_organize(self, enabled: bool = True):
        """Enable/disable organize button."""
        self.organize_btn.setEnabled(enabled)
    
    def show_error(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def show_info(self, title: str, message: str):
        """Show info message dialog."""
        QMessageBox.information(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """Show warning message dialog."""
        QMessageBox.warning(self, title, message)
    
    def ask_confirmation(self, title: str, message: str) -> bool:
        """Ask user for confirmation."""
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
