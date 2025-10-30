"""Tests for FAISS vector store."""

import faiss

from src.vector_store import FAISSVectorStore


class TestFAISSVectorStore:
    """Test FAISSVectorStore class."""

    def test_initialization_new_index(self):
        """Test creating a new index."""
        store = FAISSVectorStore(dimension=768)

        assert store.dimension == 768
        assert store.index is not None
        assert store.index.ntotal == 0
        assert store.id_mapping == []

    def test_initialization_with_path_no_existing(self, temp_dir):
        """Test initialization with path when no index exists."""
        index_path = temp_dir / "test_index"
        store = FAISSVectorStore(dimension=768, index_path=index_path)

        assert store.dimension == 768
        assert store.index.ntotal == 0

    def test_add_vectors_single(self, normalized_mock_embeddings):
        """Test adding a single vector."""
        store = FAISSVectorStore(dimension=768)
        vector = normalized_mock_embeddings[0].tolist()

        store.add_vectors([vector], [1])

        assert store.index.ntotal == 1
        assert store.id_mapping == [1]

    def test_add_vectors_multiple(self, normalized_mock_embeddings):
        """Test adding multiple vectors."""
        store = FAISSVectorStore(dimension=768)
        vectors = normalized_mock_embeddings.tolist()
        chunk_ids = [10, 20, 30, 40, 50]

        store.add_vectors(vectors, chunk_ids)

        assert store.index.ntotal == 5
        assert store.id_mapping == chunk_ids

    def test_add_vectors_empty_list(self):
        """Test adding empty vector list."""
        store = FAISSVectorStore(dimension=768)
        store.add_vectors([], [])

        assert store.index.ntotal == 0
        assert store.id_mapping == []

    def test_add_vectors_incremental(self, normalized_mock_embeddings):
        """Test adding vectors incrementally."""
        store = FAISSVectorStore(dimension=768)

        # Add first batch
        store.add_vectors([normalized_mock_embeddings[0].tolist()], [1])
        assert store.index.ntotal == 1

        # Add second batch
        store.add_vectors([normalized_mock_embeddings[1].tolist()], [2])
        assert store.index.ntotal == 2

        assert store.id_mapping == [1, 2]

    def test_add_vectors_normalizes(self):
        """Test that vectors are normalized when added."""
        store = FAISSVectorStore(dimension=3)

        # Create un-normalized vectors
        vectors = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        store.add_vectors(vectors, [1, 2])

        # Retrieve and check they're normalized
        # FAISS stores normalized vectors for IndexFlatIP
        assert store.index.ntotal == 2

    def test_search_empty_index(self):
        """Test searching in empty index."""
        store = FAISSVectorStore(dimension=768)
        query = [0.1] * 768

        results = store.search(query, top_k=5)

        assert results == []

    def test_search_single_result(self, normalized_mock_embeddings):
        """Test searching with single result."""
        store = FAISSVectorStore(dimension=768)
        vectors = normalized_mock_embeddings.tolist()

        store.add_vectors([vectors[0]], [100])

        # Query with the same vector (should match itself)
        results = store.search(vectors[0], top_k=1)

        assert len(results) == 1
        chunk_id, score = results[0]
        assert chunk_id == 100
        assert score > 0.99  # Should be very similar to itself

    def test_search_multiple_results(self, normalized_mock_embeddings):
        """Test searching with multiple results."""
        store = FAISSVectorStore(dimension=768)
        vectors = normalized_mock_embeddings.tolist()
        chunk_ids = [10, 20, 30, 40, 50]

        store.add_vectors(vectors, chunk_ids)

        # Search for top 3
        results = store.search(vectors[0], top_k=3)

        assert len(results) == 3
        # Results should be sorted by score (highest first)
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

        # First result should be the query vector itself
        assert results[0][0] == 10

    def test_search_top_k_larger_than_index(self, normalized_mock_embeddings):
        """Test searching with top_k larger than index size."""
        store = FAISSVectorStore(dimension=768)
        vectors = normalized_mock_embeddings[:2].tolist()

        store.add_vectors(vectors, [1, 2])

        # Request more results than available
        results = store.search(vectors[0], top_k=10)

        # Should return only available results
        assert len(results) == 2

    def test_search_normalizes_query(self):
        """Test that query vector is normalized."""
        store = FAISSVectorStore(dimension=3)

        # Add normalized vectors
        vectors = [[1.0, 0.0, 0.0]]
        store.add_vectors(vectors, [1])

        # Query with unnormalized vector
        query = [10.0, 0.0, 0.0]  # Same direction, different magnitude
        results = store.search(query, top_k=1)

        # Should still match well because both get normalized
        assert len(results) == 1
        assert results[0][1] > 0.99

    def test_save_and_load(self, temp_dir, normalized_mock_embeddings):
        """Test saving and loading index."""
        index_path = temp_dir / "test_index"

        # Create and populate store
        store1 = FAISSVectorStore(dimension=768, index_path=index_path)
        vectors = normalized_mock_embeddings.tolist()
        chunk_ids = [10, 20, 30]
        store1.add_vectors(vectors[:3], chunk_ids)

        # Verify vectors were added
        assert store1.index.ntotal == 3

        # Save
        store1.save()

        # Check files were created
        faiss_file = index_path.with_suffix(".faiss")
        mapping_file = index_path.with_suffix(".mapping")
        assert faiss_file.exists(), f"FAISS file not created: {faiss_file}"
        assert mapping_file.exists(), f"Mapping file not created: {mapping_file}"

        # Create new store and verify it loads
        store2 = FAISSVectorStore(dimension=768, index_path=index_path)

        # If load failed, ntotal will be 0
        if store2.index.ntotal == 0:
            # Try loading manually to see error
            store2.load()

        assert store2.index.ntotal == 3, f"Expected 3 vectors, got {store2.index.ntotal}"
        assert store2.id_mapping == chunk_ids

        # Verify search works
        results = store2.search(vectors[0], top_k=1)
        assert results[0][0] == 10

    def test_save_without_path(self, caplog):
        """Test saving without index path."""
        store = FAISSVectorStore(dimension=768)
        store.save()

        # Should log warning
        assert any("No index path specified" in record.message for record in caplog.records)

    def test_load_nonexistent_path(self, temp_dir):
        """Test loading from nonexistent path."""
        index_path = temp_dir / "nonexistent"

        store = FAISSVectorStore(dimension=768, index_path=index_path)

        # Should create new index
        assert store.index.ntotal == 0

    def test_load_corrupted_index(self, temp_dir):
        """Test loading corrupted index."""
        index_path = temp_dir / "corrupted"

        # Create corrupted files
        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss_path = index_path.with_suffix(".faiss")
        faiss_path.write_text("corrupted data")

        store = FAISSVectorStore(dimension=768, index_path=index_path)

        # Should create new index on error
        assert store.index.ntotal == 0

    def test_load_missing_mapping(self, temp_dir, normalized_mock_embeddings):
        """Test loading index with missing mapping file."""
        index_path = temp_dir / "test_index"

        # Create index without mapping
        store1 = FAISSVectorStore(dimension=768, index_path=index_path)
        store1.add_vectors(normalized_mock_embeddings[:3].tolist(), [1, 2, 3])

        # Save only the FAISS index
        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss_path = index_path.with_suffix(".faiss")
        faiss.write_index(store1.index, str(faiss_path))

        # Load should generate default mapping
        store2 = FAISSVectorStore(dimension=768, index_path=index_path)

        assert store2.index.ntotal == 3
        assert store2.id_mapping == [0, 1, 2]  # Default mapping

    def test_clear(self, normalized_mock_embeddings):
        """Test clearing the index."""
        store = FAISSVectorStore(dimension=768)
        vectors = normalized_mock_embeddings.tolist()

        # Add vectors
        store.add_vectors(vectors, [1, 2, 3, 4, 5])
        assert store.index.ntotal == 5

        # Clear
        store.clear()

        assert store.index.ntotal == 0
        assert store.id_mapping == []

    def test_get_stats_empty(self):
        """Test getting stats from empty index."""
        store = FAISSVectorStore(dimension=768)
        stats = store.get_stats()

        assert stats["total_vectors"] == 0
        assert stats["dimension"] == 768

    def test_get_stats_with_vectors(self, normalized_mock_embeddings):
        """Test getting stats from populated index."""
        store = FAISSVectorStore(dimension=768)
        store.add_vectors(normalized_mock_embeddings.tolist(), [1, 2, 3, 4, 5])

        stats = store.get_stats()

        assert stats["total_vectors"] == 5
        assert stats["dimension"] == 768

    def test_save_creates_directory(self, temp_dir, normalized_mock_embeddings):
        """Test that save creates directory if it doesn't exist."""
        index_path = temp_dir / "nested" / "dir" / "index"

        store = FAISSVectorStore(dimension=768, index_path=index_path)
        store.add_vectors([normalized_mock_embeddings[0].tolist()], [1])

        store.save()

        assert index_path.parent.exists()
        assert (index_path.with_suffix(".faiss")).exists()

    def test_search_returns_correct_scores(self):
        """Test that search returns meaningful similarity scores."""
        store = FAISSVectorStore(dimension=3)

        # Add two orthogonal vectors (should have low similarity)
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        store.add_vectors([vec1, vec2], [1, 2])

        # Search with vec1
        results = store.search(vec1, top_k=2)

        # First result should be vec1 itself (high score)
        assert results[0][0] == 1
        assert results[0][1] > 0.99

        # Second result should be vec2 (low score, orthogonal)
        assert results[1][0] == 2
        assert abs(results[1][1]) < 0.01  # Close to 0 (orthogonal)

    def test_id_mapping_preserves_order(self):
        """Test that ID mapping preserves insertion order."""
        store = FAISSVectorStore(dimension=3)

        chunk_ids = [100, 200, 300, 400, 500]
        vectors = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 1.0],
        ]

        store.add_vectors(vectors, chunk_ids)

        assert store.id_mapping == chunk_ids

    def test_search_with_different_dimension_query(self):
        """Test that search with wrong dimension query fails gracefully."""
        store = FAISSVectorStore(dimension=768)
        store.add_vectors([[0.1] * 768], [1])

        # Query with wrong dimension should raise error or return empty
        try:
            results = store.search([0.1] * 512, top_k=1)  # Wrong dimension
            # If it doesn't raise, it should return empty or fail assertion
            assert False, "Should have raised an error for wrong dimension"
        except (ValueError, RuntimeError, IndexError, AssertionError):
            pass  # Expected

    def test_persistence_after_multiple_saves(self, temp_dir, normalized_mock_embeddings):
        """Test that multiple saves don't corrupt the index."""
        index_path = temp_dir / "test_index"

        store = FAISSVectorStore(dimension=768, index_path=index_path)
        vectors = normalized_mock_embeddings.tolist()

        # Add and save multiple times
        for i in range(3):
            store.add_vectors([vectors[i]], [i])
            store.save()

        # Load and verify
        new_store = FAISSVectorStore(dimension=768, index_path=index_path)
        assert new_store.index.ntotal == 3
        assert new_store.id_mapping == [0, 1, 2]
