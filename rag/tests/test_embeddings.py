"""Tests for Ollama embedding client."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.embeddings import OllamaEmbedder


class TestOllamaEmbedder:
    """Test OllamaEmbedder class."""

    @patch('src.embeddings.ollama.Client')
    def test_initialization_default(self, mock_client_class):
        """Test default initialization."""
        mock_client = Mock()
        mock_client.embeddings.return_value = {'embedding': [0.1] * 768}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()

        assert embedder.base_url == "http://localhost:11434"
        assert embedder.model == "nomic-embed-text"
        assert embedder.batch_size == 32
        mock_client_class.assert_called_once_with(host="http://localhost:11434")

    @patch('src.embeddings.ollama.Client')
    def test_initialization_custom(self, mock_client_class):
        """Test custom initialization."""
        mock_client = Mock()
        mock_client.embeddings.return_value = {'embedding': [0.1] * 768}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder(
            base_url="http://custom:8080",
            model="custom-model",
            batch_size=16
        )

        assert embedder.base_url == "http://custom:8080"
        assert embedder.model == "custom-model"
        assert embedder.batch_size == 16
        mock_client_class.assert_called_once_with(host="http://custom:8080")

    @patch('src.embeddings.ollama.Client')
    def test_verify_model_success(self, mock_client_class):
        """Test successful model verification."""
        mock_client = Mock()
        mock_client.embeddings.return_value = {'embedding': [0.1] * 768}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()

        # Verify was called during initialization
        assert mock_client.embeddings.call_count >= 1
        first_call = mock_client.embeddings.call_args_list[0]
        assert first_call[1]['model'] == 'nomic-embed-text'
        assert first_call[1]['prompt'] == 'test'

    @patch('src.embeddings.ollama.Client')
    def test_verify_model_failure(self, mock_client_class):
        """Test model verification failure."""
        mock_client = Mock()
        mock_client.embeddings.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client

        with pytest.raises(Exception) as exc_info:
            OllamaEmbedder()

        assert "Connection failed" in str(exc_info.value)

    @patch('src.embeddings.ollama.Client')
    def test_embed_single_text(self, mock_client_class):
        """Test embedding a single text."""
        mock_client = Mock()
        test_embedding = [0.1, 0.2, 0.3] * 256  # 768 dimensions
        mock_client.embeddings.return_value = {'embedding': test_embedding}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()
        result = embedder.embed("test text")

        assert result == test_embedding
        # Check that embed was called (verification + actual call)
        assert any(
            call[1].get('prompt') == "test text"
            for call in mock_client.embeddings.call_args_list
        )

    @patch('src.embeddings.ollama.Client')
    def test_embed_empty_text(self, mock_client_class):
        """Test embedding empty text."""
        mock_client = Mock()
        empty_embedding = [0.0] * 768
        mock_client.embeddings.return_value = {'embedding': empty_embedding}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()
        result = embedder.embed("")

        assert len(result) == 768

    @patch('src.embeddings.ollama.Client')
    def test_embed_error_handling(self, mock_client_class):
        """Test error handling in embed."""
        mock_client = Mock()
        # First call succeeds (for verification), second fails
        mock_client.embeddings.side_effect = [
            {'embedding': [0.1] * 768},  # verification
            Exception("Embedding failed")  # actual call
        ]
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()

        with pytest.raises(Exception) as exc_info:
            embedder.embed("test")

        assert "Embedding failed" in str(exc_info.value)

    @patch('src.embeddings.ollama.Client')
    def test_embed_batch_single_batch(self, mock_client_class):
        """Test embedding a batch that fits in one batch."""
        mock_client = Mock()
        test_embedding = [0.1] * 768

        # Setup mock to return different embeddings for verification and actual calls
        call_count = [0]

        def embedding_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # verification call
                return {'embedding': test_embedding}
            # Actual calls
            return {'embedding': [float(call_count[0])] * 768}

        mock_client.embeddings.side_effect = embedding_side_effect
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder(batch_size=10)
        texts = [f"text {i}" for i in range(5)]
        results = embedder.embed_batch(texts)

        assert len(results) == 5
        assert all(len(emb) == 768 for emb in results)

    @patch('src.embeddings.ollama.Client')
    def test_embed_batch_multiple_batches(self, mock_client_class):
        """Test embedding texts across multiple batches."""
        mock_client = Mock()
        test_embedding = [0.1] * 768
        mock_client.embeddings.return_value = {'embedding': test_embedding}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder(batch_size=3)
        texts = [f"text {i}" for i in range(10)]
        results = embedder.embed_batch(texts)

        assert len(results) == 10
        assert all(len(emb) == 768 for emb in results)

    @patch('src.embeddings.ollama.Client')
    def test_embed_batch_with_errors(self, mock_client_class):
        """Test embed_batch with some failures uses zero vectors."""
        mock_client = Mock()

        call_count = [0]

        def embedding_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # verification
                return {'embedding': [0.1] * 768}
            elif call_count[0] % 2 == 0:  # every other call fails
                raise Exception("Embedding failed")
            else:
                return {'embedding': [0.5] * 768}

        mock_client.embeddings.side_effect = embedding_side_effect
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()
        texts = ["text1", "text2", "text3", "text4"]
        results = embedder.embed_batch(texts)

        assert len(results) == 4
        # Some should be zero vectors (failed embeddings)
        assert any(all(x == 0.0 for x in emb) for emb in results)
        # Some should be successful
        assert any(any(x != 0.0 for x in emb) for emb in results)

    @patch('src.embeddings.ollama.Client')
    def test_embed_batch_empty_list(self, mock_client_class):
        """Test embedding empty batch."""
        mock_client = Mock()
        mock_client.embeddings.return_value = {'embedding': [0.1] * 768}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()
        results = embedder.embed_batch([])

        assert results == []

    @patch('src.embeddings.ollama.Client')
    def test_get_dimension(self, mock_client_class):
        """Test getting embedding dimension."""
        mock_client = Mock()
        test_embedding = [0.1] * 768
        mock_client.embeddings.return_value = {'embedding': test_embedding}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()
        dimension = embedder.get_dimension()

        assert dimension == 768

    @patch('src.embeddings.ollama.Client')
    def test_get_dimension_custom_model(self, mock_client_class):
        """Test getting dimension for custom model."""
        mock_client = Mock()
        # Custom model with different dimension
        test_embedding = [0.1] * 384
        mock_client.embeddings.return_value = {'embedding': test_embedding}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder(model="custom-model")
        dimension = embedder.get_dimension()

        assert dimension == 384

    @patch('src.embeddings.ollama.Client')
    def test_embed_batch_respects_batch_size(self, mock_client_class):
        """Test that embed_batch processes in correct batch sizes."""
        mock_client = Mock()
        test_embedding = [0.1] * 768
        mock_client.embeddings.return_value = {'embedding': test_embedding}
        mock_client_class.return_value = mock_client

        batch_size = 5
        embedder = OllamaEmbedder(batch_size=batch_size)
        texts = [f"text {i}" for i in range(12)]
        results = embedder.embed_batch(texts)

        # Should process 12 texts: 5 + 5 + 2
        assert len(results) == 12

    @patch('src.embeddings.ollama.Client')
    def test_embed_special_characters(self, mock_client_class):
        """Test embedding text with special characters."""
        mock_client = Mock()
        test_embedding = [0.1] * 768
        mock_client.embeddings.return_value = {'embedding': test_embedding}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()
        special_text = "Special: @#$% \n\t 中文 émojis 🚀"
        result = embedder.embed(special_text)

        assert len(result) == 768

    @patch('src.embeddings.ollama.Client')
    def test_embed_very_long_text(self, mock_client_class):
        """Test embedding very long text."""
        mock_client = Mock()
        test_embedding = [0.1] * 768
        mock_client.embeddings.return_value = {'embedding': test_embedding}
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()
        long_text = "word " * 10000  # Very long text
        result = embedder.embed(long_text)

        assert len(result) == 768
