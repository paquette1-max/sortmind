"""
Tests for Tier 1 features: Preview, Rules Engine, and Duplicate Detection.
"""
import pytest
import tempfile
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.preview import PreviewManager, FilePreview, PreviewType
from core.rules_engine import (
    RulesEngine, OrganizationRule, RuleType, RuleOperator, RuleMatch
)
from core.duplicate_detector import (
    DuplicateDetector, DuplicateGroup, DuplicateType, DuplicateDetectionResult
)


class TestPreviewManager:
    """Tests for PreviewManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            import shutil
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def preview_manager(self):
        """Create PreviewManager instance."""
        return PreviewManager(max_text_preview=500)
    
    def test_preview_text_file(self, preview_manager, temp_dir):
        """Test previewing a text file."""
        test_file = temp_dir / "test.txt"
        content = "Hello, World!\nThis is a test file.\nLine 3\nLine 4"
        test_file.write_text(content)
        
        preview = preview_manager.get_preview(test_file)
        
        assert preview.preview_type == PreviewType.TEXT
        assert "Hello, World!" in preview.preview_content
        assert preview.metadata is not None
        assert 'size' in preview.metadata
        assert 'line_count' in preview.metadata
    
    def test_preview_text_file_truncation(self, preview_manager, temp_dir):
        """Test text file preview truncation."""
        test_file = temp_dir / "long.txt"
        content = "A" * 1000
        test_file.write_text(content)
        
        preview = preview_manager.get_preview(test_file)
        
        assert preview.preview_type == PreviewType.TEXT
        assert len(preview.preview_content) <= 550  # 500 + truncation message
        assert "[truncated]" in preview.preview_content
    
    def test_preview_nonexistent_file(self, preview_manager):
        """Test previewing a nonexistent file."""
        preview = preview_manager.get_preview("/nonexistent/file.txt")
        
        assert preview.preview_type == PreviewType.UNKNOWN
        assert preview.error is not None
        assert "not found" in preview.error.lower()
    
    def test_preview_image_file(self, preview_manager, temp_dir):
        """Test previewing an image file (metadata only without PIL)."""
        test_file = temp_dir / "test.jpg"
        # Create a minimal fake image file
        test_file.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
        
        preview = preview_manager.get_preview(test_file)
        
        assert preview.preview_type == PreviewType.IMAGE
        assert preview.metadata is not None
        assert 'size' in preview.metadata
    
    def test_preview_pdf_file(self, preview_manager, temp_dir):
        """Test previewing a PDF file (metadata only without PyPDF2)."""
        test_file = temp_dir / "test.pdf"
        # Create a minimal fake PDF
        test_file.write_bytes(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n')
        
        preview = preview_manager.get_preview(test_file)
        
        assert preview.preview_type == PreviewType.PDF
    
    def test_preview_binary_file_as_unknown(self, preview_manager, temp_dir):
        """Test previewing binary file."""
        test_file = temp_dir / "binary.dat"
        test_file.write_bytes(bytes(range(256)))
        
        preview = preview_manager.get_preview(test_file)
        
        # Should be detected as unknown or text fallback
        assert preview.preview_type in (PreviewType.UNKNOWN, PreviewType.TEXT)
    
    def test_format_size(self, preview_manager):
        """Test size formatting."""
        assert preview_manager._format_size(512) == "512.0 B"
        assert preview_manager._format_size(1024) == "1.0 KB"
        assert preview_manager._format_size(1024 * 1024) == "1.0 MB"
        assert preview_manager._format_size(1024 ** 3) == "1.0 GB"


class TestRulesEngine:
    """Tests for RulesEngine class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            import shutil
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def rules_engine(self):
        """Create RulesEngine instance."""
        return RulesEngine()
    
    def test_add_rule(self, rules_engine):
        """Test adding a rule."""
        rule = OrganizationRule(
            id="test-1",
            name="Test Rule",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="report",
            target_category="Reports"
        )
        
        rules_engine.add_rule(rule)
        
        assert len(rules_engine.rules) == 1
        assert rules_engine.rules[0].name == "Test Rule"
    
    def test_remove_rule(self, rules_engine):
        """Test removing a rule."""
        rule = OrganizationRule(
            id="test-1",
            name="Test Rule",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="test",
            target_category="Test"
        )
        rules_engine.add_rule(rule)
        
        result = rules_engine.remove_rule("test-1")
        
        assert result is True
        assert len(rules_engine.rules) == 0
    
    def test_remove_nonexistent_rule(self, rules_engine):
        """Test removing a nonexistent rule."""
        result = rules_engine.remove_rule("nonexistent")
        assert result is False
    
    def test_evaluate_filename_contains(self, rules_engine, temp_dir):
        """Test filename pattern rule with contains operator."""
        rule = OrganizationRule(
            id="test-1",
            name="Report Rule",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="report",
            target_category="Reports"
        )
        rules_engine.add_rule(rule)
        
        # Create test files
        report_file = temp_dir / "monthly_report.pdf"
        other_file = temp_dir / "document.txt"
        report_file.write_text("test")
        other_file.write_text("test")
        
        match = rules_engine.evaluate_file(report_file)
        
        assert match.matched is True
        assert match.target_category == "Reports"
        
        no_match = rules_engine.evaluate_file(other_file)
        assert no_match.matched is False
    
    def test_evaluate_extension_rule(self, rules_engine, temp_dir):
        """Test file extension rule."""
        rule = OrganizationRule(
            id="test-1",
            name="Image Rule",
            rule_type=RuleType.EXTENSION,
            operator=RuleOperator.EQUALS,
            value=".jpg",
            target_category="Images"
        )
        rules_engine.add_rule(rule)
        
        jpg_file = temp_dir / "photo.jpg"
        png_file = temp_dir / "photo.png"
        jpg_file.write_text("test")
        png_file.write_text("test")
        
        match = rules_engine.evaluate_file(jpg_file)
        assert match.matched is True
        
        no_match = rules_engine.evaluate_file(png_file)
        assert no_match.matched is False
    
    def test_evaluate_content_rule(self, rules_engine, temp_dir):
        """Test content keyword rule."""
        rule = OrganizationRule(
            id="test-1",
            name="Confidential Rule",
            rule_type=RuleType.CONTENT_KEYWORD,
            operator=RuleOperator.CONTAINS,
            value="CONFIDENTIAL",
            target_category="Confidential"
        )
        rules_engine.add_rule(rule)
        
        conf_file = temp_dir / "secret.txt"
        normal_file = temp_dir / "normal.txt"
        conf_file.write_text("This is CONFIDENTIAL information")
        normal_file.write_text("This is normal information")
        
        match = rules_engine.evaluate_file(conf_file)
        assert match.matched is True
        
        no_match = rules_engine.evaluate_file(normal_file)
        assert no_match.matched is False
    
    def test_evaluate_size_rule(self, rules_engine, temp_dir):
        """Test file size rule."""
        rule = OrganizationRule(
            id="test-1",
            name="Large File Rule",
            rule_type=RuleType.FILE_SIZE,
            operator=RuleOperator.GREATER_THAN,
            value="100B",
            target_category="LargeFiles"
        )
        rules_engine.add_rule(rule)
        
        large_file = temp_dir / "large.txt"
        small_file = temp_dir / "small.txt"
        large_file.write_text("A" * 200)  # 200 bytes
        small_file.write_text("sm")  # 2 bytes
        
        match = rules_engine.evaluate_file(large_file)
        assert match.matched is True
        
        no_match = rules_engine.evaluate_file(small_file)
        assert no_match.matched is False
    
    def test_evaluate_date_rule(self, rules_engine, temp_dir):
        """Test date modified rule."""
        rule = OrganizationRule(
            id="test-1",
            name="Recent Rule",
            rule_type=RuleType.DATE_MODIFIED,
            operator=RuleOperator.GREATER_THAN,
            value="1_day_ago",
            target_category="Recent"
        )
        rules_engine.add_rule(rule)
        
        recent_file = temp_dir / "recent.txt"
        recent_file.write_text("recent")
        # File is just created, so it's newer than 1 day ago
        
        match = rules_engine.evaluate_file(recent_file)
        assert match.matched is True
    
    def test_rule_priority(self, rules_engine, temp_dir):
        """Test rule priority ordering."""
        rule1 = OrganizationRule(
            id="test-1",
            name="Low Priority",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="test",
            target_category="Low",
            priority=200
        )
        rule2 = OrganizationRule(
            id="test-2",
            name="High Priority",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="test",
            target_category="High",
            priority=10
        )
        rules_engine.add_rule(rule1)
        rules_engine.add_rule(rule2)
        
        # Rules should be sorted by priority
        assert rules_engine.rules[0].priority == 10
        assert rules_engine.rules[1].priority == 200
    
    def test_rule_to_dict(self):
        """Test rule serialization."""
        rule = OrganizationRule(
            id="test-1",
            name="Test Rule",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="test",
            target_category="Test"
        )
        
        data = rule.to_dict()
        
        assert data['id'] == "test-1"
        assert data['name'] == "Test Rule"
        assert data['rule_type'] == "filename_pattern"
        assert data['operator'] == "contains"
    
    def test_rule_from_dict(self):
        """Test rule deserialization."""
        data = {
            'id': 'test-1',
            'name': 'Test Rule',
            'rule_type': 'filename_pattern',
            'operator': 'contains',
            'value': 'test',
            'target_category': 'Test',
            'priority': 50,
            'enabled': True
        }
        
        rule = OrganizationRule.from_dict(data)
        
        assert rule.id == "test-1"
        assert rule.rule_type == RuleType.FILENAME_PATTERN
        assert rule.operator == RuleOperator.CONTAINS
        assert rule.priority == 50
    
    def test_save_and_load_rules(self, rules_engine, temp_dir):
        """Test saving and loading rules to/from file."""
        rule = OrganizationRule(
            id="test-1",
            name="Test Rule",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="test",
            target_category="Test"
        )
        rules_engine.add_rule(rule)
        
        rules_file = temp_dir / "rules.json"
        rules_engine.save_to_file(rules_file)
        
        # Create new engine and load
        new_engine = RulesEngine()
        new_engine.load_from_file(rules_file)
        
        assert len(new_engine.rules) == 1
        assert new_engine.rules[0].name == "Test Rule"
    
    def test_parse_size(self, rules_engine):
        """Test size parsing."""
        assert rules_engine._parse_size("100") == 100
        assert rules_engine._parse_size("10B") == 10
        assert rules_engine._parse_size("1KB") == 1024
        assert rules_engine._parse_size("1.5MB") == int(1.5 * 1024 * 1024)
        assert rules_engine._parse_size("2GB") == 2 * 1024 ** 3
    
    def test_parse_relative_date(self, rules_engine):
        """Test relative date parsing."""
        now = datetime.now()
        
        today = rules_engine._parse_relative_date("today")
        assert today.date() == now.date()
        
        yesterday = rules_engine._parse_relative_date("yesterday")
        assert yesterday.date() == (now - timedelta(days=1)).date()
        
        week_ago = rules_engine._parse_relative_date("7_days_ago")
        # Allow for some timing variance
        days_diff = (now - week_ago).days
        assert 6 <= days_diff <= 8, f"Expected ~7 days, got {days_diff}"


class TestDuplicateDetector:
    """Tests for DuplicateDetector class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            import shutil
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def detector(self):
        """Create DuplicateDetector instance."""
        return DuplicateDetector()
    
    def test_find_exact_duplicates(self, detector, temp_dir):
        """Test finding exact duplicate files."""
        # Create duplicate files
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "unique.txt"
        
        content = "Duplicate content here"
        file1.write_text(content)
        file2.write_text(content)
        file3.write_text("Unique content")
        
        result = detector.find_duplicates([file1, file2, file3], detect_similar=False)
        
        assert len(result.exact_duplicates) == 1
        assert len(result.exact_duplicates[0].files) == 2
        assert file1 in result.exact_duplicates[0].files
        assert file2 in result.exact_duplicates[0].files
    
    def test_no_duplicates(self, detector, temp_dir):
        """Test when no duplicates exist."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        result = detector.find_duplicates([file1, file2], detect_similar=False)
        
        assert len(result.exact_duplicates) == 0
        assert result.total_duplicates == 0
    
    def test_compute_file_hash(self, detector, temp_dir):
        """Test file hash computation."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("Same content")
        file2.write_text("Same content")
        
        hash1 = detector.get_file_hash(file1)
        hash2 = detector.get_file_hash(file2)
        
        assert hash1 is not None
        assert hash1 == hash2
        assert len(hash1) == 128  # blake2b produces 128 hex chars
    
    def test_compare_files_identical(self, detector, temp_dir):
        """Test comparing identical files."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("Identical content")
        file2.write_text("Identical content")
        
        comparison = detector.compare_files(file1, file2)
        
        assert comparison['identical'] is True
        assert comparison['same_size'] is True
    
    def test_compare_files_different(self, detector, temp_dir):
        """Test comparing different files."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("Content A")
        file2.write_text("Content B")
        
        comparison = detector.compare_files(file1, file2)
        
        assert comparison['identical'] is False
    
    def test_quick_check_duplicates(self, detector, temp_dir):
        """Test quick duplicate check."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "file3.txt"
        
        file1.write_text("Duplicate")
        file2.write_text("Duplicate")
        file3.write_text("Different")
        
        duplicates = detector.quick_check_duplicates(file1, [file2, file3])
        
        assert len(duplicates) == 1
        assert file2 in duplicates
    
    def test_delete_duplicates_dry_run(self, detector, temp_dir):
        """Test duplicate deletion in dry run mode."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("Content")
        file2.write_text("Content")
        
        group = DuplicateGroup(
            group_id="test-1",
            duplicate_type=DuplicateType.EXACT,
            files=[file1, file2],
            hash_value="abc123"
        )
        
        result = detector.delete_duplicates(group, keep_indices=[0], dry_run=True)
        
        assert len(result['deleted']) == 1
        assert file2 in result['deleted']
        assert file2.exists()  # File should still exist (dry run)
        assert result['dry_run'] is True
    
    def test_duplicate_group_wasted_space(self, temp_dir):
        """Test calculating wasted space in duplicate group."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "file3.txt"
        
        content = "X" * 1000
        file1.write_text(content)
        file2.write_text(content)
        file3.write_text(content)
        
        group = DuplicateGroup(
            group_id="test-1",
            duplicate_type=DuplicateType.EXACT,
            files=[file1, file2, file3]
        )
        
        wasted = group.get_wasted_space()
        assert wasted == 2000  # 2 extra copies
    
    def test_detection_result_stats(self):
        """Test detection result statistics."""
        group1 = DuplicateGroup(
            group_id="test-1",
            duplicate_type=DuplicateType.EXACT,
            files=[Path("/a/1.txt"), Path("/b/1.txt")]
        )
        group2 = DuplicateGroup(
            group_id="test-2",
            duplicate_type=DuplicateType.SIMILAR,
            files=[Path("/a/2.jpg"), Path("/b/2.jpg"), Path("/c/2.jpg")]
        )
        
        result = DuplicateDetectionResult(
            exact_duplicates=[group1],
            similar_images=[group2],
            scanned_files=100
        )
        
        assert result.group_count == 2
        assert result.total_duplicates == 5
    
    def test_cache_functionality(self, detector, temp_dir):
        """Test hash caching."""
        file1 = temp_dir / "file1.txt"
        file1.write_text("Content")
        
        # First call computes hash
        hash1 = detector.get_file_hash(file1)
        
        # Second call should use cache
        hash2 = detector.get_file_hash(file1)
        
        assert hash1 == hash2
        assert file1 in detector._hash_cache
    
    def test_clear_cache(self, detector, temp_dir):
        """Test clearing hash cache."""
        file1 = temp_dir / "file1.txt"
        file1.write_text("Content")
        
        detector.get_file_hash(file1)
        assert len(detector._hash_cache) > 0
        
        detector.clear_cache()
        assert len(detector._hash_cache) == 0


class TestIntegration:
    """Integration tests for Tier 1 features."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            import shutil
            shutil.rmtree(temp_path)
    
    def test_rules_with_organizer(self, temp_dir):
        """Test rules engine integration with file evaluation."""
        from core.organizer import FileOrganizer
        
        # Create rules engine with rules
        rules_engine = RulesEngine()
        
        # Add a rule to categorize images
        image_rule = OrganizationRule(
            id="img-1",
            name="Image Rule",
            rule_type=RuleType.EXTENSION,
            operator=RuleOperator.EQUALS,
            value=".jpg",
            target_category="Images",
            priority=10
        )
        rules_engine.add_rule(image_rule)
        
        # Add a rule for reports
        report_rule = OrganizationRule(
            id="rpt-1",
            name="Report Rule",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="report",
            target_category="Reports",
            priority=5
        )
        rules_engine.add_rule(report_rule)
        
        # Create test files
        img_file = temp_dir / "photo.jpg"
        report_file = temp_dir / "monthly_report.pdf"
        other_file = temp_dir / "document.txt"
        
        img_file.write_text("fake image")
        report_file.write_text("report content")
        other_file.write_text("other content")
        
        # Evaluate files
        results = rules_engine.evaluate_files([img_file, report_file, other_file])
        
        assert results[img_file].matched is True
        assert results[img_file].target_category == "Images"
        
        assert results[report_file].matched is True
        assert results[report_file].target_category == "Reports"
        
        assert results[other_file].matched is False
    
    def test_preview_with_various_files(self, temp_dir):
        """Test preview manager with various file types."""
        preview_manager = PreviewManager()
        
        # Create various file types
        files = {
            'text.txt': 'Hello, World!',
            'data.json': '{"key": "value"}',
            'script.py': 'print("hello")',
            'image.jpg': b'\xff\xd8\xff\xe0' + b'\x00' * 100,
            'doc.pdf': b'%PDF-1.4 test',
            'binary.bin': bytes(range(256))
        }
        
        for filename, content in files.items():
            filepath = temp_dir / filename
            if isinstance(content, str):
                filepath.write_text(content)
            else:
                filepath.write_bytes(content)
            
            preview = preview_manager.get_preview(filepath)
            
            # All should return a valid preview (even if unknown)
            assert preview is not None
            assert preview.file_path == filepath
            assert preview.preview_type is not None
    
    def test_end_to_end_duplicate_workflow(self, temp_dir):
        """Test complete duplicate detection workflow."""
        detector = DuplicateDetector()
        
        # Create multiple sets of duplicates
        content_a = "Content A"
        content_b = "Content B"
        
        files_a = [temp_dir / f"dup_a_{i}.txt" for i in range(3)]
        files_b = [temp_dir / f"dup_b_{i}.txt" for i in range(2)]
        unique = temp_dir / "unique.txt"
        
        for f in files_a:
            f.write_text(content_a)
        for f in files_b:
            f.write_text(content_b)
        unique.write_text("Unique content")
        
        all_files = files_a + files_b + [unique]
        
        # Detect duplicates
        result = detector.find_duplicates(all_files, detect_similar=False)
        
        # Should find 2 groups
        assert len(result.exact_duplicates) == 2
        
        # Verify group sizes
        group_sizes = [len(g.files) for g in result.exact_duplicates]
        assert 3 in group_sizes  # content_a group
        assert 2 in group_sizes  # content_b group


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
