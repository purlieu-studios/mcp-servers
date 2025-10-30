"""Document loading and processing for various file types."""

import fnmatch
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a loaded document."""

    content: str
    file_path: str
    file_type: str
    metadata: dict


class DocumentProcessor:
    """Loads and processes documents from directories."""

    def __init__(self, file_types: list[str], exclude_patterns: list[str]):
        self.file_types = set(file_types)
        self.exclude_patterns = exclude_patterns

    def load_directory(self, directory: str) -> list[Document]:
        """Load all supported documents from a directory."""
        directory_path = Path(directory).expanduser().resolve()

        if not directory_path.exists():
            logger.error(f"Directory does not exist: {directory}")
            return []

        documents = []

        for file_path in self._iter_files(directory_path):
            doc = self.load_file(str(file_path))
            if doc:
                documents.append(doc)

        logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents

    def load_file(self, file_path: str) -> Document | None:
        """Load a single file."""
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return None

        if path.suffix not in self.file_types:
            return None

        try:
            # Try UTF-8 first, fallback to latin-1
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = path.read_text(encoding="latin-1")

            metadata = {
                "size": path.stat().st_size,
                "modified": path.stat().st_mtime,
            }

            return Document(
                content=content, file_path=str(path), file_type=path.suffix, metadata=metadata
            )

        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return None

    def _iter_files(self, directory: Path):
        """Iterate over all files in directory, respecting exclude patterns."""
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)

            # Filter directories
            dirs[:] = [d for d in dirs if not self._should_exclude(root_path / d, directory)]

            for file in files:
                file_path = root_path / file

                if self._should_exclude(file_path, directory):
                    continue

                if file_path.suffix in self.file_types:
                    yield file_path

    def _should_exclude(self, path: Path, base_path: Path) -> bool:
        """Check if a path should be excluded based on patterns."""
        try:
            relative = path.relative_to(base_path)
            relative_str = str(relative).replace("\\", "/")

            for pattern in self.exclude_patterns:
                # Check full path match
                if fnmatch.fnmatch(relative_str, pattern):
                    return True

                # For directory patterns (ending with /), check if any path component matches
                if pattern.endswith("/"):
                    dir_pattern = pattern.rstrip("/")
                    # Check if the path itself or any parent matches the directory name
                    if path.name == dir_pattern:
                        return True
                    for parent in relative.parents:
                        if parent.name == dir_pattern:
                            return True
                        # Also check with fnmatch for glob patterns
                        if fnmatch.fnmatch(parent.name, dir_pattern):
                            return True

            return False
        except ValueError:
            return False
