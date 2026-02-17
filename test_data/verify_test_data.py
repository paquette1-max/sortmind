#!/usr/bin/env python3
"""
Test Data Integrity Verification Script
======================================

Verifies that all test data files:
1. Have proper NOT REAL markers
2. Are in the correct directory structure
3. Have unique document IDs
4. Do not contain any real personal information patterns

Usage:
    python3 verify_test_data.py
    python3 verify_test_data.py --verbose
    python3 verify_test_data.py --fix
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


class TestDataVerifier:
    """Verifies integrity and safety of test data."""
    
    REQUIRED_MARKERS = [
        "NOT REAL",
        "TEST DOCUMENT",
        "FICTITIOUS",
    ]
    
    FORBIDDEN_PATTERNS = [
        # Real SSN patterns (not XXX-XX-XXXX format)
        r"\b\d{3}-\d{2}-\d{4}\b",
        # Real credit card numbers
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        # Real phone numbers in sensitive contexts (not (555) XXX-XXXX)
        # We allow (555) XXX-XXXX as it's reserved for fiction
    ]
    
    def __init__(self, test_data_dir: Path, verbose: bool = False):
        self.test_data_dir = test_data_dir
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        
    def log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message)
            
    def error(self, message: str):
        """Record an error."""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
        
    def warning(self, message: str):
        """Record a warning."""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
        
    def get_all_test_files(self) -> List[Path]:
        """Get all test data files."""
        files = []
        if not self.test_data_dir.exists():
            self.error(f"Test data directory not found: {self.test_data_dir}")
            return files
            
        for subdir in self.test_data_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('.'):
                for file_path in subdir.glob("*.txt"):
                    files.append(file_path)
                    
        return files
        
    def verify_not_real_markers(self, file_path: Path) -> bool:
        """Verify file has proper NOT REAL markers."""
        content = file_path.read_text()
        
        # Check for at least one required marker
        has_marker = any(marker in content for marker in self.REQUIRED_MARKERS)
        
        if not has_marker:
            self.error(f"{file_path.name}: Missing NOT REAL marker")
            return False
            
        self.log(f"✓ {file_path.name}: Has NOT REAL marker")
        return True
        
    def verify_no_real_pii(self, file_path: Path) -> bool:
        """Check for potential real PII patterns."""
        content = file_path.read_text()
        
        # Check for real SSN patterns (not the XXX-XX-XXXX format used in tests)
        # Real SSNs would have actual numbers
        ssn_pattern = r"\b[0-8]\d{2}-\d{2}-\d{4}\b"  # Real SSNs don't start with 9 or 000
        matches = re.findall(ssn_pattern, content)
        
        # Filter out the fake SSNs we use (starting with 9 is invalid anyway, 
        # and XXX-XX-XXXX is clearly marked)
        suspicious_ssns = [m for m in matches if not m.startswith("XXX")]
        
        if suspicious_ssns:
            self.warning(f"{file_path.name}: Potential real SSN pattern found: {suspicious_ssns[:3]}")
            return False
            
        self.log(f"✓ {file_path.name}: No suspicious PII patterns")
        return True
        
    def verify_unique_doc_ids(self, files: List[Path]) -> bool:
        """Verify all documents have unique IDs."""
        doc_ids = {}
        
        for file_path in files:
            # Extract doc ID from filename (last part before .txt)
            parts = file_path.stem.split('_')
            if len(parts) >= 2:
                doc_id = parts[-1]
                
                if doc_id in doc_ids:
                    self.error(f"Duplicate doc ID '{doc_id}' in files:\n"
                              f"  - {file_path.name}\n"
                              f"  - {doc_ids[doc_id].name}")
                    return False
                doc_ids[doc_id] = file_path
                
        self.log(f"✓ All {len(doc_ids)} document IDs are unique")
        return True
        
    def verify_directory_structure(self) -> bool:
        """Verify proper directory structure exists."""
        expected_dirs = [
            "bank_statements",
            "medical_bills", 
            "utility_bills",
            "tax_documents",
            "credit_card_statements",
        ]
        
        all_good = True
        for dir_name in expected_dirs:
            dir_path = self.test_data_dir / dir_name
            if not dir_path.exists():
                self.error(f"Missing directory: {dir_name}")
                all_good = False
            elif not any(dir_path.glob("*.txt")):
                self.warning(f"Empty directory: {dir_name}")
                
        if all_good:
            self.log("✓ Directory structure is correct")
            
        return all_good
        
    def verify_readme_exists(self) -> bool:
        """Verify README.md exists with warnings."""
        readme_path = self.test_data_dir / "README.md"
        
        if not readme_path.exists():
            self.error("README.md not found - needed to warn users about test data")
            return False
            
        content = readme_path.read_text()
        if "NOT REAL" not in content:
            self.warning("README.md may be missing critical NOT REAL warnings")
            return False
            
        self.log("✓ README.md exists with proper warnings")
        return True
        
    def run_all_verifications(self) -> Tuple[int, int]:
        """Run all verification checks."""
        print("="*60)
        print("TEST DATA INTEGRITY VERIFICATION")
        print("="*60)
        print(f"Test data directory: {self.test_data_dir}")
        print()
        
        # 1. Check directory structure
        print("1. Checking directory structure...")
        self.verify_directory_structure()
        
        # 2. Check README
        print("\n2. Checking README...")
        self.verify_readme_exists()
        
        # 3. Get all test files
        print("\n3. Scanning test files...")
        files = self.get_all_test_files()
        
        if not files:
            self.error("No test files found!")
            return len(self.errors), len(self.warnings)
            
        print(f"   Found {len(files)} test files")
        
        # 4. Verify NOT REAL markers
        print("\n4. Verifying NOT REAL markers...")
        for file_path in files:
            self.verify_not_real_markers(file_path)
            
        # 5. Check for real PII
        print("\n5. Checking for real PII patterns...")
        for file_path in files:
            self.verify_no_real_pii(file_path)
            
        # 6. Verify unique doc IDs
        print("\n6. Verifying unique document IDs...")
        self.verify_unique_doc_ids(files)
        
        return len(self.errors), len(self.warnings)
        
    def print_summary(self):
        """Print verification summary."""
        print()
        print("="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        if self.errors:
            print(f"❌ {len(self.errors)} ERRORS found")
        else:
            print("✅ No errors found")
            
        if self.warnings:
            print(f"⚠️  {len(self.warnings)} WARNINGS")
        else:
            print("✅ No warnings")
            
        print()
        
        if self.errors:
            print("Please fix the errors above before using this test data.")
            return False
        elif self.warnings:
            print("Review the warnings above. Test data may still be usable.")
            return True
        else:
            print("All verifications passed! Test data is safe to use.")
            return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify test data integrity and safety",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 verify_test_data.py           # Basic verification
    python3 verify_test_data.py -v        # Verbose output
    python3 verify_test_data.py -d ./data # Use different directory
        """
    )
    parser.add_argument(
        '-d', '--directory',
        type=Path,
        default=Path(__file__).parent,
        help='Test data directory to verify (default: current directory)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    verifier = TestDataVerifier(args.directory, args.verbose)
    verifier.run_all_verifications()
    success = verifier.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
