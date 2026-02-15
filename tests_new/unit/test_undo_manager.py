"""
Unit tests for UndoManager module.
"""
import pytest
import sqlite3
from datetime import datetime

from core.undo_manager import UndoManager, OperationRecord, UndoResult


@pytest.mark.unit
class TestUndoManager:
    """Tests for UndoManager class."""
    
    @pytest.fixture
    def undo_manager(self, temp_dir):
        """Create undo manager instance."""
        db_path = temp_dir / "undo.db"
        return UndoManager(db_path)
    
    def test_initialization(self, temp_dir):
        """Test undo manager initializes database."""
        # Arrange & Act
        db_path = temp_dir / "test_undo.db"
        manager = UndoManager(db_path)
        
        # Assert
        assert db_path.exists()
    
    def test_database_schema(self, undo_manager):
        """Test database schema is created correctly."""
        # Act
        conn = sqlite3.connect(str(undo_manager.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='operations'"
        )
        result = cursor.fetchone()
        conn.close()
        
        # Assert
        assert result is not None
    
    def test_record_operation(self, undo_manager, temp_dir):
        """Test recording a file operation."""
        # Arrange
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test")
        
        # Act
        undo_manager.record_operation(
            batch_id="batch-1",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        # Assert
        history = undo_manager.get_history()
        assert len(history) == 1
        assert history[0].batch_id == "batch-1"
        assert history[0].operation_type == "move"
    
    def test_record_multiple_operations(self, undo_manager, temp_dir):
        """Test recording multiple operations."""
        # Arrange
        for i in range(3):
            source = temp_dir / f"source_{i}.txt"
            target = temp_dir / f"target_{i}.txt"
            source.write_text(f"content {i}")
            
            undo_manager.record_operation(
                batch_id=f"batch-{i}",
                operation_type="move",
                source_path=source,
                target_path=target
            )
        
        # Act
        history = undo_manager.get_history()
        
        # Assert
        assert len(history) == 3
    
    def test_undo_batch_move(self, undo_manager, temp_dir):
        """Test undoing a move operation."""
        # Arrange
        source = temp_dir / "original.txt"
        target = temp_dir / "moved" / "file.txt"
        target.parent.mkdir(parents=True)
        source.write_text("test content")
        
        # Move file manually first
        import shutil
        shutil.move(str(source), str(target))
        
        undo_manager.record_operation(
            batch_id="batch-move",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        # Act
        result = undo_manager.undo_batch("batch-move")
        
        # Assert
        assert result.success is True
        assert result.operations_undone == 1
        assert source.exists()
        assert not target.exists()
    
    def test_undo_last(self, undo_manager, temp_dir):
        """Test undoing the last batch."""
        # Arrange
        source = temp_dir / "latest.txt"
        target = temp_dir / "moved_latest.txt"
        source.write_text("latest content")
        
        import shutil
        shutil.move(str(source), str(target))
        
        undo_manager.record_operation(
            batch_id="latest-batch",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        # Act
        result = undo_manager.undo_last()
        
        # Assert
        assert result.success is True
        assert result.operations_undone == 1
    
    def test_undo_no_operations(self, undo_manager):
        """Test undo when no operations exist."""
        # Act
        result = undo_manager.undo_last()
        
        # Assert
        assert result.success is True
        assert result.operations_undone == 0
    
    def test_verify_undo_possible(self, undo_manager, temp_dir):
        """Test checking if undo is possible."""
        # Arrange
        source = temp_dir / "file.txt"
        target = temp_dir / "moved.txt"
        target.write_text("content")
        
        undo_manager.record_operation(
            batch_id="verify-batch",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        # Act & Assert
        assert undo_manager.verify_undo_possible("verify-batch") is True
        
        # Delete target file
        target.unlink()
        assert undo_manager.verify_undo_possible("verify-batch") is False
    
    def test_get_history_limit(self, undo_manager, temp_dir):
        """Test history retrieval with limit."""
        # Arrange
        for i in range(10):
            source = temp_dir / f"file_{i}.txt"
            target = temp_dir / f"moved_{i}.txt"
            source.write_text(f"content {i}")
            
            undo_manager.record_operation(
                batch_id=f"batch-{i}",
                operation_type="move",
                source_path=source,
                target_path=target
            )
        
        # Act
        history = undo_manager.get_history(limit=5)
        
        # Assert
        assert len(history) == 5
    
    def test_clear_history(self, undo_manager, temp_dir):
        """Test clearing operation history."""
        # Arrange
        for i in range(3):
            source = temp_dir / f"file_{i}.txt"
            target = temp_dir / f"moved_{i}.txt"
            source.write_text(f"content {i}")
            
            undo_manager.record_operation(
                batch_id=f"batch-{i}",
                operation_type="move",
                source_path=source,
                target_path=target
            )
        
        # Act - clear all history (use older_than far in the future to get all)
        from datetime import datetime, timedelta
        deleted = undo_manager.clear_history(older_than=datetime.now() + timedelta(days=1))
        history = undo_manager.get_history()
        
        # Assert
        assert deleted == 3
        assert len(history) == 0
    
    def test_clear_old_history(self, undo_manager, temp_dir):
        """Test clearing old operation history."""
        # Arrange
        source = temp_dir / "recent.txt"
        target = temp_dir / "moved_recent.txt"
        source.write_text("content")
        
        undo_manager.record_operation(
            batch_id="recent-batch",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        # Act - clear entries older than now (should delete our entry since it's in the past)
        from datetime import datetime, timedelta
        deleted = undo_manager.clear_history(older_than=datetime.now() + timedelta(seconds=1))
        
        # Assert - our entry is in the past so it should be deleted
        assert deleted >= 1
    
    def test_compute_file_hash(self, temp_dir):
        """Test computing file hash."""
        # Arrange
        file_path = temp_dir / "test.txt"
        file_path.write_text("test content")
        
        # Act
        hash1 = UndoManager.compute_file_hash(file_path)
        hash2 = UndoManager.compute_file_hash(file_path)
        
        # Assert
        assert len(hash1) == 64
        assert hash1 == hash2
    
    def test_operations_marked_undone(self, undo_manager, temp_dir):
        """Test that operations are marked as undone after undo."""
        # Arrange
        source = temp_dir / "file.txt"
        target = temp_dir / "moved.txt"
        target.write_text("content")
        
        undo_manager.record_operation(
            batch_id="mark-undone",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        # Act
        undo_manager.undo_batch("mark-undone")
        history = undo_manager.get_history()
        
        # Assert
        assert history[0].undone == 1
    
    def test_undo_already_undone_batch(self, undo_manager, temp_dir):
        """Test undoing a batch that's already been undone."""
        # Arrange
        source = temp_dir / "file.txt"
        target = temp_dir / "moved.txt"
        target.write_text("content")
        
        undo_manager.record_operation(
            batch_id="already-undone",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        # First undo
        result1 = undo_manager.undo_batch("already-undone")
        assert result1.operations_undone == 1
        
        # Second undo - should find nothing to undo
        result2 = undo_manager.undo_batch("already-undone")
        assert result2.operations_undone == 0
