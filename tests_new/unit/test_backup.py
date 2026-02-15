"""
Unit tests for Backup module.
"""
import pytest
from pathlib import Path
import shutil

from core.backup import BackupManager, BackupStrategy


@pytest.mark.unit
class TestBackupManager:
    """Tests for BackupManager class."""
    
    @pytest.fixture
    def backup_manager(self, temp_dir):
        """Create backup manager."""
        backup_dir = temp_dir / "backups"
        return BackupManager(backup_dir, strategy=BackupStrategy.COPY)
    
    def test_initialization(self, temp_dir):
        """Test backup manager initialization."""
        # Arrange & Act
        backup_dir = temp_dir / "backups"
        manager = BackupManager(backup_dir)
        
        # Assert
        assert backup_dir.exists()
    
    def test_initialization_creates_directory(self, temp_dir):
        """Test backup directory is created if it doesn't exist."""
        # Arrange
        backup_dir = temp_dir / "new_backup_dir"
        
        # Act
        manager = BackupManager(backup_dir)
        
        # Assert
        assert backup_dir.exists()
    
    def test_create_backup_single_file(self, backup_manager, temp_dir):
        """Test backing up a single file."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Act
        backup_path = backup_manager.create_backup([test_file], "batch-1")
        
        # Assert
        assert backup_path is not None
        assert backup_path.exists()
        assert (backup_path / "test.txt").exists()
    
    def test_create_backup_multiple_files(self, backup_manager, temp_dir):
        """Test backing up multiple files."""
        # Arrange
        files = []
        for i in range(3):
            f = temp_dir / f"file_{i}.txt"
            f.write_text(f"content {i}")
            files.append(f)
        
        # Act
        backup_path = backup_manager.create_backup(files, "batch-multi")
        
        # Assert
        assert backup_path is not None
        backed_up_files = list(backup_path.glob("*.txt"))
        assert len(backed_up_files) == 3
    
    def test_create_backup_preserves_content(self, backup_manager, temp_dir):
        """Test that backup preserves file content."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("original content")
        
        # Act
        backup_path = backup_manager.create_backup([test_file], "batch-content")
        backup_file = backup_path / "test.txt"
        
        # Assert
        assert backup_file.read_text() == "original content"
    
    def test_create_backup_empty_list(self, backup_manager):
        """Test backing up empty file list."""
        # Act
        backup_path = backup_manager.create_backup([], "batch-empty")
        
        # Assert
        assert backup_path is None
    
    def test_create_backup_nonexistent_file(self, backup_manager, temp_dir, caplog):
        """Test handling nonexistent files."""
        # Arrange
        nonexistent = temp_dir / "does_not_exist.txt"
        
        # Act
        backup_path = backup_manager.create_backup([nonexistent], "batch-missing")
        
        # Assert - backup created but file skipped
        assert backup_path is not None
    
    def test_verify_backup_success(self, backup_manager, temp_dir):
        """Test successful backup verification."""
        # Arrange
        files = []
        for i in range(2):
            f = temp_dir / f"file_{i}.txt"
            f.write_text(f"content {i}")
            files.append(f)
        
        backup_path = backup_manager.create_backup(files, "batch-verify")
        
        # Act
        is_valid = backup_manager.verify_backup(backup_path, files)
        
        # Assert
        assert is_valid is True
    
    def test_verify_backup_wrong_count(self, backup_manager, temp_dir):
        """Test verification fails with wrong file count."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        backup_path = backup_manager.create_backup([test_file], "batch-wrong")
        
        # Act - verify with wrong count
        is_valid = backup_manager.verify_backup(backup_path, [test_file, test_file])
        
        # Assert
        assert is_valid is False
    
    def test_get_backup_info(self, backup_manager, temp_dir):
        """Test getting backup information."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        backup_path = backup_manager.create_backup([test_file], "batch-info")
        
        # Act
        info = backup_manager.get_backup_info(backup_path)
        
        # Assert
        assert info["path"] == str(backup_path)
        assert info["file_count"] == 1
        assert info["total_size"] == len("content")
        assert "created" in info
    
    def test_list_backups(self, backup_manager, temp_dir):
        """Test listing backups."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        backup_manager.create_backup([test_file], "batch-1")
        backup_manager.create_backup([test_file], "batch-2")
        
        # Act
        backups = backup_manager.list_backups()
        
        # Assert
        assert len(backups) == 2
    
    def test_cleanup_old_backups(self, backup_manager, temp_dir):
        """Test cleaning up old backups."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        backup_path = backup_manager.create_backup([test_file], "batch-old")
        
        # Act - should not delete recent backup
        deleted = backup_manager.cleanup_old_backups(retention_days=30)
        
        # Assert
        assert deleted == 0
        assert backup_path.exists()
    
    def test_restore_backup(self, backup_manager, temp_dir):
        """Test restoring from backup."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("original")
        
        backup_path = backup_manager.create_backup([test_file], "batch-restore")
        
        # Modify original
        test_file.write_text("modified")
        
        # Act
        success = backup_manager.restore_backup(backup_path)
        
        # Assert
        assert success is True
    
    def test_restore_nonexistent_backup(self, backup_manager):
        """Test restoring from nonexistent backup."""
        # Act
        success = backup_manager.restore_backup(Path("/nonexistent/backup"))
        
        # Assert
        assert success is False
    
    def test_none_strategy_skips_backup(self, temp_dir):
        """Test NONE strategy skips backup creation."""
        # Arrange
        backup_dir = temp_dir / "backups"
        manager = BackupManager(backup_dir, strategy=BackupStrategy.NONE)
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        # Act
        backup_path = manager.create_backup([test_file], "batch-none")
        
        # Assert
        assert backup_path is None
    
    def test_backup_preserves_nested_structure(self, backup_manager, temp_dir):
        """Test backup preserves nested directory structure."""
        # Arrange
        nested_dir = temp_dir / "level1" / "level2"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "nested.txt"
        nested_file.write_text("nested content")
        
        # Act
        backup_path = backup_manager.create_backup([nested_file], "batch-nested")
        
        # Assert
        backed_up_file = backup_path / "nested.txt"
        assert backed_up_file.exists()
        assert backed_up_file.read_text() == "nested content"
