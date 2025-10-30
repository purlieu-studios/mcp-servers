"""Integration tests for RAG MCP Server tools."""
import pytest
import pytest_asyncio
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def mock_ollama_client():
    """Mock Ollama client for testing."""
    with patch('src.embeddings.ollama.Client') as mock_client_class:
        mock_client = Mock()
        # Mock embeddings call
        mock_client.embeddings.return_value = {'embedding': [0.1] * 768}
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def test_config(tmp_path):
    """Create a temporary test configuration."""
    config = {
        "storage_path": str(tmp_path / "test_indexes"),
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "nomic-embed-text",
            "batch_size": 32
        },
        "chunking": {
            "chunk_size": 512,
            "overlap": 50
        },
        "indexes": []
    }

    # Create test directory with some files
    test_dir = tmp_path / "test_docs"
    test_dir.mkdir()

    (test_dir / "doc1.txt").write_text("This is a test document about Python programming.")
    (test_dir / "doc2.md").write_text("# Markdown\n\nThis document discusses machine learning.")
    (test_dir / "code.py").write_text("def hello():\n    print('Hello, world!')")

    config["indexes"] = [{
        "name": "test_index",
        "path": str(test_dir),
        "description": "Test index for integration tests",
        "watch": False
    }]

    return config


@pytest.fixture
def config_file(tmp_path, test_config):
    """Create a temporary config file."""
    config_path = tmp_path / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(test_config, f)
    return config_path


@pytest.mark.skip(reason="Integration tests need refactoring to match current IndexManager API")
class TestRAGServerIntegration:
    """Integration tests for RAG MCP Server."""

    @pytest.mark.asyncio
    async def test_server_initialization(self, mock_ollama_client, config_file):
        """Test that server initializes correctly."""
        with patch.dict('os.environ', {'CONFIG_PATH': str(config_file)}):
            from src.rag_server import server, config, index_managers

            # Verify config loaded
            assert config is not None
            assert "test_index" in config.get("indexes", [{}])[0].get("name", "")

    @pytest.mark.asyncio
    async def test_query_tool_basic(self, mock_ollama_client, test_config, tmp_path):
        """Test basic query functionality."""
        # This test would require full server setup
        # For now, test the IndexManager directly
        from src.index_manager import IndexManager

        index_config = test_config["indexes"][0]
        manager = IndexManager(
            name="test_index",
            directory=index_config["path"],
            storage_path=test_config["storage_path"],
            ollama_config=test_config["ollama"],
            chunking_config=test_config["chunking"]
        )

        # Initialize the index
        await manager.initialize()

        # Perform a query
        results = await manager.query("Python programming", top_k=5)

        # Should find the document about Python
        assert len(results) > 0
        assert any("Python" in result.get("text", "") for result in results)

        # Clean up
        await manager.close()

    @pytest.mark.asyncio
    async def test_index_manager_lifecycle(self, mock_ollama_client, test_config):
        """Test IndexManager initialization and operations."""
        from src.index_manager import IndexManager

        index_config = test_config["indexes"][0]
        manager = IndexManager(
            name="test_index",
            directory=index_config["path"],
            storage_path=test_config["storage_path"],
            ollama_config=test_config["ollama"],
            chunking_config=test_config["chunking"]
        )

        # Test initialization
        await manager.initialize()
        assert manager.is_initialized

        # Test getting stats
        stats = manager.get_stats()
        assert "file_count" in stats
        assert "chunk_count" in stats
        assert stats["file_count"] > 0  # Should have indexed files

        # Clean up
        await manager.close()

    @pytest.mark.asyncio
    async def test_hybrid_search(self, mock_ollama_client, test_config):
        """Test hybrid search combining semantic and keyword search."""
        from src.index_manager import IndexManager

        index_config = test_config["indexes"][0]
        manager = IndexManager(
            name="test_index",
            directory=index_config["path"],
            storage_path=test_config["storage_path"],
            ollama_config=test_config["ollama"],
            chunking_config=test_config["chunking"]
        )

        await manager.initialize()

        # Query for something in the docs
        results = await manager.query(
            query="machine learning",
            top_k=3,
            semantic_weight=0.7,
            keyword_weight=0.3
        )

        # Should find relevant results
        assert len(results) > 0

        # Results should have required fields
        for result in results:
            assert "text" in result
            assert "file_path" in result
            assert "score" in result
            assert result["score"] >= 0

        await manager.close()

    @pytest.mark.asyncio
    async def test_file_search(self, mock_ollama_client, test_config):
        """Test file search functionality."""
        from src.index_manager import IndexManager

        index_config = test_config["indexes"][0]
        manager = IndexManager(
            name="test_index",
            directory=index_config["path"],
            storage_path=test_config["storage_path"],
            ollama_config=test_config["ollama"],
            chunking_config=test_config["chunking"]
        )

        await manager.initialize()

        # Search for Python files
        files = manager.search_files("*.py")

        # Should find code.py
        assert len(files) > 0
        assert any("code.py" in f for f in files)

        await manager.close()

    @pytest.mark.asyncio
    async def test_refresh_index(self, mock_ollama_client, test_config, tmp_path):
        """Test index refresh functionality."""
        from src.index_manager import IndexManager

        index_config = test_config["indexes"][0]
        test_dir = Path(index_config["path"])

        manager = IndexManager(
            name="test_index",
            directory=str(test_dir),
            storage_path=test_config["storage_path"],
            ollama_config=test_config["ollama"],
            chunking_config=test_config["chunking"]
        )

        # Initial indexing
        await manager.initialize()
        initial_stats = manager.get_stats()

        # Add a new file
        (test_dir / "new_doc.txt").write_text("This is a new document about data science.")

        # Refresh the index
        await manager.refresh()

        # Stats should show more files
        new_stats = manager.get_stats()
        assert new_stats["file_count"] >= initial_stats["file_count"]

        await manager.close()

    @pytest.mark.asyncio
    async def test_multiple_indexes(self, mock_ollama_client, tmp_path):
        """Test managing multiple indexes."""
        from src.index_manager import IndexManager

        # Create two separate directories
        dir1 = tmp_path / "docs1"
        dir2 = tmp_path / "docs2"
        dir1.mkdir()
        dir2.mkdir()

        (dir1 / "file1.txt").write_text("Document in index 1")
        (dir2 / "file2.txt").write_text("Document in index 2")

        config = {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "nomic-embed-text",
                "batch_size": 32
            },
            "chunking": {
                "chunk_size": 512,
                "overlap": 50
            }
        }

        # Create two managers
        manager1 = IndexManager(
            name="index1",
            directory=str(dir1),
            storage_path=str(tmp_path / "storage1"),
            ollama_config=config["ollama"],
            chunking_config=config["chunking"]
        )

        manager2 = IndexManager(
            name="index2",
            directory=str(dir2),
            storage_path=str(tmp_path / "storage2"),
            ollama_config=config["ollama"],
            chunking_config=config["chunking"]
        )

        # Initialize both
        await manager1.initialize()
        await manager2.initialize()

        # Each should have different content
        stats1 = manager1.get_stats()
        stats2 = manager2.get_stats()

        assert stats1["file_count"] > 0
        assert stats2["file_count"] > 0

        # Search in each
        results1 = await manager1.query("index 1")
        results2 = await manager2.query("index 2")

        assert len(results1) > 0
        assert len(results2) > 0

        # Clean up
        await manager1.close()
        await manager2.close()

    @pytest.mark.asyncio
    async def test_error_handling_missing_directory(self, mock_ollama_client, tmp_path):
        """Test error handling when directory doesn't exist."""
        from src.index_manager import IndexManager

        manager = IndexManager(
            name="missing_index",
            directory="/nonexistent/directory",
            storage_path=str(tmp_path / "storage"),
            ollama_config={
                "base_url": "http://localhost:11434",
                "model": "nomic-embed-text",
                "batch_size": 32
            },
            chunking_config={
                "chunk_size": 512,
                "overlap": 50
            }
        )

        # Should handle gracefully
        await manager.initialize()

        # Stats should show no files
        stats = manager.get_stats()
        assert stats["file_count"] == 0

        await manager.close()

    @pytest.mark.asyncio
    async def test_empty_directory(self, mock_ollama_client, tmp_path):
        """Test indexing an empty directory."""
        from src.index_manager import IndexManager

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        manager = IndexManager(
            name="empty_index",
            directory=str(empty_dir),
            storage_path=str(tmp_path / "storage"),
            ollama_config={
                "base_url": "http://localhost:11434",
                "model": "nomic-embed-text",
                "batch_size": 32
            },
            chunking_config={
                "chunk_size": 512,
                "overlap": 50
            }
        )

        await manager.initialize()

        # Should initialize successfully with no files
        stats = manager.get_stats()
        assert stats["file_count"] == 0
        assert stats["chunk_count"] == 0

        # Query should return empty results
        results = await manager.query("anything")
        assert results == []

        await manager.close()

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self, mock_ollama_client, test_config):
        """Test queries with special characters."""
        from src.index_manager import IndexManager

        index_config = test_config["indexes"][0]
        manager = IndexManager(
            name="test_index",
            directory=index_config["path"],
            storage_path=test_config["storage_path"],
            ollama_config=test_config["ollama"],
            chunking_config=test_config["chunking"]
        )

        await manager.initialize()

        # Query with special characters
        queries = [
            "Python",
            "C++ programming",
            "@decorator",
            "hello-world",
        ]

        for query in queries:
            # Should not crash
            results = await manager.query(query, top_k=5)
            assert isinstance(results, list)

        await manager.close()

    def test_config_loading(self, config_file):
        """Test configuration loading."""
        import json

        with open(config_file, 'r') as f:
            config = json.load(f)

        assert "storage_path" in config
        assert "ollama" in config
        assert "chunking" in config
        assert "indexes" in config
        assert len(config["indexes"]) > 0

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, mock_ollama_client, test_config):
        """Test multiple concurrent queries."""
        from src.index_manager import IndexManager

        index_config = test_config["indexes"][0]
        manager = IndexManager(
            name="test_index",
            directory=index_config["path"],
            storage_path=test_config["storage_path"],
            ollama_config=test_config["ollama"],
            chunking_config=test_config["chunking"]
        )

        await manager.initialize()

        # Run multiple queries concurrently
        queries = ["Python", "machine learning", "Hello", "test"]
        tasks = [manager.query(q, top_k=3) for q in queries]

        results = await asyncio.gather(*tasks)

        # All queries should complete
        assert len(results) == len(queries)
        for result in results:
            assert isinstance(result, list)

        await manager.close()
