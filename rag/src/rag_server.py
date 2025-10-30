"""MCP server for RAG capabilities."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from .embeddings import OllamaEmbedder
from .document_processor import DocumentProcessor
from .index_manager import IndexManager
from .file_watcher import FileWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGServer:
    """MCP server providing RAG capabilities."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.server = Server("rag-mcp-server")
        self.indexes: Dict[str, IndexManager] = {}
        self.embedder: Optional[OllamaEmbedder] = None
        self.doc_processor: Optional[DocumentProcessor] = None
        self.file_watcher: Optional[FileWatcher] = None

        self._register_handlers()

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file."""
        if config_path is None:
            config_path = os.environ.get('CONFIG_PATH', 'config.json')

        config_file = Path(config_path)

        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._default_config()

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "server_name": "rag-mcp-server",
            "storage_path": "~/.rag-mcp-indexes",
            "ollama": {
                "base_url": "http://localhost:11434",
                "embedding_model": "nomic-embed-text",
                "batch_size": 32
            },
            "chunking": {
                "chunk_size": 512,
                "overlap": 50
            },
            "file_types": [".txt", ".md", ".py", ".js", ".ts"],
            "exclude_patterns": ["node_modules/**", ".git/**"],
            "auto_index": [],
            "hybrid_search": {
                "semantic_weight": 0.7,
                "keyword_weight": 0.3
            }
        }

    async def initialize(self):
        """Initialize the RAG server components."""
        logger.info("Initializing RAG server...")

        # Initialize embedder
        ollama_config = self.config.get('ollama', {})
        self.embedder = OllamaEmbedder(
            base_url=ollama_config.get('base_url', 'http://localhost:11434'),
            model=ollama_config.get('embedding_model', 'nomic-embed-text'),
            batch_size=ollama_config.get('batch_size', 32)
        )

        # Initialize document processor
        self.doc_processor = DocumentProcessor(
            file_types=self.config.get('file_types', []),
            exclude_patterns=self.config.get('exclude_patterns', [])
        )

        # Initialize file watcher
        self.file_watcher = FileWatcher()

        # Auto-index configured directories
        storage_path = Path(self.config.get('storage_path', '~/.rag-mcp-indexes')).expanduser()
        auto_index_configs = self.config.get('auto_index', [])

        for index_config in auto_index_configs:
            name = index_config.get('name')
            directory = index_config.get('path')
            watch = index_config.get('watch', False)

            if not name or not directory:
                logger.warning(f"Invalid auto_index config: {index_config}")
                continue

            # Create index manager
            index_manager = IndexManager(
                name=name,
                storage_path=storage_path,
                embedder=self.embedder,
                doc_processor=self.doc_processor,
                chunk_size=self.config['chunking']['chunk_size'],
                overlap=self.config['chunking']['overlap']
            )

            self.indexes[name] = index_manager

            # Index directory
            logger.info(f"Auto-indexing: {name} from {directory}")
            await asyncio.to_thread(index_manager.index_directory, directory)

            # Set up file watching
            if watch:
                def refresh_callback(dir_path):
                    asyncio.create_task(
                        asyncio.to_thread(index_manager.refresh, str(dir_path))
                    )

                self.file_watcher.watch_directory(
                    directory=directory,
                    file_types=set(self.config.get('file_types', [])),
                    on_change=refresh_callback
                )

        # Start file watcher
        if self.file_watcher and auto_index_configs:
            self.file_watcher.start()

        logger.info("RAG server initialized successfully")

    def _register_handlers(self):
        """Register MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="query",
                    description="Search indexed documents using semantic and keyword search",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query text"
                            },
                            "index_name": {
                                "type": "string",
                                "description": "Name of index to search (optional, searches all if not specified)"
                            },
                            "top_k": {
                                "type": "number",
                                "description": "Number of results to return (default: 5)",
                                "default": 5
                            },
                            "min_score": {
                                "type": "number",
                                "description": "Minimum score threshold (default: 0.0)",
                                "default": 0.0
                            },
                            "include_keywords": {
                                "type": "boolean",
                                "description": "Include keyword search (default: true)",
                                "default": True
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="list_indexes",
                    description="List all available indexes with statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="refresh_index",
                    description="Refresh an index by re-scanning its directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "index_name": {
                                "type": "string",
                                "description": "Name of index to refresh"
                            }
                        },
                        "required": ["index_name"]
                    }
                ),
                Tool(
                    name="get_index_info",
                    description="Get detailed information about an index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "index_name": {
                                "type": "string",
                                "description": "Name of index"
                            }
                        },
                        "required": ["index_name"]
                    }
                ),
                Tool(
                    name="search_files",
                    description="Search for files by name pattern in indexed directories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "File name pattern to search for"
                            },
                            "index_name": {
                                "type": "string",
                                "description": "Name of index to search (optional, searches all if not specified)"
                            }
                        },
                        "required": ["pattern"]
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "query":
                    return await self._handle_query(arguments)
                elif name == "list_indexes":
                    return await self._handle_list_indexes(arguments)
                elif name == "refresh_index":
                    return await self._handle_refresh_index(arguments)
                elif name == "get_index_info":
                    return await self._handle_get_index_info(arguments)
                elif name == "search_files":
                    return await self._handle_search_files(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _handle_query(self, arguments: dict) -> list[TextContent]:
        """Handle query tool."""
        query = arguments.get('query')
        index_name = arguments.get('index_name')
        top_k = arguments.get('top_k', 5)
        min_score = arguments.get('min_score', 0.0)
        include_keywords = arguments.get('include_keywords', True)

        # Determine which indexes to search
        indexes_to_search = {}
        if index_name:
            if index_name not in self.indexes:
                return [TextContent(type="text", text=f"Index '{index_name}' not found")]
            indexes_to_search[index_name] = self.indexes[index_name]
        else:
            indexes_to_search = self.indexes

        if not indexes_to_search:
            return [TextContent(type="text", text="No indexes available")]

        # Search all relevant indexes
        all_results = []
        hybrid_config = self.config.get('hybrid_search', {})

        for idx_name, index in indexes_to_search.items():
            results = await asyncio.to_thread(
                index.query,
                query,
                top_k=top_k,
                min_score=min_score,
                semantic_weight=hybrid_config.get('semantic_weight', 0.7),
                keyword_weight=hybrid_config.get('keyword_weight', 0.3),
                include_keywords=include_keywords
            )

            for result in results:
                all_results.append({
                    'index': idx_name,
                    'file': result.file_path,
                    'text': result.text,
                    'score': result.score,
                    'location': f"{result.start_char}-{result.end_char}"
                })

        # Sort by score and limit
        all_results.sort(key=lambda x: x['score'], reverse=True)
        all_results = all_results[:top_k]

        # Format results
        if not all_results:
            return [TextContent(type="text", text="No results found")]

        output = f"Found {len(all_results)} results for query: '{query}'\n\n"
        for i, result in enumerate(all_results, 1):
            output += f"Result {i} (score: {result['score']:.3f})\n"
            output += f"Index: {result['index']}\n"
            output += f"File: {result['file']}\n"
            output += f"Location: chars {result['location']}\n"
            output += f"Content:\n{result['text']}\n"
            output += "-" * 80 + "\n\n"

        return [TextContent(type="text", text=output)]

    async def _handle_list_indexes(self, arguments: dict) -> list[TextContent]:
        """Handle list_indexes tool."""
        if not self.indexes:
            return [TextContent(type="text", text="No indexes available")]

        output = "Available Indexes:\n\n"
        for name, index in self.indexes.items():
            stats = index.get_stats()
            output += f"Index: {name}\n"
            output += f"  Files: {stats['files']}\n"
            output += f"  Chunks: {stats['chunks']}\n"
            output += f"  Vectors: {stats['vectors']}\n"
            output += f"  Size: {stats['size_bytes'] / 1024:.1f} KB\n\n"

        return [TextContent(type="text", text=output)]

    async def _handle_refresh_index(self, arguments: dict) -> list[TextContent]:
        """Handle refresh_index tool."""
        index_name = arguments.get('index_name')

        if index_name not in self.indexes:
            return [TextContent(type="text", text=f"Index '{index_name}' not found")]

        # Find the directory for this index
        directory = None
        for auto_index in self.config.get('auto_index', []):
            if auto_index.get('name') == index_name:
                directory = auto_index.get('path')
                break

        if not directory:
            return [TextContent(type="text", text=f"No directory configured for index '{index_name}'")]

        # Refresh the index
        index = self.indexes[index_name]
        stats = await asyncio.to_thread(index.refresh, directory)

        output = f"Refreshed index '{index_name}'\n"
        output += f"Files indexed: {stats['files_indexed']}\n"
        output += f"Chunks created: {stats['chunks_created']}\n"

        return [TextContent(type="text", text=output)]

    async def _handle_get_index_info(self, arguments: dict) -> list[TextContent]:
        """Handle get_index_info tool."""
        index_name = arguments.get('index_name')

        if index_name not in self.indexes:
            return [TextContent(type="text", text=f"Index '{index_name}' not found")]

        index = self.indexes[index_name]
        stats = index.get_stats()
        files = index.list_files()

        output = f"Index: {index_name}\n\n"
        output += "Statistics:\n"
        output += f"  Files: {stats['files']}\n"
        output += f"  Chunks: {stats['chunks']}\n"
        output += f"  Vectors: {stats['vectors']}\n"
        output += f"  Size: {stats['size_bytes'] / 1024:.1f} KB\n\n"

        output += f"Indexed Files ({len(files)}):\n"
        for file_path in sorted(files)[:50]:  # Limit to first 50
            output += f"  {file_path}\n"

        if len(files) > 50:
            output += f"  ... and {len(files) - 50} more files\n"

        return [TextContent(type="text", text=output)]

    async def _handle_search_files(self, arguments: dict) -> list[TextContent]:
        """Handle search_files tool."""
        pattern = arguments.get('pattern', '').lower()
        index_name = arguments.get('index_name')

        # Determine which indexes to search
        indexes_to_search = {}
        if index_name:
            if index_name not in self.indexes:
                return [TextContent(type="text", text=f"Index '{index_name}' not found")]
            indexes_to_search[index_name] = self.indexes[index_name]
        else:
            indexes_to_search = self.indexes

        if not indexes_to_search:
            return [TextContent(type="text", text="No indexes available")]

        # Search for files
        matching_files = []
        for idx_name, index in indexes_to_search.items():
            files = index.list_files()
            for file_path in files:
                if pattern in file_path.lower():
                    matching_files.append({'index': idx_name, 'path': file_path})

        if not matching_files:
            return [TextContent(type="text", text=f"No files found matching pattern: {pattern}")]

        output = f"Found {len(matching_files)} files matching '{pattern}':\n\n"
        for item in sorted(matching_files, key=lambda x: x['path'])[:100]:
            output += f"[{item['index']}] {item['path']}\n"

        if len(matching_files) > 100:
            output += f"\n... and {len(matching_files) - 100} more files"

        return [TextContent(type="text", text=output)]

    async def run(self):
        """Run the MCP server."""
        await self.initialize()

        # Run server
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_init_options()
            )


async def main():
    """Main entry point."""
    server = RAGServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
