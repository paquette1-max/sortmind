"""
Unit tests for FileOrganizer core module.
Tests business logic in isolation with mocked dependencies.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from core.organizer import FileOrganizer, ExecutionResult, FileOperation
from core.config import OrganizationConfig
from core.scanner import ScannedFile


@pytest.mark.unit
class TestFileOrganizer:
    """Tests for FileOrganizer class."""
    
    @pytest.fixture
    def organizer(self):
        """Create FileOrganizer instance."""
        config = OrganizationConfig()
        return FileOrganizer(config=config)
    
    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample files for testing."""
        files = []
        for i in range(3):
            file_path = temp_dir / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append(file_path)
        return files
    
    def test_create_organization_plan_empty(self, organizer):
        """Test creating plan with no files."""
        # Arrange & Act
        plan = organizer.create_organization_plan([], [], Path("/tmp"))
        
        # Assert
        assert plan["operations"] == []
        assert "batch_id" in plan
        assert plan["total_files"] == 0
    
    def test_create_organization_plan_basic(self, organizer, temp_dir, sample_files):
        """Test basic organization plan creation."""
        # Arrange
        analysis_results = [
            {
                "file_path": str(sample_files[0]),
                "category": "documents",
                "suggested_name": "doc1.txt",
                "confidence": 0.95,
                "reasoning": "Text file"
            },
            {
                "file_path": str(sample_files[1]),
                "category": "images",
                "suggested_name": "image1.txt",
                "confidence": 0.90,
                "reasoning": "Image file"
            }
        ]
        
        # Act
        plan = organizer.create_organization_plan(
            sample_files,
            analysis_results,
            temp_dir
        )
        
        # Assert
        assert len(plan["operations"]) == 2
        assert plan["operations"][0]["destination"].parent.name == "documents"
        assert plan["operations"][1]["destination"].parent.name == "images"
        assert "batch_id" in plan
    
    def test_create_organization_plan_low_confidence_filtered(self, organizer, temp_dir, sample_files):
        """Test that low confidence items are filtered based on threshold."""
        # Arrange
        organizer.config.confidence_threshold = 0.8
        
        analysis_results = [
            {
                "file_path": str(sample_files[0]),
                "category": "documents",
                "suggested_name": "doc1.txt",
                "confidence": 0.95,  # High - should include
                "reasoning": "High confidence"
            },
            {
                "file_path": str(sample_files[1]),
                "category": "images",
                "suggested_name": "image1.txt",
                "confidence": 0.50,  # Low - should filter
                "reasoning": "Low confidence"
            }
        ]
        
        # Act
        plan = organizer.create_organization_plan(
            sample_files,
            analysis_results,
            temp_dir
        )
        
        # Assert
        assert len(plan["operations"]) == 1
        assert plan["operations"][0]["confidence"] == 0.95
    
    def test_create_organization_plan_preserves_extension(self, organizer, temp_dir):
        """Test that file extensions are preserved."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        analysis_results = [{
            "file_path": str(test_file),
            "category": "documents",
            "suggested_name": "renamed.pdf",  # Different extension
            "confidence": 0.95,
            "reasoning": "Test"
        }]
        
        # Act
        plan = organizer.create_organization_plan(
            [test_file],
            analysis_results,
            temp_dir
        )
        
        # Assert - extension should be preserved as .txt
        assert plan["operations"][0]["destination"].suffix == ".txt"
    
    def test_validate_plan_conflicts(self, organizer, temp_dir):
        """Test validation detects filename conflicts."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("test1")
        file2.write_text("test2")
        
        dest = temp_dir / "output" / "document.txt"
        
        plan = {
            "operations": [
                {"source": file1, "destination": dest},
                {"source": file2, "destination": dest}
            ]
        }
        
        # Act
        errors = organizer.validate_plan(plan)
        
        # Assert
        assert any("Conflict" in e for e in errors)
    
    def test_validate_plan_missing_source(self, organizer, temp_dir):
        """Test validation detects missing source files."""
        # Arrange
        missing_file = temp_dir / "nonexistent.txt"
        dest = temp_dir / "output" / "file.txt"
        
        plan = {
            "operations": [
                {"source": missing_file, "destination": dest}
            ]
        }
        
        # Act
        errors = organizer.validate_plan(plan)
        
        # Assert
        assert any("not found" in e.lower() for e in errors)
    
    def test_validate_plan_system_directory_target(self, organizer, temp_dir):
        """Test validation prevents targeting system directories."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file1.write_text("test")
        
        plan = {
            "operations": [
                {"source": file1, "destination": Path("/System/Library/test.txt")}
            ]
        }
        
        # Act
        errors = organizer.validate_plan(plan)
        
        # Assert
        assert any("system directory" in e.lower() for e in errors)
    
    def test_resolve_conflicts(self, organizer, temp_dir):
        """Test conflict resolution by appending numbers."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("test1")
        file2.write_text("test2")
        
        dest = temp_dir / "output" / "document.txt"
        
        plan = {
            "operations": [
                {"source": file1, "destination": dest, "operation_type": "move", 
                 "reasoning": "Test", "confidence": 0.95},
                {"source": file2, "destination": dest, "operation_type": "move",
                 "reasoning": "Test", "confidence": 0.95}
            ]
        }
        
        # Act
        resolved = organizer.resolve_conflicts(plan)
        
        # Assert - Second file should have modified destination
        assert resolved["operations"][0]["destination"] == dest
        assert resolved["operations"][1]["destination"] != dest
        assert "(1)" in str(resolved["operations"][1]["destination"])
    
    def test_resolve_conflicts_existing_file(self, organizer, temp_dir):
        """Test conflict resolution when destination file exists."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file1.write_text("test1")
        
        # Create existing file at destination
        dest = temp_dir / "output" / "document.txt"
        dest.parent.mkdir(parents=True)
        dest.write_text("existing")
        
        plan = {
            "operations": [
                {"source": file1, "destination": dest, "operation_type": "move",
                 "reasoning": "Test", "confidence": 0.95}
            ]
        }
        
        # Act
        resolved = organizer.resolve_conflicts(plan)
        
        # Assert
        assert "(1)" in str(resolved["operations"][0]["destination"])
    
    def test_execute_plan_dry_run(self, organizer, temp_dir, sample_files):
        """Test dry run doesn't move files."""
        # Arrange
        dest_dir = temp_dir / "output"
        
        plan = {
            "batch_id": "test-123",
            "operations": [
                {
                    "source": sample_files[0],
                    "destination": dest_dir / "doc.txt",
                    "operation_type": "move",
                    "reasoning": "Test",
                    "confidence": 0.95
                }
            ]
        }
        
        # Act
        result = organizer.execute_plan(plan, dry_run=True)
        
        # Assert
        assert result.success
        assert result.operations_completed == 1
        assert result.operations_failed == 0
        assert sample_files[0].exists()  # File should still be at original location
        assert not (dest_dir / "doc.txt").exists()
    
    def test_execute_plan_actual(self, organizer, temp_dir, sample_files):
        """Test actual file movement."""
        # Arrange
        dest_dir = temp_dir / "output"
        
        plan = {
            "batch_id": "test-456",
            "operations": [
                {
                    "source": sample_files[0],
                    "destination": dest_dir / "doc.txt",
                    "operation_type": "move",
                    "reasoning": "Test",
                    "confidence": 0.95
                }
            ]
        }
        
        # Act
        result = organizer.execute_plan(plan, dry_run=False)
        
        # Assert
        assert result.success
        assert result.operations_completed == 1
        assert not sample_files[0].exists()
        assert (dest_dir / "doc.txt").exists()
    
    def test_execute_plan_with_undo_manager(self, organizer, temp_dir, sample_files):
        """Test that operations are recorded for undo."""
        # Arrange
        undo_manager = Mock()
        organizer.undo_manager = undo_manager
        
        dest_dir = temp_dir / "output"
        
        plan = {
            "batch_id": "test-789",
            "operations": [
                {
                    "source": sample_files[0],
                    "destination": dest_dir / "doc.txt",
                    "operation_type": "move",
                    "reasoning": "Test",
                    "confidence": 0.95
                }
            ]
        }
        
        # Act
        result = organizer.execute_plan(plan, dry_run=False)
        
        # Assert
        assert undo_manager.record_operation.called
    
    def test_execute_plan_with_backup_manager(self, organizer, temp_dir, sample_files):
        """Test that backup is created before operations."""
        # Arrange
        backup_manager = Mock()
        backup_manager.create_backup.return_value = Path("/fake/backup")
        organizer.backup_manager = backup_manager
        
        dest_dir = temp_dir / "output"
        
        plan = {
            "batch_id": "test-backup",
            "operations": [
                {
                    "source": sample_files[0],
                    "destination": dest_dir / "doc.txt",
                    "operation_type": "move",
                    "reasoning": "Test",
                    "confidence": 0.95
                }
            ]
        }
        
        # Act
        result = organizer.execute_plan(plan, dry_run=False)
        
        # Assert
        assert backup_manager.create_backup.called
    
    def test_execute_plan_progress_callback(self, organizer, temp_dir, sample_files):
        """Test progress callback is called during execution."""
        # Arrange
        dest_dir = temp_dir / "output"
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        plan = {
            "batch_id": "test-progress",
            "operations": [
                {
                    "source": sample_files[0],
                    "destination": dest_dir / "doc.txt",
                    "operation_type": "move",
                    "reasoning": "Test",
                    "confidence": 0.95
                }
            ]
        }
        
        # Act
        result = organizer.execute_plan(plan, dry_run=False, progress_callback=progress_callback)
        
        # Assert
        assert len(progress_calls) == 1
        assert progress_calls[0] == (1, 1)
    
    def test_execute_plan_handles_errors(self, organizer, temp_dir):
        """Test that execution handles errors gracefully."""
        # Arrange
        nonexistent_file = temp_dir / "does_not_exist.txt"
        dest_dir = temp_dir / "output"
        
        plan = {
            "batch_id": "test-error",
            "operations": [
                {
                    "source": nonexistent_file,
                    "destination": dest_dir / "doc.txt",
                    "operation_type": "move",
                    "reasoning": "Test",
                    "confidence": 0.95
                }
            ]
        }
        
        # Act
        result = organizer.execute_plan(plan, dry_run=False)
        
        # Assert
        assert not result.success
        assert result.operations_failed == 1
        assert len(result.errors) > 0
    
    def test_truncate_long_filenames(self, organizer, temp_dir):
        """Test that very long filenames are truncated."""
        # Arrange
        organizer.config.max_filename_length = 50
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        long_name = "a" * 100 + ".txt"
        
        analysis_results = [{
            "file_path": str(test_file),
            "category": "documents",
            "suggested_name": long_name,
            "confidence": 0.95,
            "reasoning": "Test"
        }]
        
        # Act
        plan = organizer.create_organization_plan(
            [test_file],
            analysis_results,
            temp_dir
        )
        
        # Assert
        destination_name = plan["operations"][0]["destination"].name
        assert len(destination_name) <= 50
