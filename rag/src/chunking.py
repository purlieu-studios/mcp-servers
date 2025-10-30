"""Text chunking strategies for document processing."""

from typing import List
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    text: str
    start_char: int
    end_char: int


class RecursiveChunker:
    """Chunks text recursively with overlap, respecting natural boundaries."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        # Separators in order of preference
        self.separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

    def chunk(self, text: str) -> List[Chunk]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If this is the last chunk, take everything
            if end >= len(text):
                chunks.append(Chunk(
                    text=text[start:],
                    start_char=start,
                    end_char=len(text)
                ))
                break

            # Try to find a good breaking point
            chunk_end = self._find_break_point(text, start, end)

            chunks.append(Chunk(
                text=text[start:chunk_end],
                start_char=start,
                end_char=chunk_end
            ))

            # Next chunk starts with overlap
            start = chunk_end - self.overlap
            if start <= chunks[-1].start_char:
                start = chunk_end

        return chunks

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Find the best point to break the text."""
        # Try each separator in order
        for separator in self.separators:
            if not separator:
                return end

            # Look for separator near the end
            search_start = max(start, end - 100)
            pos = text.rfind(separator, search_start, end)

            if pos != -1 and pos > start:
                return pos + len(separator)

        return end


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[Chunk]:
    """Convenience function to chunk text."""
    chunker = RecursiveChunker(chunk_size, overlap)
    return chunker.chunk(text)
