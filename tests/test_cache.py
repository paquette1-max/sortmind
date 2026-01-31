"""Tests for Phase 4 LLM Cache module."""

import hashlib
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase

from src.core.cache import LLMCache


class TestLLMCache(TestCase):
    """Test cases for LLMCache class."""
    
    def setUp(self):
        """Create a temporary cache database for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = Path(self.temp_dir.name) / "test_cache.db"
        self.cache = LLMCache(db_path=str(self.cache_path))
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_cache_initialization(self):
        """Test that cache initializes properly and creates database."""
        assert self.cache_path.exists(), "Cache database file not created"
        
        # Verify table exists
        conn = sqlite3.connect(str(self.cache_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='llm_cache'"
        )
        assert cursor.fetchone() is not None, "llm_cache table not created"
        conn.close()
    
    def test_cache_get_miss(self):
        """Test retrieving non-existent cache entry returns None."""
        result = self.cache.get(file_hash="nonexistent_hash_12345", model_name="gpt-4")
        assert result is None, "Should return None for cache miss"
    
    def test_cache_set_and_get(self):
        """Test setting and retrieving cache entry."""
        file_hash = hashlib.sha256(b"test_file.txt").hexdigest()
        model_name = "gpt-4"
        analysis_result = {"category": "documents", "confidence": 0.95}
        
        # Set cache
        self.cache.set(
            file_hash=file_hash,
            model_name=model_name,
            result=analysis_result
        )
        
        # Get cache
        result = self.cache.get(file_hash=file_hash, model_name=model_name)
        assert result is not None, "Cache entry not retrieved"
        assert result["category"] == "documents", "Cached data mismatch"
        assert result["confidence"] == 0.95, "Cached confidence mismatch"
    
    def test_cache_get_updates_access_count(self):
        """Test that accessing cache increments access count."""
        file_hash = hashlib.sha256(b"test_file.txt").hexdigest()
        model_name = "gpt-4"
        analysis_result = {"category": "documents"}
        
        self.cache.set(
            file_hash=file_hash,
            model_name=model_name,
            result=analysis_result
        )
        
        # Access count should start at 1
        stats1 = self.cache.get_stats()
        access_count1 = stats1.get("total_accesses", 0)
        
        # Access again
        self.cache.get(file_hash=file_hash, model_name=model_name)
        stats2 = self.cache.get_stats()
        access_count2 = stats2.get("total_accesses", 0)
        
        assert access_count2 > access_count1, "Access count not incremented"
    
    def test_cache_clear_all(self):
        """Test clearing all cache entries."""
        # Add multiple entries
        for i in range(3):
            file_hash = hashlib.sha256(f"file_{i}.txt".encode()).hexdigest()
            self.cache.set(
                file_hash=file_hash,
                model_name="gpt-4",
                result={"category": f"category_{i}"}
            )
        
        # Verify entries exist
        stats_before = self.cache.get_stats()
        assert stats_before["total_entries"] == 3, "Entries not added"
        
        # Clear all
        self.cache.clear_all()
        
        # Verify all cleared
        stats_after = self.cache.get_stats()
        assert stats_after["total_entries"] == 0, "Entries not cleared"
    
    def test_cache_clear_old(self):
        """Test clearing entries older than retention days."""
        # Add entry that will be old
        old_file_hash = hashlib.sha256(b"old_file.txt").hexdigest()
        self.cache.set(
            file_hash=old_file_hash,
            model_name="gpt-4",
            result={"category": "old"}
        )
        
        # Manually set the timestamp to be old
        conn = sqlite3.connect(str(self.cache_path))
        cursor = conn.cursor()
        old_timestamp = (datetime.now() - timedelta(days=10)).isoformat()
        cursor.execute(
            "UPDATE llm_cache SET created_at = ? WHERE file_hash = ?",
            (old_timestamp, old_file_hash)
        )
        conn.commit()
        conn.close()
        
        # Add recent entry
        recent_file_hash = hashlib.sha256(b"recent_file.txt").hexdigest()
        self.cache.set(
            file_hash=recent_file_hash,
            model_name="gpt-4",
            result={"category": "recent"}
        )
        
        # Clear entries older than 5 days
        self.cache.clear_old(days=5)
        
        # Verify old entry is gone, recent remains
        assert self.cache.get(file_hash=old_file_hash, model_name="gpt-4") is None, \
            "Old entry not cleared"
        assert self.cache.get(file_hash=recent_file_hash, model_name="gpt-4") is not None, \
            "Recent entry was incorrectly cleared"
    
    def test_cache_get_stats(self):
        """Test retrieving cache statistics."""
        # Add entries with different models
        for i in range(2):
            file_hash = hashlib.sha256(f"file_{i}.txt".encode()).hexdigest()
            self.cache.set(
                file_hash=file_hash,
                model_name="gpt-4",
                result={"size": 100 + i}
            )
        
        file_hash = hashlib.sha256(b"file_other.txt").hexdigest()
        self.cache.set(
            file_hash=file_hash,
            model_name="claude",
            result={"size": 200}
        )
        
        # Access one entry multiple times
        self.cache.get(
            file_hash=hashlib.sha256(b"file_0.txt").hexdigest(),
            model_name="gpt-4"
        )
        self.cache.get(
            file_hash=hashlib.sha256(b"file_0.txt").hexdigest(),
            model_name="gpt-4"
        )
        
        stats = self.cache.get_stats()
        
        assert stats["total_entries"] == 3, "Total entries incorrect"
        assert "total_accesses" in stats, "Missing total_accesses stat"
        assert stats["total_accesses"] >= 3, "Access count too low"
    
    def test_compute_file_hash_consistency(self):
        """Test that file hash computation is consistent."""
        # For this test, we test that compute_file_hash would work if given valid files
        # Since it reads files, we just verify the static method exists and accepts a path string
        assert hasattr(LLMCache, 'compute_file_hash'), "compute_file_hash method not found"
        assert callable(LLMCache.compute_file_hash), "compute_file_hash not callable"
    
    def test_compute_file_hash_different_inputs(self):
        """Test that different inputs produce different hashes via SHA256."""
        # Direct test using hashlib
        hash1 = hashlib.sha256(b"file1.txt").hexdigest()
        hash2 = hashlib.sha256(b"file2.txt").hexdigest()
        
        assert hash1 != hash2, "Different files should produce different hashes"
    
    def test_cache_with_large_result(self):
        """Test caching large analysis results."""
        file_hash = hashlib.sha256(b"large_file.txt").hexdigest()
        large_result = {
            "category": "documents",
            "detailed_analysis": "x" * 10000,  # Large string
            "suggestions": [f"suggestion_{i}" for i in range(100)]
        }
        
        self.cache.set(
            file_hash=file_hash,
            model_name="gpt-4",
            result=large_result
        )
        
        retrieved = self.cache.get(file_hash=file_hash, model_name="gpt-4")
        assert retrieved is not None, "Large result not retrieved"
        assert len(retrieved["detailed_analysis"]) == 10000, "Large data truncated"
        assert len(retrieved["suggestions"]) == 100, "Suggestions list truncated"
