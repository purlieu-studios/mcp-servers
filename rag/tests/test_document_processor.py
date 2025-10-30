"""Tests for document processor."""

from src.document_processor import Document, DocumentProcessor


class TestDocument:
    """Test Document dataclass."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            content="test content",
            file_path="/test/file.txt",
            file_type=".txt",
            metadata={"size": 100},
        )

        assert doc.content == "test content"
        assert doc.file_path == "/test/file.txt"
        assert doc.file_type == ".txt"
        assert doc.metadata == {"size": 100}


class TestDocumentProcessor:
    """Test DocumentProcessor class."""

    def test_initialization(self):
        """Test processor initialization."""
        processor = DocumentProcessor(
            file_types=[".txt", ".py", ".md"], exclude_patterns=["*.tmp", "node_modules/"]
        )

        assert processor.file_types == {".txt", ".py", ".md"}
        assert processor.exclude_patterns == ["*.tmp", "node_modules/"]

    def test_load_file_success(self, temp_dir):
        """Test loading a valid file."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, world!")

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        doc = processor.load_file(str(test_file))

        assert doc is not None
        assert doc.content == "Hello, world!"
        assert doc.file_path == str(test_file)
        assert doc.file_type == ".txt"
        assert doc.metadata["size"] > 0
        assert "modified" in doc.metadata

    def test_load_file_nonexistent(self):
        """Test loading nonexistent file."""
        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        doc = processor.load_file("/nonexistent/file.txt")

        assert doc is None

    def test_load_file_wrong_type(self, temp_dir):
        """Test loading file with unsupported type."""
        # Create file with unsupported extension
        test_file = temp_dir / "test.xyz"
        test_file.write_text("content")

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        doc = processor.load_file(str(test_file))

        assert doc is None

    def test_load_file_utf8_encoding(self, temp_dir):
        """Test loading UTF-8 encoded file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("UTF-8 text: é, ñ, 中文", encoding="utf-8")

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        doc = processor.load_file(str(test_file))

        assert doc is not None
        assert "é" in doc.content
        assert "中文" in doc.content

    def test_load_file_fallback_encoding(self, temp_dir):
        """Test loading file with latin-1 encoding."""
        test_file = temp_dir / "test.txt"
        # Write with latin-1 encoding
        test_file.write_bytes(b"Latin-1: \xe9\xf1")

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        doc = processor.load_file(str(test_file))

        # Should fall back to latin-1
        assert doc is not None
        assert doc.content  # Content should be loaded

    def test_load_directory_empty(self, temp_dir):
        """Test loading from empty directory."""
        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        docs = processor.load_directory(str(temp_dir))

        assert docs == []

    def test_load_directory_with_files(self, sample_files):
        """Test loading from directory with files."""
        directory = sample_files["python"].parent

        processor = DocumentProcessor(file_types=[".py", ".js", ".md", ".txt"], exclude_patterns=[])

        docs = processor.load_directory(str(directory))

        assert len(docs) == 4  # python, javascript, markdown, text
        file_types = [doc.file_type for doc in docs]
        assert ".py" in file_types
        assert ".js" in file_types
        assert ".md" in file_types
        assert ".txt" in file_types

    def test_load_directory_filters_by_type(self, sample_files):
        """Test that directory loading filters by file type."""
        directory = sample_files["python"].parent

        # Only load Python files
        processor = DocumentProcessor(file_types=[".py"], exclude_patterns=[])

        docs = processor.load_directory(str(directory))

        assert len(docs) == 1
        assert docs[0].file_type == ".py"

    def test_load_directory_nonexistent(self):
        """Test loading from nonexistent directory."""
        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        docs = processor.load_directory("/nonexistent/directory")

        assert docs == []

    def test_exclude_pattern_file(self, temp_dir):
        """Test excluding files by pattern."""
        # Create files
        (temp_dir / "keep.txt").write_text("keep")
        (temp_dir / "exclude.tmp").write_text("exclude")

        processor = DocumentProcessor(file_types=[".txt", ".tmp"], exclude_patterns=["*.tmp"])

        docs = processor.load_directory(str(temp_dir))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("keep.txt")

    def test_exclude_pattern_directory(self, temp_dir):
        """Test excluding directories by pattern."""
        # Create directory structure
        keep_dir = temp_dir / "keep"
        keep_dir.mkdir()
        (keep_dir / "file.txt").write_text("keep")

        exclude_dir = temp_dir / "node_modules"
        exclude_dir.mkdir()
        (exclude_dir / "file.txt").write_text("exclude")

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=["node_modules/"])

        docs = processor.load_directory(str(temp_dir))

        # Should only find file in keep directory
        assert len(docs) == 1
        assert "keep" in docs[0].file_path
        assert "node_modules" not in docs[0].file_path

    def test_exclude_nested_directory(self, temp_dir):
        """Test excluding nested directories."""
        # Create nested structure
        nested = temp_dir / "src" / ".git" / "objects"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("exclude")

        keep = temp_dir / "src"
        (keep / "file.txt").write_text("keep")

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[".git/"])

        docs = processor.load_directory(str(temp_dir))

        # Should only find file in src, not in .git
        assert len(docs) == 1
        assert ".git" not in docs[0].file_path

    def test_multiple_exclude_patterns(self, temp_dir):
        """Test multiple exclude patterns."""
        (temp_dir / "keep.txt").write_text("keep")
        (temp_dir / "exclude1.tmp").write_text("exclude")
        (temp_dir / "exclude2.bak").write_text("exclude")

        processor = DocumentProcessor(
            file_types=[".txt", ".tmp", ".bak"], exclude_patterns=["*.tmp", "*.bak"]
        )

        docs = processor.load_directory(str(temp_dir))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("keep.txt")

    def test_iter_files_recursive(self, temp_dir):
        """Test that file iteration is recursive."""
        # Create nested structure
        (temp_dir / "file1.txt").write_text("1")

        level1 = temp_dir / "level1"
        level1.mkdir()
        (level1 / "file2.txt").write_text("2")

        level2 = level1 / "level2"
        level2.mkdir()
        (level2 / "file3.txt").write_text("3")

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        docs = processor.load_directory(str(temp_dir))

        assert len(docs) == 3

    def test_metadata_includes_size(self, temp_dir):
        """Test that metadata includes file size."""
        test_file = temp_dir / "test.txt"
        content = "A" * 1000
        test_file.write_text(content)

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        doc = processor.load_file(str(test_file))

        assert "size" in doc.metadata
        assert doc.metadata["size"] == len(content)

    def test_metadata_includes_modified_time(self, temp_dir):
        """Test that metadata includes modification time."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        doc = processor.load_file(str(test_file))

        assert "modified" in doc.metadata
        assert doc.metadata["modified"] > 0

    def test_load_file_with_special_characters(self, temp_dir):
        """Test loading file with special characters in path."""
        # Create file with space in name
        test_file = temp_dir / "test file.txt"
        test_file.write_text("content")

        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        doc = processor.load_file(str(test_file))

        assert doc is not None
        assert doc.content == "content"

    def test_code_file_types(self, sample_files):
        """Test loading various code file types."""
        directory = sample_files["python"].parent

        processor = DocumentProcessor(
            file_types=[".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".go"],
            exclude_patterns=[],
        )

        docs = processor.load_directory(str(directory))

        # Should find Python and JavaScript files
        assert len(docs) >= 2
        extensions = {doc.file_type for doc in docs}
        assert ".py" in extensions
        assert ".js" in extensions

    def test_exclude_pattern_case_sensitive(self, temp_dir):
        """Test that exclude patterns work correctly."""
        import platform

        (temp_dir / "file.txt").write_text("content1")
        (temp_dir / "FILE.TXT").write_text("content2")

        processor = DocumentProcessor(file_types=[".txt", ".TXT"], exclude_patterns=["FILE.*"])

        docs = processor.load_directory(str(temp_dir))

        # On case-sensitive filesystems (Linux/Mac), file.txt should be loaded (FILE.TXT excluded)
        # On case-insensitive filesystems (Windows), only one file exists and it gets excluded
        if platform.system() == "Windows":
            # Windows: case-insensitive, FILE.TXT overwrites file.txt, then gets excluded
            assert len(docs) == 0
        else:
            # Unix: case-sensitive, file.txt should be loaded
            assert len(docs) >= 1

    def test_expanduser_in_path(self, temp_dir):
        """Test that paths with ~ are expanded."""
        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        # This should not crash even if path doesn't exist
        docs = processor.load_directory("~/nonexistent_test_dir_12345")

        # Should return empty list, not crash
        assert docs == []

    def test_load_file_error_handling(self, temp_dir):
        """Test error handling when file read fails."""
        processor = DocumentProcessor(file_types=[".txt"], exclude_patterns=[])

        # Create file then make it unreadable (platform-dependent)
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        # Try to load a directory as a file
        doc = processor.load_file(str(temp_dir))

        # Should return None, not crash
        assert doc is None

    def test_multiple_file_types(self, temp_dir):
        """Test loading multiple file types."""
        (temp_dir / "doc.md").write_text("# Markdown")
        (temp_dir / "code.py").write_text("print('hello')")
        (temp_dir / "data.json").write_text('{"key": "value"}')
        (temp_dir / "notes.txt").write_text("notes")

        processor = DocumentProcessor(
            file_types=[".md", ".py", ".json", ".txt"], exclude_patterns=[]
        )

        docs = processor.load_directory(str(temp_dir))

        assert len(docs) == 4
        file_types = {doc.file_type for doc in docs}
        assert file_types == {".md", ".py", ".json", ".txt"}
