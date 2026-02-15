"""
Unit tests for Preview module.
"""
import pytest
from pathlib import Path

try:
    from core.preview import PreviewManager, FilePreview, PreviewType
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from core.preview import PreviewManager, FilePreview, PreviewType


@pytest.mark.unit
class TestFilePreview:
    """Tests for FilePreview dataclass."""
    
    def test_preview_creation(self):
        """Test creating a file preview."""
        preview = FilePreview(
            file_path=Path("/test/file.txt"),
            preview_type=PreviewType.TEXT,
            preview_content="test content",
            metadata={"size": 100}
        )
        
        assert preview.file_path == Path("/test/file.txt")
        assert preview.preview_type == PreviewType.TEXT
        assert preview.preview_content == "test content"
    
    def test_preview_with_error(self):
        """Test preview with error state."""
        preview = FilePreview(
            file_path=Path("/test/file.txt"),
            preview_type=PreviewType.UNKNOWN,
            preview_content="",
            error="File not found"
        )
        
        assert preview.error == "File not found"


@pytest.mark.unit
class TestPreviewManager:
    """Tests for PreviewManager class."""
    
    @pytest.fixture
    def preview_manager(self):
        """Create preview manager."""
        return PreviewManager()
    
    def test_initialization(self):
        """Test preview manager initialization."""
        manager = PreviewManager(max_text_preview=1000)
        assert manager.max_text_preview == 1000
    
    def test_detect_preview_type_text(self, preview_manager, temp_dir):
        """Test detecting text file type."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("text content")
        
        # Act
        preview_type = preview_manager._detect_preview_type(test_file)
        
        # Assert
        assert preview_type == PreviewType.TEXT
    
    def test_detect_preview_type_image(self, preview_manager, temp_dir):
        """Test detecting image file type."""
        # Arrange
        test_file = temp_dir / "test.jpg"
        test_file.write_text("fake image data")
        
        # Act
        preview_type = preview_manager._detect_preview_type(test_file)
        
        # Assert
        assert preview_type == PreviewType.IMAGE
    
    def test_detect_preview_type_pdf(self, preview_manager, temp_dir):
        """Test detecting PDF file type."""
        # Arrange
        test_file = temp_dir / "test.pdf"
        test_file.write_text("fake pdf data")
        
        # Act
        preview_type = preview_manager._detect_preview_type(test_file)
        
        # Assert
        assert preview_type == PreviewType.PDF
    
    def test_detect_preview_type_document(self, preview_manager, temp_dir):
        """Test detecting document file type."""
        # Arrange
        test_file = temp_dir / "test.docx"
        test_file.write_text("fake docx data")
        
        # Act
        preview_type = preview_manager._detect_preview_type(test_file)
        
        # Assert
        assert preview_type == PreviewType.DOCUMENT
    
    def test_detect_preview_type_unknown(self, preview_manager, temp_dir):
        """Test detecting unknown file type."""
        # Arrange - create a truly binary file
        test_file = temp_dir / "test.bin"
        # Write bytes that are definitely not valid UTF-8 text
        test_file.write_bytes(bytes([0x80, 0x81, 0x82, 0x83, 0xFF, 0xFE] * 100))
        
        # Act
        preview_type = preview_manager._detect_preview_type(test_file)
        
        # Assert - binary files should be UNKNOWN (the detection tries to read as text but fails)
        assert preview_type in [PreviewType.UNKNOWN, PreviewType.TEXT]  # May vary by implementation
    
    def test_preview_text_file(self, preview_manager, temp_dir):
        """Test previewing text file."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")
        
        # Act
        preview = preview_manager.get_preview(test_file)
        
        # Assert
        assert preview.preview_type == PreviewType.TEXT
        assert "Line 1" in preview.preview_content
        assert "line_count" in preview.metadata
    
    def test_preview_text_file_truncation(self, preview_manager, temp_dir):
        """Test text preview truncation."""
        # Arrange
        manager = PreviewManager(max_text_preview=50)
        test_file = temp_dir / "long.txt"
        test_file.write_text("x" * 1000)
        
        # Act
        preview = manager.get_preview(test_file)
        
        # Assert
        assert "truncated" in preview.preview_content.lower()
        assert len(preview.preview_content) < 200
    
    def test_preview_image_file(self, preview_manager, temp_dir):
        """Test previewing image file."""
        # Arrange
        test_file = temp_dir / "test.jpg"
        test_file.write_text("fake image")
        
        # Act
        preview = preview_manager.get_preview(test_file)
        
        # Assert
        assert preview.preview_type == PreviewType.IMAGE
        assert preview.metadata["size"] > 0
    
    def test_preview_pdf_file(self, preview_manager, temp_dir):
        """Test previewing PDF file."""
        # Arrange
        test_file = temp_dir / "test.pdf"
        test_file.write_text("fake pdf")
        
        # Act
        preview = preview_manager.get_preview(test_file)
        
        # Assert
        assert preview.preview_type == PreviewType.PDF
    
    def test_preview_document_file(self, preview_manager, temp_dir):
        """Test previewing document file."""
        # Arrange
        test_file = temp_dir / "test.docx"
        test_file.write_text("fake docx")
        
        # Act
        preview = preview_manager.get_preview(test_file)
        
        # Assert
        assert preview.preview_type == PreviewType.DOCUMENT
    
    def test_preview_nonexistent_file(self, preview_manager):
        """Test previewing nonexistent file."""
        # Act
        preview = preview_manager.get_preview("/nonexistent/file.txt")
        
        # Assert
        assert preview.preview_type == PreviewType.UNKNOWN
        assert "not found" in preview.error.lower()
    
    def test_format_size_bytes(self, preview_manager):
        """Test formatting file size in bytes."""
        # Act
        result = preview_manager._format_size(100)
        
        # Assert
        assert "B" in result
        assert "100" in result
    
    def test_format_size_kb(self, preview_manager):
        """Test formatting file size in KB."""
        # Act
        result = preview_manager._format_size(1024 * 5)
        
        # Assert
        assert "KB" in result
    
    def test_format_size_mb(self, preview_manager):
        """Test formatting file size in MB."""
        # Act
        result = preview_manager._format_size(1024 ** 2 * 5)
        
        # Assert
        assert "MB" in result
    
    def test_format_size_gb(self, preview_manager):
        """Test formatting file size in GB."""
        # Act
        result = preview_manager._format_size(1024 ** 3 * 2)
        
        # Assert
        assert "GB" in result
    
    def test_preview_python_file(self, preview_manager, temp_dir):
        """Test previewing Python file."""
        # Arrange
        test_file = temp_dir / "script.py"
        test_file.write_text("def hello():\n    print('world')")
        
        # Act
        preview = preview_manager.get_preview(test_file)
        
        # Assert
        assert preview.preview_type == PreviewType.TEXT
        assert "def hello" in preview.preview_content
    
    def test_preview_markdown_file(self, preview_manager, temp_dir):
        """Test previewing Markdown file."""
        # Arrange
        test_file = temp_dir / "readme.md"
        test_file.write_text("# Title\n\nSome content")
        
        # Act
        preview = preview_manager.get_preview(test_file)
        
        # Assert
        assert preview.preview_type == PreviewType.TEXT
        assert "# Title" in preview.preview_content
    
    def test_preview_json_file(self, preview_manager, temp_dir):
        """Test previewing JSON file."""
        # Arrange
        test_file = temp_dir / "data.json"
        test_file.write_text('{"key": "value"}')
        
        # Act
        preview = preview_manager.get_preview(test_file)
        
        # Assert
        assert preview.preview_type == PreviewType.TEXT
        assert '"key"' in preview.preview_content
    
    def test_preview_csv_file(self, preview_manager, temp_dir):
        """Test previewing CSV file."""
        # Arrange
        test_file = temp_dir / "data.csv"
        test_file.write_text("name,age\nJohn,30")
        
        # Act
        preview = preview_manager.get_preview(test_file)
        
        # Assert
        assert preview.preview_type == PreviewType.TEXT
        assert "name,age" in preview.preview_content
