"""
PDF Document Splitter Utility
Splits multi-page PDFs into separate documents based on detected segments.
"""

import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

try:
    from ..core.multi_page_analyzer import DocumentSegment
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.multi_page_analyzer import DocumentSegment

logger = logging.getLogger(__name__)


@dataclass
class SplitResult:
    """Result of splitting a PDF."""
    success: bool
    output_files: List[Path]
    errors: List[str]
    total_pages: int
    pages_split: int


class PDFDocumentSplitter:
    """Split PDF documents into separate files based on segments."""
    
    def __init__(self):
        """Initialize the PDF splitter."""
        self.errors = []
    
    def split_document(self, source_path: Path, segments: List[DocumentSegment],
                      output_directory: Optional[Path] = None,
                      dry_run: bool = False) -> SplitResult:
        """
        Split a PDF into separate documents.
        
        Args:
            source_path: Path to source PDF
            segments: List of detected document segments
            output_directory: Where to save split files (default: same as source)
            dry_run: If True, don't actually create files
            
        Returns:
            SplitResult with success status and output file paths
        """
        self.errors = []
        output_files = []
        
        if not source_path.exists():
            return SplitResult(
                success=False,
                output_files=[],
                errors=[f"Source file not found: {source_path}"],
                total_pages=0,
                pages_split=0
            )
        
        # Set output directory
        if output_directory is None:
            output_directory = source_path.parent
        
        output_directory = Path(output_directory)
        output_directory.mkdir(parents=True, exist_ok=True)
        
        # Try different PDF libraries
        result = None
        
        # Try PyPDF2 first (lightweight)
        try:
            result = self._split_with_pypdf2(
                source_path, segments, output_directory, dry_run
            )
        except ImportError:
            logger.info("PyPDF2 not available, trying PyMuPDF")
        except Exception as e:
            logger.warning(f"PyPDF2 failed: {e}")
        
        # Fallback to PyMuPDF
        if result is None:
            try:
                result = self._split_with_pymupdf(
                    source_path, segments, output_directory, dry_run
                )
            except ImportError:
                logger.error("No PDF library available (PyPDF2 or PyMuPDF)")
                return SplitResult(
                    success=False,
                    output_files=[],
                    errors=["No PDF library available. Install PyPDF2 or PyMuPDF."],
                    total_pages=0,
                    pages_split=0
                )
            except Exception as e:
                logger.error(f"PyMuPDF failed: {e}")
                return SplitResult(
                    success=False,
                    output_files=[],
                    errors=[f"Failed to split PDF: {e}"],
                    total_pages=0,
                    pages_split=0
                )
        
        return result
    
    def _split_with_pypdf2(self, source_path: Path, segments: List[DocumentSegment],
                          output_directory: Path, dry_run: bool) -> Optional[SplitResult]:
        """Split PDF using PyPDF2."""
        from PyPDF2 import PdfReader, PdfWriter
        
        reader = PdfReader(str(source_path))
        total_pages = len(reader.pages)
        output_files = []
        pages_split = 0
        
        for i, segment in enumerate(segments):
            # Generate safe filename
            filename = self._sanitize_filename(segment.suggested_filename or f"document_{i+1}.pdf")
            output_path = output_directory / filename
            
            # Handle duplicate filenames
            output_path = self._get_unique_filename(output_path)
            
            if dry_run:
                logger.info(f"[DRY RUN] Would create: {output_path}")
                output_files.append(output_path)
                pages_split += (segment.end_page - segment.start_page + 1)
                continue
            
            # Create new PDF with selected pages
            writer = PdfWriter()
            
            # PyPDF2 uses 0-based indexing
            start_idx = segment.start_page - 1
            end_idx = segment.end_page
            
            for page_num in range(start_idx, end_idx):
                if page_num < total_pages:
                    writer.add_page(reader.pages[page_num])
            
            # Write output file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            output_files.append(output_path)
            pages_split += (end_idx - start_idx)
            
            logger.info(f"Created: {output_path} ({end_idx - start_idx} pages)")
        
        return SplitResult(
            success=len(self.errors) == 0,
            output_files=output_files,
            errors=self.errors,
            total_pages=total_pages,
            pages_split=pages_split
        )
    
    def _split_with_pymupdf(self, source_path: Path, segments: List[DocumentSegment],
                           output_directory: Path, dry_run: bool) -> SplitResult:
        """Split PDF using PyMuPDF (fitz)."""
        import fitz
        
        doc = fitz.open(str(source_path))
        total_pages = len(doc)
        output_files = []
        pages_split = 0
        
        try:
            for i, segment in enumerate(segments):
                # Generate safe filename
                filename = self._sanitize_filename(segment.suggested_filename or f"document_{i+1}.pdf")
                output_path = output_directory / filename
                
                # Handle duplicate filenames
                output_path = self._get_unique_filename(output_path)
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would create: {output_path}")
                    output_files.append(output_path)
                    pages_split += (segment.end_page - segment.start_page + 1)
                    continue
                
                # Create new PDF with selected pages
                new_doc = fitz.open()
                
                # PyMuPDF uses 0-based indexing
                start_idx = segment.start_page - 1
                end_idx = min(segment.end_page, total_pages)
                
                # Insert pages
                new_doc.insert_pdf(doc, from_page=start_idx, to_page=end_idx - 1)
                
                # Save
                new_doc.save(str(output_path))
                new_doc.close()
                
                output_files.append(output_path)
                pages_split += (end_idx - start_idx)
                
                logger.info(f"Created: {output_path} ({end_idx - start_idx} pages)")
        
        finally:
            doc.close()
        
        return SplitResult(
            success=len(self.errors) == 0,
            output_files=output_files,
            errors=self.errors,
            total_pages=total_pages,
            pages_split=pages_split
        )
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe filesystem use.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        import re
        
        if not filename:
            return "document.pdf"
        
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"|?*]', '_', filename)
        
        # Ensure it ends with .pdf
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        # Limit length
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1)
            filename = name[:195] + '.' + ext
        
        return filename
    
    def _get_unique_filename(self, path: Path) -> Path:
        """
        Get a unique filename by appending a counter if needed.
        
        Args:
            path: Desired file path
            
        Returns:
            Unique path that doesn't exist
        """
        if not path.exists():
            return path
        
        counter = 1
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # Safety limit
            if counter > 999:
                import uuid
                new_name = f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
                return parent / new_name


class MultiPageScanProcessor:
    """
    High-level processor for multi-page scanned documents.
    Combines analysis, review, and splitting.
    """
    
    def __init__(self, llm_handler=None):
        """
        Initialize the processor.
        
        Args:
            llm_handler: Optional LLM handler for intelligent analysis
        """
        from ..core.multi_page_analyzer import MultiPageDocumentAnalyzer
        
        self.analyzer = MultiPageDocumentAnalyzer(llm_handler)
        self.splitter = PDFDocumentSplitter()
    
    def process_pdf(self, pdf_path: Path, parent_widget=None) -> SplitResult:
        """
        Process a multi-page PDF through the full pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            parent_widget: Parent widget for showing dialogs
            
        Returns:
            SplitResult with operation results
        """
        from PyQt6.QtWidgets import QApplication
        
        # Step 1: Extract page contents
        logger.info(f"Processing PDF: {pdf_path}")
        pages = self._extract_pages(pdf_path)
        
        if not pages:
            return SplitResult(
                success=False,
                output_files=[],
                errors=["Could not extract pages from PDF"],
                total_pages=0,
                pages_split=0
            )
        
        # Step 2: Analyze for document boundaries
        logger.info(f"Analyzing {len(pages)} pages...")
        analysis_result = self.analyzer.analyze_pages(pages)
        
        logger.info(f"Detected {len(analysis_result.detected_segments)} document segments")
        
        # Step 3: Show review dialog if segments found
        if analysis_result.detected_segments and parent_widget is not None:
            from .multi_page_dialog import MultiPageReviewDialog
            
            dialog = MultiPageReviewDialog(analysis_result, pdf_path, parent_widget)
            
            result = None
            
            def on_accepted(segments, output_dir):
                nonlocal result
                # Step 4: Split the PDF
                result = self.splitter.split_document(pdf_path, segments, output_dir)
            
            def on_rejected():
                nonlocal result
                result = SplitResult(
                    success=False,
                    output_files=[],
                    errors=["User cancelled operation"],
                    total_pages=0,
                    pages_split=0
                )
            
            dialog.segments_accepted.connect(on_accepted)
            dialog.segments_rejected.connect(on_rejected)
            
            dialog.exec()
            
            return result or SplitResult(
                success=False,
                output_files=[],
                errors=["Dialog closed without action"],
                total_pages=0,
                pages_split=0
            )
        
        elif analysis_result.detected_segments:
            # No UI - split automatically
            logger.info("No parent widget, splitting automatically")
            return self.splitter.split_document(
                pdf_path, 
                analysis_result.detected_segments,
                pdf_path.parent
            )
        
        else:
            # No segments detected
            return SplitResult(
                success=False,
                output_files=[],
                errors=["No document segments detected"],
                total_pages=len(pages),
                pages_split=0
            )
    
    def _extract_pages(self, pdf_path: Path) -> List[tuple]:
        """
        Extract text content from each page of a PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of (page_number, text_content) tuples
        """
        pages = []
        
        # Try PyMuPDF first
        try:
            import fitz
            
            with fitz.open(str(pdf_path)) as doc:
                for page_num, page in enumerate(doc, 1):
                    text = page.get_text()
                    pages.append((page_num, text))
            
            return pages
            
        except ImportError:
            logger.warning("PyMuPDF not available for page extraction")
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
        
        # Fallback to pdfplumber
        try:
            import pdfplumber
            
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    pages.append((page_num, text))
            
            return pages
            
        except ImportError:
            logger.error("No PDF extraction library available")
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
        
        return pages
