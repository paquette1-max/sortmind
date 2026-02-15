"""
Unit tests for RulesEngine module.
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta

from core.rules_engine import (
    RulesEngine, OrganizationRule, RuleType, RuleOperator, RuleMatch
)


@pytest.mark.unit
class TestOrganizationRule:
    """Tests for OrganizationRule dataclass."""
    
    def test_rule_creation(self):
        """Test creating a rule."""
        rule = OrganizationRule(
            id="rule-1",
            name="Test Rule",
            rule_type=RuleType.EXTENSION,
            operator=RuleOperator.EQUALS,
            value=".txt",
            target_category="documents",
            priority=10
        )
        
        assert rule.id == "rule-1"
        assert rule.name == "Test Rule"
        assert rule.enabled is True
    
    def test_rule_to_dict(self):
        """Test converting rule to dictionary."""
        rule = OrganizationRule(
            id="rule-1",
            name="Test Rule",
            rule_type=RuleType.EXTENSION,
            operator=RuleOperator.EQUALS,
            value=".txt",
            target_category="documents"
        )
        
        data = rule.to_dict()
        
        assert data["id"] == "rule-1"
        assert data["rule_type"] == "extension"
        assert data["operator"] == "equals"
    
    def test_rule_from_dict(self):
        """Test creating rule from dictionary."""
        data = {
            "id": "rule-1",
            "name": "Test Rule",
            "rule_type": "extension",
            "operator": "equals",
            "value": ".txt",
            "target_category": "documents",
            "priority": 10,
            "enabled": True
        }
        
        rule = OrganizationRule.from_dict(data)
        
        assert rule.id == "rule-1"
        assert rule.rule_type == RuleType.EXTENSION
        assert rule.priority == 10


@pytest.mark.unit
class TestRulesEngine:
    """Tests for RulesEngine class."""
    
    @pytest.fixture
    def rules_engine(self):
        """Create rules engine with sample rules."""
        engine = RulesEngine()
        
        # Add extension rule
        engine.add_rule(OrganizationRule(
            id="ext-txt",
            name="Text Files",
            rule_type=RuleType.EXTENSION,
            operator=RuleOperator.EQUALS,
            value=".txt",
            target_category="documents",
            priority=10
        ))
        
        # Add pattern rule
        engine.add_rule(OrganizationRule(
            id="pattern-invoice",
            name="Invoice Files",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="invoice",
            target_category="finance",
            priority=5
        ))
        
        return engine
    
    def test_add_rule(self, rules_engine):
        """Test adding rules."""
        # Arrange
        new_rule = OrganizationRule(
            id="new-rule",
            name="New Rule",
            rule_type=RuleType.EXTENSION,
            operator=RuleOperator.EQUALS,
            value=".pdf"
        )
        
        # Act
        rules_engine.add_rule(new_rule)
        
        # Assert
        assert len(rules_engine.rules) == 3
        assert rules_engine.get_rule("new-rule") is not None
    
    def test_add_rule_sorts_by_priority(self, rules_engine):
        """Test that rules are sorted by priority."""
        # Assert - lower priority number should come first
        priorities = [r.priority for r in rules_engine.rules]
        assert priorities == sorted(priorities)
    
    def test_remove_rule(self, rules_engine):
        """Test removing a rule."""
        # Act
        result = rules_engine.remove_rule("ext-txt")
        
        # Assert
        assert result is True
        assert len(rules_engine.rules) == 1
        assert rules_engine.get_rule("ext-txt") is None
    
    def test_remove_nonexistent_rule(self, rules_engine):
        """Test removing a rule that doesn't exist."""
        # Act
        result = rules_engine.remove_rule("nonexistent")
        
        # Assert
        assert result is False
    
    def test_update_rule(self, rules_engine):
        """Test updating a rule."""
        # Act
        result = rules_engine.update_rule("ext-txt", {"priority": 1})
        
        # Assert
        assert result is True
        assert rules_engine.get_rule("ext-txt").priority == 1
    
    def test_enable_disable_rule(self, rules_engine):
        """Test enabling and disabling rules."""
        # Act & Assert
        assert rules_engine.disable_rule("ext-txt") is True
        assert rules_engine.get_rule("ext-txt").enabled is False
        
        assert rules_engine.enable_rule("ext-txt") is True
        assert rules_engine.get_rule("ext-txt").enabled is True
    
    def test_evaluate_extension_rule(self, rules_engine, temp_dir):
        """Test evaluating extension rules."""
        # Arrange
        test_file = temp_dir / "document.txt"
        test_file.write_text("test content")
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert
        assert match.matched is True
        assert match.target_category == "documents"
    
    def test_evaluate_pattern_rule(self, rules_engine, temp_dir):
        """Test evaluating filename pattern rules."""
        # Arrange
        test_file = temp_dir / "invoice_2024_jan.txt"
        test_file.write_text("invoice content")
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert - should match pattern rule (higher priority)
        assert match.matched is True
        assert match.target_category == "finance"
    
    def test_evaluate_disabled_rule(self, rules_engine, temp_dir):
        """Test that disabled rules are not evaluated."""
        # Arrange
        rules_engine.disable_rule("ext-txt")
        test_file = temp_dir / "document.txt"
        test_file.write_text("test content")
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert - should not match disabled rule
        assert match.matched is False
    
    def test_evaluate_nonexistent_file(self, rules_engine):
        """Test evaluating non-existent file."""
        # Act
        match = rules_engine.evaluate_file("/nonexistent/file.txt")
        
        # Assert
        assert match.matched is False
        assert "not found" in match.reasoning.lower()
    
    def test_evaluate_multiple_files(self, rules_engine, temp_dir):
        """Test evaluating multiple files at once."""
        # Arrange
        file1 = temp_dir / "doc1.txt"
        file2 = temp_dir / "doc2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Act
        results = rules_engine.evaluate_files([file1, file2])
        
        # Assert
        assert len(results) == 2
        assert all(r.matched for r in results.values())
    
    def test_evaluate_filename_contains(self, temp_dir):
        """Test filename contains operator."""
        # Arrange - use fresh engine to avoid priority conflicts
        from core.rules_engine import RulesEngine
        rules_engine = RulesEngine()
        
        rule = OrganizationRule(
            id="contains-test",
            name="Contains Test",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="report",
            target_category="reports"
        )
        rules_engine.add_rule(rule)
        
        test_file = temp_dir / "monthly_report_2024.txt"
        test_file.write_text("report content")
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert
        assert match.matched is True
        assert match.target_category == "reports"
    
    def test_evaluate_filename_regex(self, temp_dir):
        """Test filename regex operator."""
        # Arrange - use fresh engine
        from core.rules_engine import RulesEngine
        rules_engine = RulesEngine()
        
        rule = OrganizationRule(
            id="regex-test",
            name="Regex Test",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.MATCHES_REGEX,
            value=r"^IMG_\d{4}\.",
            target_category="photos"
        )
        rules_engine.add_rule(rule)
        
        test_file = temp_dir / "IMG_2024.txt"
        test_file.write_text("photo")
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert
        assert match.matched is True
        assert match.target_category == "photos"
    
    def test_evaluate_file_size_greater_than(self, rules_engine, temp_dir):
        """Test file size greater than operator."""
        # Arrange
        rule = OrganizationRule(
            id="size-test",
            name="Large Files",
            rule_type=RuleType.FILE_SIZE,
            operator=RuleOperator.GREATER_THAN,
            value="1KB",
            target_category="large_files"
        )
        rules_engine.add_rule(rule)
        
        # Create file larger than 1KB
        test_file = temp_dir / "large_file.txt"
        test_file.write_text("x" * 2000)
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert
        assert match.matched is True
    
    def test_evaluate_file_size_between(self, rules_engine, temp_dir):
        """Test file size between operator."""
        # Arrange
        rule = OrganizationRule(
            id="size-between",
            name="Medium Files",
            rule_type=RuleType.FILE_SIZE,
            operator=RuleOperator.BETWEEN,
            value="500B",
            value2="2KB",
            target_category="medium_files"
        )
        rules_engine.add_rule(rule)
        
        test_file = temp_dir / "medium_file.txt"
        test_file.write_text("x" * 1000)
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert
        assert match.matched is True
    
    def test_evaluate_date_modified(self, rules_engine, temp_dir):
        """Test date modified rules."""
        # Arrange
        rule = OrganizationRule(
            id="recent-files",
            name="Recent Files",
            rule_type=RuleType.DATE_MODIFIED,
            operator=RuleOperator.GREATER_THAN,
            value="7_days_ago",
            target_category="recent"
        )
        rules_engine.add_rule(rule)
        
        test_file = temp_dir / "new_file.txt"
        test_file.write_text("new content")
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert - file just created should be recent
        assert match.matched is True
    
    def test_evaluate_content_keyword(self, temp_dir):
        """Test content keyword rules."""
        # Arrange - use fresh engine
        from core.rules_engine import RulesEngine
        rules_engine = RulesEngine()
        
        rule = OrganizationRule(
            id="confidential",
            name="Confidential Content",
            rule_type=RuleType.CONTENT_KEYWORD,
            operator=RuleOperator.CONTAINS,
            value="CONFIDENTIAL",
            target_category="confidential"
        )
        rules_engine.add_rule(rule)
        
        test_file = temp_dir / "secret.txt"
        test_file.write_text("This is CONFIDENTIAL information")
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert
        assert match.matched is True
        assert match.target_category == "confidential"
    
    def test_clear_rules(self, rules_engine):
        """Test clearing all rules."""
        # Act
        rules_engine.clear_rules()
        
        # Assert
        assert len(rules_engine.rules) == 0
    
    def test_get_rules_enabled_only(self, rules_engine):
        """Test getting only enabled rules."""
        # Arrange
        rules_engine.disable_rule("ext-txt")
        
        # Act
        enabled = rules_engine.get_rules(enabled_only=True)
        
        # Assert
        assert len(enabled) == 1
        assert all(r.enabled for r in enabled)
    
    def test_save_and_load_rules(self, rules_engine, temp_dir):
        """Test saving and loading rules from file."""
        # Arrange
        rules_file = temp_dir / "rules.json"
        
        # Act
        rules_engine.save_to_file(rules_file)
        
        # Create new engine and load
        new_engine = RulesEngine()
        new_engine.load_from_file(rules_file)
        
        # Assert
        assert len(new_engine.rules) == len(rules_engine.rules)
        assert new_engine.get_rule("ext-txt") is not None
    
    def test_apply_name_pattern(self, temp_dir):
        """Test applying rename patterns."""
        # Arrange - use fresh engine
        from core.rules_engine import RulesEngine
        rules_engine = RulesEngine()
        
        rule = OrganizationRule(
            id="rename",
            name="Rename Rule",
            rule_type=RuleType.EXTENSION,
            operator=RuleOperator.EQUALS,
            value=".txt",
            target_category="documents",
            target_name_pattern="{category}_{original_name}"
        )
        rules_engine.add_rule(rule)
        
        test_file = temp_dir / "report.txt"
        test_file.write_text("report content")
        
        # Act
        match = rules_engine.evaluate_file(test_file)
        
        # Assert
        assert match.matched is True
        # Pattern should be applied
        assert "documents" in (match.target_name or "")
    
    def test_parse_size(self, rules_engine):
        """Test size parsing with various units."""
        # Assert
        assert rules_engine._parse_size("100") == 100
        assert rules_engine._parse_size("1KB") == 1024
        assert rules_engine._parse_size("1kb") == 1024  # Case insensitive
        assert rules_engine._parse_size("1 MB") == 1024 ** 2
        assert rules_engine._parse_size("1.5GB") == int(1.5 * 1024 ** 3)
    
    def test_parse_relative_date(self, rules_engine):
        """Test parsing relative date strings."""
        # Act & Assert
        today = rules_engine._parse_relative_date("today")
        assert isinstance(today, datetime)
        
        yesterday = rules_engine._parse_relative_date("yesterday")
        assert isinstance(yesterday, datetime)
        
        week_ago = rules_engine._parse_relative_date("1 week ago")
        assert isinstance(week_ago, datetime)
