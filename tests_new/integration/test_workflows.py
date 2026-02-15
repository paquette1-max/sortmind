"""
Integration tests for File Organizer.
Tests full scan → analyze → organize workflow.
"""
import pytest
from pathlib import Path
import shutil
from unittest.mock import Mock, patch


@pytest.mark.integration
class TestFullWorkflow:
    """Tests for complete file organization workflow."""
    
    def test_scan_analyze_organize_workflow(self, temp_dir, mock_llm_handler):
        """Test complete workflow from scan to organize."""
        # Arrange
        from core.scanner import FileScanner
        from core.organizer import FileOrganizer
        from core.config import OrganizationConfig
        
        # Create test files
        for i in range(3):
            f = temp_dir / f"document_{i}.txt"
            f.write_text(f"Document content {i}")
        
        # Step 1: Scan
        scanner = FileScanner()
        scanned_files = scanner.scan(temp_dir)
        assert len(scanned_files) == 3
        
        # Step 2: Analyze (mock LLM)
        analysis_results = []
        for scanned in scanned_files:
            result = mock_llm_handler.analyze_file(scanned.path)
            result["file_path"] = str(scanned.path)
            analysis_results.append(result)
        
        # Step 3: Create organization plan
        config = OrganizationConfig()
        organizer = FileOrganizer(config=config)
        
        # Extract paths from scanned files (organizer expects paths, not ScannedFile objects)
        file_paths = [s.path for s in scanned_files]
        
        plan = organizer.create_organization_plan(
            file_paths,
            analysis_results,
            temp_dir
        )
        
        assert len(plan["operations"]) == 3
        
        # Step 4: Execute plan (dry run first)
        result = organizer.execute_plan(plan, dry_run=True)
        assert result.success
        
        # Verify files not moved
        for i in range(3):
            assert (temp_dir / f"document_{i}.txt").exists()
        
        # Step 5: Execute plan (actual)
        result = organizer.execute_plan(plan, dry_run=False)
        assert result.success
        
        # Verify files were moved
        for i in range(3):
            assert not (temp_dir / f"document_{i}.txt").exists()
    
    def test_workflow_with_undo(self, temp_dir, mock_llm_handler):
        """Test workflow with undo functionality."""
        from core.scanner import FileScanner
        from core.organizer import FileOrganizer
        from core.undo_manager import UndoManager
        from core.config import OrganizationConfig
        
        # Setup
        undo_manager = UndoManager(temp_dir / "undo.db")
        config = OrganizationConfig()
        organizer = FileOrganizer(config=config, undo_manager=undo_manager)
        
        # Create file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        original_path = str(test_file)
        
        # Scan and analyze
        scanner = FileScanner()
        scanned = scanner.scan(temp_dir)
        
        analysis = [{
            "file_path": str(test_file),
            "category": "documents",
            "suggested_name": "moved.txt",
            "confidence": 0.95
        }]
        
        # Create and execute plan - extract paths from scanned files
        file_paths = [s.path for s in scanned]
        plan = organizer.create_organization_plan(file_paths, analysis, temp_dir)
        result = organizer.execute_plan(plan, dry_run=False)
        
        assert result.success
        
        # Verify file was moved
        assert not test_file.exists()
        moved_file = temp_dir / "documents" / "moved.txt"
        assert moved_file.exists()
        
        # Undo
        undo_result = undo_manager.undo_last()
        assert undo_result.success
        
        # Verify file is back
        assert test_file.exists()
    
    def test_workflow_with_backup(self, temp_dir, mock_llm_handler):
        """Test workflow with backup functionality."""
        from core.scanner import FileScanner
        from core.organizer import FileOrganizer
        from core.backup import BackupManager, BackupStrategy
        from core.config import OrganizationConfig
        
        # Setup
        backup_manager = BackupManager(temp_dir / "backups", BackupStrategy.COPY)
        config = OrganizationConfig()
        organizer = FileOrganizer(config=config, backup_manager=backup_manager)
        
        # Create file
        test_file = temp_dir / "important.txt"
        test_file.write_text("important content")
        
        # Scan and analyze
        scanner = FileScanner()
        scanned = scanner.scan(temp_dir)
        
        analysis = [{
            "file_path": str(test_file),
            "category": "documents",
            "suggested_name": "organized.txt",
            "confidence": 0.95
        }]
        
        # Execute - extract paths from scanned files
        file_paths = [s.path for s in scanned]
        plan = organizer.create_organization_plan(file_paths, analysis, temp_dir)
        result = organizer.execute_plan(plan, dry_run=False)
        
        assert result.success
        
        # Verify backup was created
        backups = backup_manager.list_backups()
        assert len(backups) >= 1
    
    def test_workflow_with_rules(self, temp_dir):
        """Test workflow with custom rules."""
        from core.scanner import FileScanner
        from core.rules_engine import RulesEngine, OrganizationRule, RuleType, RuleOperator
        from core.organizer import FileOrganizer
        from core.config import OrganizationConfig
        
        # Setup rules engine
        rules_engine = RulesEngine()
        rules_engine.add_rule(OrganizationRule(
            id="txt-rule",
            name="Text Files",
            rule_type=RuleType.EXTENSION,
            operator=RuleOperator.EQUALS,
            value=".txt",
            target_category="text_files"
        ))
        
        # Create files
        test_file = temp_dir / "doc.txt"
        test_file.write_text("content")
        
        # Evaluate with rules
        match = rules_engine.evaluate_file(test_file)
        assert match.matched
        assert match.target_category == "text_files"
        
        # Create analysis from rules
        analysis = [{
            "file_path": str(test_file),
            "category": match.target_category,
            "suggested_name": test_file.name,
            "confidence": match.confidence
        }]
        
        # Execute plan - extract paths from scanned files
        scanner = FileScanner()
        scanned = scanner.scan(temp_dir)
        file_paths = [s.path for s in scanned]
        
        organizer = FileOrganizer(config=OrganizationConfig())
        plan = organizer.create_organization_plan(file_paths, analysis, temp_dir)
        
        assert plan["operations"][0]["destination"].parent.name == "text_files"
    
    def test_workflow_with_cache(self, temp_dir):
        """Test workflow with LLM caching."""
        from core.cache import LLMCache
        
        # Setup cache
        cache = LLMCache(temp_dir / "cache.db")
        
        # Simulate analysis result
        file_hash = "abc123"
        model_name = "gpt-4"
        result = {"category": "documents", "confidence": 0.95}
        
        # Store in cache
        cache.set(file_hash, model_name, result)
        
        # Retrieve from cache
        cached = cache.get(file_hash, model_name)
        assert cached == result
        
        # Verify cache hit
        stats = cache.get_stats()
        assert stats["total_entries"] == 1
    
    def test_duplicate_detection_workflow(self, temp_dir):
        """Test duplicate detection workflow."""
        from core.duplicate_detector import DuplicateDetector
        
        # Create duplicate files
        file1 = temp_dir / "original.txt"
        file2 = temp_dir / "copy.txt"
        content = "duplicate content"
        file1.write_text(content)
        file2.write_text(content)
        
        # Detect duplicates
        detector = DuplicateDetector()
        result = detector.find_duplicates([file1, file2])
        
        assert len(result.exact_duplicates) == 1
        assert len(result.exact_duplicates[0].files) == 2
    
    def test_workflow_with_progress_callback(self, temp_dir, mock_llm_handler):
        """Test workflow with progress tracking."""
        from core.scanner import FileScanner
        from core.organizer import FileOrganizer
        from core.config import OrganizationConfig
        
        # Create files
        for i in range(5):
            f = temp_dir / f"file_{i}.txt"
            f.write_text(f"content {i}")
        
        # Track progress
        progress_updates = []
        def progress_callback(current, total):
            progress_updates.append((current, total))
        
        # Scan
        scanner = FileScanner()
        scanned = scanner.scan(temp_dir)
        
        # Analyze
        analysis = [{
            "file_path": str(s.path),
            "category": "documents",
            "confidence": 0.9
        } for s in scanned]
        
        # Execute with progress - extract paths from scanned files
        file_paths = [s.path for s in scanned]
        organizer = FileOrganizer(config=OrganizationConfig())
        plan = organizer.create_organization_plan(file_paths, analysis, temp_dir)
        result = organizer.execute_plan(plan, dry_run=False, progress_callback=progress_callback)
        
        assert result.success
        assert len(progress_updates) == 5
        assert progress_updates[-1] == (5, 5)


@pytest.mark.integration
class TestDatabaseIntegration:
    """Tests for database integration."""
    
    def test_undo_manager_database(self, temp_dir):
        """Test undo manager database operations."""
        from core.undo_manager import UndoManager
        
        db_path = temp_dir / "undo.db"
        manager = UndoManager(db_path)
        
        # Record operation
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test")
        
        manager.record_operation(
            batch_id="test-batch",
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        # Verify in database
        history = manager.get_history()
        assert len(history) == 1
        assert history[0].batch_id == "test-batch"
    
    def test_cache_database(self, temp_dir):
        """Test cache database operations."""
        from core.cache import LLMCache
        
        db_path = temp_dir / "cache.db"
        cache = LLMCache(db_path)
        
        # Store and retrieve
        cache.set("hash1", "model1", {"result": "test"})
        result = cache.get("hash1", "model1")
        
        assert result == {"result": "test"}
        
        # Verify database file
        assert db_path.exists()


@pytest.mark.integration
class TestErrorHandling:
    """Tests for error handling in workflows."""
    
    def test_organize_nonexistent_file(self, temp_dir):
        """Test organizing nonexistent file."""
        from core.organizer import FileOrganizer
        
        organizer = FileOrganizer()
        
        plan = {
            "batch_id": "test",
            "operations": [{
                "source": temp_dir / "nonexistent.txt",
                "destination": temp_dir / "output.txt",
                "operation_type": "move",
                "confidence": 0.9
            }]
        }
        
        result = organizer.execute_plan(plan, dry_run=False)
        
        assert not result.success
        assert result.operations_failed == 1
    
    def test_organize_permission_error(self, temp_dir):
        """Test handling permission errors."""
        from core.organizer import FileOrganizer
        
        organizer = FileOrganizer()
        
        # Try to organize to system directory (should fail validation)
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        plan = {
            "batch_id": "test",
            "operations": [{
                "source": test_file,
                "destination": Path("/System/test.txt"),
                "operation_type": "move",
                "confidence": 0.9
            }]
        }
        
        errors = organizer.validate_plan(plan)
        assert any("system" in e.lower() for e in errors)
    
    def test_scan_permission_denied(self, temp_dir):
        """Test scanning directory with permission issues."""
        from core.scanner import FileScanner
        
        scanner = FileScanner()
        
        # This should handle permission errors gracefully
        # (in practice, we'd need restricted permissions to test this)
        result = scanner.scan(temp_dir)
        assert isinstance(result, list)


@pytest.mark.integration
class TestConcurrentOperations:
    """Tests for concurrent/parallel operations."""
    
    def test_multiple_batches(self, temp_dir):
        """Test handling multiple batches."""
        from core.undo_manager import UndoManager
        import shutil
        
        manager = UndoManager(temp_dir / "undo.db")
        
        # Record multiple batches - actually move files so undo can work
        for i in range(3):
            source = temp_dir / f"file_{i}.txt"
            target = temp_dir / f"moved_{i}.txt"
            source.write_text(f"content {i}")
            
            # Actually move the file
            shutil.move(str(source), str(target))
            
            manager.record_operation(
                batch_id=f"batch-{i}",
                operation_type="move",
                source_path=source,
                target_path=target
            )
        
        # Get history should return all
        history = manager.get_history()
        assert len(history) == 3
        
        # Undo last should undo most recent (target file exists)
        result = manager.undo_last()
        assert result.success
