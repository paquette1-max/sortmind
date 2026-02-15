"""
Main application window for AI File Organizer.
Enhanced with world-class UI features: empty states, skeleton loading,
improved keyboard navigation, and comprehensive tooltips.
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QLabel, QStatusBar,
    QMenuBar, QMenu, QToolBar, QFileDialog, QMessageBox,
    QStackedWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QFont

import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with world-class UX."""
    
    # Signals
    directory_selected = pyqtSignal(Path)
    analyze_requested = pyqtSignal()
    intelligent_analyze_requested = pyqtSignal()
    organize_requested = pyqtSignal()
    undo_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    rules_requested = pyqtSignal()
    duplicates_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    license_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SortMind")
        self.resize(1400, 900)
        
        # Store references to UI components
        self.current_directory = None
        self.status_label = None
        self.file_count_label = None
        self.empty_state_widget = None
        self.skeleton_widget = None
        self.results_stack = None
        
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_keyboard_shortcuts()
        
        logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup main UI layout with proper visual hierarchy."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Directory selection section (clear hierarchy)
        dir_section = self._create_directory_section()
        main_layout.addWidget(dir_section)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("sectionSeparator")
        main_layout.addWidget(separator)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setObjectName("mainSplitter")
        
        # Left panel: Directory info and actions
        left_widget = self._create_left_panel()
        splitter.addWidget(left_widget)
        
        # Center panel: Results with stacked widget for states
        center_widget = self._create_center_panel()
        splitter.addWidget(center_widget)
        
        # Right panel: Preview (will be set by controller)
        self.preview_container = QWidget()
        self.preview_container.setObjectName("previewContainer")
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_placeholder = QLabel("Preview Panel")
        preview_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_placeholder.setObjectName("previewPlaceholder")
        preview_layout.addWidget(preview_placeholder)
        splitter.addWidget(self.preview_container)
        
        # Set stretch factors (center gets more space)
        splitter.setStretchFactor(0, 1)  # Left panel
        splitter.setStretchFactor(1, 3)  # Results table
        splitter.setStretchFactor(2, 1)  # Preview panel
        
        # Set initial sizes
        splitter.setSizes([250, 700, 350])
        
        main_layout.addWidget(splitter, 1)  # Give it stretch
        
        central_widget.setLayout(main_layout)
    
    def _create_directory_section(self) -> QWidget:
        """Create the directory selection section with clear hierarchy."""
        section = QWidget()
        section.setObjectName("directorySection")
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Label
        dir_label = QLabel("📁 Directory:")
        dir_label.setObjectName("sectionLabel")
        font = QFont()
        font.setWeight(QFont.Weight.Medium)
        dir_label.setFont(font)
        layout.addWidget(dir_label)
        
        # Path display (read-only, prominent)
        self.dir_label = QLabel("No directory selected")
        self.dir_label.setObjectName("directoryPathLabel")
        self.dir_label.setMinimumWidth(400)
        self.dir_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        font = QFont()
        font.setPointSize(13)
        self.dir_label.setFont(font)
        layout.addWidget(self.dir_label, 1)
        
        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setToolTip("Select a folder to organize (Shortcut: Ctrl+O)")
        browse_btn.setStatusTip("Open file browser to select a directory")
        browse_btn.setMinimumWidth(100)
        browse_btn.clicked.connect(self._browse_directory)
        layout.addWidget(browse_btn)
        
        return section
    
    def _create_left_panel(self) -> QWidget:
        """Create the left panel with actions and info."""
        widget = QWidget()
        widget.setObjectName("leftPanel")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)
        
        # File count info card
        info_card = QFrame()
        info_card.setObjectName("infoCard")
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(8)
        
        info_header = QLabel("📊 Folder Info")
        info_header.setObjectName("cardHeader")
        font = QFont()
        font.setWeight(QFont.Weight.Medium)
        info_header.setFont(font)
        info_layout.addWidget(info_header)
        
        self.file_count_label = QLabel("Files found: 0")
        self.file_count_label.setObjectName("fileCountLabel")
        self.file_count_label.setToolTip("Number of files in the selected folder (not including subfolders)")
        info_layout.addWidget(self.file_count_label)
        
        self.folder_name_label = QLabel("")
        self.folder_name_label.setObjectName("folderNameLabel")
        self.folder_name_label.setWordWrap(True)
        info_layout.addWidget(self.folder_name_label)
        
        layout.addWidget(info_card)
        
        # Action buttons section
        actions_header = QLabel("🚀 Actions")
        actions_header.setObjectName("sectionHeader")
        font = QFont()
        font.setWeight(QFont.Weight.Medium)
        actions_header.setFont(font)
        layout.addWidget(actions_header)
        
        # Analyze button (primary)
        self.analyze_btn = QPushButton("🔍 Quick Analyze")
        self.analyze_btn.setObjectName("primaryButton")
        self.analyze_btn.setToolTip(
            "Quick analysis using file extensions and basic patterns\n"
            "Fast but less accurate than intelligent analysis"
        )
        self.analyze_btn.setStatusTip("Quick analysis based on file types")
        self.analyze_btn.setMinimumHeight(40)
        self.analyze_btn.clicked.connect(self.analyze_requested.emit)
        self.analyze_btn.setEnabled(False)  # Disabled until directory selected
        layout.addWidget(self.analyze_btn)
        
        # Intelligent analyze button (primary, highlighted)
        self.intelligent_analyze_btn = QPushButton("🧠 Intelligent Analyze")
        self.intelligent_analyze_btn.setObjectName("intelligentButton")
        self.intelligent_analyze_btn.setToolTip(
            "Deep document analysis using local AI (Ollama)\n"
            "• Pass 1: Pattern matching for common documents\n"
            "• Pass 2: LLM content analysis\n"
            "• Pass 3: Manual review for uncertain items\n"
            "Reads document contents to suggest descriptive filenames"
        )
        self.intelligent_analyze_btn.setStatusTip("Analyze document contents with local AI")
        self.intelligent_analyze_btn.setMinimumHeight(48)
        self.intelligent_analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
            QPushButton:disabled {
                background-color: #4B5563;
                color: #9CA3AF;
            }
        """)
        self.intelligent_analyze_btn.clicked.connect(self.intelligent_analyze_requested.emit)
        self.intelligent_analyze_btn.setEnabled(False)
        layout.addWidget(self.intelligent_analyze_btn)
        
        # Organize button (primary, disabled until analysis)
        self.organize_btn = QPushButton("📁 Organize Files")
        self.organize_btn.setObjectName("primaryButton")
        self.organize_btn.setToolTip(
            "Apply organization suggestions to files\n"
            "Creates a backup first - you can undo if needed"
        )
        self.organize_btn.setStatusTip("Apply the suggested organization to your files")
        self.organize_btn.setMinimumHeight(40)
        self.organize_btn.setEnabled(False)
        self.organize_btn.clicked.connect(self.organize_requested.emit)
        layout.addWidget(self.organize_btn)
        
        # Secondary actions
        secondary_header = QLabel("⚙️ Tools")
        secondary_header.setObjectName("sectionHeader")
        font = QFont()
        font.setWeight(QFont.Weight.Medium)
        secondary_header.setFont(font)
        layout.addWidget(secondary_header)
        
        # Undo button
        undo_btn = QPushButton("↩️ Undo Last")
        undo_btn.setObjectName("secondaryButton")
        undo_btn.setToolTip("Undo the last organization operation (Shortcut: Ctrl+Z)")
        undo_btn.setStatusTip("Restore files to their previous locations")
        undo_btn.clicked.connect(self.undo_requested.emit)
        layout.addWidget(undo_btn)
        
        # Find duplicates button
        duplicates_btn = QPushButton("📑 Find Duplicates")
        duplicates_btn.setObjectName("secondaryButton")
        duplicates_btn.setToolTip("Scan for duplicate files to free up space (Shortcut: Ctrl+D)")
        duplicates_btn.setStatusTip("Find and remove duplicate files")
        duplicates_btn.clicked.connect(self.duplicates_requested.emit)
        layout.addWidget(duplicates_btn)
        
        # Rules button
        rules_btn = QPushButton("📋 Rules...")
        rules_btn.setObjectName("secondaryButton")
        rules_btn.setToolTip("Customize organization rules (Shortcut: Ctrl+R)")
        rules_btn.setStatusTip("Configure custom organization rules")
        rules_btn.clicked.connect(self.rules_requested.emit)
        layout.addWidget(rules_btn)
        
        # Settings button
        settings_btn = QPushButton("⚙️ Settings...")
        settings_btn.setObjectName("ghostButton")
        settings_btn.setToolTip("Configure application settings (Shortcut: Ctrl+,)")
        settings_btn.setStatusTip("Open settings dialog")
        settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(settings_btn)
        
        layout.addStretch()
        
        return widget
    
    def _create_center_panel(self) -> QWidget:
        """Create the center panel with stacked widget for different states."""
        widget = QWidget()
        widget.setObjectName("centerPanel")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)
        
        # Results header with count
        header_layout = QHBoxLayout()
        
        self.results_header = QLabel("Analysis Results")
        self.results_header.setObjectName("resultsHeader")
        font = QFont()
        font.setPointSize(14)
        font.setWeight(QFont.Weight.DemiBold)
        self.results_header.setFont(font)
        header_layout.addWidget(self.results_header)
        
        self.results_count_label = QLabel("")
        self.results_count_label.setObjectName("resultsCountLabel")
        header_layout.addWidget(self.results_count_label)
        
        # Selection count label
        self.selection_count_label = QLabel("")
        self.selection_count_label.setObjectName("selectionCountLabel")
        header_layout.addWidget(self.selection_count_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Filter widget placeholder (will be set by controller)
        self.filter_widget_container = QWidget()
        self.filter_widget_container.setObjectName("filterWidgetContainer")
        filter_layout = QVBoxLayout(self.filter_widget_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.filter_widget_container)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Stacked widget for different states
        self.results_stack = QStackedWidget()
        self.results_stack.setObjectName("resultsStack")
        
        # Page 0: Empty state
        self.empty_state_widget = None  # Will be set by controller
        
        # Page 1: Skeleton loading
        from .widgets.skeleton_loading import SkeletonLoadingWidget
        self.skeleton_widget = SkeletonLoadingWidget(preset='table')
        self.results_stack.addWidget(self.skeleton_widget)
        
        # Page 2: Results table (placeholder, will be replaced)
        self.results_placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self.results_placeholder)
        placeholder_label = QLabel("Results will appear here")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(placeholder_label)
        self.results_stack.addWidget(self.results_placeholder)
        
        layout.addWidget(self.results_stack, 1)
        
        return widget
    
    def _setup_menu_bar(self):
        """Setup menu bar with comprehensive keyboard shortcuts."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.setToolTipsVisible(True)
        
        open_action = QAction("&Open Directory...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Select a directory to organize")
        open_action.triggered.connect(self._browse_directory)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.setStatusTip("Rescan the current directory")
        refresh_action.triggered.connect(self.refresh_requested.emit)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Close the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.setToolTipsVisible(True)
        
        undo_action = QAction("&Undo Last Operation", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setStatusTip("Undo the last file organization")
        undo_action.triggered.connect(self.undo_requested.emit)
        edit_menu.addAction(undo_action)
        
        edit_menu.addSeparator()
        
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.setStatusTip("Select all files in the results table")
        edit_menu.addAction(select_all_action)
        
        edit_menu.addSeparator()
        
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.setStatusTip("Configure application settings")
        settings_action.triggered.connect(self.settings_requested.emit)
        edit_menu.addAction(settings_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.setToolTipsVisible(True)
        
        analyze_action = QAction("&Analyze Files", self)
        analyze_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
        analyze_action.setStatusTip("Analyze files to get organization suggestions")
        analyze_action.triggered.connect(self.analyze_requested.emit)
        tools_menu.addAction(analyze_action)
        
        organize_action = QAction("&Organize Files", self)
        organize_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        organize_action.setStatusTip("Apply organization suggestions")
        organize_action.triggered.connect(self.organize_requested.emit)
        tools_menu.addAction(organize_action)
        
        tools_menu.addSeparator()
        
        rules_action = QAction("Organization &Rules...", self)
        rules_action.setShortcut(QKeySequence("Ctrl+R"))
        rules_action.setStatusTip("Customize organization rules")
        rules_action.triggered.connect(self.rules_requested.emit)
        tools_menu.addAction(rules_action)
        
        duplicates_action = QAction("&Find Duplicates...", self)
        duplicates_action.setShortcut(QKeySequence("Ctrl+D"))
        duplicates_action.setStatusTip("Find and remove duplicate files")
        duplicates_action.triggered.connect(self.duplicates_requested.emit)
        tools_menu.addAction(duplicates_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.setToolTipsVisible(True)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.setToolTipsVisible(True)
        
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setStatusTip("View available keyboard shortcuts")
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        license_action = QAction("🔒 &License...", self)
        license_action.setStatusTip("Manage your Pro license")
        license_action.triggered.connect(self.license_requested.emit)
        help_menu.addAction(license_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("&About", self)
        about_action.setStatusTip("About SortMind")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup toolbar with commonly used actions."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setObjectName("mainToolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # Open action
        open_action = QAction("Open", self)
        open_action.setStatusTip("Open directory (Ctrl+O)")
        open_action.triggered.connect(self._browse_directory)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # Analyze action
        analyze_action = QAction("Analyze", self)
        analyze_action.setStatusTip("Analyze files")
        analyze_action.triggered.connect(self.analyze_requested.emit)
        toolbar.addAction(analyze_action)
        
        # Organize action
        organize_action = QAction("Organize", self)
        organize_action.setStatusTip("Organize files")
        organize_action.triggered.connect(self.organize_requested.emit)
        toolbar.addAction(organize_action)
        
        toolbar.addSeparator()
        
        # Undo action
        undo_action = QAction("Undo", self)
        undo_action.setStatusTip("Undo last operation (Ctrl+Z)")
        undo_action.triggered.connect(self.undo_requested.emit)
        toolbar.addAction(undo_action)
    
    def _setup_status_bar(self):
        """Setup status bar with clear information hierarchy."""
        statusbar = self.statusBar()
        statusbar.setObjectName("mainStatusBar")
        
        # Primary status message
        self.status_label = QLabel("Ready - Select a directory to begin")
        self.status_label.setObjectName("statusLabel")
        statusbar.addWidget(self.status_label, 3)
        
        # Secondary info
        self.dir_info_label = QLabel("")
        self.dir_info_label.setObjectName("dirInfoLabel")
        statusbar.addWidget(self.dir_info_label, 1)
    
    def _setup_keyboard_shortcuts(self):
        """Setup additional keyboard shortcuts."""
        # Escape to close dialogs or cancel operations
        self.shortcut_escape = QAction("Escape", self)
        self.shortcut_escape.setShortcut(QKeySequence("Escape"))
        self.shortcut_escape.triggered.connect(self._handle_escape)
        self.addAction(self.shortcut_escape)
        
        # F1 for help
        self.shortcut_help = QAction("Help", self)
        self.shortcut_help.setShortcut(QKeySequence("F1"))
        self.shortcut_help.triggered.connect(self._show_shortcuts)
        self.addAction(self.shortcut_help)
    
    def _handle_escape(self):
        """Handle escape key press."""
        # Could be used to cancel operations or close dialogs
        logger.debug("Escape key pressed")
    
    def _browse_directory(self):
        """Open directory browser dialog with better UX."""
        initial_dir = str(self.current_directory) if self.current_directory else str(Path.home())
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Organize",
            initial_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            path = Path(directory)
            self.current_directory = path
            self.dir_label.setText(str(path))
            self.folder_name_label.setText(f"Folder: {path.name}")
            self.directory_selected.emit(path)
            logger.info(f"Directory selected: {path}")
    
    def _show_about(self):
        """Show about dialog with helpful information."""
        QMessageBox.about(
            self,
            "About SortMind",
            "<h2>🧠 SortMind v1.0</h2>"
            "<p>AI-powered document organization. 100% local. Privacy-first.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>AI-powered document analysis</li>"
            "<li>Intelligent file naming</li>"
            "<li>Duplicate file detection</li>"
            "<li>Custom organization rules</li>"
            "<li>Safe undo operations</li>"
            "</ul>"
            "<p>© 2026 <a href='https://github.com/ash-works'>ash-works</a></p>"
        )
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
        <h2>Keyboard Shortcuts</h2>
        <table>
        <tr><td><b>Ctrl+O</b></td><td>Open directory</td></tr>
        <tr><td><b>Ctrl+Shift+A</b></td><td>Analyze files</td></tr>
        <tr><td><b>Ctrl+Shift+O</b></td><td>Organize files</td></tr>
        <tr><td><b>Ctrl+Z</b></td><td>Undo last operation</td></tr>
        <tr><td><b>Ctrl+R</b></td><td>Organization rules</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Find duplicates</td></tr>
        <tr><td><b>Ctrl+,</b></td><td>Settings</td></tr>
        <tr><td><b>F5</b></td><td>Refresh</td></tr>
        <tr><td><b>Ctrl+A</b></td><td>Select all files</td></tr>
        <tr><td><b>F1</b></td><td>Show help</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Exit</td></tr>
        </table>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Keyboard Shortcuts")
        msg_box.setText(shortcuts_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    # Public API methods
    
    def set_status(self, message: str, timeout: int = 0):
        """
        Update status bar message.
        
        Args:
            message: Status message to display
            timeout: How long to show (0 = persistent)
        """
        if self.status_label:
            self.status_label.setText(message)
        self.statusBar().showMessage(message, timeout)
        logger.debug(f"Status: {message}")
    
    def set_file_count(self, count: int):
        """
        Update file count display with clear messaging.
        
        Args:
            count: Number of files found
        """
        if self.file_count_label:
            if count == 0:
                self.file_count_label.setText("📁 Files found: 0")
            elif count == 1:
                self.file_count_label.setText("📁 Files found: 1 file")
            else:
                self.file_count_label.setText(f"📁 Files found: {count} files")
        
        # Update results header count
        if count > 0:
            self.results_count_label.setText(f"({count})")
        else:
            self.results_count_label.setText("")
        
        # Status message
        folder_name = self.current_directory.name if self.current_directory else "selected folder"
        self.set_status(f"Found {count} file(s) in '{folder_name}'")
    
    def set_results_count(self, count: int):
        """Update the results count display."""
        if count > 0:
            self.results_count_label.setText(f"({count} results)")
        else:
            self.results_count_label.setText("")
    
    def enable_analyze(self, enabled: bool = True):
        """Enable/disable analyze buttons with tooltip update."""
        self.analyze_btn.setEnabled(enabled)
        self.intelligent_analyze_btn.setEnabled(enabled)
        if enabled:
            self.analyze_btn.setToolTip(
                "Quick analysis using file extensions and basic patterns\n"
                "Fast but less accurate than intelligent analysis"
            )
            self.intelligent_analyze_btn.setToolTip(
                "Deep document analysis using local AI (Ollama)\n"
                "• Pass 1: Pattern matching for common documents\n"
                "• Pass 2: LLM content analysis\n"
                "• Pass 3: Manual review for uncertain items"
            )
        else:
            self.analyze_btn.setToolTip("Select a directory first to enable analysis")
            self.intelligent_analyze_btn.setToolTip("Select a directory first to enable analysis")
    
    def enable_organize(self, enabled: bool = True):
        """Enable/disable organize button with tooltip update."""
        self.organize_btn.setEnabled(enabled)
        if enabled:
            self.organize_btn.setToolTip(
                "Apply organization suggestions to files\n"
                "Creates a backup first - you can undo if needed"
            )
        else:
            self.organize_btn.setToolTip(
                "Analyze files first to enable organization"
            )
    
    def show_empty_state(self, state_name: str):
        """Show an empty state in the results area."""
        if self.empty_state_widget:
            self.empty_state_widget.set_state(state_name)
            self.results_stack.setCurrentWidget(self.empty_state_widget)
    
    def show_skeleton_loading(self, message: str = "Loading..."):
        """Show skeleton loading animation."""
        self.skeleton_widget.start(message)
        self.results_stack.setCurrentWidget(self.skeleton_widget)
    
    def hide_skeleton_loading(self):
        """Hide skeleton loading animation."""
        self.skeleton_widget.stop()
    
    def set_results_widget(self, widget):
        """Set the results table widget."""
        # Replace placeholder with actual table
        index = self.results_stack.indexOf(self.results_placeholder)
        if index >= 0:
            self.results_stack.removeWidget(self.results_placeholder)
            self.results_placeholder.deleteLater()
        
        self.results_stack.addWidget(widget)
        self.results_stack.setCurrentWidget(widget)
    
    def show_results(self):
        """Show the results table."""
        # Find the results table (should be index 2 or later)
        for i in range(self.results_stack.count()):
            widget = self.results_stack.widget(i)
            if widget != self.empty_state_widget and widget != self.skeleton_widget:
                self.results_stack.setCurrentIndex(i)
                break
    
    def show_error(self, title: str, message: str):
        """Show error message dialog with helpful guidance."""
        logger.error(f"Error shown: {title} - {message}")
        
        # Add helpful context based on error type
        helpful_message = message
        if "permission" in message.lower():
            helpful_message += "\n\nTip: Make sure you have permission to access this folder. Try running as administrator or choosing a different folder."
        elif "not found" in message.lower() or "does not exist" in message.lower():
            helpful_message += "\n\nTip: The file or folder may have been moved or deleted. Try selecting a different folder."
        elif "network" in message.lower() or "connection" in message.lower():
            helpful_message += "\n\nTip: Check your internet connection and try again. If using a local LLM, make sure it's running."
        elif "memory" in message.lower():
            helpful_message += "\n\nTip: Try selecting a smaller folder or closing other applications to free up memory."
        
        QMessageBox.critical(self, title, helpful_message)
    
    def show_info(self, title: str, message: str):
        """Show info message dialog."""
        QMessageBox.information(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """Show warning message dialog."""
        QMessageBox.warning(self, title, message)
    
    def ask_confirmation(self, title: str, message: str) -> bool:
        """Ask user for confirmation with clear options."""
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No for safety
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def set_empty_state_widget(self, widget):
        """Set the empty state widget."""
        self.empty_state_widget = widget
        self.results_stack.insertWidget(0, widget)
    
    def get_current_directory(self) -> Path:
        """Get the currently selected directory."""
        return self.current_directory
    
    def set_filter_widget(self, widget):
        """Set the filter widget in the center panel."""
        # Clear existing layout
        layout = self.filter_widget_container.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new filter widget
        layout.addWidget(widget)
    
    def update_selection_count(self, count: int):
        """Update the selection count display."""
        if count == 0:
            self.selection_count_label.setText("")
            self.selection_count_label.setToolTip("")
        elif count == 1:
            self.selection_count_label.setText("✓ 1 selected")
            self.selection_count_label.setToolTip("1 file selected for organization")
        else:
            self.selection_count_label.setText(f"✓ {count} selected")
            self.selection_count_label.setToolTip(f"{count} files selected for organization")
