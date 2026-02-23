"""
Multi-page document analyzer with automatic document boundary detection.

Features:
- Detects blank pages as delimiters
- Identifies document type changes (bank statement vs mortgage)
- Detects date/account number changes
- Uses local LLM for intelligent boundary detection
- Groups pages into logical documents
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

try:
    import numpy as np
except ImportError:
    # Fallback for systems without numpy
    class FakeNp:
        @staticmethod
        def mean(values):
            if not values:
                return 0.0
            return sum(values) / len(values)
    np = FakeNp()

logger = logging.getLogger(__name__)


@dataclass
class PageAnalysis:
    """Analysis of a single page."""
    page_number: int
    text_content: str
    is_blank: bool = False
    detected_date: Optional[str] = None
    document_type: Optional[str] = None
    account_number: Optional[str] = None
    institution: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentSegment:
    """A detected document segment (group of pages)."""
    start_page: int
    end_page: int
    pages: List[PageAnalysis] = field(default_factory=list)
    document_type: Optional[str] = None
    date_range: Optional[str] = None
    institution: Optional[str] = None
    account_number: Optional[str] = None
    suggested_filename: Optional[str] = None
    confidence: float = 0.0
    split_reason: str = ""


@dataclass
class MultiPageAnalysisResult:
    """Result of analyzing a multi-page document."""
    source_path: Path
    total_pages: int
    detected_segments: List[DocumentSegment]
    blank_page_indices: List[int]
    analysis_confidence: float = 0.0
    needs_review: bool = False


class BlankPageDetector:
    """Detects blank pages in scanned documents."""
    
    def __init__(self, text_threshold: int = 50, whitespace_threshold: float = 0.95):
        """
        Initialize blank page detector.
        
        Args:
            text_threshold: Minimum character count to consider non-blank
            whitespace_threshold: Maximum ratio of whitespace to consider non-blank
        """
        self.text_threshold = text_threshold
        self.whitespace_threshold = whitespace_threshold
    
    def is_blank(self, text_content: str) -> bool:
        """
        Determine if a page is blank based on content analysis.
        
        Args:
            text_content: Extracted text from the page
            
        Returns:
            True if page is considered blank
        """
        if not text_content:
            return True
        
        # Remove common scanning artifacts
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text_content)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Check character count
        if len(cleaned) < self.text_threshold:
            return True
        
        # Check whitespace ratio
        if len(cleaned) > 0:
            whitespace_ratio = (cleaned.count(' ') + cleaned.count('\n')) / len(cleaned)
            if whitespace_ratio > self.whitespace_threshold:
                return True
        
        return False


class DocumentBoundaryDetector:
    """Detects boundaries between different documents in a multi-page scan."""
    
    # Document type patterns
    DOC_PATTERNS = {
        'bank_statement': [
            r'(?:statement|account statement|bank statement)',
            r'(?:checking|savings|account)\s*(?:#|number|no)',
            r'(?:opening balance|closing balance|transactions)',
            r'(?:deposits|withdrawals|checks paid)'
        ],
        'mortgage_statement': [
            r'(?:mortgage|home loan|mortgage statement)',
            r'(?:principal|interest|escrow)',
            r'(?:loan number|account number)\s*[:\-]?\s*\d+',
            r'(?:payment due|monthly payment)'
        ],
        'credit_card_statement': [
            r'(?:credit card|card statement|visa|mastercard|amex)',
            r'(?:credit limit|available credit|minimum payment)',
            r'(?:previous balance|new balance|purchases)',
            r'(?:account ending in|card ending in)'
        ],
        'investment_statement': [
            r'(?:investment|brokerage|portfolio|401k|ira)',
            r'(?:market value|positions|holdings|performance)',
            r'(?:buy|sell|dividend|capital gains)',
            r'(?:securities|equities|bonds|funds)'
        ],
        'utility_bill': [
            r'(?:electric|gas|water|utility)\s*(?:bill|statement)',
            r'(?:meter reading|usage|kwh|therms|gallons)',
            r'(?:service address|account number)\s*[:\-]?',
            r'(?:amount due|total amount|payment due)'
        ],
        'insurance_document': [
            r'(?:insurance|policy|coverage|premium)',
            r'(?:policy number|insurance id|group number)',
            r'(?:effective date|expiration|renewal)',
            r'(?:auto insurance|home insurance|health insurance)'
        ],
        'tax_document': [
            r'(?:tax|irs|form 1040|w-2|1099)',
            r'(?:tax year|filing status|adjusted gross income)',
            r'(?:federal tax|state tax|refund|amount owed)',
            r'(?:employer id|ein|ssn|taxpayer)'
        ],
    }
    
    def __init__(self, llm_handler=None):
        """
        Initialize boundary detector.
        
        Args:
            llm_handler: Optional LLM handler for intelligent analysis
        """
        self.llm_handler = llm_handler
        self.blank_detector = BlankPageDetector()
    
    def detect_document_type(self, text_content: str) -> Tuple[Optional[str], float]:
        """
        Detect document type from content.
        
        Args:
            text_content: Page text content
            
        Returns:
            Tuple of (document_type, confidence)
        """
        text_lower = text_content.lower()
        scores = {}
        
        for doc_type, patterns in self.DOC_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[doc_type] = score / len(patterns)
        
        if scores:
            best_match = max(scores, key=scores.get)
            return best_match, scores[best_match]
        
        return None, 0.0
    
    def extract_date(self, text_content: str) -> Optional[str]:
        """
        Extract date from document content.
        
        Args:
            text_content: Page text content
            
        Returns:
            Detected date string or None
        """
        # Common date patterns
        date_patterns = [
            # Statement Date: MM/DD/YYYY
            r'(?:statement date|date|period ending)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            # Month DD, YYYY
            r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
            # MM/DD/YYYY - MM/DD/YYYY (date range)
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*[-–]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def extract_account_number(self, text_content: str) -> Optional[str]:
        """
        Extract account number from document.
        
        Args:
            text_content: Page text content
            
        Returns:
            Account number string or None
        """
        # Account number patterns
        patterns = [
            r'(?:account|acct|loan)\s*(?:#|number|no)[:\s]*([\d\-Xx*]+)',
            r'(?:account|acct)[:\s]*([\d\-Xx*]{4,})',
            r'(?:ending in|ending)[:\s]*([\dXx*]{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_institution(self, text_content: str) -> Optional[str]:
        """
        Extract financial institution name.
        
        Args:
            text_content: Page text content
            
        Returns:
            Institution name or None
        """
        # Look for institution names in first few lines
        lines = text_content.strip().split('\n')[:5]
        
        for line in lines:
            line = line.strip()
            # Skip common header/footer text
            if any(skip in line.lower() for skip in ['page', 'confidential', 'www.', 'http']):
                continue
            # Look for institution-like names (2-4 words, capitalized)
            words = line.split()
            if 2 <= len(words) <= 5:
                if all(w[0].isupper() for w in words if w):
                    return line
        
        return None


class MultiPageDocumentAnalyzer:
    """Main analyzer for multi-page scanned documents."""
    
    def __init__(self, llm_handler=None, blank_threshold: int = 50):
        """
        Initialize the multi-page analyzer.
        
        Args:
            llm_handler: Optional LLM handler for intelligent analysis
            blank_threshold: Character threshold for blank page detection
        """
        self.boundary_detector = DocumentBoundaryDetector(llm_handler)
        self.blank_detector = BlankPageDetector(text_threshold=blank_threshold)
        self.llm_handler = llm_handler
    
    def analyze_pages(self, pages: List[Tuple[int, str]]) -> MultiPageAnalysisResult:
        """
        Analyze a list of pages to detect document boundaries.
        
        Args:
            pages: List of (page_number, text_content) tuples
            
        Returns:
            MultiPageAnalysisResult with detected segments
        """
        if not pages:
            return MultiPageAnalysisResult(
                source_path=Path(),
                total_pages=0,
                detected_segments=[],
                blank_page_indices=[]
            )
        
        # Analyze each page
        page_analyses = []
        blank_indices = []
        
        for page_num, text in pages:
            analysis = self._analyze_single_page(page_num, text)
            page_analyses.append(analysis)
            
            if analysis.is_blank:
                blank_indices.append(page_num)
        
        # Detect document boundaries
        segments = self._detect_boundaries(page_analyses)
        
        # Calculate overall confidence
        avg_confidence = np.mean([s.confidence for s in segments]) if segments else 0.0
        
        # Determine if review is needed
        needs_review = (
            avg_confidence < 0.7 or
            len(segments) == 0 or
            any(s.confidence < 0.5 for s in segments)
        )
        
        return MultiPageAnalysisResult(
            source_path=Path(),
            total_pages=len(pages),
            detected_segments=segments,
            blank_page_indices=blank_indices,
            analysis_confidence=avg_confidence,
            needs_review=needs_review
        )
    
    def _analyze_single_page(self, page_number: int, text_content: str) -> PageAnalysis:
        """Analyze a single page."""
        # Detect if blank
        is_blank = self.blank_detector.is_blank(text_content)
        
        # Extract information
        doc_type, confidence = self.boundary_detector.detect_document_type(text_content)
        date = self.boundary_detector.extract_date(text_content)
        account = self.boundary_detector.extract_account_number(text_content)
        institution = self.boundary_detector.extract_institution(text_content)
        
        return PageAnalysis(
            page_number=page_number,
            text_content=text_content,
            is_blank=is_blank,
            detected_date=date,
            document_type=doc_type,
            account_number=account,
            institution=institution,
            confidence=confidence
        )
    
    def _detect_boundaries(self, page_analyses: List[PageAnalysis]) -> List[DocumentSegment]:
        """
        Detect document boundaries from page analyses.
        
        Uses multiple signals:
        1. Blank pages (strong delimiter)
        2. Document type changes
        3. Account number changes
        4. Date changes (new statement period)
        5. LLM analysis (if available)
        """
        if not page_analyses:
            return []
        
        segments = []
        current_segment_pages = [page_analyses[0]]
        
        for i in range(1, len(page_analyses)):
            prev_page = page_analyses[i - 1]
            curr_page = page_analyses[i]
            
            # Check for boundary signals
            is_boundary = False
            boundary_reason = ""
            
            # Signal 1: Blank page
            if curr_page.is_blank:
                is_boundary = True
                boundary_reason = "Blank page delimiter"
            
            # Signal 2: Document type change
            elif (prev_page.document_type and curr_page.document_type and
                  prev_page.document_type != curr_page.document_type):
                is_boundary = True
                boundary_reason = f"Document type change: {prev_page.document_type} → {curr_page.document_type}"
            
            # Signal 3: Account number change
            elif (prev_page.account_number and curr_page.account_number and
                  prev_page.account_number != curr_page.account_number):
                is_boundary = True
                boundary_reason = "Account number change"
            
            # Signal 4: Institution change
            elif (prev_page.institution and curr_page.institution and
                  prev_page.institution != curr_page.institution):
                is_boundary = True
                boundary_reason = "Institution change"
            
            if is_boundary:
                # Save current segment
                segment = self._create_segment(current_segment_pages, boundary_reason)
                segments.append(segment)
                
                # Start new segment (skip blank pages)
                if not curr_page.is_blank:
                    current_segment_pages = [curr_page]
                else:
                    current_segment_pages = []
            else:
                current_segment_pages.append(curr_page)
        
        # Add final segment
        if current_segment_pages:
            segment = self._create_segment(current_segment_pages, "End of document")
            segments.append(segment)
        
        return segments
    
    def _create_segment(self, pages: List[PageAnalysis], split_reason: str) -> DocumentSegment:
        """Create a document segment from a list of pages."""
        if not pages:
            return DocumentSegment(start_page=0, end_page=0)
        
        # Aggregate information from all pages
        doc_types = [p.document_type for p in pages if p.document_type]
        dates = [p.detected_date for p in pages if p.detected_date]
        accounts = [p.account_number for p in pages if p.account_number]
        institutions = [p.institution for p in pages if p.institution]
        
        # Use most common values
        from collections import Counter
        
        doc_type = Counter(doc_types).most_common(1)[0][0] if doc_types else None
        institution = Counter(institutions).most_common(1)[0][0] if institutions else None
        account = accounts[0] if accounts else None  # Use first occurrence
        date = dates[0] if dates else None
        
        # Generate suggested filename
        suggested_name = self._generate_filename(doc_type, institution, account, date, pages[0].page_number)
        
        # Calculate confidence
        confidences = [p.confidence for p in pages]
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        return DocumentSegment(
            start_page=pages[0].page_number,
            end_page=pages[-1].page_number,
            pages=pages,
            document_type=doc_type,
            date_range=date,
            institution=institution,
            account_number=account,
            suggested_filename=suggested_name,
            confidence=avg_confidence,
            split_reason=split_reason
        )
    
    def _generate_filename(self, doc_type: Optional[str], institution: Optional[str],
                          account: Optional[str], date: Optional[str],
                          page_num: int) -> str:
        """Generate a suggested filename for a document segment."""
        parts = []
        
        # Institution
        if institution:
            # Clean up institution name
            inst_clean = re.sub(r'[^\w\s]', '', institution).strip()
            inst_clean = inst_clean.replace(' ', '_')
            parts.append(inst_clean[:30])  # Limit length
        
        # Document type
        if doc_type:
            parts.append(doc_type)
        
        # Date
        if date:
            # Try to normalize date
            date_clean = re.sub(r'[/\\\s]', '-', date)
            parts.append(date_clean)
        
        # Account number (last 4 digits)
        if account:
            account_suffix = account[-4:] if len(account) >= 4 else account
            parts.append(f"acct-{account_suffix}")
        
        if parts:
            filename = '_'.join(parts) + '.pdf'
        else:
            filename = f"document_pages_{page_num}.pdf"
        
        # Sanitize
        filename = re.sub(r'[^\w\s\.\-]', '_', filename)
        
        return filename
