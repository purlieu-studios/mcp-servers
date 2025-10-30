"""Index manager for RAG system."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .chunking import chunk_text
from .document_processor import Document, DocumentProcessor
from .embeddings import OllamaEmbedder
from .metadata_store import MetadataStore
from .vector_store import FAISSVectorStore

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result."""

    chunk_id: int
    text: str
    file_path: str
    score: float
    start_char: int
    end_char: int


class IndexManager:
    """Manages document indexes with vector and metadata stores."""

    def __init__(
        self,
        name: str,
        storage_path: Path,
        embedder: OllamaEmbedder,
        doc_processor: DocumentProcessor,
        chunk_size: int = 512,
        overlap: int = 50,
    ):
        self.name = name
        self.storage_path = storage_path / name
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.embedder = embedder
        self.doc_processor = doc_processor
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Initialize stores
        self.metadata_store = MetadataStore(self.storage_path / "metadata.db")

        vector_path = self.storage_path / "vectors"
        self.vector_store = FAISSVectorStore(
            dimension=embedder.get_dimension(), index_path=vector_path
        )

        logger.info(f"Initialized index manager for '{name}'")

    def index_directory(self, directory: str) -> dict[str, Any]:
        """Index all documents in a directory.

        Returns:
            Statistics about indexing operation
        """
        logger.info(f"Indexing directory: {directory}")

        # Load documents
        documents = self.doc_processor.load_directory(directory)

        if not documents:
            logger.warning(f"No documents found in {directory}")
            return {"files_indexed": 0, "chunks_created": 0}

        # Process each document
        files_indexed = 0
        chunks_created = 0

        for doc in documents:
            result = self._index_document(doc)
            if result:
                files_indexed += 1
                chunks_created += result

        # Save vector store
        self.vector_store.save()

        stats = {
            "files_indexed": files_indexed,
            "chunks_created": chunks_created,
        }

        logger.info(f"Indexing complete: {stats}")
        return stats

    def _index_document(self, doc: Document) -> int:
        """Index a single document.

        Returns:
            Number of chunks created
        """
        try:
            # Add file to metadata store
            file_id = self.metadata_store.add_file(
                file_path=doc.file_path,
                file_type=doc.file_type,
                content=doc.content,
                size=doc.metadata.get("size", 0),
                modified=doc.metadata.get("modified", 0),
            )

            # Check if file was unchanged
            existing_file = self.metadata_store.get_file_by_path(doc.file_path)
            if existing_file and existing_file.get("hash"):
                # File might be unchanged, but chunks were deleted if hash changed
                pass

            # Chunk the document
            chunks = chunk_text(doc.content, self.chunk_size, self.overlap)

            if not chunks:
                return 0

            # Generate embeddings
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embedder.embed_batch(chunk_texts)

            # Store chunks and embeddings
            chunk_ids = []
            for chunk, embedding in zip(chunks, embeddings, strict=False):
                # Get current position in vector store
                embedding_id = self.vector_store.index.ntotal if self.vector_store.index else 0

                # Add to metadata store
                chunk_id = self.metadata_store.add_chunk(
                    file_id=file_id,
                    text=chunk.text,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    embedding_id=embedding_id,
                )

                chunk_ids.append(chunk_id)

            # Add embeddings to vector store
            self.vector_store.add_vectors(embeddings, chunk_ids)

            logger.debug(f"Indexed {doc.file_path}: {len(chunks)} chunks")
            return len(chunks)

        except Exception as e:
            logger.error(f"Error indexing document {doc.file_path}: {e}")
            return 0

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        min_score: float = 0.0,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        include_keywords: bool = True,
    ) -> list[SearchResult]:
        """Query the index using hybrid search.

        Args:
            query_text: Search query
            top_k: Number of results to return
            min_score: Minimum score threshold
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            include_keywords: Whether to use keyword search

        Returns:
            List of search results
        """
        results_map = {}

        # Semantic search
        if semantic_weight > 0:
            query_embedding = self.embedder.embed(query_text)
            semantic_results = self.vector_store.search(query_embedding, top_k * 2)

            for chunk_id, score in semantic_results:
                results_map[chunk_id] = results_map.get(chunk_id, 0) + (score * semantic_weight)

        # Keyword search
        if include_keywords and keyword_weight > 0:
            keyword_results = self.metadata_store.search_text(query_text, top_k * 2)

            for chunk_id, score in keyword_results:
                results_map[chunk_id] = results_map.get(chunk_id, 0) + (score * keyword_weight)

        # Sort by combined score
        sorted_results = sorted(results_map.items(), key=lambda x: x[1], reverse=True)

        # Build result objects
        results = []
        for chunk_id, score in sorted_results[:top_k]:
            if score < min_score:
                continue

            chunk_data = self.metadata_store.get_chunk(chunk_id)
            if chunk_data:
                results.append(
                    SearchResult(
                        chunk_id=chunk_id,
                        text=chunk_data["text"],
                        file_path=chunk_data["file_path"],
                        score=score,
                        start_char=chunk_data["start_char"],
                        end_char=chunk_data["end_char"],
                    )
                )

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the index."""
        metadata_stats = self.metadata_store.get_stats()
        vector_stats = self.vector_store.get_stats()

        return {
            "name": self.name,
            "files": metadata_stats["file_count"],
            "chunks": metadata_stats["chunk_count"],
            "size_bytes": metadata_stats["total_size_bytes"],
            "vectors": vector_stats["total_vectors"],
        }

    def list_files(self) -> list[str]:
        """List all indexed files."""
        files = self.metadata_store.get_all_files()
        return [f["path"] for f in files]

    def refresh(self, directory: str) -> dict[str, Any]:
        """Refresh index by re-indexing directory.

        This will update changed files and remove deleted files.
        """
        logger.info(f"Refreshing index for {directory}")

        # Get current indexed files
        current_files = set(self.list_files())

        # Load documents from directory
        documents = self.doc_processor.load_directory(directory)
        new_files = set(doc.file_path for doc in documents)

        # Files to remove
        removed_files = current_files - new_files

        for file_path in removed_files:
            self.metadata_store.delete_file(file_path)
            logger.debug(f"Removed deleted file: {file_path}")

        # Re-index (will update changed files automatically)
        return self.index_directory(directory)

    def close(self):
        """Close all connections."""
        self.metadata_store.close()
