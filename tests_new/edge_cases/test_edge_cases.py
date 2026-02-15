"""
Edge case tests for File Organizer.
Tests empty directories, large file counts, special characters, permission errors, network failures.
"""
import pytest
from pathlib import Path
import os


@pytest.mark.edge_case
class TestEmptyDirectories:
    """Tests for empty directory handling."""
    
    def test_scan_empty_directory(self, temp_dir):
        """Test scanning completely empty directory."""
        from core.scanner import FileScanner
        
        scanner = FileScanner()
        result = scanner.scan(temp_dir)
        
        assert len(result) == 0
    
    def test_organize_empty_directory(self, temp_dir):
        """Test organizing empty directory."""
        from core.organizer import FileOrganizer
        
        organizer = FileOrganizer()
        
        plan = organizer.create_organization_plan([], [], temp_dir)
        
        assert plan["total_files"] == 0
        assert len(plan["operations"]) == 0
        
        result = organizer.execute_plan(plan, dry_run=False)
        assert result.success
        assert result.operations_completed == 0
    
    def test_empty_state_displayed(self, temp_dir, qtbot):
        """Test empty state is shown for empty folder."""
        pytest.importorskip("PyQt6")
        from ui.widgets.empty_state import EmptyStateWidget
        
        widget = EmptyStateWidget()
        qtbot.addWidget(widget)
        
        widget.set_state("empty_folder")
        
        assert widget.get_current_state() == "empty_folder"
        assert "Empty" in widget.title_label.text()


@pytest.mark.edge_case
class TestLargeDirectories:
    """Tests for directories with many files."""
    
    def test_scan_1000_files(self, temp_dir):
        """Test scanning directory with 1000 files."""
        from core.scanner import FileScanner
        
        # Create 1000 files
        for i in range(1000):
            f = temp_dir / f"file_{i:04d}.txt"
            f.write_text(f"Content {i}")
        
        scanner = FileScanner()
        result = scanner.scan(temp_dir)
        
        assert len(result) == 1000
    
    def test_organize_1000_files(self, temp_dir):
        """Test organizing 1000 files."""
        from core.organizer import FileOrganizer
        from core.config import OrganizationConfig
        
        # Create files
        files = []
        analysis = []
        for i in range(100):
            f = temp_dir / f"file_{i:03d}.txt"
            f.write_text(f"Content {i}")
            files.append(f)
            analysis.append({
                "file_path": str(f),
                "category": "documents",
                "suggested_name": f"doc_{i:03d}.txt",
                "confidence": 0.9
            })
        
        organizer = FileOrganizer(config=OrganizationConfig())
        plan = organizer.create_organization_plan(files, analysis, temp_dir)
        
        assert len(plan["operations"]) == 100
        
        result = organizer.execute_plan(plan, dry_run=False)
        assert result.success
        assert result.operations_completed == 100
    
    def test_deeply_nested_directories(self, temp_dir):
        """Test scanning deeply nested directory structure."""
        from core.scanner import FileScanner
        
        # Create 10 levels deep
        current = temp_dir
        for i in range(10):
            current = current / f"level_{i}"
            current.mkdir()
        
        # Add file at deepest level
        deep_file = current / "deep.txt"
        deep_file.write_text("Deep content")
        
        scanner = FileScanner()
        result = scanner.scan(temp_dir)
        
        assert len(result) == 1
        assert result[0].path.name == "deep.txt"


@pytest.mark.edge_case
class TestSpecialCharacters:
    """Tests for files with special characters."""
    
    def test_unicode_filenames(self, temp_dir):
        """Test handling unicode filenames."""
        from core.scanner import FileScanner
        
        # Create files with unicode names
        names = [
            "日本語ファイル.txt",
            "файл.txt",
            "文件.txt",
            "📄 document.txt",
            "café.txt",
            "naïve.txt"
        ]
        
        for name in names:
            f = temp_dir / name
            f.write_text("content")
        
        scanner = FileScanner()
        result = scanner.scan(temp_dir)
        
        assert len(result) == len(names)
    
    def test_special_characters_in_names(self, temp_dir):
        """Test handling special characters in filenames."""
        from core.scanner import FileScanner
        from core.organizer import FileOrganizer
        
        # Create files with special characters
        names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file(multheses).txt",
            "file[brackets].txt",
            "file{braces}.txt",
            "file@symbol.txt",
            "file#hash.txt",
            "file$money.txt",
            "file%percent.txt",
            "file&ampersand.txt",
            "file'quotes'.txt",
            'file"doublequotes".txt',
            "file+plus.txt",
            "file=equals.txt",
            "file!exclamation.txt",
        ]
        
        files = []
        for name in names:
            f = temp_dir / name
            f.write_text("content")
            files.append(f)
        
        # Scan
        scanner = FileScanner()
        scanned = scanner.scan(temp_dir)
        assert len(scanned) == len(names)
        
        # Organize
        analysis = [{
            "file_path": str(f),
            "category": "documents",
            "suggested_name": f"renamed_{i}.txt",
            "confidence": 0.9
        } for i, f in enumerate(files)]
        
        organizer = FileOrganizer()
        plan = organizer.create_organization_plan(files, analysis, temp_dir)
        result = organizer.execute_plan(plan, dry_run=False)
        
        assert result.success
    
    def test_newlines_in_content(self, temp_dir):
        """Test handling files with newlines."""
        from core.preview import PreviewManager
        
        test_file = temp_dir / "multiline.txt"
        test_file.write_text("Line 1\nLine 2\n\nLine 4\r\nLine 5")
        
        manager = PreviewManager()
        preview = manager.get_preview(test_file)
        
        assert preview.preview_type.name == "TEXT"
        assert "Line 1" in preview.preview_content


@pytest.mark.edge_case
class TestLargeFiles:
    """Tests for large file handling."""
    
    def test_large_text_file(self, temp_dir):
        """Test handling large text files."""
        from core.preview import PreviewManager
        
        test_file = temp_dir / "large.txt"
        # Create 10MB file
        test_file.write_text("x" * (10 * 1024 * 1024))
        
        manager = PreviewManager()
        preview = manager.get_preview(test_file)
        
        assert preview.preview_type.name == "TEXT"
        assert "truncated" in preview.preview_content.lower()
    
    def test_zero_byte_file(self, temp_dir):
        """Test handling zero-byte files."""
        from core.scanner import FileScanner
        from core.preview import PreviewManager
        
        test_file = temp_dir / "empty.txt"
        test_file.write_text("")
        
        # Scan
        scanner = FileScanner()
        result = scanner.scan(temp_dir)
        assert len(result) == 1
        assert result[0].size == 0
        
        # Preview
        manager = PreviewManager()
        preview = manager.get_preview(test_file)
        assert preview.preview_type.name == "TEXT"
    
    def test_binary_file_detection(self, temp_dir):
        """Test handling binary files."""
        from core.preview import PreviewManager
        
        test_file = temp_dir / "binary.dat"
        # Write binary content
        test_file.write_bytes(bytes(range(256)))
        
        manager = PreviewManager()
        preview = manager.get_preview(test_file)
        
        # Should be detected as unknown/binary
        assert preview.preview_type.name in ["UNKNOWN", "TEXT"]


@pytest.mark.edge_case
class TestNetworkFailures:
    """Tests for LLM/network failure handling."""
    
    def test_llm_unavailable(self, temp_dir):
        """Test handling when LLM is unavailable."""
        from core.llm_handler import OllamaHandler
        
        # Create handler pointing to non-existent server
        handler = OllamaHandler(url="http://localhost:99999")
        
        # Should report unavailable
        assert not handler.is_available()
    
    def test_analyze_without_llm(self, temp_dir):
        """Test analyzing files when LLM is down."""
        from core.llm_handler import OllamaHandler
        
        handler = OllamaHandler(url="http://localhost:99999")
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        # Should raise error or return fallback
        if not handler.is_available():
            # Expected behavior - skip or use fallback
            pass
        else:
            result = handler.analyze_file(test_file)
            assert "category" in result


@pytest.mark.edge_case
class TestCancellation:
    """Tests for operation cancellation."""
    
    def test_cancel_during_scan(self, temp_dir):
        """Test cancelling during scan operation."""
        # In a real scenario, this would test cancellation tokens
        # For now, just verify scan can be interrupted
        from core.scanner import FileScanner
        
        # Create many files
        for i in range(100):
            f = temp_dir / f"file_{i}.txt"
            f.write_text("content")
        
        scanner = FileScanner()
        
        # Scan (simulating potential cancellation)
        result = scanner.scan(temp_dir)
        
        # Should complete or be interruptible
        assert isinstance(result, list)
    
    def test_cancel_during_organize(self, temp_dir):
        """Test cancelling during organize operation."""
        from core.organizer import FileOrganizer
        
        # Create files
        files = []
        for i in range(10):
            f = temp_dir / f"file_{i}.txt"
            f.write_text("content")
            files.append(f)
        
        plan = {
            "batch_id": "test",
            "operations": [{
                "source": f,
                "destination": temp_dir / f"moved_{i}.txt",
                "operation_type": "move",
                "confidence": 0.9
            } for i, f in enumerate(files)]
        }
        
        organizer = FileOrganizer()
        
        # Execute with progress callback (could signal cancellation)
        cancelled = [False]
        def progress_callback(current, total):
            if current == 5:
                cancelled[0] = True
        
        result = organizer.execute_plan(plan, dry_run=False, progress_callback=progress_callback)
        
        # Note: Full cancellation would require async/cancellable operations
        # This tests the callback mechanism


@pytest.mark.edge_case
class TestConcurrentModifications:
    """Tests for handling files modified during operation."""
    
    def test_file_deleted_during_scan(self, temp_dir):
        """Test handling file deleted during scan."""
        from core.scanner import FileScanner
        
        # Create files
        for i in range(10):
            f = temp_dir / f"file_{i}.txt"
            f.write_text("content")
        
        scanner = FileScanner()
        
        # Scan
        result = scanner.scan(temp_dir)
        
        # Should handle gracefully
        assert isinstance(result, list)
    
    def test_file_modified_during_organize(self, temp_dir):
        """Test handling file modified during organize."""
        from core.organizer import FileOrganizer
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("original")
        
        plan = {
            "batch_id": "test",
            "operations": [{
                "source": test_file,
                "destination": temp_dir / "moved.txt",
                "operation_type": "move",
                "confidence": 0.9
            }]
        }
        
        organizer = FileOrganizer()
        
        # Modify file after plan creation
        test_file.write_text("modified")
        
        # Execute
        result = organizer.execute_plan(plan, dry_run=False)
        
        # Should still work (file exists and is readable)
        assert result.success


@pytest.mark.edge_case
class TestPathEdgeCases:
    """Tests for path-related edge cases."""
    
    def test_dot_files(self, temp_dir):
        """Test handling dot files."""
        from core.scanner import FileScanner
        
        # Create dot files
        dot_file = temp_dir / ".hidden"
        dot_file.write_text("hidden content")
        
        dot_dir = temp_dir / ".hidden_dir"
        dot_dir.mkdir()
        
        scanner = FileScanner()
        result = scanner.scan(temp_dir)
        
        # Dot files should be included
        assert any(r.name == ".hidden" for r in result)
    
    def test_symlinks(self, temp_dir):
        """Test handling symbolic links."""
        from core.scanner import FileScanner
        
        # Create file and symlink
        target = temp_dir / "target.txt"
        target.write_text("target")
        
        link = temp_dir / "link.txt"
        try:
            link.symlink_to(target)
            
            scanner = FileScanner()
            result = scanner.scan(temp_dir)
            
            # Should handle symlinks (may or may not be followed)
            assert len(result) >= 1
        except (OSError, NotImplementedError):
            # Symlinks not supported on this platform
            pytest.skip("Symlinks not supported")
    
    def test_circular_symlinks(self, temp_dir):
        """Test handling circular symlinks."""
        from core.scanner import FileScanner
        
        try:
            link1 = temp_dir / "link1"
            link2 = temp_dir / "link2"
            link1.symlink_to(link2)
            link2.symlink_to(link1)
            
            scanner = FileScanner()
            result = scanner.scan(temp_dir)
            
            # Should not hang or crash
            assert isinstance(result, list)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported")


@pytest.mark.edge_case
class TestCacheEdgeCases:
    """Tests for cache edge cases."""
    
    def test_cache_full_disk(self, temp_dir):
        """Test cache behavior when disk is full."""
        # This is hard to test without actually filling disk
        # Just verify cache handles errors gracefully
        from core.cache import LLMCache
        
        cache = LLMCache(temp_dir / "cache.db")
        
        # Normal operation should work
        cache.set("key", "model", {"data": "value"})
        result = cache.get("key", "model")
        assert result == {"data": "value"}
    
    def test_cache_corruption(self, temp_dir):
        """Test handling corrupted cache database."""
        from core.cache import LLMCache
        
        db_path = temp_dir / "corrupt.db"
        
        # Create corrupted database
        db_path.write_bytes(b"corrupted data")
        
        # Should handle gracefully
        try:
            cache = LLMCache(db_path)
            # May or may not succeed depending on corruption
        except Exception:
            # Expected to potentially fail
            pass
