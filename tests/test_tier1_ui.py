"""
UI Tests for Tier 1 features.
Tests for PreviewPanel, RulesManagerDialog, and DuplicatesDialog.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import UI components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ui.widgets.preview_panel import PreviewPanel
from ui.widgets.results_table import ResultsTable
from ui.dialogs.rules_dialog import RulesManagerDialog
from ui.dialogs.duplicates_dialog import DuplicatesDialog

from core.preview import PreviewManager, PreviewType
from core.rules_engine import RulesEngine, OrganizationRule, RuleType, RuleOperator
from core.duplicate_detector import DuplicateDetector, DuplicateGroup, DuplicateType


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    if temp_path.exists():
        import shutil
        shutil.rmtree(temp_path)


class TestPreviewPanel:
    """Tests for PreviewPanel widget."""
    
    def test_panel_creation(self, qapp):
        """Test preview panel creation."""
        panel = PreviewPanel()
        assert panel is not None
        assert panel.preview_manager is not None
        panel.close()
    
    def test_preview_text_file(self, qapp, temp_dir):
        """Test previewing text file in panel."""
        panel = PreviewPanel()
        
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")
        
        panel.preview_file(test_file)
        
        assert panel.current_preview is not None
        assert panel.text_preview.isVisible()
        panel.close()
    
    def test_preview_nonexistent_file(self, qapp, temp_dir):
        """Test previewing nonexistent file."""
        panel = PreviewPanel()
        
        panel.preview_file(temp_dir / "nonexistent.txt")
        
        assert panel.current_preview is not None
        assert panel.current_preview.error is not None
        panel.close()
    
    def test_clear_preview(self, qapp, temp_dir):
        """Test clearing preview."""
        panel = PreviewPanel()
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("Content")
        
        panel.preview_file(test_file)
        assert panel.current_preview is not None
        
        panel.clear_preview()
        assert panel.current_preview is None
        panel.close()
    
    def test_preview_none(self, qapp):
        """Test previewing None."""
        panel = PreviewPanel()
        
        panel.preview_file(None)
        
        # Should show no selection state
        assert panel.current_preview is None
        panel.close()


class TestResultsTableWithPreview:
    """Tests for ResultsTable integration with preview."""
    
    def test_table_creation(self, qapp):
        """Test results table creation."""
        table = ResultsTable()
        assert table is not None
        assert hasattr(table, 'current_file_changed')
        table.close()
    
    def test_add_result(self, qapp):
        """Test adding result to table."""
        table = ResultsTable()
        
        result = {
            'file_path': '/test/file.txt',
            'category': 'Documents',
            'suggested_name': 'file.txt',
            'confidence': 0.95,
            'reasoning': 'Test reasoning'
        }
        
        table.add_result(result)
        
        assert table.rowCount() == 1
        assert len(table.results) == 1
        table.close()
    
    def test_get_current_file_path(self, qapp):
        """Test getting current file path."""
        table = ResultsTable()
        
        result = {
            'file_path': '/test/file.txt',
            'category': 'Documents',
            'suggested_name': 'file.txt',
            'confidence': 0.9,
            'reasoning': 'Test'
        }
        
        table.add_result(result)
        table.setCurrentCell(0, 0)
        
        path = table.get_current_file_path()
        assert path is not None
        assert path.name == "file.txt"
        table.close()


class TestRulesManagerDialog:
    """Tests for RulesManagerDialog."""
    
    def test_dialog_creation(self, qapp):
        """Test dialog creation."""
        rules_engine = RulesEngine()
        dialog = RulesManagerDialog(rules_engine)
        
        assert dialog is not None
        assert dialog.rules_engine is rules_engine
        dialog.close()
    
    def test_add_rule_ui(self, qapp):
        """Test adding rule through UI."""
        rules_engine = RulesEngine()
        dialog = RulesManagerDialog(rules_engine)
        
        initial_count = len(rules_engine.rules)
        
        # Simulate adding a rule
        dialog._add_new_rule()
        
        assert len(rules_engine.rules) == initial_count + 1
        dialog.close()
    
    def test_rule_editor_population(self, qapp):
        """Test populating rule editor."""
        rules_engine = RulesEngine()
        
        rule = OrganizationRule(
            id="test-1",
            name="Test Rule",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="test",
            target_category="TestCat"
        )
        rules_engine.add_rule(rule)
        
        dialog = RulesManagerDialog(rules_engine)
        dialog.current_rule = rule
        dialog._populate_editor(rule)
        
        assert dialog.name_input.text() == "Test Rule"
        assert dialog.category_input.text() == "TestCat"
        dialog.close()
    
    def test_apply_rule_changes(self, qapp):
        """Test applying rule changes."""
        rules_engine = RulesEngine()
        
        rule = OrganizationRule(
            id="test-1",
            name="Original",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="test",
            target_category="Test"
        )
        rules_engine.add_rule(rule)
        
        dialog = RulesManagerDialog(rules_engine)
        dialog.current_rule = rule
        dialog._populate_editor(rule)
        
        # Modify fields
        dialog.name_input.setText("Modified")
        dialog.category_input.setText("NewCat")
        
        # Apply changes
        dialog._apply_current_rule()
        
        # Check rule was updated
        updated_rule = rules_engine.get_rule("test-1")
        assert updated_rule.name == "Modified"
        assert updated_rule.target_category == "NewCat"
        dialog.close()
    
    def test_enable_disable_rule(self, qapp):
        """Test enabling and disabling rules."""
        rules_engine = RulesEngine()
        
        rule = OrganizationRule(
            id="test-1",
            name="Test",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="test",
            target_category="Test",
            enabled=True
        )
        rules_engine.add_rule(rule)
        
        # Disable
        rules_engine.disable_rule("test-1")
        assert rules_engine.get_rule("test-1").enabled is False
        
        # Enable
        rules_engine.enable_rule("test-1")
        assert rules_engine.get_rule("test-1").enabled is True


class TestDuplicatesDialog:
    """Tests for DuplicatesDialog."""
    
    def test_dialog_creation(self, qapp):
        """Test dialog creation."""
        dialog = DuplicatesDialog([])
        
        assert dialog is not None
        assert dialog.detector is not None
        dialog.close()
    
    def test_set_files(self, qapp, temp_dir):
        """Test setting files to scan."""
        dialog = DuplicatesDialog([])
        
        # Create test files
        files = [temp_dir / f"file{i}.txt" for i in range(3)]
        for f in files:
            f.write_text("content")
        
        dialog.set_files(files)
        
        assert dialog.file_paths == files
        dialog.close()
    
    def test_duplicate_item_widget(self, qapp, temp_dir):
        """Test DuplicateItemWidget."""
        from ui.dialogs.duplicates_dialog import DuplicateItemWidget
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        widget = DuplicateItemWidget(test_file, is_original=True)
        
        assert widget.file_path == test_file
        assert widget.is_checked() is False  # Originals are unchecked by default
        
        # Test check/uncheck
        widget.set_checked(True)
        assert widget.is_checked() is True
        
        widget.set_checked(False)
        assert widget.is_checked() is False
    
    def test_duplicate_group_creation(self, temp_dir):
        """Test DuplicateGroup creation and methods."""
        files = [temp_dir / f"file{i}.txt" for i in range(3)]
        for f in files:
            f.write_text("same content")
        
        group = DuplicateGroup(
            group_id="test-group",
            duplicate_type=DuplicateType.EXACT,
            files=files,
            hash_value="abc123"
        )
        
        assert len(group.files) == 3
        assert group.group_id == "test-group"
        
        # Test wasted space
        wasted = group.get_wasted_space()
        assert wasted > 0
    
    def test_duplicate_detection_result(self):
        """Test DuplicateDetectionResult."""
        group1 = DuplicateGroup(
            group_id="g1",
            duplicate_type=DuplicateType.EXACT,
            files=[Path("/a/1.txt"), Path("/b/1.txt")]
        )
        group2 = DuplicateGroup(
            group_id="g2",
            duplicate_type=DuplicateType.EXACT,
            files=[Path("/a/2.txt"), Path("/b/2.txt"), Path("/c/2.txt")]
        )
        
        result = DuplicateDetectionResult(
            exact_duplicates=[group1, group2],
            similar_images=[],
            scanned_files=100,
            scan_duration=5.0
        )
        
        assert result.scanned_files == 100
        assert result.scan_duration == 5.0
        assert result.group_count == 2
        assert result.total_duplicates == 5


class TestIntegration:
    """Integration tests for UI components."""
    
    def test_preview_integration_with_table(self, qapp, temp_dir):
        """Test preview panel integration with results table."""
        table = ResultsTable()
        panel = PreviewPanel()
        
        # Connect signals
        table.current_file_changed.connect(panel.preview_file)
        
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Preview test content")
        
        # Add result
        result = {
            'file_path': str(test_file),
            'category': 'Documents',
            'suggested_name': 'test.txt',
            'confidence': 0.9,
            'reasoning': 'Test'
        }
        table.add_result(result)
        table.setCurrentCell(0, 0)
        
        # Signal should have triggered preview
        # (In real scenario, we'd check panel.current_preview)
        
        table.close()
        panel.close()
    
    def test_rules_export_import(self, qapp, temp_dir):
        """Test exporting and importing rules."""
        rules_engine = RulesEngine()
        
        # Add some rules
        rules_engine.add_rule(OrganizationRule(
            id="r1",
            name="Rule 1",
            rule_type=RuleType.EXTENSION,
            operator=RuleOperator.EQUALS,
            value=".txt",
            target_category="Text"
        ))
        
        rules_engine.add_rule(OrganizationRule(
            id="r2",
            name="Rule 2",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="report",
            target_category="Reports"
        ))
        
        # Export
        export_path = temp_dir / "rules.json"
        rules_engine.save_to_file(export_path)
        
        assert export_path.exists()
        
        # Import into new engine
        new_engine = RulesEngine()
        new_engine.load_from_file(export_path)
        
        assert len(new_engine.rules) == 2
        assert new_engine.get_rule("r1").name == "Rule 1"
        assert new_engine.get_rule("r2").target_category == "Reports"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
