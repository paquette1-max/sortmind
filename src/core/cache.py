"""
LLM Response Cache - reduces redundant LLM calls for same files.
"""
import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class LLMCache:
    """Cache for LLM analysis results indexed by file hash and model name."""
    
    def __init__(self, db_path: Path):
        """
        Initialize LLM cache.
        
        Args:
            db_path: Path to SQLite cache database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite cache database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS llm_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_hash TEXT NOT NULL,
                        model_name TEXT NOT NULL,
                        analysis_result TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        access_count INTEGER DEFAULT 1,
                        UNIQUE(file_hash, model_name)
                    )
                ''')
                
                # Create indexes for performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_file_hash ON llm_cache(file_hash)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_model_name ON llm_cache(model_name)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON llm_cache(created_at)')
                
                conn.commit()
                logger.debug(f"Initialized LLM cache at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM cache: {e}")
            raise
    
    def get(self, file_hash: str, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis result for a file and model.
        
        Args:
            file_hash: SHA256 hash of the file
            model_name: Name of the LLM model used
        
        Returns:
            Analysis result dict, or None if not in cache
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    '''SELECT analysis_result FROM llm_cache 
                       WHERE file_hash = ? AND model_name = ?''',
                    (file_hash, model_name)
                )
                
                row = cursor.fetchone()
                
                if row:
                    # Update last_accessed and access_count
                    conn.execute(
                        '''UPDATE llm_cache SET last_accessed = CURRENT_TIMESTAMP, 
                           access_count = access_count + 1
                           WHERE file_hash = ? AND model_name = ?''',
                        (file_hash, model_name)
                    )
                    conn.commit()
                    
                    result = json.loads(row[0])
                    logger.debug(f"Cache hit: {file_hash[:8]}... / {model_name}")
                    return result
            
            logger.debug(f"Cache miss: {file_hash[:8]}... / {model_name}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to retrieve from cache: {e}")
            return None
    
    def set(self, file_hash: str, model_name: str, result: Dict[str, Any]) -> bool:
        """
        Store analysis result in cache.
        
        Args:
            file_hash: SHA256 hash of the file
            model_name: Name of the LLM model
            result: Analysis result dictionary
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result_json = json.dumps(result)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    '''INSERT OR REPLACE INTO llm_cache 
                       (file_hash, model_name, analysis_result, created_at, last_accessed)
                       VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)''',
                    (file_hash, model_name, result_json)
                )
                conn.commit()
            
            logger.debug(f"Cached result: {file_hash[:8]}... / {model_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store in cache: {e}")
            return False
    
    def clear_old(self, days: int = 30) -> int:
        """
        Clear cache entries older than specified days.
        
        Args:
            days: Days to retain cache entries
        
        Returns:
            Number of entries deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'DELETE FROM llm_cache WHERE created_at < ?',
                    (cutoff_date.isoformat(),)
                )
                conn.commit()
                
                deleted = cursor.rowcount
                logger.info(f"Cleared {deleted} old cache entries (older than {days} days)")
                return deleted
        
        except Exception as e:
            logger.error(f"Failed to clear old cache entries: {e}")
            return 0
    
    def clear_all(self) -> int:
        """Clear entire cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('DELETE FROM llm_cache')
                conn.commit()
                
                deleted = cursor.rowcount
                logger.info(f"Cleared entire cache ({deleted} entries)")
                return deleted
        
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    '''SELECT 
                       COUNT(*) as total_entries,
                       COUNT(DISTINCT file_hash) as unique_files,
                       COUNT(DISTINCT model_name) as unique_models,
                       SUM(access_count) as total_accesses,
                       AVG(access_count) as avg_accesses
                       FROM llm_cache'''
                )
                
                row = cursor.fetchone()
                
                return {
                    'total_entries': row[0] or 0,
                    'unique_files': row[1] or 0,
                    'unique_models': row[2] or 0,
                    'total_accesses': row[3] or 0,
                    'avg_accesses': row[4] or 0.0
                }
        
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    @staticmethod
    def compute_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """
        Compute hash of file for cache lookup.
        
        Args:
            file_path: Path to file (string)
            algorithm: Hash algorithm ('sha256', 'md5', etc.)
        
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
