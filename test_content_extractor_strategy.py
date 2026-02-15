#!/usr/bin/env python3
"""
Comprehensive tests for ContentExtractor Strategy Pattern implementation.
"""
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, '/Users/ripley/.openclaw/workspace/file_organizer/src')

from core.content_extractor import (
    ContentExtractor, PDFExtractor, ImageExtractor, TextExtractor,
    OfficeExtractor, GenericExtractor, ExtractedContent, DocumentType
)


class TestResult:
    def __init__(self, name, passed, message=""):
        self.name = name
        self.passed = passed
        self.message = message
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        msg = f"\n   {self.message}" if self.message else ""
        return f"{status}: {self.name}{msg}"


class ContentExtractorTestSuite:
    def __init__(self):
        self.results = []
        self.temp_dir = None
    
    def setup(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
        return self
    
    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def assert_true(self, condition, name, message=""):
        """Record test result."""
        if condition:
            self.results.append(TestResult(name, True, message))
        else:
            self.results.append(TestResult(name, False, message or "Assertion failed"))
        return condition
    
    def assert_equals(self, expected, actual, name):
        """Record equality test."""
        if expected == actual:
            self.results.append(TestResult(name, True))
        else:
            self.results.append(TestResult(name, False, f"Expected {expected}, got {actual}"))
        return expected == actual
    
    def assert_in(self, item, container, name):
        """Record containment test."""
        if item in container:
            self.results.append(TestResult(name, True))
        else:
            self.results.append(TestResult(name, False, f"'{item}' not found in {container}"))
        return item in container
    
    # ==================== Strategy Pattern Tests ====================
    
    def test_strategy_pattern_classes_exist(self):
        """Test that all extractor classes exist."""
        extractor = ContentExtractor()
        
        self.assert_true(hasattr(PDFExtractor, 'can_extract'), 
                        "PDFExtractor has can_extract method")
        self.assert_true(hasattr(PDFExtractor, 'extract'),
                        "PDFExtractor has extract method")
        self.assert_true(hasattr(ImageExtractor, 'can_extract'),
                        "ImageExtractor has can_extract method")
        self.assert_true(hasattr(ImageExtractor, 'extract'),
                        "ImageExtractor has extract method")
        self.assert_true(hasattr(TextExtractor, 'can_extract'),
                        "TextExtractor has can_extract method")
        self.assert_true(hasattr(TextExtractor, 'extract'),
                        "TextExtractor has extract method")
        self.assert_true(hasattr(OfficeExtractor, 'can_extract'),
                        "OfficeExtractor has can_extract method")
        self.assert_true(hasattr(OfficeExtractor, 'extract'),
                        "OfficeExtractor has extract method")
        self.assert_true(hasattr(GenericExtractor, 'can_extract'),
                        "GenericExtractor has can_extract method")
        self.assert_true(hasattr(GenericExtractor, 'extract'),
                        "GenericExtractor has extract method")
        
        # Check SUPPORTED_EXTENSIONS
        self.assert_true(hasattr(PDFExtractor, 'SUPPORTED_EXTENSIONS'),
                        "PDFExtractor has SUPPORTED_EXTENSIONS")
        self.assert_true(hasattr(ImageExtractor, 'SUPPORTED_EXTENSIONS'),
                        "ImageExtractor has SUPPORTED_EXTENSIONS")
        self.assert_true(hasattr(TextExtractor, 'SUPPORTED_EXTENSIONS'),
                        "TextExtractor has SUPPORTED_EXTENSIONS")
        self.assert_true(hasattr(OfficeExtractor, 'SUPPORTED_EXTENSIONS'),
                        "OfficeExtractor has SUPPORTED_EXTENSIONS")
    
    def test_default_extractors_loaded(self):
        """Test that default extractors are loaded."""
        extractor = ContentExtractor()
        
        self.assert_equals(5, len(extractor.extractors), 
                          "Default extractors count is 5")
        
        # Check types
        extractor_types = [type(e).__name__ for e in extractor.extractors]
        self.assert_in('PDFExtractor', extractor_types,
                      "PDFExtractor in default extractors")
        self.assert_in('ImageExtractor', extractor_types,
                      "ImageExtractor in default extractors")
        self.assert_in('TextExtractor', extractor_types,
                      "TextExtractor in default extractors")
        self.assert_in('OfficeExtractor', extractor_types,
                      "OfficeExtractor in default extractors")
        self.assert_in('GenericExtractor', extractor_types,
                      "GenericExtractor (fallback) in default extractors")
    
    # ==================== Pluggable Architecture Tests ====================
    
    def test_register_extractor(self):
        """Test registering a custom extractor at runtime."""
        extractor = ContentExtractor()
        
        # Create a custom extractor class
        class ExcelExtractor:
            SUPPORTED_EXTENSIONS = {'.xlsx'}
            
            def can_extract(self, path):
                return path.suffix == '.xlsx'
            
            def extract(self, path, max_pages, max_text):
                return ExtractedContent(
                    file_path=path,
                    doc_type=DocumentType.UNKNOWN,
                    text_content="Excel content",
                    metadata={},
                    extraction_method="excel"
                )
        
        # Register the extractor
        excel_ext = ExcelExtractor()
        initial_count = len(extractor.extractors)
        extractor.register_extractor(excel_ext)
        
        self.assert_equals(initial_count + 1, len(extractor.extractors),
                          "Extractor count increases after registration")
        self.assert_true(any(isinstance(e, ExcelExtractor) for e in extractor.extractors),
                        "Custom extractor instance found in extractors list")
    
    def test_unregister_extractor(self):
        """Test unregistering an extractor by type."""
        extractor = ContentExtractor()
        initial_count = len(extractor.extractors)
        
        # Unregister PDFExtractor
        extractor.unregister_extractor(PDFExtractor)
        
        self.assert_equals(initial_count - 1, len(extractor.extractors),
                          "Extractor count decreases after unregistration")
        self.assert_true(not any(isinstance(e, PDFExtractor) for e in extractor.extractors),
                        "PDFExtractor no longer in extractors list")
    
    def test_register_at_position(self):
        """Test registering extractor at specific position."""
        extractor = ContentExtractor()
        
        class PriorityExtractor:
            SUPPORTED_EXTENSIONS = {'.xyz'}
            
            def can_extract(self, path):
                return path.suffix == '.xyz'
            
            def extract(self, path, max_pages, max_text):
                return ExtractedContent(
                    file_path=path,
                    doc_type=DocumentType.UNKNOWN,
                    text_content="Priority",
                    metadata={},
                    extraction_method="priority"
                )
        
        # Register at position 0 (highest priority)
        extractor.register_extractor(PriorityExtractor(), position=0)
        
        self.assert_true(isinstance(extractor.extractors[0], PriorityExtractor),
                        "Extractor registered at position 0")
    
    # ==================== Path Validation Tests ====================
    
    def test_base_path_enforcement(self):
        """Test base_path enforcement prevents directory traversal."""
        extractor = ContentExtractor()
        
        # Create a safe directory structure
        safe_dir = self.base_path / "safe"
        safe_dir.mkdir()
        
        # Try to access file outside safe directory
        result = extractor.extract("../../../etc/passwd", base_path=safe_dir)
        
        self.assert_true(result.error is not None,
                        "Path outside base_path returns error")
        self.assert_in("Access denied", result.error,
                      "Error message mentions 'Access denied'")
    
    def test_symlink_rejection(self):
        """Test that symlinks are rejected."""
        extractor = ContentExtractor()
        
        # Create a real file
        real_file = self.base_path / "real.txt"
        real_file.write_text("real content")
        
        # Create a symlink
        symlink_file = self.base_path / "link.txt"
        try:
            symlink_file.symlink_to(real_file)
            
            result = extractor.extract(symlink_file)
            
            self.assert_true(result.error is not None,
                            "Symlink access returns error")
            self.assert_in("symlink", result.error.lower(),
                          "Error message mentions symlink")
        except OSError:
            # Symlinks might not be supported on all platforms
            self.results.append(TestResult("Symlink rejection", True, "Skipped - symlinks not supported"))
    
    def test_file_not_found(self):
        """Test handling of non-existent files."""
        extractor = ContentExtractor()
        
        result = extractor.extract(self.base_path / "nonexistent.txt")
        
        self.assert_true(result.error is not None,
                        "Non-existent file returns error")
        self.assert_in("not found", result.error.lower(),
                      "Error message mentions 'not found'")
    
    # ==================== Extractor Selection Tests ====================
    
    def test_extractor_selection_pdf(self):
        """Test PDF extractor is selected for .pdf files."""
        extractor = ContentExtractor()
        
        pdf_file = self.base_path / "test.pdf"
        pdf_file.write_text("fake pdf content")
        
        # Check can_extract for PDF
        pdf_ext = PDFExtractor()
        self.assert_true(pdf_ext.can_extract(pdf_file),
                        "PDFExtractor.can_extract returns True for .pdf")
    
    def test_extractor_selection_text(self):
        """Test Text extractor is selected for text files."""
        extractor = ContentExtractor()
        
        # Test various text extensions
        text_ext = TextExtractor()
        
        for ext in ['.txt', '.md', '.py', '.json', '.csv']:
            test_file = self.base_path / f"test{ext}"
            test_file.write_text("test content")
            
            self.assert_true(text_ext.can_extract(test_file),
                            f"TextExtractor.can_extract returns True for {ext}")
    
    def test_extractor_selection_image(self):
        """Test Image extractor is selected for image files."""
        extractor = ContentExtractor()
        
        image_ext = ImageExtractor()
        
        for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.webp']:
            test_file = self.base_path / f"test{ext}"
            test_file.write_text("fake image")
            
            self.assert_true(image_ext.can_extract(test_file),
                            f"ImageExtractor.can_extract returns True for {ext}")
    
    def test_extractor_selection_office(self):
        """Test Office extractor is selected for office files."""
        extractor = ContentExtractor()
        
        office_ext = OfficeExtractor()
        
        for ext in ['.docx', '.odt', '.doc', '.rtf']:
            test_file = self.base_path / f"test{ext}"
            test_file.write_text("fake doc")
            
            self.assert_true(office_ext.can_extract(test_file),
                            f"OfficeExtractor.can_extract returns True for {ext}")
    
    def test_generic_extractor_fallback(self):
        """Test GenericExtractor as fallback."""
        generic = GenericExtractor()
        
        # Generic should accept any file
        weird_file = self.base_path / "file.unknown"
        weird_file.write_text("content")
        
        self.assert_true(generic.can_extract(weird_file),
                        "GenericExtractor accepts unknown file types")
    
    # ==================== Text Extraction Tests ====================
    
    def test_text_extraction(self):
        """Test actual text file extraction."""
        extractor = ContentExtractor()
        
        test_file = self.base_path / "test.txt"
        test_content = "Hello, World!\nThis is a test file.\nLine 3."
        test_file.write_text(test_content)
        
        result = extractor.extract(test_file)
        
        self.assert_equals(DocumentType.TEXT, result.doc_type,
                          "Text file has TEXT doc_type")
        self.assert_in("Hello", result.text_content,
                      "Extracted content includes text")
        self.assert_equals("direct_read", result.extraction_method,
                          "Text extraction uses direct_read method")
        self.assert_true(result.error is None,
                        "Text extraction has no error")
    
    def test_text_truncation(self):
        """Test text truncation for large files."""
        extractor = ContentExtractor()
        extractor.max_text_length = 50  # Small limit for testing
        
        test_file = self.base_path / "long.txt"
        test_file.write_text("A" * 100)
        
        result = extractor.extract(test_file)
        
        self.assert_in("truncated", result.text_content.lower(),
                      "Long text is truncated")
    
    # ==================== PDF Fallback Tests ====================
    
    def test_pdf_fallback_chain(self):
        """Test PDF fallback chain when dependencies missing."""
        pdf_ext = PDFExtractor()
        
        # Create a fake PDF (it won't be valid but we can test the structure)
        pdf_file = self.base_path / "fake.pdf"
        pdf_file.write_text("%PDF-1.4 fake pdf content")
        
        # Test that the fallback methods exist
        self.assert_true(hasattr(pdf_ext, '_try_pymupdf'),
                        "PDFExtractor has _try_pymupdf method")
        self.assert_true(hasattr(pdf_ext, '_try_pdfplumber'),
                        "PDFExtractor has _try_pdfplumber method")
        self.assert_true(hasattr(pdf_ext, '_try_ocr'),
                        "PDFExtractor has _try_ocr method")
    
    def test_pdf_extraction_with_missing_dependencies(self):
        """Test PDF extraction handles missing dependencies gracefully."""
        pdf_ext = PDFExtractor()
        
        pdf_file = self.base_path / "test.pdf"
        pdf_file.write_text("%PDF-1.4")
        
        # Without PyMuPDF installed, should return error result
        with patch.dict('sys.modules', {'fitz': None}):
            result = pdf_ext.extract(pdf_file)
            
            # Should have an error since no backends available
            self.assert_true(result.error is not None or result.text_content == "",
                            "PDF extraction with no backends returns error or empty content")
    
    # ==================== Error Handling Tests ====================
    
    def test_missing_dependency_handling(self):
        """Test graceful handling of missing dependencies."""
        # Test ImageExtractor without pytesseract
        img_ext = ImageExtractor()
        
        img_file = self.base_path / "test.png"
        img_file.write_text("fake png")
        
        with patch.dict('sys.modules', {'pytesseract': None}):
            result = img_ext.extract(img_file)
            
            self.assert_true(result.error is not None,
                            "Image extraction without pytesseract returns error")
            self.assert_in("requires", result.error.lower(),
                          "Error mentions required dependency")
    
    def test_office_extractor_docx_without_dependency(self):
        """Test OfficeExtractor handles missing python-docx."""
        office_ext = OfficeExtractor()
        
        docx_file = self.base_path / "test.docx"
        docx_file.write_text("fake docx")
        
        with patch.dict('sys.modules', {'docx': None}):
            result = office_ext.extract(docx_file)
            
            self.assert_true(result.error is not None,
                            "DOCX extraction without python-docx returns error")
    
    # ==================== Metadata Tests ====================
    
    def test_extraction_metadata(self):
        """Test that metadata is populated correctly."""
        extractor = ContentExtractor()
        
        test_file = self.base_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")
        
        result = extractor.extract(test_file)
        
        self.assert_true("lines" in result.metadata,
                        "Text extraction includes line count")
        self.assert_true("size" in result.metadata,
                        "Text extraction includes file size")
    
    def test_get_supported_types(self):
        """Test get_supported_types method."""
        extractor = ContentExtractor()
        
        types = extractor.get_supported_types()
        
        self.assert_true('PDFExtractor' in types,
                        "get_supported_types includes PDFExtractor")
        self.assert_true('TextExtractor' in types,
                        "get_supported_types includes TextExtractor")
        self.assert_true(len(types['TextExtractor']) > 0,
                        "TextExtractor has supported extensions")
    
    def test_get_installation_instructions(self):
        """Test get_installation_instructions method."""
        extractor = ContentExtractor()
        
        instructions = extractor.get_installation_instructions()
        
        self.assert_true('tesseract' in instructions,
                        "Instructions include tesseract")
        self.assert_true('pymupdf' in instructions,
                        "Instructions include pymupdf")
    
    # ==================== Run All Tests ====================
    
    def run_all(self):
        """Run all tests and return results."""
        print("=" * 70)
        print("CONTENT EXTRACTOR STRATEGY PATTERN TEST SUITE")
        print("=" * 70)
        
        try:
            self.setup()
            
            # Strategy Pattern Tests
            print("\n📋 STRATEGY PATTERN IMPLEMENTATION")
            print("-" * 50)
            self.test_strategy_pattern_classes_exist()
            self.test_default_extractors_loaded()
            
            # Pluggable Architecture Tests
            print("\n🔌 PLUGGABLE ARCHITECTURE")
            print("-" * 50)
            self.test_register_extractor()
            self.test_unregister_extractor()
            self.test_register_at_position()
            
            # Path Validation Tests
            print("\n🔒 PATH VALIDATION")
            print("-" * 50)
            self.test_base_path_enforcement()
            self.test_symlink_rejection()
            self.test_file_not_found()
            
            # Extractor Selection Tests
            print("\n🎯 EXTRACTOR SELECTION")
            print("-" * 50)
            self.test_extractor_selection_pdf()
            self.test_extractor_selection_text()
            self.test_extractor_selection_image()
            self.test_extractor_selection_office()
            self.test_generic_extractor_fallback()
            
            # Text Extraction Tests
            print("\n📝 TEXT EXTRACTION")
            print("-" * 50)
            self.test_text_extraction()
            self.test_text_truncation()
            
            # PDF Fallback Tests
            print("\n📄 PDF FALLBACK CHAIN")
            print("-" * 50)
            self.test_pdf_fallback_chain()
            self.test_pdf_extraction_with_missing_dependencies()
            
            # Error Handling Tests
            print("\n⚠️ ERROR HANDLING")
            print("-" * 50)
            self.test_missing_dependency_handling()
            self.test_office_extractor_docx_without_dependency()
            
            # Metadata Tests
            print("\n📊 METADATA & UTILITIES")
            print("-" * 50)
            self.test_extraction_metadata()
            self.test_get_supported_types()
            self.test_get_installation_instructions()
            
        finally:
            self.cleanup()
        
        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        
        for result in self.results:
            print(result)
        
        print("\n" + "=" * 70)
        print(f"TOTAL: {len(self.results)} tests | ✅ {passed} passed | ❌ {failed} failed")
        print("=" * 70)
        
        return passed, failed, self.results


if __name__ == "__main__":
    suite = ContentExtractorTestSuite()
    passed, failed, results = suite.run_all()
    sys.exit(0 if failed == 0 else 1)
