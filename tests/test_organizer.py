"""
Tests for file organizer module.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from src.core.organizer import FileOrganizer, ExecutionResult, FileOperation
from src.core.undo_manager import UndoManager
from src.core.backup import BackupManager, BackupStrategy


class TestFileOrganizer:
    """Tests for FileOrganizer class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        # Cleanup
        if temp_path.exists():
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def organizer(self):
        """Create FileOrganizer instance."""
        return FileOrganizer()
    
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
        plan = organizer.create_organization_plan([], [], Path("/tmp"))
        assert plan["operations"] == []
        assert "batch_id" in plan
    
    def test_create_organization_plan_basic(self, organizer, temp_dir, sample_files):
        """Test basic organization plan creation."""
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
                "category": "documents",
                "suggested_name": "doc2.txt",
                "confidence": 0.90,
                "reasoning": "Text file"
            }
        ]
        
        plan = organizer.create_organization_plan(
            sample_files,
            analysis_results,
            temp_dir
        )
        
        assert len(plan["operations"]) == 2
        assert plan["operations"][0]["destination"].parent.name == "documents"
        assert plan["batch_id"]
    
    def test_validate_plan_conflicts(self, organizer, temp_dir):
        """Test validation detects filename conflicts."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("test")
        file2.write_text("test")
        
        dest = temp_dir / "output" / "document.txt"
        
        plan = {
            "operations": [
                {"source": file1, "destination": dest},
                {"source": file2, "destination": dest}
            ]
        }
        
        errors = organizer.validate_plan(plan)
        assert any("Conflict" in e for e in errors)
    
    def test_validate_plan_missing_source(self, organizer, temp_dir):
        """Test validation detects missing source files."""
        missing_file = temp_dir / "nonexistent.txt"
        dest = temp_dir / "output" / "file.txt"
        
        plan = {
            "operations": [
                {"source": missing_file, "destination": dest}
            ]
        }
        
        errors = organizer.validate_plan(plan)
        assert any("not found" in e.lower() or "not exist" in e.lower() for e in errors)
    
    def test_resolve_conflicts(self, organizer, temp_dir):
        """Test conflict resolution by appending numbers."""
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
        
        resolved = organizer.resolve_conflicts(plan)
        
        # Second file should have modified destination
        assert resolved["operations"][0]["destination"] == dest
        assert resolved["operations"][1]["destination"] != dest
        assert "(1)" in str(resolved["operations"][1]["destination"])
    
    def test_execute_plan_dry_run(self, organizer, temp_dir, sample_files):
        """Test dry run doesn't move files."""
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
        
        result = organizer.execute_plan(plan, dry_run=True)
        
        assert result.success
        assert result.operations_completed == 1
        assert result.operations_failed == 0
        # File should still be at original location
        assert sample_files[0].exists()
        assert not (dest_dir / "doc.txt").exists()
    
    def test_execute_plan_actual(self, organizer, temp_dir, sample_files):
        """Test actual file movement."""
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
        
        result = organizer.execute_plan(plan, dry_run=False)
        
        assert result.success
        assert result.operations_completed == 1
        # File should be moved
        assert not sample_files[0].exists()
        assert (dest_dir / "doc.txt").exists()


class TestUndoManager:
    """Tests for UndoManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def undo_manager(self, temp_dir):
        """Create UndoManager instance."""
        db_path = temp_dir / "undo.db"
        return UndoManager(db_path)
    
    def test_database_initialization(self, undo_manager):
        """Test database is properly initialized."""
        assert undo_manager.db_path.exists()
    
    def test_record_operation(self, undo_manager, temp_dir):
        """Test recording file operations."""
        source = temp_dir / "original.txt"
        target = temp_dir / "moved.txt"
        
        source.write_text("test")
        
        undo_manager.record_operation(
            batch_id="batch-1",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        history = undo_manager.get_history(limit=1)
        assert len(history) == 1
        assert history[0].batch_id == "batch-1"
        assert history[0].operation_type == "move"
    
    def test_get_history(self, undo_manager, temp_dir):
        """Test retrieving operation history."""
        # Record multiple operations
        for i in range(3):
            source = temp_dir / f"file_{i}.txt"
            target = temp_dir / f"moved_{i}.txt"
            source.write_text(f"test {i}")
            
            undo_manager.record_operation(
                batch_id=f"batch-{i}",
                operation_type="move",
                source_path=source,
                target_path=target
            )
        
        history = undo_manager.get_history(limit=10)
        assert len(history) >= 3
    
    def test_verify_undo_possible(self, undo_manager, temp_dir):
        """Test checking if undo is possible."""
        source = temp_dir / "original.txt"
        target = temp_dir / "moved.txt"
        target.write_text("test")
        
        undo_manager.record_operation(
            batch_id="batch-verify",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        # Should be possible if target exists
        assert undo_manager.verify_undo_possible("batch-verify")
        
        # Should not be possible if target is deleted
        target.unlink()
        assert not undo_manager.verify_undo_possible("batch-verify")
    
    def test_file_hash_computation(self, temp_dir):
        """Test computing file hash."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("test content")
        
        hash_val = UndoManager.compute_file_hash(file_path)
        assert len(hash_val) == 64  # SHA256 hex
        
        # Same content should produce same hash
        hash_val2 = UndoManager.compute_file_hash(file_path)
        assert hash_val == hash_val2


class TestBackupManager:
    """Tests for BackupManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def backup_manager(self, temp_dir):
        """Create BackupManager instance."""
        backup_dir = temp_dir / "backups"
        return BackupManager(backup_dir, strategy=BackupStrategy.COPY)
    
    def test_initialization(self, backup_manager):
        """Test backup manager initialization."""
        assert backup_manager.backup_dir.exists()
        assert backup_manager.strategy == BackupStrategy.COPY
    
    def test_create_backup(self, backup_manager, temp_dir):
        """Test creating backup of files."""
        # Create test files
        test_files = []
        for i in range(2):
            file_path = temp_dir / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            test_files.append(file_path)
        
        backup_path = backup_manager.create_backup(test_files, "batch-123")
        
        assert backup_path is not None
        assert backup_path.exists()
        
        # Check files were backed up
        backup_files = list(backup_path.rglob("*.txt"))
        assert len(backup_files) == 2
    
    def test_backup_verification(self, backup_manager, temp_dir):
        """Test backup verification."""
        test_files = []
        for i in range(2):
            file_path = temp_dir / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            test_files.append(file_path)
        
        backup_path = backup_manager.create_backup(test_files, "batch-456")
        
        # Should pass verification
        assert backup_manager.verify_backup(backup_path, test_files)
    
    def test_cleanup_old_backups(self, backup_manager):
        """Test cleanup of old backups."""
        # Create a backup (this won't actually be old)
        deleted = backup_manager.cleanup_old_backups(retention_days=30)
        # Just verify the method runs without error
        assert isinstance(deleted, int)
    
    def test_list_backups(self, backup_manager, temp_dir):
        """Test listing available backups."""
        # Create a backup
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")
        
        backup_manager.create_backup([test_file], "batch-789")
        
        backups = backup_manager.list_backups()
        assert len(backups) >= 1
        assert 'file_count' in backups[0]
        assert 'total_size' in backups[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
