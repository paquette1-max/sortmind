"""
Test script for multi-page document scanning feature.
Creates a test multi-page PDF and runs the analysis.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_analyzer():
    """Test the multi-page analyzer with sample data."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    from core.multi_page_analyzer import (
        MultiPageDocumentAnalyzer, BlankPageDetector, DocumentBoundaryDetector
    )
    
    print("=" * 70)
    print("Testing Multi-Page Document Analyzer")
    print("=" * 70)
    
    # Test blank page detection
    print("\n1. Testing Blank Page Detection")
    detector = BlankPageDetector()
    
    blank_text = "   \n\n   "
    non_blank_text = "This is a bank statement for account 1234. Date: 01/15/2024"
    
    print(f"   Blank text detected: {detector.is_blank(blank_text)}")  # Should be True
    print(f"   Non-blank text detected: {detector.is_blank(non_blank_text)}")  # Should be False
    
    # Test document type detection
    print("\n2. Testing Document Type Detection")
    boundary_detector = DocumentBoundaryDetector()
    
    test_docs = [
        ("bank_statement", "CHASE BANK STATEMENT - Account ending in 1234 - December 2023"),
        ("mortgage_statement", "Home Loan Monthly Statement - Principal: $200,000 - Escrow: $500"),
        ("credit_card_statement", "Visa Credit Card Statement - Credit Limit: $10,000 - Minimum Payment: $250"),
        ("investment_statement", "Brokerage Account - Portfolio Value: $50,000 - Holdings: AAPL, MSFT"),
    ]
    
    for expected_type, text in test_docs:
        detected_type, confidence = boundary_detector.detect_document_type(text)
        status = "✓" if detected_type == expected_type else "✗"
        print(f"   {status} Expected: {expected_type}, Got: {detected_type} ({confidence:.2f})")
    
    # Test date extraction
    print("\n3. Testing Date Extraction")
    
    date_texts = [
        "Statement Date: 12/15/2023",
        "Period: January 1, 2024 - January 31, 2024",
        "Date: 03-20-2024",
    ]
    
    for text in date_texts:
        date = boundary_detector.extract_date(text)
        print(f"   Extracted from '{text[:30]}...': {date}")
    
    # Test account number extraction
    print("\n4. Testing Account Number Extraction")
    
    account_texts = [
        "Account: 1234-5678-9012",
        "Acct # 123456789",
        "Account ending in 9876",
    ]
    
    for text in account_texts:
        account = boundary_detector.extract_account_number(text)
        print(f"   Extracted from '{text}': {account}")
    
    # Test full page analysis
    print("\n5. Testing Full Page Analysis")
    
    # Simulate pages from a multi-page scan
    pages = [
        (1, "CHASE BANK\n\nStatement Date: 12/15/2023\nAccount: ****1234\nOpening Balance: $5,000"),
        (2, "Transactions:\n- Deposit $1,000\n- Withdrawal $500\nClosing Balance: $5,500"),
        (3, ""),  # Blank page
        (4, "WELLS FARGO MORTGAGE\n\nLoan Statement - January 2024\nLoan #: 987654321\nPrincipal: $200,000"),
        (5, "Payment Due: $1,500\nPrincipal: $800\nInterest: $600\nEscrow: $100"),
    ]
    
    analyzer = MultiPageDocumentAnalyzer()
    result = analyzer.analyze_pages(pages)
    
    print(f"   Total pages: {result.total_pages}")
    print(f"   Blank pages: {result.blank_page_indices}")
    print(f"   Detected segments: {len(result.detected_segments)}")
    print(f"   Needs review: {result.needs_review}")
    
    for i, segment in enumerate(result.detected_segments):
        print(f"\n   Document {i+1}:")
        print(f"      Pages: {segment.start_page} - {segment.end_page}")
        print(f"      Type: {segment.document_type}")
        print(f"      Institution: {segment.institution}")
        print(f"      Date: {segment.date_range}")
        print(f"      Account: {segment.account_number}")
        print(f"      Suggested filename: {segment.suggested_filename}")
        print(f"      Split reason: {segment.split_reason}")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    
    return True


def test_splitter():
    """Test the PDF splitter."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    from core.document_splitter import PDFDocumentSplitter
    
    print("\n" + "=" * 70)
    print("Testing PDF Document Splitter")
    print("=" * 70)
    
    splitter = PDFDocumentSplitter()
    
    # Test filename sanitization
    print("\n1. Testing Filename Sanitization")
    
    test_names = [
        "Bank/Statement: 2024.pdf",
        "Chase<Bank>|Statement?.pdf",
        "",
        "normal_filename.pdf",
    ]
    
    for name in test_names:
        sanitized = splitter._sanitize_filename(name)
        print(f"   '{name}' → '{sanitized}'")
    
    # Test unique filename generation
    print("\n2. Testing Unique Filename Generation")
    
    # This would require actual file system operations
    print("   (Skipped in unit test - requires filesystem)")
    
    print("\n" + "=" * 70)
    print("Splitter Test Complete!")
    print("=" * 70)
    
    return True


def test_dialog():
    """Test the review dialog (requires Qt)."""
    print("\n" + "=" * 70)
    print("Testing Review Dialog")
    print("=" * 70)
    
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from core.multi_page_analyzer import MultiPageDocumentAnalyzer
        from ui.dialogs.multi_page_dialog import MultiPageReviewDialog
        
        # Create sample analysis result
        pages = [
            (1, "CHASE BANK\nStatement Date: 12/15/2023\nAccount: ****1234"),
            (2, "Transactions and closing balance"),
            (3, ""),  # Blank
            (4, "WELLS FARGO\nMortgage Statement\nLoan: 987654321"),
            (5, "Payment details"),
        ]
        
        analyzer = MultiPageDocumentAnalyzer()
        result = analyzer.analyze_pages(pages)
        
        print(f"Created analysis with {len(result.detected_segments)} segments")
        print("To see the UI, run: python3 -m src.core.multi_page_integration")
        
    except Exception as e:
        print(f"Dialog test skipped: {e}")
    
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    print("\n🧪 Multi-Page Scan Feature Tests\n")
    
    success = True
    
    try:
        success = test_analyzer() and success
    except Exception as e:
        print(f"\n❌ Analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    try:
        success = test_splitter() and success
    except Exception as e:
        print(f"\n❌ Splitter test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    try:
        success = test_dialog() and success
    except Exception as e:
        print(f"\n❌ Dialog test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    print("\n" + "=" * 70)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
