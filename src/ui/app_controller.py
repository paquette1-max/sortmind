"""
Main application controller connecting UI and backend.
"""
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow
from .widgets.results_table import ResultsTable
from .widgets.progress_dialog import ProgressDialog
from .dialogs.settings_dialog import SettingsDialog
from .workers import ScanWorker, AnalysisWorker, OrganizeWorker, BackupWorker

import logging

logger = logging.getLogger(__name__)


class AppController:
    """Main application controller connecting UI and backend."""
    
    def __init__(self, config=None):
        self.config = config
        self.main_window = MainWindow()
        
        # Backend components (lazy loaded)
        self.scanner = None
        self.llm_handler = None
        self.organizer = None
        self.undo_manager = None
        self.backup_manager = None
        
        # State
        self.scanned_files = []
        self.analysis_results = []
        self.current_plan = None
        self.current_directory = None
        
        # Worker threads
        self.scan_worker = None
        self.analysis_worker = None
        self.organize_worker = None
        self.backup_worker = None
        
        # Results table
        self.results_table = ResultsTable()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("AppController initialized")
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Window signals
        self.main_window.directory_selected.connect(self.on_directory_selected)
        self.main_window.analyze_requested.connect(self.on_analyze_requested)
        self.main_window.organize_requested.connect(self.on_organize_requested)
        self.main_window.undo_requested.connect(self.on_undo_requested)
        self.main_window.settings_requested.connect(self.on_settings_requested)
        
        # Replace placeholder results container with actual table widget in-place
        placeholder = self.main_window.results_container
        parent = placeholder.parent()
        if parent is not None:
            layout = parent.layout()
            # Try to find the index of the placeholder and replace it
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget() is placeholder:
                    # Replace widget
                    layout.removeWidget(placeholder)
                    placeholder.deleteLater()
                    layout.insertWidget(i, self.results_table)
                    break
        # Keep reference on main window
        self.main_window.results_container = self.results_table
    
    def on_directory_selected(self, directory: Path):
        """Handle directory selection."""
        logger.info(f"Directory selected: {directory}")
        self.current_directory = directory
        self.main_window.set_status(f"Scanning {directory}...")
        self.main_window.enable_analyze(False)
        self.main_window.enable_organize(False)
        
        # Clear previous results
        self.results_table.clear_results()
        self.scanned_files = []
        self.analysis_results = []
        
        # Start scan worker
        self.scan_worker = ScanWorker(directory, self.config)
        self.scan_worker.progress.connect(self._on_scan_progress)
        self.scan_worker.finished.connect(self._on_scan_finished)
        self.scan_worker.error.connect(self._on_scan_error)
        self.scan_worker.start()
    
    def _on_scan_progress(self, current: int, total: int):
        """Update scan progress."""
        self.main_window.set_status(f"Scanning... ({current}/{total})")
    
    def _on_scan_finished(self, files: list):
        """Handle scan completion."""
        self.scanned_files = files
        self.main_window.set_file_count(len(files))
        self.main_window.set_status(f"Found {len(files)} files. Ready to analyze.")
        self.main_window.enable_analyze(True)
        logger.info(f"Scan finished: {len(files)} files found")
    
    def _on_scan_error(self, error: str):
        """Handle scan error."""
        self.main_window.set_status(f"Error: {error}")
        self.main_window.show_error("Scan Error", error)
        logger.error(f"Scan error: {error}")
    
    def on_analyze_requested(self):
        """Handle analyze button click."""
        if not self.scanned_files:
            self.main_window.show_error("No Files", "Please select a directory first")
            return
        
        logger.info(f"Starting analysis of {len(self.scanned_files)} files")
        self.main_window.set_status("Analyzing files...")
        self.main_window.enable_analyze(False)
        self.main_window.enable_organize(False)
        
        # Clear previous results
        self.results_table.clear_results()
        self.analysis_results = []
        
        # Show progress dialog
        self.progress_dialog = ProgressDialog("Analyzing Files", self.main_window)
        self.progress_dialog.show()
        
        # Start analysis worker
        self.analysis_worker = AnalysisWorker(self.scanned_files, self.llm_handler)
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.result.connect(self._on_analysis_result)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        self.analysis_worker.error.connect(self._on_analysis_error)
        self.analysis_worker.start()
    
    def _on_analysis_progress(self, current: int, total: int, filename: str):
        """Update analysis progress."""
        self.progress_dialog.update_progress(current, total, filename)
        self.main_window.set_status(f"Analyzing: {filename}")
    
    def _on_analysis_result(self, result: dict):
        """Handle individual analysis result."""
        self.analysis_results.append(result)
        self.results_table.add_result(result)
    
    def _on_analysis_finished(self):
        """Handle analysis completion."""
        self.progress_dialog.close()
        self.main_window.set_status(f"Analysis complete. {len(self.analysis_results)} files analyzed.")
        self.main_window.enable_analyze(True)
        self.main_window.enable_organize(len(self.analysis_results) > 0)
        logger.info(f"Analysis finished: {len(self.analysis_results)} results")
    
    def _on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.progress_dialog.close()
        self.main_window.set_status(f"Error: {error}")
        self.main_window.show_error("Analysis Error", error)
        self.main_window.enable_analyze(True)
        logger.error(f"Analysis error: {error}")
    
    def on_organize_requested(self):
        """Handle organize button click."""
        if not self.analysis_results:
            self.main_window.show_error("No Results", "Please analyze files first")
            return
        
        selected = self.results_table.get_selected_results()
        if not selected:
            self.main_window.show_error("No Selection", "Please select files to organize")
            return
        
        # Create organization plan
        if not self.organizer:
            self.main_window.show_error("Not Ready", "Organizer not initialized")
            return
        
        logger.info(f"Creating organization plan for {len(selected)} files")
        
        # Show confirmation dialog
        count = len(selected)
        confirmed = self.main_window.ask_confirmation(
            "Confirm Organization",
            f"Organize {count} file(s)?\n\nThis will create a backup and can be undone."
        )
        
        if not confirmed:
            logger.info("Organization cancelled by user")
            return
        
        # Create plan
        try:
            self.current_plan = self.organizer.create_organization_plan(
                self.scanned_files,
                selected,
                self.current_directory or Path.home() / "organized"
            )
            
            # Validate plan
            errors = self.organizer.validate_plan(self.current_plan)
            if errors:
                error_msg = "\n".join(errors[:5])  # Show first 5 errors
                self.main_window.show_error("Validation Failed", error_msg)
                logger.warning(f"Plan validation failed: {errors}")
                return
            
            # Show preview
            operations = len(self.current_plan.get("operations", []))
            preview = f"Will organize {operations} file(s)."
            
            confirmed = self.main_window.ask_confirmation(
                "Review Plan",
                preview + "\n\nProceed with organization?"
            )
            
            if not confirmed:
                logger.info("Organization cancelled at preview")
                return
            
            # Execute plan
            self._execute_organization_plan()
            
        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            self.main_window.show_error("Error", f"Failed to create plan: {str(e)}")
    
    def _execute_organization_plan(self):
        """Execute the organization plan."""
        if not self.current_plan:
            return
        
        logger.info("Executing organization plan")
        self.main_window.set_status("Organizing files...")
        self.main_window.enable_organize(False)
        
        # Show progress dialog
        self.progress_dialog = ProgressDialog("Organizing Files", self.main_window)
        self.progress_dialog.show()
        
        # Start organize worker
        self.organize_worker = OrganizeWorker(self.current_plan, self.organizer)
        self.organize_worker.progress.connect(self._on_organize_progress)
        self.organize_worker.finished.connect(self._on_organize_finished)
        self.organize_worker.error.connect(self._on_organize_error)
        self.organize_worker.start()
    
    def _on_organize_progress(self, current: int, total: int, message: str):
        """Update organize progress."""
        self.progress_dialog.update_progress(current, total, message)
    
    def _on_organize_finished(self, result):
        """Handle organization completion."""
        self.progress_dialog.close()
        
        if result.success:
            self.main_window.set_status(f"Organization complete! {result.operations_completed} files moved.")
            self.main_window.show_info(
                "Success",
                f"Successfully organized {result.operations_completed} files!\n\n"
                f"Batch ID: {result.batch_id}\n"
                f"You can undo this operation."
            )
            logger.info(f"Organization successful: {result.operations_completed} files")
        else:
            error_msg = "\n".join(result.errors[:5])
            self.main_window.show_error("Organization Failed", error_msg)
            logger.error(f"Organization failed: {result.errors}")
        
        self.main_window.enable_analyze(True)
    
    def _on_organize_error(self, error: str):
        """Handle organization error."""
        self.progress_dialog.close()
        self.main_window.set_status(f"Error: {error}")
        self.main_window.show_error("Organization Error", error)
        self.main_window.enable_organize(True)
        logger.error(f"Organization error: {error}")
    
    def on_undo_requested(self):
        """Handle undo button click."""
        if not self.undo_manager:
            self.main_window.show_error("Not Ready", "Undo manager not initialized")
            return
        
        logger.info("Undo requested")
        
        # Show confirmation
        confirmed = self.main_window.ask_confirmation(
            "Confirm Undo",
            "Undo the most recent organization?\n\nFiles will be moved back to original locations."
        )
        
        if not confirmed:
            return
        
        try:
            result = self.undo_manager.undo_last()
            
            if result.success:
                self.main_window.show_info(
                    "Success",
                    f"Undone {result.operations_undone} operations.\n\nFiles restored to original locations."
                )
                logger.info(f"Undo successful: {result.operations_undone} operations reversed")
            else:
                error_msg = "\n".join(result.errors)
                self.main_window.show_error("Undo Failed", error_msg)
                logger.warning(f"Undo failed: {result.errors}")
                
        except Exception as e:
            logger.error(f"Undo error: {e}")
            self.main_window.show_error("Error", f"Undo failed: {str(e)}")
    
    def on_settings_requested(self):
        """Handle settings request."""
        settings_dialog = SettingsDialog(self.config, self.main_window)
        if settings_dialog.exec() == SettingsDialog.Accepted:
            settings = settings_dialog.get_settings()
            logger.info("Settings updated")
            self.main_window.show_info("Settings", "Settings saved successfully")
    
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
        if self.organize_worker and self.organize_worker.isRunning():
            self.organize_worker.requestInterruption()
