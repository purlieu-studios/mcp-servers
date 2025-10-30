"""Basic usage example for RAG MCP Server components.

This example shows how to use the RAG components programmatically
(outside of the MCP server context) for testing or custom applications.
"""

import logging
from pathlib import Path

from src.embeddings import OllamaEmbedder
from src.document_processor import DocumentProcessor
from src.index_manager import IndexManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Demonstrate basic RAG functionality."""

    # Configuration
    directory_to_index = r"C:\path\to\your\project"  # Update this path
    storage_path = Path("./test_indexes")
    storage_path.mkdir(exist_ok=True)

    # Initialize embedder
    logger.info("Connecting to Ollama...")
    embedder = OllamaEmbedder(
        base_url="http://localhost:11434",
        model="nomic-embed-text",
        batch_size=32
    )

    # Initialize document processor
    doc_processor = DocumentProcessor(
        file_types=[".txt", ".md", ".py", ".js", ".ts"],
        exclude_patterns=["node_modules/**", ".git/**", "__pycache__/**"]
    )

    # Create index manager
    logger.info("Creating index manager...")
    index_manager = IndexManager(
        name="test-index",
        storage_path=storage_path,
        embedder=embedder,
        doc_processor=doc_processor,
        chunk_size=512,
        overlap=50
    )

    # Index directory
    logger.info(f"Indexing directory: {directory_to_index}")
    stats = index_manager.index_directory(directory_to_index)
    logger.info(f"Indexing complete: {stats}")

    # Query the index
    queries = [
        "authentication flow",
        "database connection",
        "error handling",
    ]

    for query_text in queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Query: {query_text}")
        logger.info(f"{'='*60}")

        results = index_manager.query(
            query_text=query_text,
            top_k=3,
            semantic_weight=0.7,
            keyword_weight=0.3
        )

        if not results:
            logger.info("No results found")
            continue

        for i, result in enumerate(results, 1):
            logger.info(f"\nResult {i} (score: {result.score:.3f})")
            logger.info(f"File: {result.file_path}")
            logger.info(f"Location: chars {result.start_char}-{result.end_char}")
            logger.info(f"Content:\n{result.text[:200]}...")

    # Get index statistics
    logger.info(f"\n{'='*60}")
    logger.info("Index Statistics")
    logger.info(f"{'='*60}")
    stats = index_manager.get_stats()
    for key, value in stats.items():
        logger.info(f"{key}: {value}")

    # Close connections
    index_manager.close()
    logger.info("\nDone!")


if __name__ == "__main__":
    main()
