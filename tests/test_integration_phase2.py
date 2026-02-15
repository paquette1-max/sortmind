"""
Integration tests for Phase 2 file operations.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import time

from src.core.organizer import FileOrganizer
from src.core.undo_manager import UndoManager
from src.core.backup import BackupManager, BackupStrategy


class TestPhase2Integration:
    """End-to-end tests for Phase 2."""
    
    @pytest.fixture
    def workspace(self):
        """Create test workspace with source and target directories."""
        workspace_path = Path(tempfile.mkdtemp())
        
        # Create source directory with test files
        source_dir = workspace_path / "source"
        source_dir.mkdir()
        
        for i in range(5):
            file_path = source_dir / f"document_{i}.txt"
            file_path.write_text(f"This is document number {i}\n" * 10)
        
        # Create target directory
        target_dir = workspace_path / "organized"
        target_dir.mkdir()
        
        # Create backup directory
        backup_dir = workspace_path / "backups"
        
        # Create database directory
        db_dir = workspace_path / "db"
        db_dir.mkdir()
        
        yield {
            'workspace': workspace_path,
            'source': source_dir,
            'target': target_dir,
            'backup': backup_dir,
            'db': db_dir
        }
        
        # Cleanup
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
    
    def test_complete_organize_workflow(self, workspace):
        """Test complete workflow: scan -> plan -> execute."""
        source_files = list(workspace['source'].glob("*.txt"))
        assert len(source_files) == 5
        
        # Create organizer
        organizer = FileOrganizer()
        
        # Create mock analysis results
        analysis_results = []
        for file_path in source_files:
            analysis_results.append({
                "file_path": str(file_path),
                "category": "documents",
                "suggested_name": file_path.name,
                "confidence": 0.95,
                "reasoning": "Text document"
            })
        
        # Create plan
        plan = organizer.create_organization_plan(
            source_files,
            analysis_results,
            workspace['target']
        )
        
        assert len(plan['operations']) == 5
        assert all(op['source'].exists() for op in plan['operations'])
        
        # Validate plan
        errors = organizer.validate_plan(plan)
        assert len(errors) == 0
        
        # Execute plan
        result = organizer.execute_plan(plan, dry_run=False)
        
        assert result.success
        assert result.operations_completed == 5
        assert result.operations_failed == 0
        
        # Verify files were moved
        target_docs = list(workspace['target'].rglob("*.txt"))
        assert len(target_docs) == 5
        
        # Original files should be gone
        assert len(list(workspace['source'].glob("*.txt"))) == 0
    
    def test_organize_with_undo(self, workspace):
        """Test organization and undo workflow."""
        source_files = list(workspace['source'].glob("*.txt"))
        
        # Setup components
        undo_manager = UndoManager(workspace['db'] / "undo.db")
        organizer = FileOrganizer(undo_manager=undo_manager)
        
        # Create analysis results
        analysis_results = []
        for file_path in source_files:
            analysis_results.append({
                "file_path": str(file_path),
                "category": "documents",
                "suggested_name": file_path.name,
                "confidence": 0.95,
                "reasoning": "Text document"
            })
        
        # Create and execute plan
        plan = organizer.create_organization_plan(
            source_files,
            analysis_results,
            workspace['target']
        )
        
        result = organizer.execute_plan(plan, dry_run=False)
        assert result.success
        
        batch_id = result.batch_id
        moved_files = list(workspace['target'].rglob("*.txt"))
        assert len(moved_files) == 5
        
        # Now undo the operation
        undo_result = undo_manager.undo_batch(batch_id)
        
        assert undo_result.success
        assert undo_result.operations_undone == 5
        
        # Files should be back in source
        source_files_restored = list(workspace['source'].glob("*.txt"))
        assert len(source_files_restored) == 5
        
        # Target should be empty or just have the category folder
        target_docs = list(workspace['target'].rglob("*.txt"))
        assert len(target_docs) == 0
    
    def test_organize_with_backup(self, workspace):
        """Test organization with backup creation."""
        source_files = list(workspace['source'].glob("*.txt"))
        
        # Setup components
        backup_manager = BackupManager(workspace['backup'], strategy=BackupStrategy.COPY)
        organizer = FileOrganizer(backup_manager=backup_manager)
        
        # Create analysis results
        analysis_results = []
        for file_path in source_files:
            analysis_results.append({
                "file_path": str(file_path),
                "category": "documents",
                "suggested_name": file_path.name,
                "confidence": 0.95,
                "reasoning": "Text document"
            })
        
        # Create and execute plan
        plan = organizer.create_organization_plan(
            source_files,
            analysis_results,
            workspace['target']
        )
        
        result = organizer.execute_plan(plan, dry_run=False)
        assert result.success
        
        # Check backup was created
        backups = backup_manager.list_backups()
        assert len(backups) > 0
        assert backups[0]['file_count'] == 5
    
    def test_conflict_resolution_workflow(self, workspace):
        """Test handling filename conflicts."""
        # Create files with same name in different locations
        source_dir = workspace['source']
        subdir = source_dir / "subdir"
        subdir.mkdir()
        
        file1 = source_dir / "document.txt"
        file2 = subdir / "document.txt"
        file1.write_text("File 1")
        file2.write_text("File 2")
        
        organizer = FileOrganizer()
        
        # Create analysis results pointing to same destination
        analysis_results = [
            {
                "file_path": str(file1),
                "category": "documents",
                "suggested_name": "document.txt",
                "confidence": 0.95,
                "reasoning": "Test"
            },
            {
                "file_path": str(file2),
                "category": "documents",
                "suggested_name": "document.txt",
                "confidence": 0.95,
                "reasoning": "Test"
            }
        ]
        
        files = [file1, file2]
        
        # Create plan
        plan = organizer.create_organization_plan(
            files,
            analysis_results,
            workspace['target']
        )
        
        # Resolve conflicts
        plan = organizer.resolve_conflicts(plan)
        
        # Both operations should have unique destinations
        destinations = [op['destination'] for op in plan['operations']]
        assert len(destinations) == len(set(destinations))  # All unique
        
        # One should have the original name, one should have (1)
        dest_names = [d.name for d in destinations]
        assert "document.txt" in dest_names
        assert any("(1)" in name for name in dest_names)
        
        # Execute plan
        result = organizer.execute_plan(plan, dry_run=False)
        assert result.success
        assert result.operations_completed == 2
    
    def test_organize_with_mixed_operations(self, workspace):
        """Test organization with full integration of all components."""
        source_files = list(workspace['source'].glob("*.txt"))
        
        # Setup all components
        undo_manager = UndoManager(workspace['db'] / "undo.db")
        backup_manager = BackupManager(workspace['backup'], strategy=BackupStrategy.COPY)
        organizer = FileOrganizer(
            undo_manager=undo_manager,
            backup_manager=backup_manager
        )
        
        # Create analysis results
        analysis_results = []
        for i, file_path in enumerate(source_files):
            category = "important" if i < 2 else "routine"
            analysis_results.append({
                "file_path": str(file_path),
                "category": category,
                "suggested_name": file_path.name,
                "confidence": 0.95 - (i * 0.05),  # Varying confidence
                "reasoning": "Test document"
            })
        
        # Create plan
        plan = organizer.create_organization_plan(
            source_files,
            analysis_results,
            workspace['target']
        )
        
        # Validate
        errors = organizer.validate_plan(plan)
        assert len(errors) == 0
        
        # Execute with backup
        result = organizer.execute_plan(plan, dry_run=False)
        assert result.success
        assert result.operations_completed == 5
        
        # Verify organization structure
        important_docs = list(workspace['target'] / "important" / "*.txt")
        routine_docs = list(workspace['target'] / "routine" / "*.txt")
        assert len(important_docs) == 2
        assert len(routine_docs) == 3
        
        # Verify backup exists
        backups = backup_manager.list_backups()
        assert len(backups) > 0
        
        # Verify undo is possible
        assert undo_manager.verify_undo_possible(result.batch_id)
        
        # Test undo
        undo_result = undo_manager.undo_batch(result.batch_id)
        assert undo_result.success
        
        # Verify restoration
        restored_files = list(workspace['source'].glob("*.txt"))
        assert len(restored_files) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
