# Multi-Page Document Scanning Feature

This feature adds intelligent multi-page document scanning to SortMind, allowing automatic detection and splitting of multiple documents within a single scanned PDF.

## Features

### 🔍 Automatic Document Boundary Detection
The system analyzes scanned pages and detects when one document ends and another begins using:

- **Blank page detection** - Uses blank pages as natural delimiters
- **Document type changes** - Detects switches between bank statements, mortgage docs, etc.
- **Account number changes** - Identifies different accounts
- **Date changes** - Recognizes new statement periods
- **Institution changes** - Detects different banks/companies

### 📋 Supported Document Types

- Bank statements (checking, savings)
- Mortgage statements
- Credit card statements
- Investment/brokerage statements
- Utility bills
- Insurance documents
- Tax documents (W-2, 1099, etc.)

### 🖥️ User Interface

The review dialog shows:
- Detected document segments with page ranges
- Suggested filenames based on document content
- Confidence scores for each split
- Document metadata (institution, date, account number)
- Page-by-page preview
- Ability to edit filenames before splitting

## Installation

### Required Dependencies

```bash
# Core PDF processing
pip install PyMuPDF  # or
pip install PyPDF2

# For scanned PDF OCR (optional)
pip install pdfplumber

# For local LLM analysis (optional but recommended)
pip install ollama
```

### File Structure

```
src/
├── core/
│   ├── multi_page_analyzer.py      # Document boundary detection
│   ├── document_splitter.py         # PDF splitting logic
│   └── multi_page_integration.py    # Menu integration
└── ui/dialogs/
    └── multi_page_dialog.py         # Review dialog UI
```

## Usage

### From the UI

1. Go to **Tools → Split Multi-Page Scan...** (or press Ctrl+M)
2. Select your multi-page scanned PDF
3. Review the detected document boundaries
4. Edit suggested filenames if needed
5. Click "Accept & Split Documents"

### Programmatic Usage

```python
from src.core.multi_page_analyzer import MultiPageDocumentAnalyzer
from src.core.document_splitter import PDFDocumentSplitter

# Analyze a PDF
analyzer = MultiPageDocumentAnalyzer()
pages = [(1, "text from page 1"), (2, "text from page 2"), ...]
result = analyzer.analyze_pages(pages)

# Split the PDF
splitter = PDFDocumentSplitter()
result = splitter.split_document(
    source_path=Path("scan.pdf"),
    segments=result.detected_segments,
    output_directory=Path("output/")
)

print(f"Created {len(result.output_files)} documents")
```

## How It Works

### 1. Page Analysis
Each page is analyzed for:
- Whether it's blank (using text density and whitespace ratio)
- Document type (using keyword patterns)
- Dates (statement dates, periods)
- Account numbers
- Institution names

### 2. Boundary Detection
The system looks for:
1. **Blank pages** - Strongest signal, always creates a split
2. **Document type changes** - Bank statement → Mortgage statement
3. **Account number changes** - Different account numbers
4. **Institution changes** - Different banks
5. **Date discontinuities** - Gaps in statement periods

### 3. Filename Generation
Suggested filenames include:
- Institution name (e.g., "Chase_Bank")
- Document type (e.g., "bank_statement")
- Date (e.g., "2024-01")
- Account suffix (e.g., "acct-1234")

Example: `Chase_Bank_bank_statement_2024-01_acct-1234.pdf`

### 4. User Review
Before splitting, the user can:
- Review all detected segments
- Edit suggested filenames
- Add manual split points
- Merge segments
- Preview page content
- Choose output directory

## Configuration

### Blank Page Detection

Adjust sensitivity in `multi_page_analyzer.py`:

```python
blank_detector = BlankPageDetector(
    text_threshold=50,        # Min characters to be non-blank
    whitespace_threshold=0.95  # Max whitespace ratio
)
```

### Document Type Patterns

Add custom document types in `DocumentBoundaryDetector.DOC_PATTERNS`:

```python
'custom_document': [
    r'pattern 1',
    r'pattern 2',
]
```

## Integration with Main Application

Add to your `app_controller.py` or `main_window.py`:

```python
from src.core.multi_page_integration import add_multi_page_scan_menu

# In your setup method:
add_multi_page_scan_menu(self, self.menuBar())
```

## Testing

Run the integration test:

```bash
cd /Users/ripley/.openclaw/workspace/file_organizer
python3 src/core/multi_page_integration.py
```

Or test with a sample PDF:

```bash
python3 -c "
from src.core.document_splitter import MultiPageScanProcessor
from pathlib import Path

processor = MultiPageScanProcessor()
result = processor.process_pdf(Path('test_scan.pdf'))
print(f'Success: {result.success}')
print(f'Created: {result.output_files}')
"
```

## Troubleshooting

### "No PDF library available"
Install PyMuPDF or PyPDF2:
```bash
pip install PyMuPDF
```

### Blank pages not detected
Adjust the `text_threshold` parameter. Lower values detect more pages as blank.

### Wrong document type detected
Add more specific keywords to `DOC_PATTERNS` for that document type.

### Low confidence scores
The LLM can help improve detection. Make sure Ollama is running with a model:
```bash
ollama run llama3.2:3b
```

## Future Enhancements

- [ ] Machine learning model for document classification
- [ ] Support for more file formats (TIFF, JPEG2000)
- [ ] Batch processing multiple scans
- [ ] Automatic OCR for better text extraction
- [ ] Integration with cloud storage (Dropbox, Google Drive)
- [ ] Duplicate detection across split documents

## License

Part of the SortMind File Organizer project.
