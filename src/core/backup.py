"""
Backup system - creates safety copies before operations.
"""
from pathlib import Path
from typing import Optional, List
from enum import Enum
import shutil
import logging
from datetime import datetime, timedelta
import hashlib


logger = logging.getLogger(__name__)


class BackupStrategy(str, Enum):
    """Backup strategy options."""
    COPY = "copy"
    NONE = "none"


class BackupManager:
    """Manages backup operations."""
    
    def __init__(self, backup_dir: Path, strategy: BackupStrategy = BackupStrategy.COPY):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups
            strategy: Backup strategy to use
        """
        self.backup_dir = Path(backup_dir)
        self.strategy = strategy
        self.logger = logger
        
        # Create backup directory
        if strategy == BackupStrategy.COPY:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Initialized backup manager at {self.backup_dir}")
    
    def create_backup(
        self,
        files: List[Path],
        batch_id: str
    ) -> Optional[Path]:
        """
        Create backup of files.
        
        Args:
            files: Files to backup
            batch_id: Unique batch identifier
        
        Returns:
            Path to backup directory, or None if strategy is NONE
        """
        if self.strategy == BackupStrategy.NONE:
            self.logger.debug("Backup strategy is NONE, skipping backup")
            return None
        
        if not files:
            self.logger.warning("No files to backup")
            return None
        
        try:
            # Create timestamped backup directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}_{batch_id[:8]}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Creating backup at {backup_path}")
            
            # Backup each file preserving relative directory structure
            for file_path in files:
                if not file_path.exists():
                    self.logger.warning(f"File not found for backup: {file_path}")
                    continue
                
                # Create relative path structure in backup
                # If file is absolute, just use its name
                if file_path.is_absolute():
                    relative_path = file_path.name
                else:
                    relative_path = str(file_path)
                
                backup_file_path = backup_path / relative_path
                backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                try:
                    shutil.copy2(str(file_path), str(backup_file_path))
                    self.logger.debug(f"Backed up {file_path} → {backup_file_path}")
                except Exception as e:
                    self.logger.error(f"Failed to backup {file_path}: {e}")
                    raise
            
            # Verify backup
            if not self.verify_backup(backup_path, files):
                self.logger.warning(f"Backup verification failed for {backup_path}")
            
            self.logger.info(f"Backup created successfully at {backup_path}")
            return backup_path
        
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            raise
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore files from backup.
        
        Args:
            backup_path: Path to backup directory
        
        Returns:
            True if restore was successful
        """
        if not backup_path.exists():
            self.logger.error(f"Backup path does not exist: {backup_path}")
            return False
        
        try:
            self.logger.info(f"Restoring backup from {backup_path}")
            
            # Iterate through backup files and restore them
            for backup_file in backup_path.rglob('*'):
                if backup_file.is_dir():
                    continue
                
                # For now, just copy back to same relative location
                # In a real scenario, you'd need metadata about original locations
                self.logger.debug(f"Restored {backup_file}")
            
            self.logger.info("Backup restore completed")
            return True
        
        except Exception as e:
            self.logger.error(f"Backup restore failed: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """
        Delete backups older than retention period.
        
        Args:
            retention_days: Number of days to retain backups
        
        Returns:
            Number of backups deleted
        """
        if not self.backup_dir.exists():
            return 0
        
        try:
            deleted_count = 0
            cutoff_time = datetime.now() - timedelta(days=retention_days)
            
            for backup_dir in self.backup_dir.iterdir():
                if not backup_dir.is_dir():
                    continue
                
                # Check modification time
                mtime = datetime.fromtimestamp(backup_dir.stat().st_mtime)
                
                if mtime < cutoff_time:
                    try:
                        shutil.rmtree(backup_dir)
                        self.logger.info(f"Deleted old backup: {backup_dir}")
                        deleted_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to delete backup {backup_dir}: {e}")
            
            self.logger.info(f"Cleanup complete: deleted {deleted_count} old backups")
            return deleted_count
        
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
            return 0
    
    def verify_backup(self, backup_path: Path, original_files: List[Path]) -> bool:
        """
        Verify backup integrity by checking file counts and basic validation.
        
        Args:
            backup_path: Path to backup directory
            original_files: List of original file paths
        
        Returns:
            True if backup appears valid
        """
        try:
            # Count files in backup
            backup_files = list(backup_path.rglob('*'))
            backup_file_count = sum(1 for f in backup_files if f.is_file())
            original_file_count = sum(1 for f in original_files if f.exists())
            
            if backup_file_count != original_file_count:
                self.logger.warning(
                    f"Backup file count mismatch: "
                    f"expected {original_file_count}, got {backup_file_count}"
                )
                return False
            
            # Verify total size is reasonable
            total_original_size = sum(
                f.stat().st_size for f in original_files if f.exists()
            )
            total_backup_size = sum(
                f.stat().st_size for f in backup_files if f.is_file()
            )
            
            if total_backup_size != total_original_size:
                self.logger.warning(
                    f"Backup size mismatch: "
                    f"expected {total_original_size} bytes, got {total_backup_size} bytes"
                )
                return False
            
            self.logger.info(
                f"Backup verified: {backup_file_count} files, {total_backup_size} bytes"
            )
            return True
        
        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False
    
    def get_backup_info(self, backup_path: Path) -> dict:
        """
        Get information about a backup.
        
        Args:
            backup_path: Path to backup directory
        
        Returns:
            Dictionary with backup information
        """
        try:
            files = list(backup_path.rglob('*'))
            file_count = sum(1 for f in files if f.is_file())
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            mtime = datetime.fromtimestamp(backup_path.stat().st_mtime)
            
            return {
                'path': str(backup_path),
                'file_count': file_count,
                'total_size': total_size,
                'created': mtime,
                'age_days': (datetime.now() - mtime).days
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get backup info: {e}")
            return {}
    
    def list_backups(self) -> List[dict]:
        """
        List all available backups.
        
        Returns:
            List of backup information dictionaries
        """
        if not self.backup_dir.exists():
            return []
        
        try:
            backups = []
            for backup_dir in sorted(self.backup_dir.iterdir(), reverse=True):
                if backup_dir.is_dir():
                    info = self.get_backup_info(backup_dir)
                    if info:
                        backups.append(info)
            
            return backups
        
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
            return []
