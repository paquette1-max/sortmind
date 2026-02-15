"""
Unit tests for Scanner module.
"""
import pytest
from pathlib import Path

from core.scanner import FileScanner, ScannedFile


@pytest.mark.unit
class TestScannedFile:
    """Tests for ScannedFile dataclass."""
    
    def test_scanned_file_creation(self):
        """Test creating scanned file."""
        file = ScannedFile(
            path=Path("/test/file.txt"),
            name="file.txt",
            size=1024,
            mtime=1234567890.0
        )
        
        assert file.path == Path("/test/file.txt")
        assert file.name == "file.txt"
        assert file.size == 1024
        assert file.mtime == 1234567890.0
    
    def test_scanned_file_with_metadata(self):
        """Test scanned file with metadata."""
        file = ScannedFile(
            path=Path("/test/file.txt"),
            name="file.txt",
            size=1024,
            metadata={"mime_type": "text/plain"}
        )
        
        assert file.metadata["mime_type"] == "text/plain"


@pytest.mark.unit
class TestFileScanner:
    """Tests for FileScanner class."""
    
    @pytest.fixture
    def scanner(self):
        """Create file scanner."""
        return FileScanner()
    
    def test_scan_empty_directory(self, scanner, empty_directory):
        """Test scanning empty directory."""
        # Act
        results = scanner.scan(empty_directory)
        
        # Assert
        assert len(results) == 0
    
    def test_scan_single_file(self, scanner, temp_dir):
        """Test scanning directory with single file."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Act
        results = scanner.scan(temp_dir)
        
        # Assert
        assert len(results) == 1
        assert results[0].name == "test.txt"
        assert results[0].size > 0
    
    def test_scan_multiple_files(self, scanner, sample_files):
        """Test scanning directory with multiple files."""
        # Arrange
        scanner = FileScanner()
        
        # Act
        results = scanner.scan(sample_files[0].parent)
        
        # Assert
        assert len(results) == len(sample_files)
    
    def test_scan_nested_directories(self, scanner, temp_dir):
        """Test scanning nested directory structure."""
        # Arrange
        nested = temp_dir / "level1" / "level2" / "level3"
        nested.mkdir(parents=True)
        
        (temp_dir / "root.txt").write_text("root")
        (temp_dir / "level1" / "level1.txt").write_text("level1")
        (temp_dir / "level1" / "level2" / "level2.txt").write_text("level2")
        (nested / "level3.txt").write_text("level3")
        
        # Act
        results = scanner.scan(temp_dir)
        
        # Assert
        assert len(results) == 4
        paths = [r.path for r in results]
        assert any("root.txt" in str(p) for p in paths)
        assert any("level3.txt" in str(p) for p in paths)
    
    def test_scan_returns_scanned_file_objects(self, scanner, temp_dir):
        """Test that scan returns ScannedFile objects."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        # Act
        results = scanner.scan(temp_dir)
        
        # Assert
        assert len(results) == 1
        assert isinstance(results[0], ScannedFile)
        assert hasattr(results[0], 'path')
        assert hasattr(results[0], 'size')
        assert hasattr(results[0], 'mtime')
    
    def test_scan_with_config(self, temp_dir):
        """Test scanner with configuration."""
        # Arrange
        config = {"max_depth": 2}
        scanner = FileScanner(config=config)
        
        # Create nested structure
        (temp_dir / "file1.txt").write_text("content")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "file2.txt").write_text("content")
        
        # Act
        results = scanner.scan(temp_dir)
        
        # Assert - basic scan still works
        assert len(results) >= 1
    
    def test_scan_file_sizes(self, scanner, temp_dir):
        """Test that scanned files have correct sizes."""
        # Arrange
        small = temp_dir / "small.txt"
        large = temp_dir / "large.txt"
        small.write_text("x")
        large.write_text("x" * 1000)
        
        # Act
        results = scanner.scan(temp_dir)
        
        # Assert
        sizes = {r.name: r.size for r in results}
        assert sizes["small.txt"] == 1
        assert sizes["large.txt"] == 1000
    
    def test_scan_skips_directories_as_results(self, scanner, temp_dir):
        """Test that directories are not returned as results."""
        # Arrange
        (temp_dir / "file.txt").write_text("content")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "nested.txt").write_text("nested")
        
        # Act
        results = scanner.scan(temp_dir)
        
        # Assert
        for result in results:
            assert result.path.is_file() or not result.path.exists()
            # Should not have directory names as results
            assert result.name != "subdir"
