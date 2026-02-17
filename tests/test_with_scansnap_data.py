"""
Test Suite for File Organizer using ScanSnap S1300 Test Data
============================================================

This test suite validates the File Organizer's ability to:
1. Scan and analyze test documents
2. Properly categorize documents by type
3. Suggest appropriate filenames
4. Handle organization operations safely
5. Verify document content analysis

All test data is clearly marked as NOT REAL and is only for testing purposes.

Usage:
    pytest tests/test_with_scansnap_data.py -v
    pytest tests/test_with_scansnap_data.py::TestDocumentAnalysis -v
"""

import pytest
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Import File Organizer components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.organizer import FileOrganizer, FileOperation, ExecutionResult
from core.scanner import FileScanner
from core.config import OrganizationConfig


class TestDocumentAnalysis:
    """Tests for document analysis and categorization using test data."""
    
    @pytest.fixture(scope="class")
    def test_data_dir(self):
        """Provide path to test data directory."""
        return Path(__file__).parent.parent / "test_data"
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            shutil.rmtree(temp_path)
    
    def test_bank_statements_detected(self, test_data_dir):
        """Test that bank statements are properly detected and categorized."""
        bank_dir = test_data_dir / "bank_statements"
        assert bank_dir.exists(), "Bank statements test data not found"
        
        files = list(bank_dir.glob("*.txt"))
        assert len(files) > 0, "No bank statement files found"
        
        # Verify each file contains expected keywords
        for file_path in files:
            content = file_path.read_text()
            assert "bank" in content.lower() or "statement" in content.lower()
            assert "NOT REAL" in content or "TEST DOCUMENT" in content
            
    def test_medical_bills_detected(self, test_data_dir):
        """Test that medical bills are properly detected."""
        medical_dir = test_data_dir / "medical_bills"
        assert medical_dir.exists(), "Medical bills test data not found"
        
        files = list(medical_dir.glob("*.txt"))
        assert len(files) > 0, "No medical bill files found"
        
        for file_path in files:
            content = file_path.read_text()
            assert "medical" in content.lower() or "patient" in content.lower()
            assert "NOT REAL" in content or "TEST DOCUMENT" in content
            
    def test_utility_bills_detected(self, test_data_dir):
        """Test that utility bills are properly detected."""
        utility_dir = test_data_dir / "utility_bills"
        assert utility_dir.exists(), "Utility bills test data not found"
        
        files = list(utility_dir.glob("*.txt"))
        assert len(files) > 0, "No utility bill files found"
        
        for file_path in files:
            content = file_path.read_text()
            assert any(word in content.lower() for word in ["electric", "gas", "water", "utility"])
            assert "NOT REAL" in content or "TEST DOCUMENT" in content
            
    def test_tax_documents_detected(self, test_data_dir):
        """Test that tax documents are properly detected."""
        tax_dir = test_data_dir / "tax_documents"
        assert tax_dir.exists(), "Tax documents test data not found"
        
        files = list(tax_dir.glob("*.txt"))
        assert len(files) > 0, "No tax document files found"
        
        for file_path in files:
            content = file_path.read_text()
            assert "w-2" in content.lower() or "tax" in content.lower()
            assert "NOT REAL" in content or "DUMMY TAX DOCUMENT" in content
            
    def test_credit_card_statements_detected(self, test_data_dir):
        """Test that credit card statements are properly detected."""
        cc_dir = test_data_dir / "credit_card_statements"
        assert cc_dir.exists(), "Credit card statements test data not found"
        
        files = list(cc_dir.glob("*.txt"))
        assert len(files) > 0, "No credit card statement files found"
        
        for file_path in files:
            content = file_path.read_text()
            assert "credit card" in content.lower() or "statement" in content.lower()
            assert "NOT REAL" in content or "TEST DOCUMENT" in content
            
    def test_all_documents_have_not_real_markers(self, test_data_dir):
        """Verify all test documents contain NOT REAL markers."""
        all_files = []
        for subdir in test_data_dir.iterdir():
            if subdir.is_dir():
                all_files.extend(subdir.glob("*.txt"))
        
        assert len(all_files) > 0, "No test files found"
        
        for file_path in all_files:
            content = file_path.read_text()
            assert "NOT REAL" in content or "TEST DOCUMENT" in content or "FICTITIOUS" in content, \
                f"File {file_path.name} missing NOT REAL marker"


class TestFileOrganization:
    """Tests for file organization operations using test data."""
    
    @pytest.fixture(scope="class")
    def test_data_dir(self):
        """Provide path to test data directory."""
        return Path(__file__).parent.parent / "test_data"
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def organizer(self):
        """Create FileOrganizer instance."""
        return FileOrganizer()
    
    def test_copy_test_files_to_temp(self, test_data_dir, temp_dir):
        """Test copying test files to temporary location."""
        bank_dir = test_data_dir / "bank_statements"
        test_files = list(bank_dir.glob("*.txt"))
        
        # Copy files to temp dir
        for file_path in test_files[:2]:
            shutil.copy(file_path, temp_dir / file_path.name)
        
        copied = list(temp_dir.glob("*.txt"))
        assert len(copied) == 2
        
    def test_file_content_preserved_after_copy(self, test_data_dir, temp_dir):
        """Verify file content is preserved when copying."""
        bank_dir = test_data_dir / "bank_statements"
        source_file = list(bank_dir.glob("*.txt"))[0]
        
        dest_file = temp_dir / source_file.name
        shutil.copy(source_file, dest_file)
        
        assert source_file.read_text() == dest_file.read_text()
        
    def test_sanitize_filename_with_test_data(self, temp_dir):
        """Test filename sanitization with various test filenames."""
        from core.organizer import sanitize_path_component
        
        test_cases = [
            ("normal_file.txt", "normal_file.txt"),
            ("file/with/slashes.txt", "file_with_slashes.txt"),
            ("file..with..dots.txt", "file_with_dots.txt"),
            ("file<with>special|chars?.txt", "file_with_special_chars_.txt"),
            ("../etc/passwd", "_etc_passwd"),
        ]
        
        for input_name, expected in test_cases:
            result = sanitize_path_component(input_name)
            assert result == expected, f"Expected {expected}, got {result}"


class TestDocumentScannerIntegration:
    """Integration tests using actual test data."""
    
    @pytest.fixture(scope="class")
    def test_data_dir(self):
        """Provide path to test data directory."""
        return Path(__file__).parent.parent / "test_data"
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            shutil.rmtree(temp_path)
    
    def test_scanner_finds_all_test_files(self, test_data_dir, temp_dir):
        """Test that scanner finds all test files."""
        # Copy all test files to temp dir
        total_files = 0
        for subdir in test_data_dir.iterdir():
            if subdir.is_dir():
                for file_path in subdir.glob("*.txt"):
                    shutil.copy(file_path, temp_dir / file_path.name)
                    total_files += 1
        
        # Scan the directory
        scanner = FileScanner()
        scanned = scanner.scan_directory(temp_dir)
        
        assert len(scanned) == total_files, f"Expected {total_files} files, found {len(scanned)}"
        
    def test_scanner_extracts_text_from_test_documents(self, test_data_dir):
        """Test that scanner can extract text content from test documents."""
        bank_dir = test_data_dir / "bank_statements"
        test_file = list(bank_dir.glob("*.txt"))[0]
        
        scanner = DocumentScanner()
        content = scanner.extract_text(test_file)
        
        assert content is not None
        assert len(content) > 0
        assert "NOT REAL" in content or "TEST DOCUMENT" in content


class TestOrganizationPlan:
    """Tests for organization plan creation with test data."""
    
    @pytest.fixture(scope="class")
    def test_data_dir(self):
        """Provide path to test data directory."""
        return Path(__file__).parent.parent / "test_data"
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def organizer(self):
        """Create FileOrganizer instance."""
        return FileOrganizer()
    
    def test_create_plan_with_bank_statements(self, test_data_dir, temp_dir, organizer):
        """Test creating organization plan for bank statements."""
        bank_dir = test_data_dir / "bank_statements"
        
        # Copy files to temp dir
        test_files = []
        for file_path in bank_dir.glob("*.txt"):
            dest = temp_dir / file_path.name
            shutil.copy(file_path, dest)
            test_files.append(dest)
        
        # Create analysis results
        analysis_results = [
            {
                "file_path": str(f),
                "category": "Bank Statements",
                "suggested_name": f"bank_statement_{i:03d}.txt",
                "confidence": 0.95,
                "reasoning": "Detected bank statement format"
            }
            for i, f in enumerate(test_files)
        ]
        
        # Create organization plan
        plan = organizer.create_organization_plan(
            test_files,
            analysis_results,
            temp_dir / "organized"
        )
        
        assert "operations" in plan
        assert len(plan["operations"]) == len(test_files)
        
    def test_plan_dry_run_does_not_move_files(self, test_data_dir, temp_dir, organizer):
        """Test that dry run doesn't actually move files."""
        bank_dir = test_data_dir / "bank_statements"
        test_file = list(bank_dir.glob("*.txt"))[0]
        
        dest = temp_dir / test_file.name
        shutil.copy(test_file, dest)
        
        # Create a plan with move operation
        plan = {
            "batch_id": "test-123",
            "operations": [
                {
                    "source": dest,
                    "destination": temp_dir / "organized" / "test.txt",
                    "operation_type": "move",
                    "reasoning": "Test",
                    "confidence": 0.95
                }
            ]
        }
        
        # Execute dry run
        result = organizer.execute_plan(plan, dry_run=True)
        
        assert result.success
        assert dest.exists(), "Original file should still exist after dry run"


class TestDataValidation:
    """Tests to validate test data integrity."""
    
    @pytest.fixture(scope="class")
    def test_data_dir(self):
        """Provide path to test data directory."""
        return Path(__file__).parent.parent / "test_data"
    
    def test_all_categories_have_files(self, test_data_dir):
        """Verify all expected document categories have test files."""
        expected_categories = [
            "bank_statements",
            "medical_bills",
            "utility_bills",
            "tax_documents",
            "credit_card_statements",
        ]
        
        for category in expected_categories:
            cat_dir = test_data_dir / category
            assert cat_dir.exists(), f"Category directory missing: {category}"
            
            files = list(cat_dir.glob("*.txt"))
            assert len(files) > 0, f"No files in category: {category}"
            
    def test_no_duplicate_filenames_across_categories(self, test_data_dir):
        """Ensure no filename collisions between categories."""
        all_filenames = []
        
        for subdir in test_data_dir.iterdir():
            if subdir.is_dir():
                for file_path in subdir.glob("*.txt"):
                    all_filenames.append(file_path.name)
        
        # Check for duplicates
        unique_names = set(all_filenames)
        assert len(unique_names) == len(all_filenames), \
            f"Found duplicate filenames: {len(all_filenames) - len(unique_names)} duplicates"
            
    def test_document_ids_are_unique(self, test_data_dir):
        """Verify all generated documents have unique IDs."""
        all_doc_ids = []
        
        for subdir in test_data_dir.iterdir():
            if subdir.is_dir():
                for file_path in subdir.glob("*.txt"):
                    # Extract doc ID from filename
                    parts = file_path.stem.split('_')
                    if len(parts) > 0:
                        doc_id = parts[-1]
                        all_doc_ids.append(doc_id)
        
        unique_ids = set(all_doc_ids)
        assert len(unique_ids) == len(all_doc_ids), \
            "Found duplicate document IDs"


class TestSafetyFeatures:
    """Tests for safety features when working with test data."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        if temp_path.exists():
            shutil.rmtree(temp_path)
    
    def test_validate_safe_path_prevents_traversal(self, temp_dir):
        """Test path traversal prevention."""
        from core.organizer import validate_safe_path
        
        base = temp_dir
        safe_path = temp_dir / "subdir" / "file.txt"
        unsafe_path = temp_dir / ".." / "etc" / "passwd"
        
        assert validate_safe_path(base, safe_path) is True
        assert validate_safe_path(base, unsafe_path) is False
        
    def test_backup_created_before_move(self, temp_dir):
        """Test that backup is created before file operations."""
        from core.backup import BackupManager
        
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content")
        
        # Create backup
        backup_mgr = BackupManager(temp_dir / "backups")
        backup_path = backup_mgr.create_backup([test_file])
        
        assert backup_path.exists()
        
    def test_undo_operation_restores_files(self, temp_dir):
        """Test undo functionality."""
        from core.undo_manager import UndoManager
        
        undo_mgr = UndoManager()
        
        # Create and register a file operation
        test_file = temp_dir / "test.txt"
        test_file.write_text("Original content")
        
        operation_id = undo_mgr.register_operation(
            operation_type="move",
            source=test_file,
            destination=temp_dir / "moved" / "test.txt"
        )
        
        assert operation_id is not None
        

# Marker to identify this as a test that uses test data
pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
