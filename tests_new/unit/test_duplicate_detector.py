"""
Unit tests for DuplicateDetector module.
"""
import pytest
from pathlib import Path
import hashlib

from core.duplicate_detector import (
    DuplicateDetector, DuplicateGroup, DuplicateDetectionResult, DuplicateType
)


@pytest.mark.unit
class TestDuplicateGroup:
    """Tests for DuplicateGroup dataclass."""
    
    def test_group_creation(self):
        """Test creating a duplicate group."""
        group = DuplicateGroup(
            group_id="test-group",
            duplicate_type=DuplicateType.EXACT,
            files=[Path("/path/to/file1.txt")],
            hash_value="abc123"
        )
        
        assert group.group_id == "test-group"
        assert group.duplicate_type == DuplicateType.EXACT
        assert len(group.files) == 1
    
    def test_add_file(self):
        """Test adding file to group."""
        group = DuplicateGroup(
            group_id="test",
            duplicate_type=DuplicateType.EXACT
        )
        
        group.add_file(Path("/path/to/file1.txt"))
        group.add_file(Path("/path/to/file2.txt"))
        
        assert len(group.files) == 2
    
    def test_add_duplicate_file_ignored(self):
        """Test that adding duplicate file is ignored."""
        group = DuplicateGroup(
            group_id="test",
            duplicate_type=DuplicateType.EXACT
        )
        
        path = Path("/path/to/file1.txt")
        group.add_file(path)
        group.add_file(path)  # Add again
        
        assert len(group.files) == 1
    
    def test_remove_file(self, temp_dir):
        """Test removing file from group."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file1.write_text("content")
        
        group = DuplicateGroup(
            group_id="test",
            duplicate_type=DuplicateType.EXACT,
            files=[file1]
        )
        
        # Act
        result = group.remove_file(file1)
        
        # Assert
        assert result is True
        assert len(group.files) == 0
    
    def test_get_total_size(self, temp_dir):
        """Test calculating total size of group."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("x" * 100)
        file2.write_text("x" * 200)
        
        group = DuplicateGroup(
            group_id="test",
            duplicate_type=DuplicateType.EXACT,
            files=[file1, file2]
        )
        
        # Act
        total = group.get_total_size()
        
        # Assert
        assert total == 300
    
    def test_get_wasted_space(self, temp_dir):
        """Test calculating wasted space in group."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("x" * 1000)
        file2.write_text("x" * 1000)
        
        group = DuplicateGroup(
            group_id="test",
            duplicate_type=DuplicateType.EXACT,
            files=[file1, file2]
        )
        
        # Act
        wasted = group.get_wasted_space()
        
        # Assert - wasted = size * (count - 1)
        assert wasted == 1000
    
    def test_get_wasted_space_single_file(self, temp_dir):
        """Test wasted space with single file."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file1.write_text("content")
        
        group = DuplicateGroup(
            group_id="test",
            duplicate_type=DuplicateType.EXACT,
            files=[file1]
        )
        
        # Act
        wasted = group.get_wasted_space()
        
        # Assert - no waste with single file
        assert wasted == 0


@pytest.mark.unit
class TestDuplicateDetectionResult:
    """Tests for DuplicateDetectionResult dataclass."""
    
    def test_empty_result(self):
        """Test empty result."""
        result = DuplicateDetectionResult()
        
        assert result.total_duplicates == 0
        assert result.total_wasted_space == 0
        assert result.group_count == 0
    
    def test_result_with_groups(self, temp_dir):
        """Test result with duplicate groups."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "file3.txt"
        file1.write_text("x" * 100)
        file2.write_text("x" * 100)
        file3.write_text("x" * 100)
        
        group1 = DuplicateGroup(
            group_id="g1",
            duplicate_type=DuplicateType.EXACT,
            files=[file1, file2]
        )
        group2 = DuplicateGroup(
            group_id="g2",
            duplicate_type=DuplicateType.EXACT,
            files=[file3]
        )
        
        # Act
        result = DuplicateDetectionResult(
            exact_duplicates=[group1, group2],
            scanned_files=3
        )
        
        # Assert
        assert result.total_duplicates == 3
        assert result.group_count == 2


@pytest.mark.unit
class TestDuplicateDetector:
    """Tests for DuplicateDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create duplicate detector."""
        return DuplicateDetector()
    
    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = DuplicateDetector(
            hash_algorithm="sha256",
            chunk_size=4096
        )
        
        assert detector.hash_algorithm == "sha256"
        assert detector.chunk_size == 4096
    
    def test_compute_file_hash(self, detector, temp_dir):
        """Test computing file hash."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Act
        hash1 = detector._compute_file_hash(test_file)
        hash2 = detector._compute_file_hash(test_file)
        
        # Assert
        assert hash1 is not None
        assert len(hash1) == 128  # blake2b hex is 128 chars
        assert hash1 == hash2  # Same file = same hash
    
    def test_compute_file_hash_different_content(self, detector, temp_dir):
        """Test that different content produces different hashes."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Act
        hash1 = detector._compute_file_hash(file1)
        hash2 = detector._compute_file_hash(file2)
        
        # Assert
        assert hash1 != hash2
    
    def test_compute_file_hash_caching(self, detector, temp_dir):
        """Test that hashes are cached."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Act
        hash1 = detector._compute_file_hash(test_file)
        hash2 = detector._compute_file_hash(test_file)  # Should use cache
        
        # Assert
        assert test_file in detector._hash_cache
        assert hash1 == hash2
    
    def test_find_exact_duplicates(self, detector, temp_dir):
        """Test finding exact duplicates."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "file3.txt"
        file1.write_text("duplicate content")
        file2.write_text("duplicate content")  # Same content
        file3.write_text("different content")
        
        # Act
        result = detector.find_duplicates(
            [file1, file2, file3],
            detect_exact=True,
            detect_similar=False
        )
        
        # Assert
        assert len(result.exact_duplicates) == 1
        assert len(result.exact_duplicates[0].files) == 2
    
    def test_find_duplicates_with_progress(self, detector, temp_dir):
        """Test progress callback during duplicate detection."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        # Act
        detector.find_duplicates(
            [file1, file2],
            detect_exact=True,
            detect_similar=False,
            progress_callback=progress_callback
        )
        
        # Assert
        assert len(progress_calls) > 0
    
    def test_quick_check_duplicates(self, detector, temp_dir):
        """Test quick duplicate check for a single file."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "file3.txt"
        file1.write_text("same content")
        file2.write_text("same content")
        file3.write_text("different")
        
        # Act
        duplicates = detector.quick_check_duplicates(file1, [file2, file3])
        
        # Assert
        assert len(duplicates) == 1
        assert file2 in duplicates
    
    def test_delete_duplicates_dry_run(self, detector, temp_dir):
        """Test dry run deletion doesn't actually delete."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content")
        file2.write_text("content")
        
        group = DuplicateGroup(
            group_id="test",
            duplicate_type=DuplicateType.EXACT,
            files=[file1, file2]
        )
        
        # Act
        result = detector.delete_duplicates(group, keep_indices=[0], dry_run=True)
        
        # Assert
        assert file2.exists()  # Not actually deleted
        assert result["dry_run"] is True
        assert len(result["deleted"]) == 1
    
    def test_delete_duplicates_actual(self, detector, temp_dir):
        """Test actual file deletion."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content")
        file2.write_text("content")
        
        group = DuplicateGroup(
            group_id="test",
            duplicate_type=DuplicateType.EXACT,
            files=[file1, file2]
        )
        
        # Act
        result = detector.delete_duplicates(group, keep_indices=[0], dry_run=False)
        
        # Assert
        assert file1.exists()
        assert not file2.exists()
        assert len(result["deleted"]) == 1
    
    def test_delete_all_but_one(self, detector, temp_dir):
        """Test deleting all but one file."""
        # Arrange
        files = []
        for i in range(3):
            f = temp_dir / f"file{i}.txt"
            f.write_text("same content")
            files.append(f)
        
        group = DuplicateGroup(
            group_id="test",
            duplicate_type=DuplicateType.EXACT,
            files=files
        )
        
        # Act
        result = detector.delete_all_but_one(group, keep_index=0, dry_run=False)
        
        # Assert
        assert files[0].exists()
        assert not files[1].exists()
        assert not files[2].exists()
    
    def test_compare_files_identical(self, detector, temp_dir):
        """Test comparing identical files."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("identical content")
        file2.write_text("identical content")
        
        # Act
        result = detector.compare_files(file1, file2)
        
        # Assert
        assert result["identical"] is True
        assert result["same_size"] is True
    
    def test_compare_files_different(self, detector, temp_dir):
        """Test comparing different files."""
        # Arrange
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2 - longer")
        
        # Act
        result = detector.compare_files(file1, file2)
        
        # Assert
        assert result["identical"] is False
        assert result["same_size"] is False
    
    def test_clear_cache(self, detector, temp_dir):
        """Test clearing hash cache."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        detector._compute_file_hash(test_file)
        
        assert len(detector._hash_cache) > 0
        
        # Act
        detector.clear_cache()
        
        # Assert
        assert len(detector._hash_cache) == 0
    
    def test_find_duplicates_nonexistent_files(self, detector):
        """Test handling nonexistent files gracefully."""
        # Act
        result = detector.find_duplicates(
            [Path("/nonexistent/file1.txt"), Path("/nonexistent/file2.txt")],
            detect_exact=True,
            detect_similar=False
        )
        
        # Assert
        assert result.scanned_files == 2
        assert len(result.exact_duplicates) == 0
    
    def test_different_hash_algorithms(self, temp_dir):
        """Test different hash algorithms work."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Act
        md5_detector = DuplicateDetector(hash_algorithm="md5")
        sha256_detector = DuplicateDetector(hash_algorithm="sha256")
        blake2b_detector = DuplicateDetector(hash_algorithm="blake2b")
        
        md5_hash = md5_detector._compute_file_hash(test_file)
        sha256_hash = sha256_detector._compute_file_hash(test_file)
        blake2b_hash = blake2b_detector._compute_file_hash(test_file)
        
        # Assert - different algorithms produce different hash lengths
        assert len(md5_hash) == 32
        assert len(sha256_hash) == 64
        assert len(blake2b_hash) == 128
