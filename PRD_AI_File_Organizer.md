# Product Requirements Document (PRD)
## AI File Organizer

**Version:** 1.0  
**Date:** January 30, 2026  
**Status:** Phase 1 Complete - Phases 2-4 In Planning

---

## Executive Summary

AI File Organizer is a desktop application that uses local Large Language Models (LLMs) to intelligently organize messy files. The application analyzes file content, suggests logical categories, and renames files with descriptive names—all while maintaining user privacy through local-only processing optimized for Apple Silicon.

### Target Users
- **Primary:** Professionals with disorganized file systems (photographers, researchers, content creators)
- **Secondary:** General users wanting automated file management
- **Technical Level:** Non-technical to moderately technical users

### Key Differentiators
1. **100% Local Processing** - No cloud services, complete privacy
2. **Multiple LLM Support** - Works with Ollama, LM Studio, LocalAI, and OpenAI-compatible APIs
3. **Apple Silicon Optimized** - Leverages M1/M2/M3/M4 Metal acceleration
4. **Content-Aware** - Analyzes actual file content, not just metadata
5. **Safe Operations** - Dry-run mode, undo capability, automatic backups

---

## Product Vision

**Vision Statement:**  
"Empower users to effortlessly organize their digital lives using AI, while maintaining complete privacy and control over their data."

**Success Metrics:**
- 85%+ of AI suggestions accepted by users
- Process 100 files in <2 minutes on M4 MacBook Pro
- Zero data loss incidents
- 90%+ user satisfaction rating

---

## Phase Overview

### ✅ Phase 1: Core Backend (COMPLETE)
**Status:** Production-ready  
**Duration:** Completed  
**Test Coverage:** 90%+

#### Delivered Components:
1. **Configuration System**
   - Pydantic-based type-safe configuration
   - JSON persistence with hot-reload
   - Environment variable support
   - Nested configuration for LLM, organization, UI settings

2. **LLM Integration**
   - Abstract handler interface for extensibility
   - Ollama handler (local inference)
   - OpenAI-compatible handler (LM Studio, LocalAI)
   - Factory pattern for provider switching
   - Smart prompting with context awareness
   - Robust JSON response parsing

3. **File Scanner**
   - Recursive directory traversal
   - Pattern-based filtering (hidden files, extensions)
   - Progress callbacks for UI integration
   - Comprehensive error handling
   - File statistics and metadata extraction

4. **File Parsers**
   - Extensible parser registry
   - PDF (pypdf) - text and metadata extraction
   - Word (python-docx) - paragraphs, tables, properties
   - Excel (openpyxl) - multi-sheet support
   - Images (Pillow) - EXIF data extraction
   - Text (40+ formats) - multi-encoding support
   - Graceful degradation for unsupported formats

5. **Testing Infrastructure**
   - Unit tests for all core modules
   - Mock-based LLM testing
   - Async test support
   - Coverage reporting
   - Integration test framework

#### Technical Specifications:
- **Language:** Python 3.11+
- **Dependencies:** PyQt6, Ollama, pypdf, python-docx, openpyxl, Pillow, Pydantic
- **Architecture:** Modular, event-driven, async-capable
- **Code Quality:** Type hints, docstrings, PEP 8 compliant

---

### 🔄 Phase 2: File Operations (PLANNED)

**Estimated Duration:** 1-2 weeks  
**Priority:** High  
**Dependencies:** Phase 1 complete

#### Objectives:
Implement safe file organization operations with preview, undo, and backup capabilities.

#### Requirements:

##### 2.1 File Organizer Module
**Priority:** P0 (Critical)

**Functional Requirements:**
- FR-2.1.1: Move files to suggested category directories
- FR-2.1.2: Rename files according to LLM suggestions
- FR-2.1.3: Create directory structure as needed
- FR-2.1.4: Handle filename conflicts (append numbers, ask user)
- FR-2.1.5: Preserve file extensions
- FR-2.1.6: Validate target paths (no system directories)
- FR-2.1.7: Support batch operations
- FR-2.1.8: Atomic operations (all-or-nothing for batches)

**Non-Functional Requirements:**
- NFR-2.1.1: Process 100 files in <30 seconds
- NFR-2.1.2: Zero data corruption
- NFR-2.1.3: Graceful handling of permission errors
- NFR-2.1.4: Progress reporting every 100ms

**Technical Specification:**
```python
class FileOrganizer:
    def create_organization_plan(files: List[ScannedFile], 
                                 results: List[FileAnalysisResult]) -> OrganizationPlan
    def execute_plan(plan: OrganizationPlan, dry_run: bool = True) -> ExecutionResult
    def validate_plan(plan: OrganizationPlan) -> List[ValidationError]
    def resolve_conflicts(plan: OrganizationPlan) -> OrganizationPlan
```

##### 2.2 Dry-Run Mode
**Priority:** P0 (Critical)

**Functional Requirements:**
- FR-2.2.1: Preview all changes before execution
- FR-2.2.2: Show source → destination mappings
- FR-2.2.3: Highlight potential conflicts
- FR-2.2.4: Calculate total disk space changes
- FR-2.2.5: Identify permission issues before execution
- FR-2.2.6: Allow user to accept/reject individual operations

**User Interface:**
- Preview table with columns: Original Path, New Path, Action, Confidence
- Filters: Show only high/medium/low confidence
- Bulk actions: Accept all, Reject all, Accept >90% confidence

##### 2.3 Undo Manager
**Priority:** P0 (Critical)

**Functional Requirements:**
- FR-2.3.1: Record all file operations in SQLite database
- FR-2.3.2: Support undo of last N operations (configurable, default 100)
- FR-2.3.3: Undo entire batch or individual files
- FR-2.3.4: Verify files exist before undo
- FR-2.3.5: Clear undo history on user request
- FR-2.3.6: Auto-cleanup old history (configurable retention)

**Database Schema:**
```sql
CREATE TABLE operations (
    id INTEGER PRIMARY KEY,
    batch_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    operation_type TEXT NOT NULL,  -- 'move', 'rename'
    source_path TEXT NOT NULL,
    target_path TEXT NOT NULL,
    file_hash TEXT,  -- SHA256 for verification
    undone BOOLEAN DEFAULT 0
);

CREATE INDEX idx_batch ON operations(batch_id);
CREATE INDEX idx_timestamp ON operations(timestamp);
```

**Technical Specification:**
```python
class UndoManager:
    def record_operation(op: FileOperation) -> None
    def undo_batch(batch_id: str) -> UndoResult
    def undo_last() -> UndoResult
    def get_history(limit: int = 100) -> List[OperationRecord]
    def clear_history(older_than: datetime = None) -> int
    def verify_undo_possible(batch_id: str) -> bool
```

##### 2.4 Backup System
**Priority:** P1 (High)

**Functional Requirements:**
- FR-2.4.1: Create backup before any operation (if enabled)
- FR-2.4.2: Configurable backup strategies:
  - Copy files to backup directory
  - Use filesystem snapshots (macOS Time Machine)
  - No backup (user accepts risk)
- FR-2.4.3: Backup retention policies
- FR-2.4.4: Restore from backup
- FR-2.4.5: Verify backup integrity

**Configuration Options:**
```python
class BackupConfig:
    enabled: bool = True
    strategy: BackupStrategy = BackupStrategy.COPY
    backup_dir: Path = Path("~/.file-organizer/backups")
    retention_days: int = 30
    max_backup_size_gb: int = 10
    verify_backups: bool = True
```

##### 2.5 Error Handling & Recovery
**Priority:** P0 (Critical)

**Requirements:**
- FR-2.5.1: Rollback on any operation failure in batch
- FR-2.5.2: Detailed error logging with stack traces
- FR-2.5.3: User-friendly error messages
- FR-2.5.4: Retry logic for transient errors (3 attempts)
- FR-2.5.5: Quarantine files that fail repeatedly
- FR-2.5.6: Email/notification on critical errors (optional)

#### Acceptance Criteria:
- ✅ All file operations are reversible
- ✅ Dry-run mode shows accurate preview
- ✅ No data loss in 1000+ file test scenarios
- ✅ Undo works correctly for all operation types
- ✅ Backup system creates valid backups
- ✅ Error messages guide user to resolution
- ✅ Performance: 100 files in <30 seconds
- ✅ Unit test coverage >85%

---

### 🖥️ Phase 3: PyQt6 User Interface (PLANNED)

**Estimated Duration:** 2-3 weeks  
**Priority:** High  
**Dependencies:** Phase 2 complete

#### Objectives:
Create a modern, intuitive desktop interface using PyQt6 that provides seamless interaction with the file organization system.

#### Requirements:

##### 3.1 Main Window
**Priority:** P0 (Critical)

**Functional Requirements:**
- FR-3.1.1: Menu bar with File, Edit, View, Tools, Help
- FR-3.1.2: Toolbar with common actions
- FR-3.1.3: Status bar with current operation and statistics
- FR-3.1.4: Dockable panels for flexibility
- FR-3.1.5: Keyboard shortcuts for all actions
- FR-3.1.6: Window state persistence (size, position, layout)

**Layout:**
```
┌─────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help          [_][□][X]│
├─────────────────────────────────────────────────┤
│ [📁] [🔍] [▶] [⏸] [↩] [⚙]                      │
├─────────────────┬───────────────────────────────┤
│                 │                               │
│  Directory      │     Preview Results           │
│  Tree           │                               │
│                 │                               │
│  [Select]       │  [Analyze] [Organize]         │
│                 │                               │
├─────────────────┴───────────────────────────────┤
│ Status: Ready | Files: 0 | Progress: 0%        │
└─────────────────────────────────────────────────┘
```

##### 3.2 Directory Selection Panel
**Priority:** P0 (Critical)

**Functional Requirements:**
- FR-3.2.1: Native folder browser
- FR-3.2.2: Recent directories dropdown
- FR-3.2.3: Bookmarks/favorites
- FR-3.2.4: Recursive scan toggle
- FR-3.2.5: Quick preview of file counts by type
- FR-3.2.6: Drag-and-drop folder support

**UI Elements:**
- Text field with browse button
- Checkbox: "Include subdirectories"
- Dropdown: "Recent folders"
- Label: "X files found (Y supported)"

##### 3.3 File Preview & Results Table
**Priority:** P0 (Critical)

**Functional Requirements:**
- FR-3.3.1: Sortable table with columns:
  - Checkbox (select)
  - Original Path
  - Original Name
  - Suggested Category
  - Suggested Name
  - Confidence (with color coding)
  - Status (Ready/Processing/Done/Error)
- FR-3.3.2: Multi-select for bulk actions
- FR-3.3.3: Context menu (Accept, Reject, Edit, View Details)
- FR-3.3.4: Inline editing of suggestions
- FR-3.3.5: Color coding by confidence:
  - Green: >90% (high confidence)
  - Yellow: 70-90% (medium)
  - Red: <70% (low confidence)
- FR-3.3.6: Filter by confidence, file type, status
- FR-3.3.7: Search/filter text box

**Table Interactions:**
- Double-click: Edit suggestion
- Right-click: Context menu
- Ctrl+A: Select all
- Space: Toggle selection

##### 3.4 Progress Tracking
**Priority:** P0 (Critical)

**Functional Requirements:**
- FR-3.4.1: Progress bar with percentage
- FR-3.4.2: Current operation description
- FR-3.4.3: Time elapsed and estimated remaining
- FR-3.4.4: Files processed / total
- FR-3.4.5: Cancel button (graceful cancellation)
- FR-3.4.6: Pause/Resume for long operations
- FR-3.4.7: Mini-log showing recent operations

**UI Elements:**
```
┌──────────────────────────────────────────┐
│ Analyzing files...                       │
│ ████████████░░░░░░░░░░░░░░ 45% (45/100) │
│                                          │
│ Current: analyzing budget_2024.pdf       │
│ Elapsed: 01:23 | Remaining: ~01:50      │
│                                          │
│              [Pause] [Cancel]            │
└──────────────────────────────────────────┘
```

##### 3.5 Settings/Preferences Dialog
**Priority:** P1 (High)

**Functional Requirements:**
- FR-3.5.1: Tabbed interface with sections:
  - General
  - LLM Settings
  - Organization Rules
  - Advanced
- FR-3.5.2: LLM provider selection dropdown
- FR-3.5.3: Model selection (with "Refresh Models" button)
- FR-3.5.4: Temperature slider (0.0 - 2.0)
- FR-3.5.5: Confidence threshold slider
- FR-3.5.6: File type filters (checkboxes)
- FR-3.5.7: Ignore patterns list editor
- FR-3.5.8: Dry-run mode toggle
- FR-3.5.9: Backup settings
- FR-3.5.10: Theme selection (Light/Dark)
- FR-3.5.11: Reset to defaults button
- FR-3.5.12: Test LLM connection button

**Settings Tabs:**

**General:**
- Default directory
- Auto-scan on startup
- Show notifications
- Theme selection
- Language (future)

**LLM Settings:**
- Provider: [Ollama ▼]
- Model: [llama3.2:3b ▼] [Refresh]
- Base URL: [http://localhost:11434]
- Temperature: [━━━━━●━━━━] 0.3
- Max Tokens: [1024]
- Test Connection: [Button] Status: ✅ Connected

**Organization Rules:**
- Confidence threshold: [━━━━━━━●━] 80%
- Auto-accept high confidence: [✓]
- Preserve extensions: [✓]
- Ignore hidden files: [✓]
- Max filename length: [100]

**Advanced:**
- Cache LLM responses: [✓]
- Backup before operations: [✓]
- Undo history size: [100]
- Log level: [INFO ▼]

##### 3.6 Undo History View
**Priority:** P1 (High)

**Functional Requirements:**
- FR-3.6.1: List of recent operations (newest first)
- FR-3.6.2: Show batch operations grouped
- FR-3.6.3: Undo button for each batch
- FR-3.6.4: Clear history button
- FR-3.6.5: Export history to CSV
- FR-3.6.6: Search/filter history

**UI Layout:**
```
┌─────────────────────────────────────────┐
│ Undo History                            │
├─────────────────────────────────────────┤
│ 🔄 Batch #123 - Jan 30, 2026 14:23     │
│    ├─ Moved 45 files                    │
│    └─ Renamed 45 files                  │
│    [Undo This Batch]                    │
├─────────────────────────────────────────┤
│ 🔄 Batch #122 - Jan 30, 2026 13:15     │
│    ├─ Moved 12 files                    │
│    └─ Renamed 12 files                  │
│    [Undo This Batch]                    │
├─────────────────────────────────────────┤
│         [Clear All History]             │
└─────────────────────────────────────────┘
```

##### 3.7 Notifications & Feedback
**Priority:** P1 (High)

**Functional Requirements:**
- FR-3.7.1: Toast notifications for operations
- FR-3.7.2: System tray integration (minimize to tray)
- FR-3.7.3: macOS notification center integration
- FR-3.7.4: Sound effects (optional, configurable)
- FR-3.7.5: Visual feedback (button states, loading spinners)

**Notification Types:**
- Success: "✅ Organized 45 files successfully"
- Warning: "⚠️ 3 files skipped due to errors"
- Error: "❌ Operation failed: Permission denied"
- Info: "ℹ️ Analysis complete, review results"

##### 3.8 Keyboard Shortcuts
**Priority:** P2 (Medium)

**Required Shortcuts:**
- Cmd+O: Open folder
- Cmd+R: Refresh / Re-scan
- Cmd+A: Select all
- Cmd+D: Deselect all
- Cmd+Z: Undo last operation
- Cmd+,: Open settings
- Cmd+Q: Quit
- Cmd+F: Focus search/filter
- Space: Toggle selection
- Enter: Accept selected suggestions
- Escape: Cancel current operation

#### Technical Specifications:

**UI Framework:**
```python
# Main window structure
class MainWindow(QMainWindow):
    def __init__(self):
        self.setup_ui()
        self.setup_signals()
        self.load_state()
    
    def setup_ui(self):
        # Menu bar, toolbar, status bar
        # Central widget with splitter
        # Dockable panels
    
    def setup_signals(self):
        # Connect UI events to handlers
        # Setup progress callbacks
        # Handle async operations
```

**Threading Model:**
- UI thread: All PyQt widgets and events
- Worker threads: File scanning, LLM analysis, file operations
- QThread for long-running operations
- Signals/slots for thread communication
- Progress callbacks via Qt signals

**State Management:**
```python
class AppState:
    selected_directory: Optional[Path]
    scanned_files: List[ScannedFile]
    analysis_results: List[FileAnalysisResult]
    organization_plan: Optional[OrganizationPlan]
    operation_status: OperationStatus
```

#### Design Guidelines:

**Visual Design:**
- Native macOS look and feel
- Consistent with macOS Big Sur+ design language
- Minimum window size: 1000x700
- Responsive layout (resizable panels)
- High DPI support (Retina displays)

**Color Scheme (Light Mode):**
- Primary: #007AFF (macOS blue)
- Success: #34C759 (green)
- Warning: #FF9500 (orange)
- Error: #FF3B30 (red)
- Background: #FFFFFF
- Text: #000000

**Color Scheme (Dark Mode):**
- Primary: #0A84FF
- Success: #32D74B
- Warning: #FF9F0A
- Error: #FF453A
- Background: #1E1E1E
- Text: #FFFFFF

**Typography:**
- System font (SF Pro on macOS)
- UI Labels: 13pt
- Table text: 12pt
- Status bar: 11pt

**Icons:**
- SF Symbols (macOS native)
- Fallback to Material Icons
- Consistent 24x24 size

#### Acceptance Criteria:
- ✅ Window launches in <2 seconds
- ✅ Responsive UI (no freezing during operations)
- ✅ All operations cancelable
- ✅ Settings persist across sessions
- ✅ Keyboard navigation fully functional
- ✅ Works on macOS 12.0+
- ✅ High DPI support verified
- ✅ Dark mode fully supported
- ✅ No memory leaks in 8-hour stress test
- ✅ Accessibility features work (VoiceOver compatible)

---

### 🚀 Phase 4: Advanced Features (PLANNED)

**Estimated Duration:** 1-2 weeks  
**Priority:** Medium  
**Dependencies:** Phase 3 complete

#### Objectives:
Add advanced features that enhance functionality and user experience.

#### Requirements:

##### 4.1 Multi-Modal Analysis (Vision)
**Priority:** P1 (High)

**Functional Requirements:**
- FR-4.1.1: Analyze image content using vision-capable LLMs
- FR-4.1.2: Extract objects, scenes, text from images
- FR-4.1.3: Use visual content for categorization
- FR-4.1.4: Support for models: LLaVA, Qwen-VL, CogVLM

**Use Cases:**
- Photos: Categorize by content (beach, mountain, city)
- Screenshots: Extract and organize by application
- Diagrams: Categorize by type (flowchart, UML, architecture)

**Technical Specification:**
```python
class VisionLLMHandler(BaseLLMHandler):
    def analyze_image(self, image_path: Path, 
                     prompt: str) -> ImageAnalysisResult
    def extract_text_from_image(self, image_path: Path) -> str
    def detect_objects(self, image_path: Path) -> List[str]
```

##### 4.2 Custom Rules Engine
**Priority:** P2 (Medium)

**Functional Requirements:**
- FR-4.2.1: Define custom categorization rules
- FR-4.2.2: Rule types:
  - Pattern-based (regex on filename/content)
  - Extension-based
  - Size-based
  - Date-based
  - Metadata-based
- FR-4.2.3: Rule priority/ordering
- FR-4.2.4: Rule testing interface
- FR-4.2.5: Import/export rule sets

**Example Rules:**
```python
rules = [
    Rule(
        name="Tax Documents",
        condition=lambda f: "tax" in f.content.lower() or "1040" in f.name,
        category="Financial/Taxes",
        priority=10
    ),
    Rule(
        name="Photos by Year",
        condition=lambda f: f.metadata.get('exif', {}).get('DateTimeOriginal'),
        category=lambda f: f"Photos/{extract_year(f)}",
        priority=5
    ),
]
```

**UI:**
- Rules editor with add/edit/delete
- Test rule on selected files
- Enable/disable individual rules
- Import from JSON/YAML

##### 4.3 Watch Mode (Auto-Organize)
**Priority:** P2 (Medium)

**Functional Requirements:**
- FR-4.3.1: Monitor specified directories for new files
- FR-4.3.2: Automatically analyze and organize new files
- FR-4.3.3: Configurable watch directories
- FR-4.3.4: Configurable delay before organizing
- FR-4.3.5: Notification when files are organized
- FR-4.3.6: Start watch mode on app launch (optional)

**Configuration:**
```python
class WatchConfig:
    enabled: bool = False
    watch_directories: List[Path] = []
    organize_delay_seconds: int = 30
    auto_accept_threshold: float = 0.9
    notify_on_organize: bool = True
```

**Implementation:**
- Use watchdog library for filesystem monitoring
- Debounce file events (wait for write completion)
- Queue files for processing
- Background thread for watching

##### 4.4 Batch Optimization
**Priority:** P2 (Medium)

**Functional Requirements:**
- FR-4.4.1: Parallel LLM calls for multiple files
- FR-4.4.2: Request batching (group similar files)
- FR-4.4.3: Response caching (avoid re-analyzing)
- FR-4.4.4: Intelligent scheduling (prioritize by confidence)
- FR-4.4.5: Resource throttling (CPU/memory limits)

**Optimizations:**
- Group files by type for batch analysis
- Cache responses by file hash
- Parallel processing with configurable concurrency
- Skip re-analysis of unchanged files

**Performance Targets:**
- 5x faster for batches of 100+ files
- 50% reduction in LLM API calls via caching
- Memory usage <500MB for 1000 files

##### 4.5 Advanced Search & Filters
**Priority:** P2 (Medium)

**Functional Requirements:**
- FR-4.5.1: Search file content (full-text search)
- FR-4.5.2: Filter by:
  - Confidence range
  - File type/extension
  - Size range
  - Date range
  - Analysis status
  - Category
- FR-4.5.3: Save filter presets
- FR-4.5.4: Combined filters (AND/OR logic)

**UI:**
```
┌─────────────────────────────────────┐
│ 🔍 Search: [____________] [Search] │
│                                     │
│ Filters:                            │
│ Confidence: [70%] to [100%]        │
│ Type: [☑ PDF] [☑ DOCX] [☐ Images] │
│ Size: [Any ▼]                      │
│ Date: [Last 7 days ▼]              │
│                                     │
│ [Clear] [Save Preset]              │
└─────────────────────────────────────┘
```

##### 4.6 Export & Reporting
**Priority:** P3 (Low)

**Functional Requirements:**
- FR-4.6.1: Export results to CSV/Excel
- FR-4.6.2: Generate organization report (HTML/PDF)
- FR-4.6.3: Statistics dashboard
- FR-4.6.4: Charts: files by category, confidence distribution
- FR-4.6.5: Export undo history

**Report Contents:**
- Summary statistics
- Category breakdown
- Confidence distribution chart
- List of organized files
- Errors and warnings
- Timestamp and user info

##### 4.7 Cloud Integration (Optional)
**Priority:** P3 (Low)

**Functional Requirements:**
- FR-4.7.1: Organize files in cloud storage (Google Drive, Dropbox)
- FR-4.7.2: OAuth authentication
- FR-4.7.3: Sync local and cloud organizations
- FR-4.7.4: Respect cloud storage quotas

**Note:** Cloud integration reduces privacy benefits and should be clearly optional.

#### Acceptance Criteria:
- ✅ Vision analysis improves photo categorization by 30%
- ✅ Custom rules apply correctly 100% of the time
- ✅ Watch mode organizes files within 60 seconds
- ✅ Batch optimization achieves 5x speedup
- ✅ Search returns results in <500ms for 10,000 files
- ✅ Reports generate in <5 seconds
- ✅ All features configurable via UI
- ✅ Documentation updated for all new features

---

## Technical Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     PyQt6 UI Layer                      │
│  (Main Window, Dialogs, Progress, Settings)            │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────┴───────────────────────────────────────┐
│              Application Controller                     │
│  (State Management, Event Handling, Workflows)         │
└────────┬───────────┬──────────┬─────────┬─────────────┘
         │           │          │         │
    ┌────▼───┐  ┌───▼────┐ ┌───▼───┐ ┌──▼──────┐
    │ File   │  │  LLM   │ │ File  │ │ Undo    │
    │Scanner │  │Handler │ │Organiz│ │ Manager │
    └────┬───┘  └───┬────┘ └───┬───┘ └──┬──────┘
         │          │          │         │
    ┌────▼──────────▼──────────▼─────────▼──────┐
    │          Storage Layer                     │
    │  (SQLite, FileSystem, Cache, Config)      │
    └────────────────────────────────────────────┘
```

### Data Flow

```
1. User selects directory
       ↓
2. FileScanner traverses and parses files
       ↓
3. Parsers extract content → ScannedFile objects
       ↓
4. LLMHandler analyzes each file → FileAnalysisResult
       ↓
5. FileOrganizer creates OrganizationPlan
       ↓
6. User reviews in UI (dry-run mode)
       ↓
7. User accepts → FileOrganizer executes plan
       ↓
8. UndoManager records operations
       ↓
9. Backup system creates safety copy (if enabled)
       ↓
10. Files are moved/renamed
       ↓
11. UI updates with results
```

### Technology Stack

**Language:** Python 3.11+

**Core Dependencies:**
- **PyQt6** 6.6.0+ - GUI framework
- **Ollama** 0.1.0+ - Local LLM inference
- **Pydantic** 2.5.0+ - Data validation
- **SQLite** 3.x - Undo history database

**File Parsing:**
- **pypdf** 3.17.0+ - PDF parsing
- **python-docx** 1.1.0+ - Word documents
- **openpyxl** 3.1.0+ - Excel files
- **Pillow** 10.1.0+ - Images and EXIF

**Optional:**
- **watchdog** - File system monitoring (Phase 4)
- **pytesseract** - OCR for scanned documents
- **openai** - OpenAI-compatible API client

**Development:**
- **pytest** 7.4.0+ - Testing framework
- **black** 23.12.0+ - Code formatting
- **ruff** 0.1.8+ - Linting
- **mypy** 1.7.0+ - Type checking

### Database Schema

**Undo Operations Table:**
```sql
CREATE TABLE operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    operation_type TEXT NOT NULL,  -- 'move', 'rename', 'delete'
    source_path TEXT NOT NULL,
    target_path TEXT,
    file_hash TEXT,
    metadata TEXT,  -- JSON
    undone BOOLEAN DEFAULT 0,
    undo_timestamp REAL
);

CREATE INDEX idx_batch ON operations(batch_id);
CREATE INDEX idx_timestamp ON operations(timestamp DESC);
CREATE INDEX idx_undone ON operations(undone);
```

**Cache Table (Phase 4):**
```sql
CREATE TABLE llm_cache (
    file_hash TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    content_preview TEXT,
    analysis_result TEXT NOT NULL,  -- JSON
    model_name TEXT NOT NULL,
    timestamp REAL NOT NULL,
    confidence REAL
);

CREATE INDEX idx_timestamp ON llm_cache(timestamp DESC);
```

### Configuration Files

**Location:** `~/.file-organizer/`

**Files:**
- `config.json` - Main configuration
- `organizer.db` - SQLite database
- `app.log` - Application logs
- `cache/` - LLM response cache

**Config Structure:**
```json
{
  "app_name": "AI File Organizer",
  "app_version": "0.1.0",
  "llm": {
    "provider": "ollama",
    "model_name": "llama3.2:3b",
    "base_url": "http://localhost:11434",
    "temperature": 0.3,
    "max_tokens": 1024
  },
  "organization": {
    "dry_run": true,
    "confidence_threshold": 0.8,
    "auto_accept_high_confidence": false,
    "preserve_extensions": true,
    "ignore_hidden_files": true
  },
  "ui": {
    "window_width": 1200,
    "window_height": 800,
    "theme": "light"
  }
}
```

---

## Performance Requirements

### Response Times
- **Application Launch:** <3 seconds (cold start)
- **Directory Scan (1000 files):** <10 seconds
- **LLM Analysis (per file):** <2 seconds average
- **File Operation (per file):** <100ms
- **Undo Operation:** <1 second
- **Settings Save:** <500ms
- **UI Responsiveness:** <100ms for all interactions

### Scalability
- **Max Files per Batch:** 10,000
- **Max File Size:** 100MB per file
- **Max Total Size:** 10GB per batch
- **Concurrent LLM Calls:** Configurable (default: 3)
- **Memory Usage:** <1GB for 1000 files
- **Database Size:** <100MB for 100,000 operations

### Resource Limits
- **CPU Usage:** <50% average on M4
- **Memory Usage:** <2GB with 3B model, <8GB with 7B model
- **Disk I/O:** <100MB/s sustained
- **Network:** Local only (no internet required after setup)

---

## Security & Privacy

### Privacy Requirements
- **PR-1:** All file processing happens locally
- **PR-2:** No data sent to external servers (except user-enabled cloud features)
- **PR-3:** No telemetry or analytics without explicit consent
- **PR-4:** User data stays on user's machine
- **PR-5:** LLM models run locally via Ollama

### Security Requirements
- **SR-1:** Validate all file paths to prevent directory traversal
- **SR-2:** Sanitize filenames to prevent shell injection
- **SR-3:** Check file permissions before operations
- **SR-4:** Secure storage of API keys (if cloud features used)
- **SR-5:** No execution of file contents
- **SR-6:** Sandboxed file operations (no system directories)

### Data Protection
- **DP-1:** Backups encrypted with user's file system encryption
- **DP-2:** Undo database protected with file permissions
- **DP-3:** Logs don't contain sensitive file contents
- **DP-4:** Configuration files readable only by user

---

## Testing Requirements

### Unit Tests
- **Coverage Target:** 85%+ for core modules
- **Test Frameworks:** pytest, pytest-cov, pytest-asyncio
- **Mock LLM Calls:** All LLM tests use mocks
- **Test Data:** Synthetic test files (no real user data)

### Integration Tests
- **End-to-End Workflows:** Scan → Analyze → Organize → Undo
- **LLM Integration:** Test with real Ollama instance
- **File System Operations:** Test in temporary directories
- **Error Scenarios:** Permission errors, disk full, etc.

### UI Tests
- **Manual Testing:** Required for all UI changes
- **Automated UI Tests:** Optional (QTest framework)
- **Accessibility Testing:** VoiceOver compatibility
- **Visual Regression:** Screenshot comparisons

### Performance Tests
- **Benchmark Suite:** 100, 1000, 10000 file scenarios
- **Memory Profiling:** Check for leaks
- **Stress Testing:** 8-hour continuous operation
- **Platform Testing:** macOS 12, 13, 14

### Acceptance Tests
- **User Acceptance Testing:** 5+ beta testers
- **Real-World Scenarios:** Actual messy directories
- **Edge Cases:** Unusual filenames, large files, corrupted files

---

## Documentation Requirements

### User Documentation
- **Installation Guide:** Step-by-step setup (SETUP.md)
- **User Manual:** How to use all features
- **FAQ:** Common questions and issues
- **Troubleshooting:** Error messages and solutions
- **Video Tutorials:** Screen recordings for key workflows

### Developer Documentation
- **Architecture Guide:** System design and patterns
- **API Documentation:** All public classes and methods
- **Contributing Guide:** How to contribute code
- **Code Style Guide:** Python conventions used
- **Testing Guide:** How to write and run tests

### Code Documentation
- **Docstrings:** All public methods and classes
- **Type Hints:** Full type coverage
- **Inline Comments:** Complex logic explained
- **README Files:** In each major directory

---

## Deployment & Distribution

### macOS App Bundle
- **Format:** .app bundle
- **Installer:** DMG with drag-to-Applications
- **Signing:** Apple Developer ID signed (future)
- **Notarization:** Apple notarized (future)

### Distribution Channels
- **GitHub Releases:** Primary distribution
- **Homebrew Cask:** `brew install --cask file-organizer`
- **Direct Download:** From project website (future)

### Auto-Update (Future)
- Check for updates on launch
- Download and install updates
- Changelog display
- Opt-in/out of updates

---

## Success Metrics

### Adoption Metrics
- GitHub stars: Target 1000+ in 6 months
- Downloads: Target 5000+ in first year
- Active users: Target 1000+ monthly

### Quality Metrics
- User satisfaction: 4.5/5 stars average
- Crash rate: <1% of sessions
- Data loss incidents: 0
- Critical bugs: <5 open at any time

### Performance Metrics
- 85%+ suggestion acceptance rate
- 100 files organized in <2 minutes
- UI responsive (<100ms) 99.9% of time
- Memory usage <2GB with 3B model

### Engagement Metrics
- Average files organized per user: 500+
- Feature usage: 80%+ use at least 3 major features
- Retention: 70%+ return after first use
- Undo usage: <10% of operations (high confidence in AI)

---

## Future Roadmap (Beyond Phase 4)

### Phase 5: Advanced AI Features
- **Multi-language support** for file content analysis
- **Semantic search** using embeddings
- **Duplicate detection** using content similarity
- **Smart tagging** with auto-generated tags
- **File relationships** detection (related documents)

### Phase 6: Collaboration Features
- **Shared organization templates**
- **Team workspaces** (networked directories)
- **Organization rule sharing** (community rules)
- **Cloud sync** for multi-device use

### Phase 7: Enterprise Features
- **Admin controls** and policies
- **Audit logging** for compliance
- **Active Directory integration**
- **Network drive support**
- **Batch deployment** tools

### Phase 8: Cross-Platform
- **Windows version**
- **Linux version**
- **Web version** (optional)

---

## Glossary

**Terms:**
- **LLM:** Large Language Model
- **Ollama:** Local LLM inference engine
- **Dry-Run:** Preview mode without actual file operations
- **Confidence:** AI's certainty in its suggestion (0.0-1.0)
- **Batch:** Group of files processed together
- **Organization Plan:** Set of proposed file operations
- **Undo Operation:** Reversal of file operations

**Abbreviations:**
- **FR:** Functional Requirement
- **NFR:** Non-Functional Requirement
- **PR:** Privacy Requirement
- **SR:** Security Requirement
- **DP:** Data Protection
- **UI:** User Interface
- **API:** Application Programming Interface

---

## Appendix

### A. Example Use Cases

**Use Case 1: Photographer Organizing Photos**
- User: Professional photographer with 5000+ unsorted photos
- Goal: Organize by event, date, and location
- Workflow:
  1. Select photo directory
  2. AI analyzes EXIF data and visual content
  3. Creates categories: Events/Wedding/2024-01-15, Travel/Paris/2024-03
  4. User reviews, accepts high-confidence suggestions
  5. Files organized in seconds

**Use Case 2: Student Organizing Research Papers**
- User: Graduate student with 200+ PDFs
- Goal: Organize by topic and author
- Workflow:
  1. Select downloads folder
  2. AI reads paper abstracts and titles
  3. Creates categories: Research/ML/Transformers, Research/CV/Detection
  4. Renames files: Smith_2023_Attention_Mechanisms.pdf
  5. Student reviews and accepts

**Use Case 3: Professional Cleaning Desktop**
- User: Knowledge worker with cluttered desktop
- Goal: Clear desktop, organize documents
- Workflow:
  1. Select desktop folder
  2. AI categorizes: Work/Reports, Personal/Receipts, Downloads/Software
  3. Suggests moving to organized folders
  4. User accepts all high-confidence
  5. Desktop clear in 30 seconds

### B. Competitive Analysis

**Existing Solutions:**
1. **Manual Organization:** Time-consuming, inconsistent
2. **Hazel (macOS):** Rule-based, requires manual rule creation
3. **Default Folders X:** Not AI-powered, limited intelligence
4. **Cloud Services:** Privacy concerns, requires internet

**Our Advantages:**
- AI-powered (truly intelligent)
- Privacy-first (local processing)
- Easy to use (no rule writing)
- Fast (optimized for M4)
- Free and open source

### C. Risk Assessment

**Risks and Mitigations:**

1. **Risk:** AI makes incorrect suggestions
   - **Mitigation:** Dry-run mode, confidence scoring, user review

2. **Risk:** Data loss during file operations
   - **Mitigation:** Backups, undo system, extensive testing

3. **Risk:** Poor LLM performance on M4
   - **Mitigation:** Optimized models (3B), Metal acceleration, testing

4. **Risk:** Users don't trust AI suggestions
   - **Mitigation:** Transparency (show reasoning), high accuracy target

5. **Risk:** Too slow for large directories
   - **Mitigation:** Batch optimization, caching, parallel processing

---

**Document Version:** 1.0  
**Last Updated:** January 30, 2026  
**Next Review:** After Phase 2 completion
