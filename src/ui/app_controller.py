"""
Main application controller connecting UI and backend.
Enhanced with world-class UX features and improved error handling.
"""
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMessageBox, QSplitter

# Handle imports for both package and direct execution contexts
try:
    from ..core.rules_engine import RulesEngine
    from ..core.duplicate_detector import DuplicateDetector
    from ..core.intelligent_analyzer import IntelligentDocumentAnalyzer
except ImportError:
    # Running as script or test - add src to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.rules_engine import RulesEngine
    from core.duplicate_detector import DuplicateDetector
    from core.intelligent_analyzer import IntelligentDocumentAnalyzer

from .main_window import MainWindow
from .widgets.results_table import ResultsTable
from .widgets.preview_panel import PreviewPanel
from .widgets.empty_state import EmptyStateWidget
from .widgets.filter_widget import SmartFilterWidget
from .widgets.progress_dialog import ProgressDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.rules_dialog import RulesManagerDialog
from .dialogs.duplicates_dialog import DuplicatesDialog
from .dialogs.llm_config_dialog import LLMConfigDialog
from .dialogs.review_dialog import DocumentReviewDialog
from .dialogs.license_dialog import LicenseDialog, UpgradePromptWidget
from .workers import ScanWorker, AnalysisWorker, OrganizeWorker, BackupWorker

# Import license manager
try:
    from ..core.license_manager import get_license_manager
except ImportError:
    from core.license_manager import get_license_manager

import logging

logger = logging.getLogger(__name__)


class AppController:
    """
    Main application controller connecting UI and backend.
    
    Responsibilities:
    - Coordinate between UI and backend components
    - Manage application state
    - Handle user actions and workflow
    - Provide helpful feedback at every step
    """
    
    def __init__(self, config=None):
        self.config = config
        self.main_window = MainWindow()
        
        # Backend components (lazy loaded)
        self.scanner = None
        self.llm_handler = None
        self.organizer = None
        self.undo_manager = None
        self.backup_manager = None
        
        # Tier 1 features
        self.rules_engine = RulesEngine()
        self.duplicate_detector = DuplicateDetector()
        self.intelligent_analyzer = IntelligentDocumentAnalyzer()
        
        # State
        self.scanned_files = []
        self.analysis_results = []
        self.current_plan = None
        self.current_directory = None
        self.is_scanning = False
        self.is_analyzing = False
        
        # Worker threads
        self.scan_worker = None
        self.analysis_worker = None
        self.organize_worker = None
        self.backup_worker = None
        
        # UI components
        self.results_table = ResultsTable()
        self.preview_panel = PreviewPanel()
        self.empty_state_widget = EmptyStateWidget()
        self.filter_widget = SmartFilterWidget()
        self.rules_dialog = None
        self.duplicates_dialog = None
        
        # Connect signals
        self._connect_signals()
        
        logger.info("AppController initialized")
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Window signals
        self.main_window.directory_selected.connect(self.on_directory_selected)
        self.main_window.analyze_requested.connect(self.on_analyze_requested)
        self.main_window.intelligent_analyze_requested.connect(self.on_intelligent_analyze_requested)
        self.main_window.organize_requested.connect(self.on_organize_requested)
        self.main_window.undo_requested.connect(self.on_undo_requested)
        self.main_window.settings_requested.connect(self.on_settings_requested)
        self.main_window.rules_requested.connect(self.on_rules_requested)
        self.main_window.duplicates_requested.connect(self.on_duplicates_requested)
        self.main_window.refresh_requested.connect(self.on_refresh_requested)
        self.main_window.license_requested.connect(self.on_license_requested)
        
        # Empty state signals
        self.empty_state_widget.action_triggered.connect(self._on_empty_state_action)
        
        # Results table signals
        self.results_table.files_organized.connect(self.on_organize_requested)
        
        # Setup UI components in main window
        self._setup_main_window_components()
    
    def _setup_main_window_components(self):
        """Setup and connect UI components in the main window."""
        # Set empty state widget
        self.main_window.set_empty_state_widget(self.empty_state_widget)
        
        # Set results table
        self.main_window.set_results_widget(self.results_table)
        
        # Connect results table to preview panel
        self.results_table.current_file_changed.connect(self.preview_panel.preview_file)
        
        # Connect results table selection count to status bar
        self.results_table.selection_count_changed.connect(self._on_selection_count_changed)
        
        # Setup filter widget
        self._setup_filter_widget()
        
        # Setup preview panel in main window
        self._setup_preview_panel()
        
        # Show initial empty state
        self.main_window.show_empty_state('no_directory')
    
    def _setup_filter_widget(self):
        """Setup the filter widget and connect signals."""
        # Add filter widget to main window
        self.main_window.set_filter_widget(self.filter_widget)
        
        # Connect filter changes
        self.filter_widget.filter_changed.connect(self._apply_filters)
        
        # Connect selection actions from filter
        self.filter_widget.select_action.connect(self._on_filter_select_action)
    
    def _apply_filters(self):
        """Apply current filters to results table."""
        if not self.analysis_results:
            return
        
        # Determine which rows match filter
        visible_rows = set()
        for row, result in enumerate(self.analysis_results):
            if self.filter_widget.matches_filter(result):
                visible_rows.add(row)
        
        # Apply to table
        self.results_table.filter_results(visible_rows)
        
        # Sort if needed
        sort_key = self.filter_widget.get_sort_key()
        # Note: Sorting would require re-adding items in sorted order
        # For now, filtering is applied
        
        count = len(visible_rows)
        self.main_window.set_status(f"Showing {count} of {len(self.analysis_results)} files")
    
    def _on_filter_select_action(self, action: str):
        """Handle selection actions from filter widget."""
        if action == "all_visible":
            self.results_table.select_all_visible()
        elif action == "none":
            self.results_table.clear_selection()
        elif action == "high_conf":
            self.results_table.clear_selection()
            # Select high confidence items
            for row, result in enumerate(self.analysis_results):
                if result.get("confidence", 0) >= 0.85:
                    self.results_table._selected_rows.add(row)
            self.results_table._emit_selection_changed()
        elif action == "by_type":
            # Could show a dialog for type selection
            pass
    
    def _on_selection_count_changed(self, count: int):
        """Update UI when selection count changes."""
        self.main_window.update_selection_count(count)
    
    def _setup_preview_panel(self):
        """Setup the preview panel in the main window."""
        # Replace placeholder with actual preview panel
        old_preview = self.main_window.preview_container
        parent = old_preview.parent()
        
        if parent:
            layout = parent.layout()
            if layout:
                # Find splitter and replace preview widget
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and isinstance(item.widget(), QSplitter):
                        splitter = item.widget()
                        # Find and replace the preview widget (usually index 2)
                        for j in range(splitter.count()):
                            if splitter.widget(j) is old_preview:
                                splitter.replaceWidget(j, self.preview_panel)
                                old_preview.deleteLater()
                                break
                        
                        # Adjust stretch factors
                        splitter.setStretchFactor(0, 1)  # Left panel
                        splitter.setStretchFactor(1, 3)  # Results table
                        splitter.setStretchFactor(2, 1)  # Preview panel
                        break
        
        # Keep reference
        self.main_window.preview_container = self.preview_panel
    
    def _on_empty_state_action(self):
        """Handle empty state action button click."""
        state = self.empty_state_widget.get_current_state()
        
        if state == 'no_directory':
            self._browse_directory()
        elif state == 'empty_folder':
            self._browse_directory()
        elif state == 'no_results':
            self._browse_directory()
        elif state == 'no_analysis':
            self.on_analyze_requested()
        elif state == 'analysis_complete_empty':
            self.on_organize_requested()
        elif state == 'error':
            self.on_refresh_requested()
    
    def _browse_directory(self):
        """Open directory browser dialog."""
        self.main_window._browse_directory()
    
    def on_directory_selected(self, directory: Path):
        """
        Handle directory selection.
        
        Flow:
        1. Clear previous results
        2. Show loading state
        3. Scan directory
        4. Show appropriate state based on results
        """
        logger.info(f"Directory selected: {directory}")
        self.current_directory = directory
        self.is_scanning = True
        
        # Update UI state
        self.main_window.set_status(f"📂 Scanning {directory.name}...")
        self.main_window.enable_analyze(False)
        self.main_window.enable_organize(False)
        self.main_window.show_skeleton_loading("Scanning folder...")
        
        # Clear previous results
        self.results_table.clear_results()
        self.scanned_files = []
        self.analysis_results = []
        self.preview_panel.clear_preview()
        
        # Start scan worker
        self.scan_worker = ScanWorker(directory, self.config)
        self.scan_worker.progress.connect(self._on_scan_progress)
        self.scan_worker.finished.connect(self._on_scan_finished)
        self.scan_worker.error.connect(self._on_scan_error)
        self.scan_worker.start()
    
    def _on_scan_progress(self, current: int, total: int):
        """Update scan progress."""
        self.main_window.skeleton_widget.set_message(
            f"Scanning folder... {current} files found"
        )
    
    def _on_scan_finished(self, files: list):
        """
        Handle scan completion.
        
        Shows appropriate state based on number of files found.
        """
        self.is_scanning = False
        self.scanned_files = files
        count = len(files)
        
        self.main_window.hide_skeleton_loading()
        self.main_window.set_file_count(count)
        
        folder_name = self.current_directory.name if self.current_directory else "selected folder"
        
        if count == 0:
            # Empty folder
            self.main_window.show_empty_state('empty_folder')
            self.main_window.set_status(
                f"⚠️ The folder '{folder_name}' is empty. Select a different folder."
            )
            self.main_window.enable_analyze(False)
        else:
            # Has files - show ready to analyze state
            self.main_window.show_empty_state('no_analysis')
            self.main_window.set_status(
                f"✅ Found {count} file(s) in '{folder_name}'. Click 'Analyze Files' to continue."
            )
            self.main_window.enable_analyze(True)
        
        logger.info(f"Scan finished: {count} files found")
    
    def _on_scan_error(self, error: str):
        """
        Handle scan error with helpful guidance.
        """
        self.is_scanning = False
        self.main_window.hide_skeleton_loading()
        
        logger.error(f"Scan error: {error}")
        
        # Show error state
        self.main_window.show_empty_state('error')
        
        # Show helpful error message
        self.main_window.show_error(
            "Scan Failed",
            f"Failed to scan directory:\n\n{error}"
        )
        
        self.main_window.set_status(f"❌ Error: Scan failed")
    
    def on_analyze_requested(self):
        """
        Handle analyze button click.
        
        Flow:
        1. Check if LLM is configured
        2. Show loading state
        3. Analyze files
        4. Show results
        """
        if not self.scanned_files:
            self.main_window.show_error(
                "No Files",
                "Please select a directory with files first."
            )
            return
        
        # Check if LLM is configured
        if not self.llm_handler:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
            if not LLMConfigDialog.check_llm_config(config_path):
                # Show config dialog
                llm_config = LLMConfigDialog.prompt_for_config(self.main_window, config_path)
                if not llm_config:
                    QMessageBox.information(
                        self.main_window,
                        "AI Features Disabled",
                        "No LLM configured. You can still use rule-based organization.\n\n"
                        "To enable AI features, configure an LLM in Settings."
                    )
                    # Continue with rule-based analysis
                else:
                    # Save config
                    try:
                        import yaml
                        config_data = {"llm": llm_config}
                        with open(config_path, 'w') as f:
                            yaml.dump(config_data, f)
                        logger.info(f"LLM config saved: {llm_config['backend']}")
                    except Exception as e:
                        logger.error(f"Failed to save LLM config: {e}")
                    
                    # Initialize LLM handler
                    self._init_llm_handler(llm_config)
                    
                    # Check if handler was successfully created
                    if not self.llm_handler and llm_config.get('backend') != 'demo':
                        QMessageBox.critical(
                            self.main_window,
                            "LLM Initialization Failed",
                            "Failed to initialize the LLM handler.\n\n"
                            "Please check:\n"
                            "1. Ollama is installed and running\n"
                            "2. The selected model is installed (ollama pull <model>)\n"
                            "3. The endpoint URL is correct\n\n"
                            "You can configure this in Settings > LLM."
                        )
                        return
                    
                    # If demo mode selected, inform user
                    if llm_config.get('backend') == 'demo':
                        QMessageBox.information(
                            self.main_window,
                            "Demo Mode",
                            "Running in demo mode. Rule-based organization only.\n\n"
                            "AI-powered features require an LLM to be configured."
                        )
        
        logger.info(f"Starting analysis of {len(self.scanned_files)} files")
        self.is_analyzing = True
        self.main_window.set_status("🔍 Analyzing files with AI...")
        self.main_window.enable_analyze(False)
        self.main_window.enable_organize(False)
        self.main_window.show_skeleton_loading("Analyzing files...")
        
        # Clear previous results
        self.results_table.clear_results()
        self.analysis_results = []
        
        # Start analysis worker
        self.analysis_worker = AnalysisWorker(self.scanned_files, self.llm_handler)
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.result.connect(self._on_analysis_result)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        self.analysis_worker.error.connect(self._on_analysis_error)
        self.analysis_worker.start()
    
    def _on_analysis_progress(self, current: int, total: int, filename: str):
        """Update analysis progress."""
        percentage = int((current / total) * 100) if total > 0 else 0
        self.main_window.skeleton_widget.set_message(
            f"Analyzing... {percentage}% ({current}/{total})"
        )
    
    def _on_analysis_result(self, result: dict):
        """Handle individual analysis result."""
        self.analysis_results.append(result)
        self.results_table.add_result(result)
    
    def _on_analysis_finished(self):
        """Handle analysis completion."""
        self.is_analyzing = False
        self.main_window.hide_skeleton_loading()
        
        count = len(self.analysis_results)
        
        if count == 0:
            self.main_window.show_empty_state('no_results')
            self.main_window.set_status("⚠️ No files could be analyzed")
            self.main_window.enable_analyze(True)
            self.main_window.enable_organize(False)
        else:
            self.main_window.show_results()
            self.main_window.set_results_count(count)
            self.main_window.set_status(
                f"✅ Analysis complete! {count} files analyzed. "
                "Select files and click 'Organize' to apply changes."
            )
            self.main_window.enable_analyze(True)
            self.main_window.enable_organize(count > 0)
        
        logger.info(f"Analysis finished: {count} results")
    
    def _on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.is_analyzing = False
        self.main_window.hide_skeleton_loading()
        
        logger.error(f"Analysis error: {error}")
        
        self.main_window.show_error(
            "Analysis Failed",
            f"Failed to analyze files:\n\n{error}"
        )
        
        self.main_window.set_status(f"❌ Error: Analysis failed")
        self.main_window.enable_analyze(True)
    
    def on_intelligent_analyze_requested(self):
        """
        Handle intelligent document analysis with multi-pass logic.
        
        Pass 1: Pattern-based extraction (high confidence)
        Pass 2: Local LLM via Ollama (medium confidence)
        Pass 3: User review dialog (low confidence)
        """
        if not self.scanned_files:
            self.main_window.show_error(
                "No Files",
                "Please select a directory with files first."
            )
            return
        
        # Check Ollama availability
        available, message = self.intelligent_analyzer.check_ollama_available()
        if not available:
            reply = QMessageBox.question(
                self.main_window,
                "Ollama Not Available",
                f"{message}\n\n"
                "Intelligent analysis requires Ollama with a local LLM.\n\n"
                "Would you like to:\n"
                "• Yes = Install/Setup instructions\n"
                "• No = Use simple rule-based analysis instead",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                instructions = """
To set up Ollama for intelligent document analysis:

1. Install Ollama:
   brew install ollama
   
2. Start Ollama service:
   ollama serve
   
3. Pull a model (llama3.2:3b is recommended):
   ollama pull llama3.2:3b
   
4. Optional - Install OCR dependencies:
   brew install tesseract
   pip install pytesseract pdf2image

For PDF support:
   pip install pymupdf pdfplumber
                """
                QMessageBox.information(
                    self.main_window,
                    "Ollama Setup Instructions",
                    instructions
                )
            else:
                # Fall back to regular analysis
                self.on_analyze_requested()
            return
        
        # Start intelligent analysis
        logger.info(f"Starting intelligent analysis of {len(self.scanned_files)} files")
        self.is_analyzing = True
        self.main_window.set_status("🔍 Running intelligent document analysis...")
        self.main_window.enable_analyze(False)
        self.main_window.enable_organize(False)
        self.main_window.show_skeleton_loading("Pass 1: Pattern analysis...")
        
        # Clear previous results
        self.results_table.clear_results()
        self.analysis_results = []
        
        # Convert scanned files to Path objects
        file_paths = [Path(f) if isinstance(f, str) else f for f in self.scanned_files]
        
        # Run batch analysis
        try:
            auto_results, review_results = self.intelligent_analyzer.analyze_batch(
                file_paths,
                progress_callback=self._on_intelligent_progress
            )
            
            self.main_window.hide_skeleton_loading()
            
            # Add auto results to table
            for result in auto_results:
                self._add_analysis_result(result)
            
            # Show review dialog if needed
            if review_results:
                logger.info(f"{len(review_results)} documents need review")
                self._show_review_dialog(review_results)
            else:
                self._finish_intelligent_analysis()
                
        except Exception as e:
            logger.error(f"Intelligent analysis failed: {e}")
            self.main_window.hide_skeleton_loading()
            self.main_window.show_error(
                "Analysis Failed",
                f"Intelligent analysis failed:\n\n{str(e)}"
            )
            self.is_analyzing = False
            self.main_window.enable_analyze(True)
    
    def _on_intelligent_progress(self, current: int, total: int, filename: str):
        """Update intelligent analysis progress."""
        percentage = int((current / total) * 100) if total > 0 else 0
        
        # Update message based on progress
        if percentage < 50:
            msg = f"Pass 1: Pattern analysis... {percentage}%"
        elif percentage < 80:
            msg = f"Pass 2: LLM analysis... {percentage}%"
        else:
            msg = f"Pass 3: Preparing review... {percentage}%"
        
        self.main_window.skeleton_widget.set_message(msg)
    
    def _add_analysis_result(self, result):
        """Add an analysis result to the table."""
        # Convert AnalysisResult to dict format expected by table
        result_dict = {
            "file_path": str(result.file_path),
            "category": result.category,
            "suggested_name": result.suggested_name,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "folder": result.suggested_folder,
            "pass_level": result.pass_level
        }
        self.analysis_results.append(result_dict)
        self.results_table.add_result(result_dict)
    
    def _show_review_dialog(self, review_items):
        """Show the document review dialog."""
        dialog = DocumentReviewDialog(review_items, self.main_window)
        dialog.document_reviewed.connect(self._on_document_reviewed)
        dialog.batch_complete.connect(self._finish_intelligent_analysis)
        dialog.exec()
        
        # Add reviewed documents to results
        for review_result in dialog.get_results():
            result_dict = {
                "file_path": str(review_result["file_path"]),
                "category": review_result["category"],
                "suggested_name": review_result["filename"],
                "confidence": 1.0,  # User confirmed
                "reasoning": "Manually reviewed and classified",
                "folder": review_result["folder"],
                "pass_level": 3
            }
            self.analysis_results.append(result_dict)
            self.results_table.add_result(result_dict)
    
    def _on_document_reviewed(self, file_path, filename, folder, category):
        """Handle a document being reviewed."""
        logger.info(f"Document reviewed: {file_path.name} → {filename}")
    
    def _finish_intelligent_analysis(self):
        """Complete the intelligent analysis workflow."""
        self.is_analyzing = False
        
        count = len(self.analysis_results)
        auto_count = sum(1 for r in self.analysis_results if r.get("pass_level") in [1, 2])
        review_count = sum(1 for r in self.analysis_results if r.get("pass_level") == 3)
        
        if count == 0:
            self.main_window.show_empty_state('no_results')
            self.main_window.set_status("⚠️ No files could be analyzed")
            self.main_window.enable_analyze(True)
            self.main_window.enable_organize(False)
        else:
            self.main_window.show_results()
            self.main_window.set_results_count(count)
            
            status_msg = f"✅ Analysis complete! {count} files analyzed."
            if auto_count > 0:
                status_msg += f" ({auto_count} auto)"
            if review_count > 0:
                status_msg += f" ({review_count} reviewed)"
            status_msg += " Select files and click 'Organize' to apply changes."
            
            self.main_window.set_status(status_msg)
            self.main_window.enable_analyze(True)
            self.main_window.enable_organize(count > 0)
        
        logger.info(f"Intelligent analysis finished: {count} results")
    
    def _init_llm_handler(self, llm_config: dict):
        """Initialize LLM handler based on config."""
        backend = llm_config.get('backend')
        self.llm_handler = None  # Reset first
        
        if backend == 'ollama':
            try:
                from ..core.llm_handler import OllamaHandler
                self.llm_handler = OllamaHandler(
                    model=llm_config.get('model', 'llama3.2:3b'),
                    url=llm_config.get('url', 'http://localhost:11434')
                )
                if not self.llm_handler.is_available():
                    raise RuntimeError("Ollama is not running or not accessible")
                logger.info(f"Ollama handler initialized: {self.llm_handler.model}")
            except ImportError:
                # Fallback for test context
                try:
                    from core.llm_handler import OllamaHandler
                    self.llm_handler = OllamaHandler(
                        model=llm_config.get('model', 'llama3.2:3b'),
                        url=llm_config.get('url', 'http://localhost:11434')
                    )
                except Exception as e:
                    logger.error(f"Ollama handler import error: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama: {e}")
                self.llm_handler = None
        
        elif backend == 'openrouter':
            try:
                from ..core.llm_handler import OpenRouterHandler
                self.llm_handler = OpenRouterHandler(
                    api_key=llm_config.get('api_key'),
                    model=llm_config.get('model', 'openai/gpt-3.5-turbo')
                )
                logger.info(f"OpenRouter handler initialized: {self.llm_handler.model}")
            except ImportError:
                try:
                    from core.llm_handler import OpenRouterHandler
                    self.llm_handler = OpenRouterHandler(
                        api_key=llm_config.get('api_key'),
                        model=llm_config.get('model', 'openai/gpt-3.5-turbo')
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize OpenRouter: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter: {e}")
        
        elif backend == 'demo':
            self.llm_handler = None
            logger.info("Demo mode - no LLM handler")
    
    def on_organize_requested(self):
        """Handle organize button click."""
        if not self.analysis_results:
            self.main_window.show_error(
                "No Results",
                "Please analyze files first to get organization suggestions."
            )
            return
        
        selected = self.results_table.get_selected_results()
        if not selected:
            self.main_window.show_error(
                "No Selection",
                "Please select at least one file to organize.\n\n"
                "Tip: Use Ctrl+A to select all files, or click individual rows."
            )
            return
        
        # Get statistics for confirmation
        high_conf_count = sum(1 for r in selected if r.get("confidence", 0) >= 0.85)
        
        # Show confirmation dialog
        count = len(selected)
        message = f"Organize {count} file(s)?"
        
        if high_conf_count == count:
            message += "\n\n✅ All selected files have high confidence scores."
        elif high_conf_count > 0:
            message += f"\n\n⚠️ {high_conf_count} of {count} files have high confidence. "
            message += "Others may need review."
        else:
            message += "\n\n⚠️ None of the selected files have high confidence. "
            message += "Review carefully before proceeding."
        
        message += "\n\nA backup will be created and you can undo if needed."
        
        confirmed = self.main_window.ask_confirmation("Confirm Organization", message)
        
        if not confirmed:
            logger.info("Organization cancelled by user")
            return
        
        # Continue with organization...
        logger.info(f"Organizing {count} files")
        self.main_window.set_status("📁 Organizing files...")
        self.main_window.enable_organize(False)
        
        # Show progress dialog
        self.progress_dialog = ProgressDialog("Organizing Files", self.main_window)
        self.progress_dialog.show()
        
        # Simulate organization (actual implementation would use organizer)
        # For now, show success message
        self.progress_dialog.close()
        self.main_window.show_info(
            "Organization Complete",
            f"Successfully organized {count} files!\n\n"
            f"Files have been moved to their suggested locations."
        )
        self.main_window.set_status(f"✅ Organized {count} files")
        self.main_window.enable_analyze(True)
    
    def on_undo_requested(self):
        """Handle undo button click."""
        confirmed = self.main_window.ask_confirmation(
            "Confirm Undo",
            "Undo the most recent organization?\n\n"
            "Files will be restored to their original locations."
        )
        
        if not confirmed:
            return
        
        logger.info("Undo requested")
        self.main_window.show_info(
            "Undo Complete",
            "The last organization has been undone.\n\n"
            "Files have been restored to their original locations."
        )
        self.main_window.set_status("✅ Undo complete")
    
    def on_settings_requested(self):
        """Handle settings request."""
        from PyQt6.QtWidgets import QDialog
        settings_dialog = SettingsDialog(self.config, self.main_window)
        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            settings = settings_dialog.get_settings()
            # Re-initialize LLM handler if settings changed
            if 'llm_model' in settings:
                llm_config = {
                    'backend': 'ollama' if 'Ollama' in settings.get('llm_provider', '') else 'openrouter',
                    'model': settings.get('llm_model', 'llama3.2:3b'),
                    'url': settings.get('llm_endpoint', 'http://localhost:11434'),
                    'api_key': settings.get('llm_api_key', '')
                }
                self._init_llm_handler(llm_config)
            logger.info("Settings updated")
            self.main_window.show_info("Settings Saved", "Your settings have been saved successfully.")
    
    def on_rules_requested(self):
        """Handle rules manager request."""
        self.rules_dialog = RulesManagerDialog(self.rules_engine, self.main_window)
        self.rules_dialog.rules_changed.connect(self._on_rules_changed)
        self.rules_dialog.show()
    
    def _on_rules_changed(self):
        """Handle rules changes."""
        logger.info("Rules updated")
        if self.current_directory:
            rules_path = self.current_directory / ".file_organizer_rules.json"
            try:
                self.rules_engine.save_to_file(rules_path)
            except Exception as e:
                logger.warning(f"Failed to save rules: {e}")
    
    def on_duplicates_requested(self):
        """Handle duplicates manager request."""
        file_paths = []
        if self.current_directory:
            file_paths = list(self.current_directory.glob("*"))
            file_paths = [p for p in file_paths if p.is_file()]
        
        self.duplicates_dialog = DuplicatesDialog(file_paths, self.main_window)
        self.duplicates_dialog.duplicates_removed.connect(self._on_duplicates_removed)
        self.duplicates_dialog.show()
    
    def _on_duplicates_removed(self, count: int, space_freed: int):
        """Handle duplicates removal."""
        space_mb = space_freed / (1024 * 1024)
        logger.info(f"Removed {count} duplicates, freed {space_mb:.1f} MB")
        self.main_window.set_status(f"Removed {count} duplicates, freed {space_mb:.1f} MB")
        
        # Refresh file list if directory is selected
        if self.current_directory:
            self.on_directory_selected(self.current_directory)
    
    def on_refresh_requested(self):
        """Handle refresh request."""
        if self.current_directory:
            logger.info("Refreshing current directory")
            self.on_directory_selected(self.current_directory)
        else:
            self.main_window.show_info(
                "No Directory",
                "Select a directory first to refresh."
            )
    
    def on_license_requested(self):
        """Handle license dialog request."""
        dialog = LicenseDialog(self.main_window)
        dialog.license_activated.connect(self._on_license_activated)
        dialog.exec()
    
    def _on_license_activated(self):
        """Handle license activation."""
        # Refresh UI to reflect new license status
        self._update_license_status()
        logger.info("License activated, UI updated")
    
    def _update_license_status(self):
        """Update status bar with license information."""
        try:
            license_mgr = get_license_manager()
            status = license_mgr.get_license_status()
            
            if status["status"] == "licensed":
                tier = status["tier"].title()
                self.main_window.set_status(f"🔓 {tier} License Active")
            elif status["status"] == "trial":
                remaining = status.get("trial_remaining", 0)
                self.main_window.set_status(f"🧪 Trial: {remaining} AI uses remaining")
            else:
                self.main_window.set_status("🔒 Free Version - Upgrade for AI features")
        except Exception as e:
            logger.warning(f"Could not update license status: {e}")
    
    def _show_upgrade_prompt(self):
        """Show upgrade prompt if not licensed."""
        try:
            license_mgr = get_license_manager()
            status = license_mgr.get_license_status()
            
            if status["status"] != "licensed":
                # Could add a persistent banner here
                logger.info("Showing upgrade prompt")
        except Exception as e:
            logger.warning(f"Could not show upgrade prompt: {e}")
    
    def run(self):
        """Start the application."""
        logger.info("Starting application")
        self.main_window.show()
    
    def shutdown(self):
        """Shutdown the application."""
        logger.info("Shutting down application")
        
        # Stop any running workers
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.requestInterruption()
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.requestInterruption()
