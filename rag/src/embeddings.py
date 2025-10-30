"""Ollama embedding client for generating vector embeddings."""

import logging

import ollama

logger = logging.getLogger(__name__)


class OllamaEmbedder:
    """Client for generating embeddings using Ollama."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        batch_size: int = 32,
    ):
        self.base_url = base_url
        self.model = model
        self.batch_size = batch_size
        self.client = ollama.Client(host=base_url)
        self._dimension = None  # Cache dimension
        self._verify_model()

    def _verify_model(self):
        """Verify the embedding model is available."""
        try:
            # Test with a small embedding
            self.client.embeddings(model=self.model, prompt="test")
            logger.info(f"Successfully connected to Ollama with model {self.model}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama or load model: {e}")
            logger.info(f"Make sure Ollama is running and model '{self.model}' is available")
            logger.info(f"You can pull the model with: ollama pull {self.model}")
            raise

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        try:
            response = self.client.embeddings(model=self.model, prompt=text)
            return response["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            logger.debug(
                f"Processing batch {i//self.batch_size + 1}/{(len(texts)-1)//self.batch_size + 1}"
            )

            for text in batch:
                try:
                    emb = self.embed(text)
                    embeddings.append(emb)
                except Exception as e:
                    logger.error(f"Failed to embed text: {text[:50]}... Error: {e}")
                    # Use zero vector as fallback
                    embeddings.append([0.0] * self.get_dimension())

        return embeddings

    def get_dimension(self) -> int:
        """Get the dimension of embeddings from this model."""
        if self._dimension is None:
            # nomic-embed-text produces 768-dimensional embeddings
            # We'll verify by generating a test embedding
            test_emb = self.embed("test")
            self._dimension = len(test_emb)
        return self._dimension
