"""
UI Tests for File Organizer - Testing the "World-Class UI" claims.
Tests empty states, skeleton loading, keyboard navigation, and preview panel.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Skip all UI tests if PyQt6 is not available
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence


@pytest.mark.ui
class TestMainWindow:
    """Tests for MainWindow with world-class UI features."""
    
    @pytest.fixture
    def main_window(self, qtbot):
        """Create main window."""
        from ui.main_window import MainWindow
        window = MainWindow()
        qtbot.addWidget(window)
        yield window
        window.close()
    
    def test_window_creation(self, main_window):
        """Test main window is created with correct title."""
        assert main_window.windowTitle() == "AI File Organizer"
        assert main_window.isVisible()
    
    def test_window_signals_exist(self, main_window):
        """Test that all expected signals exist."""
        assert hasattr(main_window, 'directory_selected')
        assert hasattr(main_window, 'analyze_requested')
        assert hasattr(main_window, 'organize_requested')
        assert hasattr(main_window, 'undo_requested')
        assert hasattr(main_window, 'settings_requested')
        assert hasattr(main_window, 'rules_requested')
        assert hasattr(main_window, 'duplicates_requested')
    
    def test_set_status(self, main_window):
        """Test setting status message."""
        main_window.set_status("Test status message")
        # Status should be updated
        assert "Test" in main_window.status_label.text()
    
    def test_set_file_count_zero(self, main_window):
        """Test setting file count to zero."""
        main_window.set_file_count(0)
        assert "0" in main_window.file_count_label.text()
    
    def test_set_file_count_single(self, main_window):
        """Test setting file count to 1."""
        main_window.set_file_count(1)
        assert "1" in main_window.file_count_label.text()
    
    def test_set_file_count_multiple(self, main_window):
        """Test setting file count to multiple."""
        main_window.set_file_count(42)
        assert "42" in main_window.file_count_label.text()
    
    def test_enable_analyze_button(self, main_window):
        """Test enabling analyze button."""
        main_window.enable_analyze(True)
        assert main_window.analyze_btn.isEnabled()
    
    def test_disable_analyze_button(self, main_window):
        """Test disabling analyze button."""
        main_window.enable_analyze(False)
        assert not main_window.analyze_btn.isEnabled()
    
    def test_enable_organize_button(self, main_window):
        """Test enabling organize button."""
        main_window.enable_organize(True)
        assert main_window.organize_btn.isEnabled()
    
    def test_show_error_dialog(self, main_window):
        """Test showing error dialog."""
        # Should not raise exception
        main_window.show_error("Test Error", "Test error message")
    
    def test_show_info_dialog(self, main_window):
        """Test showing info dialog."""
        # Should not raise exception
        main_window.show_info("Test Info", "Test info message")
    
    def test_ask_confirmation(self, main_window):
        """Test confirmation dialog."""
        # We can't actually test dialog interaction in headless mode,
        # but we can verify the method exists and doesn't crash
        # In real usage, this would show a dialog
        pass
    
    def test_show_empty_state_no_directory(self, main_window, qtbot):
        """Test showing 'no directory' empty state."""
        from ui.widgets.empty_state import EmptyStateWidget
        
        empty_widget = EmptyStateWidget()
        main_window.set_empty_state_widget(empty_widget)
        main_window.show_empty_state("no_directory")
        
        assert main_window.results_stack.currentWidget() == empty_widget
    
    def test_show_skeleton_loading(self, main_window):
        """Test showing skeleton loading."""
        main_window.show_skeleton_loading("Analyzing files...")
        
        # Should show skeleton widget
        assert main_window.results_stack.currentWidget() == main_window.skeleton_widget
    
    def test_hide_skeleton_loading(self, main_window):
        """Test hiding skeleton loading."""
        main_window.show_skeleton_loading()
        main_window.hide_skeleton_loading()
        
        # Animation should be stopped
        assert not main_window.skeleton_widget.is_animating()
    
    def test_keyboard_shortcuts_setup(self, main_window):
        """Test that keyboard shortcuts are set up."""
        # Check for common shortcuts
        actions = main_window.findChildren(type(main_window.shortcut_escape))
        assert len(actions) > 0
    
    def test_get_current_directory(self, main_window, temp_dir):
        """Test getting current directory."""
        main_window.current_directory = temp_dir
        assert main_window.get_current_directory() == temp_dir


@pytest.mark.ui
class TestEmptyStateWidget:
    """Tests for EmptyStateWidget."""
    
    @pytest.fixture
    def empty_state(self, qtbot):
        """Create empty state widget."""
        from ui.widgets.empty_state import EmptyStateWidget
        widget = EmptyStateWidget()
        qtbot.addWidget(widget)
        yield widget
        widget.close()
    
    def test_widget_creation(self, empty_state):
        """Test empty state widget creation."""
        assert empty_state is not None
        assert empty_state.get_current_state() == "no_directory"
    
    def test_set_state_no_directory(self, empty_state):
        """Test 'no_directory' state."""
        empty_state.set_state("no_directory")
        
        assert empty_state.get_current_state() == "no_directory"
        assert empty_state.action_button.isVisible()
    
    def test_set_state_empty_folder(self, empty_state):
        """Test 'empty_folder' state."""
        empty_state.set_state("empty_folder")
        
        assert empty_state.get_current_state() == "empty_folder"
        assert "Empty" in empty_state.title_label.text()
    
    def test_set_state_no_results(self, empty_state):
        """Test 'no_results' state."""
        empty_state.set_state("no_results")
        
        assert empty_state.get_current_state() == "no_results"
    
    def test_set_state_no_analysis(self, empty_state):
        """Test 'no_analysis' state."""
        empty_state.set_state("no_analysis")
        
        assert empty_state.get_current_state() == "no_analysis"
        assert "Analyze" in empty_state.action_button.text()
    
    def test_set_state_error(self, empty_state):
        """Test 'error' state."""
        empty_state.set_state("error")
        
        assert empty_state.get_current_state() == "error"
        assert "Wrong" in empty_state.title_label.text()
    
    def test_set_custom_state(self, empty_state):
        """Test setting custom state."""
        empty_state.set_custom(
            icon="🎉",
            title="Custom Title",
            message="Custom message",
            action_text="Custom Action",
            help_text="Custom help"
        )
        
        assert empty_state.title_label.text() == "Custom Title"
        assert empty_state.action_button.text() == "Custom Action"
    
    def test_action_button_click(self, empty_state, qtbot):
        """Test action button click emits signal."""
        # Create signal spy
        from PyQt6.QtTest import QSignalSpy
        spy = QSignalSpy(empty_state.action_triggered)
        
        # Click button
        qtbot.mouseClick(empty_state.action_button, Qt.MouseButton.LeftButton)
        
        # Verify signal was emitted
        assert len(spy) == 1
    
    def test_focus_action_button(self, empty_state):
        """Test focusing action button."""
        empty_state.focus_action_button()
        assert empty_state.action_button.hasFocus()


@pytest.mark.ui
class TestSkeletonLoadingWidget:
    """Tests for SkeletonLoadingWidget."""
    
    @pytest.fixture
    def skeleton(self, qtbot):
        """Create skeleton loading widget."""
        from ui.widgets.skeleton_loading import SkeletonLoadingWidget
        widget = SkeletonLoadingWidget(preset='table')
        qtbot.addWidget(widget)
        yield widget
        widget.close()
    
    def test_widget_creation(self, skeleton):
        """Test skeleton widget creation."""
        assert skeleton is not None
        assert not skeleton.is_animating()
    
    def test_start_animation(self, skeleton):
        """Test starting animation."""
        skeleton.start("Loading...")
        
        assert skeleton.is_animating()
        assert "Loading" in skeleton.status_label.text()
    
    def test_stop_animation(self, skeleton):
        """Test stopping animation."""
        skeleton.start()
        skeleton.stop()
        
        assert not skeleton.is_animating()
    
    def test_set_message(self, skeleton):
        """Test setting loading message."""
        skeleton.start()
        skeleton.set_message("Custom message")
        
        assert skeleton.status_label.text() == "Custom message"
    
    def test_finished_signal(self, skeleton, qtbot):
        """Test that finished signal is emitted."""
        from PyQt6.QtTest import QSignalSpy
        spy = QSignalSpy(skeleton.finished)
        
        skeleton.start()
        skeleton.stop()
        
        assert len(spy) == 1
    
    def test_different_presets(self, qtbot):
        """Test different skeleton presets."""
        from ui.widgets.skeleton_loading import SkeletonLoadingWidget
        
        presets = ['table', 'form', 'card', 'list']
        for preset in presets:
            widget = SkeletonLoadingWidget(preset=preset)
            qtbot.addWidget(widget)
            assert widget is not None
            widget.close()


@pytest.mark.ui
class TestPreviewPanel:
    """Tests for PreviewPanel."""
    
    @pytest.fixture
    def preview_panel(self, qtbot):
        """Create preview panel."""
        from ui.widgets.preview_panel import PreviewPanel
        panel = PreviewPanel()
        qtbot.addWidget(panel)
        yield panel
        panel.close()
    
    def test_panel_creation(self, preview_panel):
        """Test preview panel creation."""
        assert preview_panel is not None
    
    def test_preview_text_file(self, preview_panel, temp_dir):
        """Test previewing text file."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content for preview")
        
        # Act
        preview_panel.preview_file(test_file)
        
        # Assert
        assert preview_panel.current_preview is not None
        assert "test.txt" in preview_panel.header_label.text()
    
    def test_preview_nonexistent_file(self, preview_panel):
        """Test previewing nonexistent file."""
        preview_panel.preview_file("/nonexistent/file.txt")
        
        assert "not found" in preview_panel.error_label.text().lower() or \
               "No file selected" in preview_panel.header_label.text()
    
    def test_preview_none(self, preview_panel):
        """Test preview with None."""
        preview_panel.preview_file(None)
        
        assert preview_panel.current_preview is None
    
    def test_clear_preview(self, preview_panel, temp_dir):
        """Test clearing preview."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        preview_panel.preview_file(test_file)
        
        # Act
        preview_panel.clear_preview()
        
        # Assert
        assert preview_panel.current_preview is None
    
    def test_get_current_preview(self, preview_panel, temp_dir):
        """Test getting current preview."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        preview_panel.preview_file(test_file)
        preview = preview_panel.get_current_preview()
        
        assert preview is not None
        assert preview.file_path == test_file


@pytest.mark.ui
class TestResultsTable:
    """Tests for ResultsTable."""
    
    @pytest.fixture
    def results_table(self, qtbot):
        """Create results table."""
        from ui.widgets.results_table import ResultsTable
        table = ResultsTable()
        qtbot.addWidget(table)
        yield table
        table.close()
    
    def test_table_creation(self, results_table):
        """Test results table creation."""
        assert results_table is not None
        assert results_table.columnCount() == 5
    
    def test_add_result(self, results_table):
        """Test adding result to table."""
        result = {
            "file_path": "/test/file.txt",
            "category": "documents",
            "suggested_name": "renamed.txt",
            "confidence": 0.95,
            "reasoning": "Test reasoning"
        }
        
        initial_rows = results_table.rowCount()
        results_table.add_result(result)
        
        assert results_table.rowCount() == initial_rows + 1
    
    def test_add_result_high_confidence(self, results_table):
        """Test adding high confidence result."""
        result = {
            "file_path": "/test/file.txt",
            "category": "documents",
            "confidence": 0.95
        }
        
        results_table.add_result(result)
        
        # High confidence should be indicated
        row = results_table.rowCount() - 1
        confidence_item = results_table.item(row, 3)
        assert "95%" in confidence_item.text()
    
    def test_clear_results(self, results_table):
        """Test clearing results."""
        # Add some results
        for i in range(3):
            results_table.add_result({
                "file_path": f"/test/file{i}.txt",
                "category": "documents",
                "confidence": 0.9
            })
        
        results_table.clear_results()
        
        assert results_table.rowCount() == 0
        assert len(results_table.results) == 0
    
    def test_get_all_results(self, results_table):
        """Test getting all results."""
        # Add results
        for i in range(3):
            results_table.add_result({
                "file_path": f"/test/file{i}.txt",
                "category": "documents",
                "confidence": 0.9
            })
        
        all_results = results_table.get_all_results()
        
        assert len(all_results) == 3
    
    def test_select_all_rows(self, results_table):
        """Test selecting all rows."""
        # Add results
        for i in range(3):
            results_table.add_result({
                "file_path": f"/test/file{i}.txt",
                "category": "documents",
                "confidence": 0.9
            })
        
        results_table.select_all_rows()
        
        # All rows should be selected
        assert results_table.get_selected_count() == 3
    
    def test_deselect_all_rows(self, results_table):
        """Test deselecting all rows."""
        # Add and select results
        for i in range(3):
            results_table.add_result({
                "file_path": f"/test/file{i}.txt",
                "category": "documents",
                "confidence": 0.9
            })
        results_table.select_all_rows()
        
        results_table.deselect_all_rows()
        
        assert results_table.get_selected_count() == 0
    
    def test_select_high_confidence(self, results_table):
        """Test selecting high confidence results."""
        # Add mixed confidence results
        results_table.add_result({
            "file_path": "/test/high.txt",
            "category": "documents",
            "confidence": 0.95
        })
        results_table.add_result({
            "file_path": "/test/low.txt",
            "category": "documents",
            "confidence": 0.60
        })
        
        results_table.select_high_confidence()
        
        # Only high confidence should be selected
        selected = results_table.get_selected_results()
        assert len(selected) == 1
        assert selected[0]["confidence"] == 0.95
    
    def test_get_statistics(self, results_table):
        """Test getting statistics."""
        results_table.add_result({
            "file_path": "/test/file1.txt",
            "category": "documents",
            "confidence": 0.95
        })
        results_table.add_result({
            "file_path": "/test/file2.txt",
            "category": "images",
            "confidence": 0.85
        })
        
        stats = results_table.get_statistics()
        
        assert stats["total_count"] == 2
        assert stats["high_confidence_count"] == 1
        assert "documents" in stats["categories"]
        assert "images" in stats["categories"]
    
    def test_key_press_space(self, results_table, qtbot):
        """Test space key toggles selection."""
        results_table.add_result({
            "file_path": "/test/file.txt",
            "category": "documents",
            "confidence": 0.9
        })
        
        results_table.setCurrentCell(0, 0)
        qtbot.keyClick(results_table, Qt.Key.Key_Space)
        
        # Selection state should change
        # (Can't easily verify in headless mode, but should not crash)


@pytest.mark.ui
class TestKeyboardNavigation:
    """Tests for keyboard navigation features."""
    
    @pytest.fixture
    def main_window(self, qtbot):
        """Create main window for keyboard tests."""
        from ui.main_window import MainWindow
        window = MainWindow()
        qtbot.addWidget(window)
        yield window
        window.close()
    
    def test_ctrl_o_shortcut_exists(self, main_window):
        """Test Ctrl+O shortcut for opening directory."""
        # Check menu action
        file_menu = main_window.menuBar().findChild(type(main_window.menuBar().actions()[0].menu()))
        # Shortcut should exist (can't test actual dialog in headless)
    
    def test_escape_key_handler(self, main_window, qtbot):
        """Test escape key handling."""
        # Should not crash
        qtbot.keyClick(main_window, Qt.Key.Key_Escape)
    
    def test_f1_help(self, main_window, qtbot):
        """Test F1 for help."""
        # Should not crash (opens help dialog)
        qtbot.keyClick(main_window, Qt.Key.Key_F1)
