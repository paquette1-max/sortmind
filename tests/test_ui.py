"""
Tests for Phase 3 UI components.
"""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QSignalSpy

# Import components to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ui.main_window import MainWindow
from ui.widgets.results_table import ResultsTable
from ui.widgets.progress_dialog import ProgressDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.workers import ScanWorker, AnalysisWorker, OrganizeWorker, BackupWorker
from ui.app_controller import AppController


class TestMainWindow(unittest.TestCase):
    """Test MainWindow component."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        self.window = MainWindow()
    
    def tearDown(self):
        """Clean up after tests."""
        self.window.close()
    
    def test_window_creation(self):
        """Test main window is created correctly."""
        self.assertIsNotNone(self.window)
        self.assertEqual(self.window.windowTitle(), "AI File Organizer")
    
    def test_window_signals_exist(self):
        """Test that all expected signals exist."""
        self.assertTrue(hasattr(self.window, 'directory_selected'))
        self.assertTrue(hasattr(self.window, 'analyze_requested'))
        self.assertTrue(hasattr(self.window, 'organize_requested'))
        self.assertTrue(hasattr(self.window, 'undo_requested'))
        self.assertTrue(hasattr(self.window, 'settings_requested'))
    
    def test_set_status(self):
        """Test set_status method."""
        self.window.set_status("Test status")
        self.assertIn("Test status", self.window.statusBar().currentMessage())
    
    def test_set_file_count(self):
        """Test set_file_count method."""
        self.window.set_file_count(42)
        status = self.window.statusBar().currentMessage()
        self.assertIn("42", status)
    
    def test_enable_disable_buttons(self):
        """Test button enable/disable."""
        self.window.enable_analyze(False)
        self.window.enable_organize(False)
        # Cannot directly test button state without accessing private widgets
        # but this tests that methods don't raise exceptions
    
    def test_show_dialogs(self):
        """Test dialog methods."""
        # Test error dialog (doesn't actually show)
        self.window.show_error("Test Error", "Test message")
        
        # Test info dialog
        self.window.show_info("Test Info", "Test message")
        
        # Test warning dialog
        self.window.show_warning("Test Warning", "Test message")


class TestResultsTable(unittest.TestCase):
    """Test ResultsTable widget."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        self.table = ResultsTable()
    
    def tearDown(self):
        """Clean up after tests."""
        self.table.close()
    
    def test_table_creation(self):
        """Test results table is created."""
        self.assertIsNotNone(self.table)
        self.assertGreater(self.table.columnCount(), 0)
    
    def test_add_result(self):
        """Test adding results to table."""
        result = {
            'original_path': 'test.txt',
            'new_name': 'test.txt',
            'category': 'Documents',
            'confidence': 0.95,
            'reasoning': 'Test'
        }
        
        initial_rows = self.table.rowCount()
        self.table.add_result(result)
        self.assertEqual(self.table.rowCount(), initial_rows + 1)
    
    def test_clear_results(self):
        """Test clearing results."""
        # Add some results
        for i in range(5):
            result = {
                'original_path': f'file{i}.txt',
                'new_name': f'file{i}.txt',
                'category': 'Documents',
                'confidence': 0.9,
                'reasoning': 'Test'
            }
            self.table.add_result(result)
        
        self.assertGreater(self.table.rowCount(), 0)
        self.table.clear_results()
        self.assertEqual(self.table.rowCount(), 0)
    
    def test_color_coding(self):
        """Test confidence color coding."""
        results = [
            {'original_path': 'high.txt', 'new_name': 'high.txt', 'category': 'Docs', 'confidence': 0.95, 'reasoning': ''},
            {'original_path': 'med.txt', 'new_name': 'med.txt', 'category': 'Docs', 'confidence': 0.75, 'reasoning': ''},
            {'original_path': 'low.txt', 'new_name': 'low.txt', 'category': 'Docs', 'confidence': 0.60, 'reasoning': ''},
        ]
        
        for result in results:
            self.table.add_result(result)
        
        # Verify rows were added
        self.assertEqual(self.table.rowCount(), 3)


class TestProgressDialog(unittest.TestCase):
    """Test ProgressDialog component."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        self.dialog = ProgressDialog("Test Progress")
    
    def tearDown(self):
        """Clean up after tests."""
        self.dialog.close()
    
    def test_dialog_creation(self):
        """Test progress dialog is created."""
        self.assertIsNotNone(self.dialog)
    
    def test_update_progress(self):
        """Test updating progress."""
        self.dialog.update_progress(5, 10, "Processing item 5")
        # Dialog should be updated without errors
        self.assertIsNotNone(self.dialog)
    
    def test_set_title(self):
        """Test setting dialog title."""
        self.dialog.set_title("New Title")
        self.assertIn("New Title", self.dialog.windowTitle())
    
    def test_cancel_signal(self):
        """Test cancel signal exists."""
        self.assertTrue(hasattr(self.dialog, 'cancel_requested'))


class TestSettingsDialog(unittest.TestCase):
    """Test SettingsDialog component."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        self.dialog = SettingsDialog()
    
    def tearDown(self):
        """Clean up after tests."""
        self.dialog.close()
    
    def test_dialog_creation(self):
        """Test settings dialog is created."""
        self.assertIsNotNone(self.dialog)
    
    def test_get_settings(self):
        """Test retrieving settings."""
        settings = self.dialog.get_settings()
        self.assertIsInstance(settings, dict)
        # Should have settings for different tabs
        self.assertIn('theme', settings)
        self.assertIn('provider', settings)


class TestScanWorker(unittest.TestCase):
    """Test ScanWorker thread."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def test_worker_creation(self):
        """Test worker is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            worker = ScanWorker(Path(tmpdir))
            self.assertIsNotNone(worker)
            self.assertTrue(hasattr(worker, 'progress'))
            self.assertTrue(hasattr(worker, 'finished'))
    
    def test_worker_signals(self):
        """Test worker has required signals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            worker = ScanWorker(Path(tmpdir))
            # Signals exist and don't raise exceptions
            self.assertTrue(hasattr(worker, 'progress'))
            self.assertTrue(hasattr(worker, 'finished'))
            self.assertTrue(hasattr(worker, 'error'))


class TestAnalysisWorker(unittest.TestCase):
    """Test AnalysisWorker thread."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def test_worker_creation(self):
        """Test worker is created."""
        files = []
        handler = Mock()
        worker = AnalysisWorker(files, handler)
        self.assertIsNotNone(worker)
    
    def test_worker_signals(self):
        """Test worker has required signals."""
        files = []
        handler = Mock()
        worker = AnalysisWorker(files, handler)
        # Signals exist
        self.assertTrue(hasattr(worker, 'progress'))
        self.assertTrue(hasattr(worker, 'finished'))
        self.assertTrue(hasattr(worker, 'error'))
        self.assertTrue(hasattr(worker, 'result'))


class TestOrganizeWorker(unittest.TestCase):
    """Test OrganizeWorker thread."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def test_worker_creation(self):
        """Test worker is created."""
        plan = {'operations': []}
        organizer = Mock()
        worker = OrganizeWorker(plan, organizer)
        self.assertIsNotNone(worker)
    
    def test_worker_signals(self):
        """Test worker has required signals."""
        plan = {'operations': []}
        organizer = Mock()
        worker = OrganizeWorker(plan, organizer)
        # Signals exist
        self.assertTrue(hasattr(worker, 'progress'))
        self.assertTrue(hasattr(worker, 'finished'))
        self.assertTrue(hasattr(worker, 'error'))


class TestBackupWorker(unittest.TestCase):
    """Test BackupWorker thread."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def test_worker_creation(self):
        """Test worker is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = Mock()
            worker = BackupWorker(Path(tmpdir), manager)
            self.assertIsNotNone(worker)
    
    def test_worker_signals(self):
        """Test worker has required signals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = Mock()
            worker = BackupWorker(Path(tmpdir), manager)
            # Signals exist
            self.assertTrue(hasattr(worker, 'progress'))
            self.assertTrue(hasattr(worker, 'finished'))
            self.assertTrue(hasattr(worker, 'error'))


class TestAppController(unittest.TestCase):
    """Test AppController."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def test_controller_creation(self):
        """Test controller is created."""
        controller = AppController()
        self.assertIsNotNone(controller)
        self.assertIsNotNone(controller.main_window)
        self.assertIsNotNone(controller.results_table)
    
    def test_controller_initialization(self):
        """Test controller state initialization."""
        controller = AppController()
        self.assertEqual(controller.scanned_files, [])
        self.assertEqual(controller.analysis_results, [])
        self.assertIsNone(controller.current_plan)
        self.assertIsNone(controller.current_directory)
    
    def test_directory_selection(self):
        """Test directory selection handler."""
        controller = AppController()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Note: This will try to scan but may not complete
            # Just verify it doesn't crash
            controller.on_directory_selected(Path(tmpdir))
            self.assertEqual(controller.current_directory, Path(tmpdir))


if __name__ == '__main__':
    unittest.main()
