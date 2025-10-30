"""FAISS-based vector store for semantic search."""

import logging
import pickle
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import faiss

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """Vector store using FAISS for efficient similarity search."""

    def __init__(self, dimension: int, index_path: Optional[Path] = None):
        self.dimension = dimension
        self.index_path = index_path
        self.index = None
        self.id_mapping = []  # Maps FAISS index positions to chunk IDs

        # Check if index file exists (with .faiss extension)
        if index_path and index_path.with_suffix('.faiss').exists():
            self.load()
        else:
            self._create_index()

    def _create_index(self):
        """Create a new FAISS index."""
        # Using IndexFlatIP for inner product (cosine similarity with normalized vectors)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.id_mapping = []
        logger.info(f"Created new FAISS index with dimension {self.dimension}")

    def add_vectors(self, vectors: List[List[float]], chunk_ids: List[int]):
        """Add vectors to the index."""
        if not vectors:
            return

        # Convert to numpy array and normalize
        vectors_np = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(vectors_np)

        # Add to index
        self.index.add(vectors_np)

        # Update ID mapping
        self.id_mapping.extend(chunk_ids)

        logger.debug(f"Added {len(vectors)} vectors to index")

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[int, float]]:
        """Search for similar vectors.

        Returns:
            List of (chunk_id, similarity_score) tuples
        """
        if self.index.ntotal == 0:
            return []

        # Normalize query vector
        query_np = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query_np)

        # Search
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_np, k)

        # Convert to chunk IDs and scores
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx < len(self.id_mapping):
                chunk_id = self.id_mapping[idx]
                results.append((chunk_id, float(score)))

        return results

    def save(self):
        """Save index to disk."""
        if not self.index_path:
            logger.warning("No index path specified, cannot save")
            return

        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss_path = self.index_path.with_suffix('.faiss')
        faiss.write_index(self.index, str(faiss_path))

        # Save ID mapping
        mapping_path = self.index_path.with_suffix('.mapping')
        with open(mapping_path, 'wb') as f:
            pickle.dump(self.id_mapping, f)

        logger.info(f"Saved vector store to {self.index_path}")

    def load(self):
        """Load index from disk."""
        if not self.index_path:
            logger.warning("No index path specified, creating new index")
            self._create_index()
            return

        try:
            # Load FAISS index
            faiss_path = self.index_path.with_suffix('.faiss')
            if not faiss_path.exists():
                logger.warning(f"FAISS index not found: {faiss_path}, creating new index")
                self._create_index()
                return

            self.index = faiss.read_index(str(faiss_path))

            # Load ID mapping
            mapping_path = self.index_path.with_suffix('.mapping')
            if mapping_path.exists():
                with open(mapping_path, 'rb') as f:
                    self.id_mapping = pickle.load(f)
            else:
                self.id_mapping = list(range(self.index.ntotal))

            logger.info(f"Loaded vector store from {self.index_path} ({self.index.ntotal} vectors)")

        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            self._create_index()

    def clear(self):
        """Clear the index."""
        self._create_index()

    def get_stats(self) -> dict:
        """Get statistics about the index."""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
        }
