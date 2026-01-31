# Implementation Prompt: AI File Organizer Phases 2-4

## Context

You are continuing development of an AI-powered file organization application. Phase 1 (core backend) is complete and production-ready. Your task is to implement Phases 2-4 following the Product Requirements Document.

## What Exists (Phase 1 - Complete)

The following components are already implemented and tested:

### Core Backend (`src/core/`)
- **config.py**: Pydantic-based configuration system with LLMConfig, OrganizationConfig, AppConfig
- **llm_handler.py**: LLM integration with OllamaHandler, OpenAICompatibleHandler, factory pattern
- **scanner.py**: FileScanner with recursive traversal, filtering, progress callbacks

### File Parsers (`src/parsers/`)
- **base_parser.py**: Abstract parser interface and registry
- **pdf_parser.py**: PDF text extraction using pypdf
- **docx_parser.py**: Word document parsing with python-docx
- **excel_parser.py**: Excel parsing with openpyxl
- **image_parser.py**: Image metadata extraction with Pillow
- **text_parser.py**: 40+ text format support

### Infrastructure
- **utils/logging.py**: Logging configuration
- **tests/**: Comprehensive unit tests (90%+ coverage)
- **demo.py**: Working demonstration script
- **Complete documentation**: README.md, SETUP.md

### Project Structure
```
file-organizer/
├── src/
│   ├── core/
│   ├── parsers/
│   ├── ui/          # Empty - Phase 3
│   └── utils/
├── tests/
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Your Task: Implement Phases 2-4

Implement the remaining phases according to the PRD. Follow the existing code style, architecture patterns, and best practices established in Phase 1.

---

## Phase 2: File Operations (Week 1-2)

### Priority: Implement in this order

#### 2.1 Create File Organizer Module

**File:** `src/core/organizer.py`

**Requirements:**
```python
"""
File organizer - executes file organization operations safely.
"""
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import shutil
import logging

from .config import OrganizationConfig, FileAnalysisResult, OrganizationPlan
from .scanner import ScannedFile


@dataclass
class FileOperation:
    """Represents a single file operation."""
    source: Path
    destination: Path
    operation_type: str  # 'move', 'rename', 'copy'
    confidence: float
    reasoning: str


@dataclass
class ExecutionResult:
    """Result of executing an organization plan."""
    success: bool
    operations_completed: int
    operations_failed: int
    errors: List[str]
    batch_id: str


class FileOrganizer:
    """Organizes files based on LLM analysis results."""
    
    def __init__(self, config: OrganizationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def create_organization_plan(
        self,
        scanned_files: List[ScannedFile],
        analysis_results: List[FileAnalysisResult],
        base_directory: Path
    ) -> OrganizationPlan:
        """
        Create a plan for organizing files.
        
        Args:
            scanned_files: List of scanned files
            analysis_results: LLM analysis results
            base_directory: Base directory for organization
        
        Returns:
            OrganizationPlan with proposed operations
        """
        # TODO: Implement
        pass
    
    def validate_plan(self, plan: OrganizationPlan) -> List[str]:
        """
        Validate organization plan for issues.
        
        Returns:
            List of validation errors (empty if valid)
        """
        # TODO: Check for:
        # - Conflicts (multiple files to same destination)
        # - Permission issues
        # - System directory targets
        # - Invalid paths
        # - Disk space
        pass
    
    def execute_plan(
        self,
        plan: OrganizationPlan,
        dry_run: bool = True
    ) -> ExecutionResult:
        """
        Execute organization plan.
        
        Args:
            plan: Organization plan to execute
            dry_run: If True, only simulate execution
        
        Returns:
            ExecutionResult with operation status
        """
        # TODO: Implement
        # - Generate unique batch_id
        # - Create directories as needed
        # - Move/rename files
        # - Handle errors gracefully
        # - Return detailed results
        pass
    
    def resolve_conflicts(self, plan: OrganizationPlan) -> OrganizationPlan:
        """
        Resolve filename conflicts by appending numbers.
        
        Returns:
            Updated plan with conflicts resolved
        """
        # TODO: Implement
        # - Detect conflicts
        # - Append (1), (2), etc. to filenames
        # - Update plan
        pass
```

**Key Implementation Details:**
- Use `shutil.move()` for file operations
- Always validate paths before operations
- Check disk space before executing
- Generate UUID for batch_id
- Respect `dry_run` mode (no actual file ops)
- Create directories with `Path.mkdir(parents=True, exist_ok=True)`
- Handle filename conflicts intelligently
- Log all operations

**Tests:** Create `tests/test_organizer.py` with:
- Test plan creation
- Test validation (conflicts, permissions, system dirs)
- Test dry-run mode
- Test conflict resolution
- Test error handling

---

#### 2.2 Create Undo Manager Module

**File:** `src/core/undo_manager.py`

**Requirements:**
```python
"""
Undo manager - tracks and reverses file operations.
"""
import sqlite3
import hashlib
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OperationRecord:
    """Record of a file operation."""
    id: int
    batch_id: str
    timestamp: float
    operation_type: str
    source_path: str
    target_path: str
    file_hash: Optional[str]
    undone: bool


@dataclass
class UndoResult:
    """Result of undo operation."""
    success: bool
    operations_undone: int
    errors: List[str]


class UndoManager:
    """Manages undo functionality for file operations."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database."""
        # TODO: Create operations table
        # See PRD for schema
        pass
    
    def record_operation(
        self,
        batch_id: str,
        operation_type: str,
        source_path: Path,
        target_path: Path,
        file_hash: Optional[str] = None
    ) -> None:
        """Record a file operation."""
        # TODO: Insert into database
        pass
    
    def undo_batch(self, batch_id: str) -> UndoResult:
        """
        Undo all operations in a batch.
        
        Args:
            batch_id: Batch ID to undo
        
        Returns:
            UndoResult with status
        """
        # TODO: Implement
        # - Get all operations for batch
        # - Reverse each operation (move back)
        # - Mark as undone in database
        # - Handle errors gracefully
        pass
    
    def undo_last(self) -> UndoResult:
        """Undo the most recent batch."""
        # TODO: Get most recent batch_id and call undo_batch()
        pass
    
    def get_history(self, limit: int = 100) -> List[OperationRecord]:
        """Get operation history."""
        # TODO: Query database, return list
        pass
    
    def clear_history(self, older_than: Optional[datetime] = None) -> int:
        """Clear operation history."""
        # TODO: Delete old records, return count
        pass
    
    def verify_undo_possible(self, batch_id: str) -> bool:
        """Check if undo is possible for a batch."""
        # TODO: Verify target files still exist
        pass
    
    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        # TODO: Implement file hashing
        pass
```

**Key Implementation Details:**
- Use context managers for database connections
- Create indexes for performance
- Compute file hashes for verification
- Handle missing files gracefully during undo
- Transaction-safe database operations
- Close database connections properly

**Tests:** Create `tests/test_undo_manager.py` with:
- Test database initialization
- Test recording operations
- Test undo single batch
- Test undo last operation
- Test history retrieval
- Test clear history
- Test file verification

---

#### 2.3 Create Backup System Module

**File:** `src/core/backup.py`

**Requirements:**
```python
"""
Backup system - creates safety copies before operations.
"""
from pathlib import Path
from typing import Optional, List
from enum import Enum
import shutil
import logging


class BackupStrategy(str, Enum):
    """Backup strategy options."""
    COPY = "copy"
    NONE = "none"


class BackupManager:
    """Manages backup operations."""
    
    def __init__(self, backup_dir: Path, strategy: BackupStrategy):
        self.backup_dir = backup_dir
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
    
    def create_backup(
        self,
        files: List[Path],
        batch_id: str
    ) -> Optional[Path]:
        """
        Create backup of files.
        
        Args:
            files: Files to backup
            batch_id: Unique batch identifier
        
        Returns:
            Path to backup directory, or None if strategy is NONE
        """
        # TODO: Implement
        # - Create backup directory with batch_id
        # - Copy files preserving directory structure
        # - Verify copies
        # - Return backup path
        pass
    
    def restore_backup(self, backup_path: Path) -> bool:
        """Restore files from backup."""
        # TODO: Implement restore logic
        pass
    
    def cleanup_old_backups(self, retention_days: int) -> int:
        """Delete backups older than retention period."""
        # TODO: Implement cleanup
        pass
    
    def verify_backup(self, backup_path: Path, original_files: List[Path]) -> bool:
        """Verify backup integrity."""
        # TODO: Compare file hashes
        pass
```

**Key Implementation Details:**
- Create timestamped backup directories
- Preserve relative paths in backups
- Verify backups after creation
- Handle large files efficiently
- Clean up old backups automatically

**Tests:** Create `tests/test_backup.py` with:
- Test backup creation
- Test backup verification
- Test restore functionality
- Test cleanup of old backups

---

#### 2.4 Integration

**Update:** `src/core/organizer.py`

Integrate UndoManager and BackupManager:

```python
class FileOrganizer:
    def __init__(
        self,
        config: OrganizationConfig,
        undo_manager: Optional[UndoManager] = None,
        backup_manager: Optional[BackupManager] = None
    ):
        self.config = config
        self.undo_manager = undo_manager
        self.backup_manager = backup_manager
    
    def execute_plan(self, plan: OrganizationPlan, dry_run: bool = True) -> ExecutionResult:
        # 1. Validate plan
        # 2. Create backup (if enabled)
        # 3. Execute operations
        # 4. Record in undo manager
        # 5. Return results
        pass
```

---

#### 2.5 Phase 2 Testing

Create comprehensive integration tests:

**File:** `tests/test_integration_phase2.py`

```python
"""
Integration tests for Phase 2 file operations.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

# Test complete workflow: scan -> analyze -> organize -> undo


class TestPhase2Integration:
    """End-to-end tests for Phase 2."""
    
    def test_organize_and_undo_workflow(self):
        """Test complete organize and undo workflow."""
        # TODO: Implement
        # 1. Create test files
        # 2. Scan files
        # 3. Mock LLM analysis
        # 4. Create organization plan
        # 5. Execute plan
        # 6. Verify files moved
        # 7. Undo operation
        # 8. Verify files restored
        pass
    
    def test_backup_and_restore(self):
        """Test backup creation and restoration."""
        # TODO: Implement
        pass
    
    def test_conflict_resolution(self):
        """Test handling of filename conflicts."""
        # TODO: Implement
        pass
```

---

## Phase 3: PyQt6 User Interface (Week 3-5)

### Priority: Implement in this order

#### 3.1 Setup PyQt6 Infrastructure

**File:** `src/ui/__init__.py`

**Requirements:**
- Create main application entry point
- Setup QApplication
- Handle high DPI displays
- Setup application icon and metadata

#### 3.2 Create Main Window

**File:** `src/ui/main_window.py`

**Requirements:**
```python
"""
Main application window.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QLabel, QStatusBar,
    QMenuBar, QMenu, QToolBar
)
from PyQt6.QtCore import Qt, pyqtSignal


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    directory_selected = pyqtSignal(Path)
    analyze_requested = pyqtSignal()
    organize_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI File Organizer")
        self.resize(1200, 800)
        
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_signals()
    
    def _setup_ui(self):
        """Setup main UI layout."""
        # TODO: Create layout with:
        # - Directory selection panel (left)
        # - Results table (center)
        # - Preview panel (right, optional)
        pass
    
    def _setup_menu_bar(self):
        """Setup menu bar."""
        # TODO: File, Edit, View, Tools, Help menus
        pass
    
    def _setup_toolbar(self):
        """Setup toolbar."""
        # TODO: Common action buttons
        pass
    
    def _setup_status_bar(self):
        """Setup status bar."""
        # TODO: Status messages, progress indicator
        pass
```

**Key Features:**
- Menu bar: File (Open, Exit), Edit (Undo, Settings), View, Help
- Toolbar: Open Folder, Analyze, Organize, Undo buttons
- Status bar: Current operation, file count, progress
- Splitter for resizable panels
- Keyboard shortcuts (Cmd+O, Cmd+Z, etc.)

#### 3.3 Create Directory Selection Widget

**File:** `src/ui/widgets/directory_selector.py`

**Requirements:**
```python
class DirectorySelector(QWidget):
    """Widget for selecting directories to organize."""
    
    directory_changed = pyqtSignal(Path)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI with browse button, path field, recent dropdown."""
        pass
    
    def browse_directory(self):
        """Open directory browser dialog."""
        # TODO: Use QFileDialog.getExistingDirectory()
        pass
```

#### 3.4 Create Results Table Widget

**File:** `src/ui/widgets/results_table.py`

**Requirements:**
```python
class ResultsTable(QTableWidget):
    """Table widget displaying analysis results."""
    
    def __init__(self):
        super().__init__()
        self._setup_table()
    
    def _setup_table(self):
        """Setup table columns and behavior."""
        # Columns: Checkbox, Original Path, New Category, New Name, Confidence, Status
        pass
    
    def add_result(self, result: FileAnalysisResult):
        """Add a result row to the table."""
        pass
    
    def get_selected_results(self) -> List[FileAnalysisResult]:
        """Get results that are checked."""
        pass
    
    def update_row_status(self, row: int, status: str):
        """Update status column for a row."""
        pass
```

**Key Features:**
- Sortable columns
- Color-coded confidence (green/yellow/red)
- Checkboxes for selection
- Context menu (right-click)
- Inline editing of suggestions

#### 3.5 Create Progress Dialog

**File:** `src/ui/widgets/progress_dialog.py`

**Requirements:**
```python
class ProgressDialog(QDialog):
    """Dialog showing operation progress."""
    
    cancel_requested = pyqtSignal()
    
    def __init__(self, title: str):
        super().__init__()
        self.setWindowTitle(title)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup progress bar, labels, cancel button."""
        pass
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress display."""
        pass
```

#### 3.6 Create Settings Dialog

**File:** `src/ui/dialogs/settings_dialog.py`

**Requirements:**
```python
class SettingsDialog(QDialog):
    """Settings/preferences dialog."""
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup tabbed interface with settings."""
        # Tabs: General, LLM, Organization, Advanced
        pass
    
    def save_settings(self):
        """Save settings to config."""
        pass
```

**Tabs:**
1. **General**: Theme, default directory
2. **LLM**: Provider, model, temperature, test connection
3. **Organization**: Confidence threshold, filters
4. **Advanced**: Logging, cache, backup

#### 3.7 Create Worker Threads

**File:** `src/ui/workers.py`

**Requirements:**
```python
from PyQt6.QtCore import QThread, pyqtSignal


class ScanWorker(QThread):
    """Worker thread for file scanning."""
    
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(list)  # scanned files
    error = pyqtSignal(str)
    
    def __init__(self, directory: Path, config: OrganizationConfig):
        super().__init__()
        self.directory = directory
        self.config = config
    
    def run(self):
        """Run file scanning in background thread."""
        # TODO: Use FileScanner, emit progress signals
        pass


class AnalysisWorker(QThread):
    """Worker thread for LLM analysis."""
    
    progress = pyqtSignal(int, int, str)  # current, total, current file
    result = pyqtSignal(FileAnalysisResult)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, files: List[ScannedFile], llm_handler):
        super().__init__()
        self.files = files
        self.llm_handler = llm_handler
    
    def run(self):
        """Run LLM analysis in background thread."""
        # TODO: Analyze files, emit results
        pass


class OrganizeWorker(QThread):
    """Worker thread for file organization."""
    
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(ExecutionResult)
    error = pyqtSignal(str)
    
    def __init__(self, plan: OrganizationPlan, organizer: FileOrganizer):
        super().__init__()
        self.plan = plan
        self.organizer = organizer
    
    def run(self):
        """Execute organization plan in background thread."""
        # TODO: Execute plan, emit progress
        pass
```

**Key Points:**
- Use QThread for all long-running operations
- Never block the UI thread
- Emit signals for progress updates
- Handle cancellation gracefully
- Proper cleanup in thread termination

#### 3.8 Main Application Controller

**File:** `src/ui/app_controller.py`

**Requirements:**
```python
class AppController:
    """Main application controller connecting UI and backend."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.main_window = MainWindow()
        
        # Backend components
        self.scanner = FileScanner(config.organization)
        self.llm_handler = LLMHandlerFactory.create_handler(config.llm)
        self.organizer = FileOrganizer(config.organization)
        self.undo_manager = UndoManager(config.db_path)
        
        # State
        self.scanned_files = []
        self.analysis_results = []
        self.current_plan = None
        
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        self.main_window.directory_selected.connect(self.on_directory_selected)
        self.main_window.analyze_requested.connect(self.on_analyze_requested)
        self.main_window.organize_requested.connect(self.on_organize_requested)
    
    def on_directory_selected(self, directory: Path):
        """Handle directory selection."""
        # TODO: Start scan worker
        pass
    
    def on_analyze_requested(self):
        """Handle analyze button click."""
        # TODO: Start analysis worker
        pass
    
    def on_organize_requested(self):
        """Handle organize button click."""
        # TODO: Create plan, show preview, execute
        pass
    
    def run(self):
        """Start the application."""
        self.main_window.show()
```

#### 3.9 Main Entry Point

**File:** `src/main.py`

**Requirements:**
```python
#!/usr/bin/env python3
"""
Main entry point for AI File Organizer.
"""
import sys
from PyQt6.QtWidgets import QApplication
from pathlib import Path

from .core import AppConfig
from .ui.app_controller import AppController
from .utils import setup_logging


def main():
    """Main application entry point."""
    # Load config
    config = AppConfig.load()
    config.ensure_directories()
    
    # Setup logging
    setup_logging(log_file=config.log_path, level=logging.INFO)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("AI File Organizer")
    app.setOrganizationName("Your Organization")
    
    # Create and run controller
    controller = AppController(config)
    controller.run()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

---

## Phase 4: Advanced Features (Week 6-7)

### 4.1 LLM Response Caching

**File:** `src/core/cache.py`

**Requirements:**
```python
class LLMCache:
    """Cache for LLM analysis results."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()
    
    def get(self, file_hash: str, model_name: str) -> Optional[FileAnalysisResult]:
        """Get cached result."""
        pass
    
    def set(self, file_hash: str, model_name: str, result: FileAnalysisResult):
        """Cache result."""
        pass
    
    def clear_old(self, days: int = 30):
        """Clear old cache entries."""
        pass
```

### 4.2 Batch Optimization

**Update:** `src/ui/workers.py`

Add parallel processing:
```python
class AnalysisWorker(QThread):
    def run(self):
        # Use concurrent.futures.ThreadPoolExecutor
        # Process multiple files in parallel
        # Respect max_concurrent setting
        pass
```

### 4.3 Custom Rules Engine (Optional)

**File:** `src/core/rules.py`

Basic rule system for power users.

---

## Implementation Guidelines

### Code Style
- Follow existing patterns from Phase 1
- Use type hints throughout
- Add comprehensive docstrings
- Follow PEP 8 (use Black formatter)
- Write tests for all new code

### Testing Strategy
- Unit tests for each new module
- Integration tests for workflows
- Manual testing for UI
- Aim for 85%+ coverage

### Error Handling
- Use try/except blocks liberally
- Log errors with context
- Show user-friendly error messages in UI
- Never crash without recovery option

### Performance
- Profile code before optimizing
- Use async/await for I/O operations
- Keep UI responsive with worker threads
- Cache expensive operations

### Documentation
- Update README.md with new features
- Document all public APIs
- Add usage examples
- Create troubleshooting guide

---

## Deliverables

### Phase 2 Deliverables
- [ ] `src/core/organizer.py` with tests
- [ ] `src/core/undo_manager.py` with tests
- [ ] `src/core/backup.py` with tests
- [ ] Integration tests
- [ ] Updated documentation

### Phase 3 Deliverables
- [ ] `src/ui/main_window.py`
- [ ] `src/ui/widgets/` (all widgets)
- [ ] `src/ui/dialogs/` (all dialogs)
- [ ] `src/ui/workers.py`
- [ ] `src/ui/app_controller.py`
- [ ] `src/main.py`
- [ ] UI screenshots for documentation
- [ ] User manual

### Phase 4 Deliverables
- [ ] `src/core/cache.py`
- [ ] Batch optimization
- [ ] Performance benchmarks
- [ ] Updated documentation

---

## Testing Checklist

### Phase 2 Testing
- [ ] File organization creates correct directory structure
- [ ] Conflict resolution works correctly
- [ ] Undo restores files to original locations
- [ ] Backup creates valid copies
- [ ] Dry-run mode doesn't modify files
- [ ] Error handling graceful for all scenarios
- [ ] Database operations are transaction-safe

### Phase 3 Testing
- [ ] UI launches without errors
- [ ] All buttons and menus work
- [ ] Worker threads don't block UI
- [ ] Progress updates in real-time
- [ ] Settings persist across restarts
- [ ] Keyboard shortcuts work
- [ ] Responsive on different screen sizes
- [ ] No memory leaks in long sessions

### Phase 4 Testing
- [ ] Cache improves performance
- [ ] Parallel processing works correctly
- [ ] No race conditions in concurrent operations

---

## Success Criteria

### Phase 2
- ✅ Can organize 100 files in <30 seconds
- ✅ Undo works 100% reliably
- ✅ Zero data loss in stress tests
- ✅ All tests pass with >85% coverage

### Phase 3
- ✅ UI responsive (<100ms for all actions)
- ✅ Application launches in <3 seconds
- ✅ User can complete full workflow in <5 clicks
- ✅ Works on macOS 12.0+

### Phase 4
- ✅ Cache reduces LLM calls by 50%+
- ✅ Batch processing 5x faster for 100+ files
- ✅ Memory usage <2GB for 1000 files

---

## Tips for Implementation

1. **Start small**: Implement and test each component independently
2. **Use the existing code**: Phase 1 has good patterns to follow
3. **Test frequently**: Run tests after each feature
4. **Commit often**: Small, focused commits
5. **Document as you go**: Update docs with each feature
6. **Profile before optimizing**: Measure performance first
7. **Handle errors gracefully**: Never let the app crash
8. **Keep UI responsive**: Always use worker threads
9. **Ask for help**: Review Phase 1 code when stuck
10. **Follow the PRD**: It has all requirements and specs

---

## Example Workflow Implementation

Here's how to implement a complete workflow:

```python
# In AppController

def on_analyze_requested(self):
    """Handle analyze button click."""
    if not self.scanned_files:
        self.show_error("No files scanned. Please select a directory first.")
        return
    
    # Show progress dialog
    progress = ProgressDialog("Analyzing Files")
    progress.show()
    
    # Create worker thread
    self.analysis_worker = AnalysisWorker(
        self.scanned_files,
        self.llm_handler
    )
    
    # Connect signals
    self.analysis_worker.progress.connect(progress.update_progress)
    self.analysis_worker.result.connect(self.on_analysis_result)
    self.analysis_worker.finished.connect(progress.close)
    self.analysis_worker.error.connect(self.on_analysis_error)
    
    # Start worker
    self.analysis_worker.start()

def on_analysis_result(self, result: FileAnalysisResult):
    """Handle individual analysis result."""
    self.analysis_results.append(result)
    self.main_window.results_table.add_result(result)

def on_organize_requested(self):
    """Handle organize button click."""
    # Create organization plan
    selected_results = self.main_window.results_table.get_selected_results()
    plan = self.organizer.create_organization_plan(
        self.scanned_files,
        selected_results,
        base_directory=self.config.organization.target_dir
    )
    
    # Validate plan
    errors = self.organizer.validate_plan(plan)
    if errors:
        self.show_validation_errors(errors)
        return
    
    # Show preview dialog
    if self.show_preview_dialog(plan):
        # User accepted, execute
        self.execute_organization_plan(plan)
```

---

## Questions to Ask During Implementation

If you get stuck, ask yourself:

1. **Does this follow Phase 1 patterns?**
2. **Is this properly tested?**
3. **Will this work for 1000+ files?**
4. **Is the UI still responsive?**
5. **What happens if this fails?**
6. **Is this documented?**
7. **Can a user understand the error messages?**
8. **Is this secure (path validation, etc.)?**

---

## Final Notes

- **Take your time**: Quality over speed
- **Test thoroughly**: Better to catch bugs now
- **Think about UX**: Users should love using this
- **Consider edge cases**: What if the file is locked? Disk is full?
- **Be consistent**: Follow the patterns from Phase 1
- **Document well**: Future you will thank you

Good luck with implementation! The foundation is solid, now build something amazing on top of it.
