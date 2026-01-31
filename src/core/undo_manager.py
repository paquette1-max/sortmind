"""
Undo manager - tracks and reverses file operations.
"""
import sqlite3
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


@dataclass
class OperationRecord:
    """Record of a file operation."""
    id: int
    batch_id: str
    timestamp: float
    operation_type: str
    source_path: str
    target_path: str
    file_hash: Optional[str]
    undone: bool


@dataclass
class UndoResult:
    """Result of undo operation."""
    success: bool
    operations_undone: int
    errors: List[str]


class UndoManager:
    """Manages undo functionality for file operations."""
    
    def __init__(self, db_path: Path):
        """
        Initialize undo manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        operation_type TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        target_path TEXT NOT NULL,
                        file_hash TEXT,
                        undone BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_batch_id ON operations(batch_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON operations(timestamp)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_undone ON operations(undone)')
                
                conn.commit()
                self.logger.debug(f"Initialized undo database at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize undo database: {e}")
            raise
    
    def record_operation(
        self,
        batch_id: str,
        operation_type: str,
        source_path: Path,
        target_path: Path,
        file_hash: Optional[str] = None
    ) -> None:
        """
        Record a file operation.
        
        Args:
            batch_id: Unique batch identifier
            operation_type: Type of operation ('move', 'rename', 'copy')
            source_path: Original file path
            target_path: New file path
            file_hash: Optional hash of the file for verification
        """
        try:
            timestamp = datetime.now().timestamp()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO operations 
                    (batch_id, timestamp, operation_type, source_path, target_path, file_hash, undone)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                ''', (batch_id, timestamp, operation_type, str(source_path), str(target_path), file_hash))
                conn.commit()
            
            self.logger.debug(
                f"Recorded {operation_type} operation: {source_path} → {target_path} "
                f"(batch: {batch_id})"
            )
        except Exception as e:
            self.logger.error(f"Failed to record operation: {e}")
            raise
    
    def undo_batch(self, batch_id: str) -> UndoResult:
        """
        Undo all operations in a batch.
        
        Args:
            batch_id: Batch ID to undo
        
        Returns:
            UndoResult with status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get all operations for this batch in reverse order
                cursor = conn.execute('''
                    SELECT id, batch_id, timestamp, operation_type, source_path, 
                           target_path, file_hash, undone
                    FROM operations
                    WHERE batch_id = ? AND undone = 0
                    ORDER BY timestamp DESC
                ''', (batch_id,))
                
                operations = [OperationRecord(*row) for row in cursor.fetchall()]
            
            if not operations:
                self.logger.warning(f"No undoable operations found for batch {batch_id}")
                return UndoResult(success=True, operations_undone=0, errors=[])
            
            undone_count = 0
            errors = []
            
            # Reverse each operation
            for op in operations:
                try:
                    source = Path(op.source_path)
                    target = Path(op.target_path)
                    
                    # Verify target file still exists
                    if not target.exists():
                        errors.append(f"Target file not found: {target}")
                        continue
                    
                    # Move file back to original location
                    if op.operation_type == 'move' or op.operation_type == 'rename':
                        source.parent.mkdir(parents=True, exist_ok=True)
                        target.rename(source)
                        self.logger.info(f"Undone {op.operation_type}: {target} → {source}")
                    elif op.operation_type == 'copy':
                        # For copy, just delete the copied file
                        target.unlink()
                        self.logger.info(f"Undone copy: deleted {target}")
                    
                    # Mark as undone in database
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute(
                            'UPDATE operations SET undone = 1 WHERE id = ?',
                            (op.id,)
                        )
                        conn.commit()
                    
                    undone_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to undo {op.operation_type} {op.target_path}: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            return UndoResult(
                success=(len(errors) == 0),
                operations_undone=undone_count,
                errors=errors
            )
        
        except Exception as e:
            error_msg = f"Failed to undo batch {batch_id}: {e}"
            self.logger.error(error_msg)
            return UndoResult(success=False, operations_undone=0, errors=[error_msg])
    
    def undo_last(self) -> UndoResult:
        """
        Undo the most recent batch.
        
        Returns:
            UndoResult with status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT DISTINCT batch_id
                    FROM operations
                    WHERE undone = 0
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''')
                
                row = cursor.fetchone()
            
            if not row:
                self.logger.warning("No batches available to undo")
                return UndoResult(success=True, operations_undone=0, errors=[])
            
            batch_id = row[0]
            self.logger.info(f"Undoing last batch: {batch_id}")
            return self.undo_batch(batch_id)
        
        except Exception as e:
            error_msg = f"Failed to undo last batch: {e}"
            self.logger.error(error_msg)
            return UndoResult(success=False, operations_undone=0, errors=[error_msg])
    
    def get_history(self, limit: int = 100) -> List[OperationRecord]:
        """
        Get operation history.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of operation records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT id, batch_id, timestamp, operation_type, source_path,
                           target_path, file_hash, undone
                    FROM operations
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                return [OperationRecord(*row) for row in cursor.fetchall()]
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve operation history: {e}")
            return []
    
    def clear_history(self, older_than: Optional[datetime] = None) -> int:
        """
        Clear operation history.
        
        Args:
            older_than: Delete records older than this datetime.
                       If None, deletes only marked undone operations.
        
        Returns:
            Number of records deleted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if older_than:
                    timestamp = older_than.timestamp()
                    cursor = conn.execute(
                        'DELETE FROM operations WHERE timestamp < ?',
                        (timestamp,)
                    )
                else:
                    cursor = conn.execute('DELETE FROM operations WHERE undone = 1')
                
                conn.commit()
                deleted = cursor.rowcount
                self.logger.info(f"Deleted {deleted} operation records")
                return deleted
        
        except Exception as e:
            self.logger.error(f"Failed to clear operation history: {e}")
            return 0
    
    def verify_undo_possible(self, batch_id: str) -> bool:
        """
        Check if undo is possible for a batch.
        
        Args:
            batch_id: Batch ID to verify
        
        Returns:
            True if all target files still exist
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT target_path FROM operations
                    WHERE batch_id = ? AND undone = 0
                ''', (batch_id,))
                
                for (target_path,) in cursor.fetchall():
                    if not Path(target_path).exists():
                        self.logger.warning(f"Target file missing: {target_path}")
                        return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to verify undo possibility: {e}")
            return False
    
    @staticmethod
    def compute_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Compute hash of file.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm to use ('sha256', 'md5', etc.)
        
        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)
            
            return hasher.hexdigest()
        
        except Exception as e:
            logger.error(f"Failed to compute hash for {file_path}: {e}")
            return ""
