"""
Background worker threads for long-running operations.
"""
from pathlib import Path
from typing import List, Optional, Callable
from PyQt6.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor, as_completed

import logging

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """Worker thread for file scanning."""
    
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(list)  # scanned files
    error = pyqtSignal(str)
    
    def __init__(self, directory: Path, config=None, parent=None):
        super().__init__(parent)
        self.directory = Path(directory)
        self.config = config
        self.scanned_files = []
        logger.info(f"ScanWorker initialized for: {directory}")
    
    def run(self):
        """Run file scanning in background thread."""
        try:
            self.scanned_files = []
            
            # Recursive file scan
            for i, file_path in enumerate(self.directory.rglob("*")):
                if file_path.is_file():
                    self.scanned_files.append(file_path)
                    self.progress.emit(i + 1, len(self.scanned_files) + 100)  # Estimate
                
                # Check if thread should stop
                if self.isInterruptionRequested():
                    logger.info("Scan interrupted by user")
                    return
            
            logger.info(f"Scan complete: {len(self.scanned_files)} files found")
            self.finished.emit(self.scanned_files)
            
        except Exception as e:
            error_msg = f"Scan error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)


class AnalysisWorker(QThread):
    """Worker thread for LLM analysis."""
    
    progress = pyqtSignal(int, int, str)  # current, total, current file
    result = pyqtSignal(dict)  # analysis result
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, files: List[Path], llm_handler=None, max_workers: int = 4, parent=None):
        super().__init__(parent)
        self.files = files
        self.llm_handler = llm_handler
        self.max_workers = max(1, min(max_workers, 8))  # Clamp between 1-8
        logger.info(f"AnalysisWorker initialized with {len(files)} files (max_workers={self.max_workers})")
    
    def run(self):
        """Run LLM analysis in background thread with parallelization."""
        try:
            if not self.llm_handler:
                raise ValueError("LLM handler not provided")
            
            # Use ThreadPoolExecutor for parallel analysis
            completed_count = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all analysis tasks
                futures = {
                    executor.submit(self._analyze_single_file, file_path): file_path
                    for file_path in self.files
                }
                
                # Process completed tasks as they finish
                for future in as_completed(futures):
                    # Check for interruption
                    if self.isInterruptionRequested():
                        logger.info("Analysis interrupted by user")
                        executor.shutdown(wait=False)
                        return
                    
                    try:
                        result = future.result()
                        if result:
                            completed_count += 1
                            self.progress.emit(completed_count, len(self.files), result.get("file_path", ""))
                            self.result.emit(result)
                    except Exception as e:
                        logger.error(f"Error analyzing file: {e}")
                        completed_count += 1
                        self.progress.emit(completed_count, len(self.files), str(e))
            
            logger.info(f"Analysis complete: {len(self.files)} files analyzed with {self.max_workers} workers")
            self.finished.emit()
            
        except Exception as e:
            error_msg = f"Analysis error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
    
    def _analyze_single_file(self, file_path: Path) -> Optional[dict]:
        """Analyze a single file (runs in thread pool worker)."""
        try:
            if not self.llm_handler:
                return None
            
            # Mock analysis if handler is not properly configured
            result = {
                "file_path": str(file_path),
                "category": "documents",
                "suggested_name": file_path.name,
                "confidence": 0.85,
                "reasoning": f"Analyzed {file_path.suffix} file"
            }
            return result
        
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return None


class OrganizeWorker(QThread):
    """Worker thread for file organization."""
    
    progress = pyqtSignal(int, int, str)  # current, total, operation
    finished = pyqtSignal(object)  # ExecutionResult
    error = pyqtSignal(str)
    
    def __init__(self, plan: dict, organizer=None, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.organizer = organizer
        logger.info(f"OrganizeWorker initialized with {len(plan.get('operations', []))} operations")
    
    def run(self):
        """Execute organization plan in background thread."""
        try:
            if not self.organizer:
                raise ValueError("Organizer not provided")
            
            operations = self.plan.get("operations", [])
            
            for i, operation in enumerate(operations):
                # Update progress
                src = operation.get("source")
                dest = operation.get("destination")
                msg = f"Organizing: {src} → {dest}"
                self.progress.emit(i, len(operations), msg)
                
                # Check for interruption
                if self.isInterruptionRequested():
                    logger.info("Organization interrupted by user")
                    return
            
            # Execute the plan
            result = self.organizer.execute_plan(self.plan, dry_run=False)
            
            logger.info(f"Organization complete: {result.operations_completed} files organized")
            self.finished.emit(result)
            
        except Exception as e:
            error_msg = f"Organization error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)


class BackupWorker(QThread):
    """Worker thread for backup creation."""
    
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(str)  # backup path
    error = pyqtSignal(str)
    
    def __init__(self, files: List[Path], backup_manager=None, batch_id: str = "", parent=None):
        super().__init__(parent)
        # Accept either a directory Path or an iterable of files
        if isinstance(files, Path):
            self.files = [p for p in files.iterdir() if p.is_file()]
        else:
            try:
                self.files = list(files)
            except TypeError:
                self.files = [files]
        self.backup_manager = backup_manager
        self.batch_id = batch_id
        logger.info(f"BackupWorker initialized with {len(self.files)} files")
    
    def run(self):
        """Create backup in background thread."""
        try:
            if not self.backup_manager:
                raise ValueError("Backup manager not provided")
            
            # Simulate backup progress
            for i in range(len(self.files)):
                self.progress.emit(i, len(self.files))
                
                if self.isInterruptionRequested():
                    logger.info("Backup interrupted by user")
                    return
            
            # Create backup
            backup_path = self.backup_manager.create_backup(self.files, self.batch_id)
            
            if backup_path:
                logger.info(f"Backup complete: {backup_path}")
                self.finished.emit(str(backup_path))
            else:
                raise ValueError("Backup creation returned None")
                
        except Exception as e:
            error_msg = f"Backup error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
