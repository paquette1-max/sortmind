"""
Unit tests for Cache module.
"""
import pytest
import hashlib
import sqlite3
from datetime import datetime, timedelta

from core.cache import LLMCache


@pytest.mark.unit
class TestLLMCache:
    """Tests for LLMCache class."""
    
    @pytest.fixture
    def cache(self, temp_dir):
        """Create cache instance."""
        db_path = temp_dir / "test_cache.db"
        return LLMCache(db_path)
    
    def test_initialization(self, temp_dir):
        """Test cache initializes and creates database."""
        # Arrange & Act
        db_path = temp_dir / "cache.db"
        cache = LLMCache(db_path)
        
        # Assert
        assert db_path.exists()
    
    def test_database_schema(self, cache, temp_dir):
        """Test database schema is created correctly."""
        # Act
        conn = sqlite3.connect(str(cache.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='llm_cache'"
        )
        result = cursor.fetchone()
        conn.close()
        
        # Assert
        assert result is not None
    
    def test_cache_miss(self, cache):
        """Test retrieving non-existent entry returns None."""
        # Act
        result = cache.get("nonexistent_hash", "gpt-4")
        
        # Assert
        assert result is None
    
    def test_cache_set_and_get(self, cache):
        """Test setting and retrieving cache entry."""
        # Arrange
        file_hash = hashlib.sha256(b"test").hexdigest()
        model_name = "gpt-4"
        analysis = {"category": "documents", "confidence": 0.95}
        
        # Act
        cache.set(file_hash, model_name, analysis)
        result = cache.get(file_hash, model_name)
        
        # Assert
        assert result is not None
        assert result["category"] == "documents"
        assert result["confidence"] == 0.95
    
    def test_cache_overwrite(self, cache):
        """Test that setting same key overwrites value."""
        # Arrange
        file_hash = hashlib.sha256(b"test").hexdigest()
        model_name = "gpt-4"
        
        cache.set(file_hash, model_name, {"category": "old"})
        cache.set(file_hash, model_name, {"category": "new"})
        
        # Act
        result = cache.get(file_hash, model_name)
        
        # Assert
        assert result["category"] == "new"
    
    def test_cache_different_models(self, cache):
        """Test caching for different models."""
        # Arrange
        file_hash = hashlib.sha256(b"test").hexdigest()
        
        cache.set(file_hash, "gpt-4", {"model": "gpt-4-result"})
        cache.set(file_hash, "claude", {"model": "claude-result"})
        
        # Act
        gpt_result = cache.get(file_hash, "gpt-4")
        claude_result = cache.get(file_hash, "claude")
        
        # Assert
        assert gpt_result["model"] == "gpt-4-result"
        assert claude_result["model"] == "claude-result"
    
    def test_cache_access_count_incremented(self, cache):
        """Test that access count increments on get."""
        # Arrange
        file_hash = hashlib.sha256(b"test").hexdigest()
        cache.set(file_hash, "gpt-4", {"test": "data"})
        
        initial_stats = cache.get_stats()
        
        # Act
        cache.get(file_hash, "gpt-4")
        cache.get(file_hash, "gpt-4")
        
        final_stats = cache.get_stats()
        
        # Assert
        assert final_stats["total_accesses"] > initial_stats["total_accesses"]
    
    def test_clear_all(self, cache):
        """Test clearing all cache entries."""
        # Arrange
        for i in range(3):
            file_hash = hashlib.sha256(f"file{i}".encode()).hexdigest()
            cache.set(file_hash, "gpt-4", {"index": i})
        
        # Act
        deleted = cache.clear_all()
        stats = cache.get_stats()
        
        # Assert
        assert deleted == 3
        assert stats["total_entries"] == 0
    
    def test_clear_old_entries(self, cache):
        """Test clearing old cache entries."""
        # Arrange
        file_hash = hashlib.sha256(b"recent").hexdigest()
        cache.set(file_hash, "gpt-4", {"test": "recent"})
        
        # Manually set old timestamp for another entry
        file_hash_old = hashlib.sha256(b"old").hexdigest()
        cache.set(file_hash_old, "gpt-4", {"test": "old"})
        
        # Update old entry timestamp
        conn = sqlite3.connect(str(cache.db_path))
        old_time = (datetime.now() - timedelta(days=10)).isoformat()
        conn.execute(
            "UPDATE llm_cache SET created_at = ? WHERE file_hash = ?",
            (old_time, file_hash_old)
        )
        conn.commit()
        conn.close()
        
        # Act
        deleted = cache.clear_old(days=5)
        
        # Assert
        assert deleted == 1
        assert cache.get(file_hash, "gpt-4") is not None  # Recent still there
    
    def test_get_stats(self, cache):
        """Test getting cache statistics."""
        # Arrange
        for i in range(3):
            file_hash = hashlib.sha256(f"file{i}".encode()).hexdigest()
            cache.set(file_hash, "gpt-4", {"index": i})
        
        # Access one entry multiple times
        file_hash = hashlib.sha256(b"file0").hexdigest()
        cache.get(file_hash, "gpt-4")
        cache.get(file_hash, "gpt-4")
        
        # Act
        stats = cache.get_stats()
        
        # Assert
        assert stats["total_entries"] == 3
        assert stats["unique_files"] == 3
        assert stats["total_accesses"] >= 5  # 3 initial + 2 more
    
    def test_compute_file_hash(self, temp_dir):
        """Test file hash computation."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Act
        hash1 = LLMCache.compute_file_hash(str(test_file))
        hash2 = LLMCache.compute_file_hash(str(test_file))
        
        # Assert
        assert len(hash1) == 64  # SHA-256 hex
        assert hash1 == hash2
    
    def test_compute_file_hash_different_content(self, temp_dir):
        """Test different content produces different hashes."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Act
        hash1 = LLMCache.compute_file_hash(str(file1))
        hash2 = LLMCache.compute_file_hash(str(file2))
        
        # Assert
        assert hash1 != hash2
    
    def test_cache_large_result(self, cache):
        """Test caching large analysis results."""
        # Arrange
        file_hash = hashlib.sha256(b"large").hexdigest()
        large_result = {
            "category": "documents",
            "detailed_analysis": "x" * 10000,
            "suggestions": [f"suggestion_{i}" for i in range(100)]
        }
        
        # Act
        cache.set(file_hash, "gpt-4", large_result)
        result = cache.get(file_hash, "gpt-4")
        
        # Assert
        assert result is not None
        assert len(result["detailed_analysis"]) == 10000
        assert len(result["suggestions"]) == 100
    
    def test_cache_with_special_chars(self, cache):
        """Test caching results with special characters."""
        # Arrange
        file_hash = hashlib.sha256(b"special").hexdigest()
        special_result = {
            "text": "Special chars: émojis 🎉 quotes \"test\"",
            "unicode": "日本語テキスト"
        }
        
        # Act
        cache.set(file_hash, "gpt-4", special_result)
        result = cache.get(file_hash, "gpt-4")
        
        # Assert
        assert result["text"] == special_result["text"]
        assert result["unicode"] == special_result["unicode"]
    
    def test_database_creates_directories(self, temp_dir):
        """Test that cache creates parent directories."""
        # Arrange - create cache with nested path
        nested_path = temp_dir / "nonexistent" / "subdir" / "cache.db"
        
        # Act - should create directories automatically
        cache = LLMCache(nested_path)
        
        # Assert - directories and file should exist
        assert nested_path.exists()
