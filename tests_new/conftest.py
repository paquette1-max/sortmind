"""
Shared fixtures and configuration for all tests.
Follows the patterns from python_testing skill.
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set headless mode for UI tests
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = []
    for i in range(5):
        file_path = temp_dir / f"file_{i}.txt"
        file_path.write_text(f"Content {i}")
        files.append(file_path)
    return files


@pytest.fixture
def sample_files_with_types(temp_dir):
    """Create sample files of various types for testing."""
    files = {}
    
    # Text files
    files['txt'] = temp_dir / "document.txt"
    files['txt'].write_text("This is a text document")
    
    # Python file
    files['py'] = temp_dir / "script.py"
    files['py'].write_text("print('hello world')")
    
    # Markdown file
    files['md'] = temp_dir / "readme.md"
    files['md'].write_text("# README\n\nThis is a readme file.")
    
    # JSON file
    files['json'] = temp_dir / "data.json"
    files['json'].write_text('{"key": "value"}')
    
    # CSV file
    files['csv'] = temp_dir / "data.csv"
    files['csv'].write_text("name,age\nJohn,30\nJane,25")
    
    return files


@pytest.fixture
def empty_directory(temp_dir):
    """Create an empty subdirectory."""
    empty_dir = temp_dir / "empty_folder"
    empty_dir.mkdir()
    return empty_dir


@pytest.fixture
def deeply_nested_directory(temp_dir):
    """Create a deeply nested directory structure."""
    current = temp_dir
    for i in range(10):
        current = current / f"level_{i}"
        current.mkdir()
    
    # Add a file at the deepest level
    deep_file = current / "deep_file.txt"
    deep_file.write_text("Deep content")
    
    return temp_dir


@pytest.fixture
def directory_with_special_chars(temp_dir):
    """Create files with special characters in names."""
    special_names = [
        "file with spaces.txt",
        "file-with-dashes.txt",
        "file_with_underscores.txt",
        "file.multiple.dots.txt",
        "file@symbol.txt",
        "file#hash.txt",
        "file$money.txt",
        "file%percent.txt",
        "file&ampersand.txt",
        "file(parentheses).txt",
        "file[brackets].txt",
        "file{braces}.txt",
        "file'quotes'.txt",
        'file"doublequotes".txt',
        "file+plus.txt",
        "file=equals.txt",
        "file!exclamation.txt",
    ]
    
    files = []
    for name in special_names:
        file_path = temp_dir / name
        file_path.write_text(f"Content of {name}")
        files.append(file_path)
    
    return files


@pytest.fixture
def large_directory(temp_dir):
    """Create a directory with many files."""
    files = []
    for i in range(1000):
        file_path = temp_dir / f"file_{i:04d}.txt"
        file_path.write_text(f"Content {i}")
        files.append(file_path)
    return files


@pytest.fixture
def mock_llm_handler():
    """Create a mock LLM handler."""
    handler = Mock()
    handler.analyze_file.return_value = {
        "file_path": "test.txt",
        "category": "documents",
        "suggested_name": "renamed.txt",
        "confidence": 0.95,
        "reasoning": "Test reasoning",
        "should_organize": True
    }
    handler.is_available.return_value = True
    return handler


@pytest.fixture
def mock_undo_manager():
    """Create a mock undo manager."""
    manager = Mock()
    manager.record_operation.return_value = None
    manager.undo_last.return_value = Mock(
        success=True,
        operations_undone=1,
        errors=[]
    )
    return manager


@pytest.fixture
def mock_backup_manager():
    """Create a mock backup manager."""
    manager = Mock()
    manager.create_backup.return_value = Path("/fake/backup/path")
    manager.verify_backup.return_value = True
    return manager


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for UI tests (session-scoped)."""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(["test"])
    
    yield app


@pytest.fixture
def qtbot(qapp):
    """Create qtbot-like fixture for UI testing."""
    from PyQt6.QtTest import QTest
    
    class QtBot:
        def __init__(self, app):
            self.app = app
            self.widgets = []
        
        def addWidget(self, widget):
            """Add widget for cleanup."""
            self.widgets.append(widget)
            widget.show()
            self.app.processEvents()
        
        def mouseClick(self, widget, button, pos=None):
            """Simulate mouse click."""
            QTest.mouseClick(widget, button, pos=pos)
            self.app.processEvents()
        
        def keyClick(self, widget, key, modifier=None):
            """Simulate key click."""
            if modifier:
                QTest.keyClick(widget, key, modifier)
            else:
                QTest.keyClick(widget, key)
            self.app.processEvents()
        
        def keyClicks(self, widget, text):
            """Simulate typing text."""
            QTest.keyClicks(widget, text)
            self.app.processEvents()
        
        def cleanup(self):
            """Clean up all widgets."""
            for widget in self.widgets:
                widget.close()
                widget.deleteLater()
            self.widgets.clear()
            self.app.processEvents()
    
    bot = QtBot(qapp)
    yield bot
    bot.cleanup()


# Markers for test categorization
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "ui: UI tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "edge_case: Edge case tests")
    config.addinivalue_line("markers", "slow: Slow tests")
