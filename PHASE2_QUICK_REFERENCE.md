# Phase 2 Quick Reference Guide

## File Structure Summary

✅ **Phase 2 Implementation Complete** - All files created and implemented

### Core Modules Created

```
src/core/
├── organizer.py          - File organization engine (200+ lines)
├── undo_manager.py       - Operation tracking & reversal (350+ lines)
├── backup.py             - Backup management system (300+ lines)
└── __init__.py          - Module initialization
```

### Tests Created

```
tests/
├── test_organizer.py              - Unit tests (400+ lines)
├── test_integration_phase2.py     - Integration tests (500+ lines)
└── __init__.py                    - Test module initialization
```

### Documentation Created

```
├── PHASE2_IMPLEMENTATION.md  - Complete Phase 2 guide
├── PROJECT_STRUCTURE.md      - Full project structure overview
└── README (updated)          - Project documentation
```

## Key Classes & Methods

### FileOrganizer
```python
# Main class for file organization operations
organizer = FileOrganizer(undo_manager=..., backup_manager=...)

# Create a plan from analysis results
plan = organizer.create_organization_plan(files, results, target_dir)

# Validate plan before execution
errors = organizer.validate_plan(plan)

# Execute organization (dry-run or actual)
result = organizer.execute_plan(plan, dry_run=False)

# Resolve naming conflicts
plan = organizer.resolve_conflicts(plan)
```

### UndoManager
```python
# Initialize with database path
undo_mgr = UndoManager(db_path)

# Record operations (done automatically by FileOrganizer)
undo_mgr.record_operation(batch_id, op_type, source, target)

# Undo a specific batch
undo_result = undo_mgr.undo_batch(batch_id)

# Undo the last operation batch
undo_result = undo_mgr.undo_last()

# Get operation history
history = undo_mgr.get_history(limit=100)

# Verify undo is possible
can_undo = undo_mgr.verify_undo_possible(batch_id)
```

### BackupManager
```python
# Initialize with backup directory
backup_mgr = BackupManager(backup_dir, strategy=BackupStrategy.COPY)

# Create backup before organization
backup_path = backup_mgr.create_backup(files, batch_id)

# List available backups
backups = backup_mgr.list_backups()

# Verify backup integrity
is_valid = backup_mgr.verify_backup(backup_path, original_files)

# Clean old backups
deleted = backup_mgr.cleanup_old_backups(retention_days=30)
```

## Running Tests

```bash
# Run all Phase 2 tests
pytest tests/test_organizer.py tests/test_integration_phase2.py -v

# Run with coverage report
pytest tests/ --cov=src.core --cov-report=html

# Run specific test class
pytest tests/test_organizer.py::TestFileOrganizer -v

# Run specific test method
pytest tests/test_organizer.py::TestFileOrganizer::test_execute_plan_actual -v
```

## Integration Example

```python
from pathlib import Path
from src.core.organizer import FileOrganizer
from src.core.undo_manager import UndoManager
from src.core.backup import BackupManager, BackupStrategy

# Setup all components
db_path = Path.home() / ".file_organizer" / "undo.db"
backup_dir = Path.home() / ".file_organizer" / "backups"

undo_mgr = UndoManager(db_path)
backup_mgr = BackupManager(backup_dir, BackupStrategy.COPY)
organizer = FileOrganizer(undo_manager=undo_mgr, backup_manager=backup_mgr)

# Example files and analysis results
files = [Path("document.pdf"), Path("image.jpg")]
results = [
    {
        "file_path": "document.pdf",
        "category": "documents",
        "suggested_name": "important_doc.pdf",
        "confidence": 0.95,
        "reasoning": "PDF document"
    },
    {
        "file_path": "image.jpg",
        "category": "photos",
        "suggested_name": "photo_2024.jpg",
        "confidence": 0.88,
        "reasoning": "JPEG image from 2024"
    }
]

# Create and validate plan
plan = organizer.create_organization_plan(files, results, Path("/organized"))
errors = organizer.validate_plan(plan)

if not errors:
    # Dry run to preview
    preview = organizer.execute_plan(plan, dry_run=True)
    print(f"Would organize {preview.operations_completed} files")
    
    # Actually execute
    result = organizer.execute_plan(plan, dry_run=False)
    if result.success:
        print(f"✓ Organized {result.operations_completed} files")
        print(f"  Batch ID: {result.batch_id}")
        
        # Can undo later
        undo_result = undo_mgr.undo_batch(result.batch_id)
        if undo_result.success:
            print(f"✓ Undone {undo_result.operations_undone} operations")
    else:
        print(f"✗ Failed: {result.errors}")
else:
    print(f"✗ Validation errors: {errors}")
```

## Data Flow

```
Files to Organize
       ↓
FileScanner → Scanned Files
       ↓
LLM Analysis → Analysis Results
       ↓
FileOrganizer.create_organization_plan() → Plan
       ↓
FileOrganizer.validate_plan() → Validation (Errors or OK)
       ↓
BackupManager.create_backup() → Backup Copy (if enabled)
       ↓
FileOrganizer.execute_plan() → File Operations
       ↓
UndoManager.record_operation() → Operation Log
       ↓
Result with Batch ID → Can Undo Later
```

## Important Concepts

### Batch ID
- Unique identifier for a set of operations
- Generated automatically by FileOrganizer
- Used to undo multiple operations together
- Returned in ExecutionResult

### Dry Run Mode
- Safe preview of what would happen
- Doesn't move files
- Shows all validation errors
- Perfect for testing plans before execution

### Conflict Resolution
- Detects when multiple files map to same destination
- Automatically renames using (1), (2), etc.
- Preserves file extensions
- Applied before execution

### Backup Strategy
- `COPY`: Creates full backup before organizing
- `NONE`: Skips backup (for testing only)
- Backups are timestamped and retained
- Old backups automatically cleaned up

## Common Workflows

### Workflow 1: Simple Organization
```
Plan → Validate → Execute (dry-run) → Execute (actual)
```

### Workflow 2: Organization with Safety
```
Plan → Validate → Backup → Execute → Record in Undo
```

### Workflow 3: Organization with Conflict Handling
```
Plan → Validate → Resolve Conflicts → Execute
```

### Workflow 4: Safe Organization with Full Recovery
```
Plan → Validate → Backup → Resolve Conflicts → Execute → Record
(If needed: Undo → Restore from Backup)
```

## File Organization Output Structure

After running FileOrganizer.execute_plan():

```
/organized/
├── documents/
│   ├── important_doc.pdf
│   └── memo.docx
├── photos/
│   ├── photo_2024.jpg
│   └── vacation_2023.png
└── other/
    └── misc_file.txt
```

## Error Messages

### Validation Errors
- "Conflict: Multiple files targeting..."
- "Source file not found..."
- "Cannot organize into system directory..."
- "Insufficient disk space..."
- "No read permission..."

### Execution Errors
- "Failed to move..." (with reason)
- "Backup creation failed..."
- "Backup verification failed..."

### Undo Errors
- "Target file not found..." (can't reverse operation)
- "No undoable operations found for batch..."

## Performance Tips

1. **Dry Run First**: Always preview with `dry_run=True`
2. **Validate Before Execute**: Call `validate_plan()` first
3. **Batch Operations**: Organize multiple files at once
4. **Disable Backups for Testing**: Use `BackupStrategy.NONE`
5. **Clean Old Backups**: Run `cleanup_old_backups()` periodically

## Database Location

UndoManager uses SQLite database at:
```
~/.file_organizer/undo.db
```

Contains tables:
- `operations`: All recorded operations with batch tracking
- Indexes on `batch_id`, `timestamp`, `undone` for fast queries

## What's Next (Phase 3)

Phase 3 will add the PyQt6 graphical user interface:
- Main window with menu and toolbar
- Directory selection dialog
- Results table showing analysis
- Progress indicators
- Settings dialog
- Background worker threads

---

**Phase 2 Status**: ✅ COMPLETE
**Test Coverage**: Unit tests + Integration tests implemented
**Documentation**: Complete with examples and guides
**Ready for**: Phase 3 UI Development
