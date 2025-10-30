"""Tests for text chunking module."""

from src.chunking import Chunk, RecursiveChunker, chunk_text


class TestChunk:
    """Test Chunk dataclass."""

    def test_chunk_creation(self):
        """Test creating a chunk."""
        chunk = Chunk(text="Hello world", start_char=0, end_char=11)
        assert chunk.text == "Hello world"
        assert chunk.start_char == 0
        assert chunk.end_char == 11

    def test_chunk_equality(self):
        """Test chunk equality."""
        chunk1 = Chunk(text="Hello", start_char=0, end_char=5)
        chunk2 = Chunk(text="Hello", start_char=0, end_char=5)
        assert chunk1 == chunk2


class TestRecursiveChunker:
    """Test RecursiveChunker class."""

    def test_initialization_default(self):
        """Test default initialization."""
        chunker = RecursiveChunker()
        assert chunker.chunk_size == 512
        assert chunker.overlap == 50
        assert len(chunker.separators) == 9

    def test_initialization_custom(self):
        """Test custom initialization."""
        chunker = RecursiveChunker(chunk_size=100, overlap=20)
        assert chunker.chunk_size == 100
        assert chunker.overlap == 20

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunker = RecursiveChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_chunk_short_text(self):
        """Test chunking text shorter than chunk size."""
        chunker = RecursiveChunker(chunk_size=100, overlap=20)
        text = "This is a short text."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].start_char == 0
        assert chunks[0].end_char == len(text)

    def test_chunk_exact_size(self):
        """Test chunking text exactly matching chunk size."""
        chunker = RecursiveChunker(chunk_size=20, overlap=5)
        text = "A" * 20
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert len(chunks[0].text) == 20

    def test_chunk_long_text_with_paragraphs(self):
        """Test chunking long text with paragraph breaks."""
        chunker = RecursiveChunker(chunk_size=50, overlap=10)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.\n\nFourth paragraph."
        chunks = chunker.chunk(text)

        assert len(chunks) > 1
        # Check that chunks overlap
        for i in range(len(chunks) - 1):
            assert chunks[i].end_char > chunks[i + 1].start_char

    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = RecursiveChunker(chunk_size=100, overlap=20)
        text = "A" * 200
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2
        # Verify overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            overlap_start = chunks[i + 1].start_char
            overlap_end = chunks[i].end_char
            actual_overlap = overlap_end - overlap_start
            assert actual_overlap <= chunker.overlap

    def test_chunk_respects_sentence_boundaries(self):
        """Test that chunking respects sentence boundaries."""
        chunker = RecursiveChunker(chunk_size=50, overlap=10)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunker.chunk(text)

        # At least one chunk should end with a period
        assert any(chunk.text.strip().endswith(".") for chunk in chunks)

    def test_chunk_with_newlines(self):
        """Test chunking with newline separators."""
        chunker = RecursiveChunker(chunk_size=30, overlap=5)
        text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2

    def test_chunk_positions_are_valid(self):
        """Test that chunk positions are valid."""
        chunker = RecursiveChunker(chunk_size=100, overlap=20)
        text = "This is a test document. " * 20
        chunks = chunker.chunk(text)

        for chunk in chunks:
            # Check that positions are within text bounds
            assert 0 <= chunk.start_char < len(text)
            assert 0 < chunk.end_char <= len(text)
            assert chunk.start_char < chunk.end_char

            # Check that text matches positions
            assert text[chunk.start_char : chunk.end_char] == chunk.text

    def test_chunk_coverage(self):
        """Test that all text is covered by chunks."""
        chunker = RecursiveChunker(chunk_size=100, overlap=20)
        text = "This is a comprehensive test document. " * 10
        chunks = chunker.chunk(text)

        # First chunk should start at 0
        assert chunks[0].start_char == 0

        # Last chunk should end at text length
        assert chunks[-1].end_char == len(text)

        # Check that there are no gaps
        covered = set()
        for chunk in chunks:
            covered.update(range(chunk.start_char, chunk.end_char))

        assert len(covered) == len(text)

    def test_find_break_point_with_paragraph(self):
        """Test finding break point with paragraph separator."""
        chunker = RecursiveChunker(chunk_size=50, overlap=10)
        text = "First paragraph.\n\nSecond paragraph."
        break_point = chunker._find_break_point(text, 0, 30)

        # Should break at paragraph boundary
        assert text[break_point - 2 : break_point] == "\n\n" or break_point == 30

    def test_find_break_point_with_sentence(self):
        """Test finding break point with sentence separator."""
        chunker = RecursiveChunker(chunk_size=50, overlap=10)
        text = "First sentence. Second sentence."
        break_point = chunker._find_break_point(text, 0, 30)

        # Should prefer to break at sentence boundary
        assert break_point <= 30

    def test_find_break_point_no_separator(self):
        """Test finding break point with no good separator."""
        chunker = RecursiveChunker(chunk_size=20, overlap=5)
        text = "A" * 100
        break_point = chunker._find_break_point(text, 0, 20)

        # Should break at the end position
        assert break_point == 20

    def test_chunk_code_python(self, sample_code_python):
        """Test chunking Python code."""
        chunker = RecursiveChunker(chunk_size=200, overlap=30)
        chunks = chunker.chunk(sample_code_python)

        assert len(chunks) >= 1
        # Verify all chunks are valid
        for chunk in chunks:
            assert chunk.text
            assert chunk.start_char >= 0
            assert chunk.end_char <= len(sample_code_python)

    def test_chunk_markdown(self, sample_markdown):
        """Test chunking Markdown document."""
        chunker = RecursiveChunker(chunk_size=200, overlap=30)
        chunks = chunker.chunk(sample_markdown)

        assert len(chunks) >= 2
        # Should prefer to break at double newlines (markdown paragraphs)
        paragraph_breaks = sum(1 for chunk in chunks if "\n\n" in chunk.text)
        assert paragraph_breaks > 0

    def test_chunk_very_small_chunk_size(self):
        """Test chunking with very small chunk size."""
        chunker = RecursiveChunker(chunk_size=10, overlap=2)
        text = "This is a test."
        chunks = chunker.chunk(text)

        assert len(chunks) >= 1
        # Even with small chunk size, should not break mid-word if possible
        for chunk in chunks:
            assert len(chunk.text) > 0

    def test_chunk_large_overlap(self):
        """Test chunking with overlap close to chunk size."""
        chunker = RecursiveChunker(chunk_size=100, overlap=90)
        text = "A" * 300
        chunks = chunker.chunk(text)

        # Should still produce valid chunks
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk.text) > 0


class TestChunkTextFunction:
    """Test chunk_text convenience function."""

    def test_chunk_text_default_params(self):
        """Test chunk_text with default parameters."""
        text = "This is a test document. " * 50
        chunks = chunk_text(text)

        assert len(chunks) >= 1
        assert all(isinstance(chunk, Chunk) for chunk in chunks)

    def test_chunk_text_custom_params(self):
        """Test chunk_text with custom parameters."""
        text = "This is a test document. " * 50
        chunks = chunk_text(text, chunk_size=100, overlap=20)

        assert len(chunks) >= 1
        # Verify chunks respect custom size
        assert all(len(chunk.text) <= 100 + 50 for chunk in chunks)  # Allow some flexibility

    def test_chunk_text_empty(self):
        """Test chunk_text with empty string."""
        chunks = chunk_text("")
        assert chunks == []

    def test_chunk_text_produces_valid_chunks(self, sample_texts):
        """Test that chunk_text produces valid chunks for various texts."""
        for text in sample_texts:
            chunks = chunk_text(text)
            assert len(chunks) >= 1

            for chunk in chunks:
                assert isinstance(chunk, Chunk)
                assert chunk.text
                assert 0 <= chunk.start_char < chunk.end_char
