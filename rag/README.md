# RAG MCP Server

A reusable MCP (Model Context Protocol) server that provides Retrieval Augmented Generation (RAG) capabilities using local Ollama embeddings. This server allows Claude Code and other MCP clients to search through indexed codebases and documentation.

## Features

- **Local Ollama Embeddings**: Uses Ollama's nomic-embed-text model for fully local, cost-free operation
- **Hybrid Search**: Combines semantic search (vector similarity) with keyword search (BM25)
- **Auto-indexing**: Automatically indexes configured directories on startup
- **File Watching**: Monitors directories for changes and refreshes indexes automatically
- **Persistent Storage**: Indexes are saved to disk and loaded on startup
- **Multi-format Support**: Handles text, markdown, code files, and more
- **Efficient**: Uses FAISS for fast vector search and SQLite for metadata

## Architecture

```
┌─────────────────────────────────────────────┐
│           MCP Client (Claude Code)          │
└─────────────────┬───────────────────────────┘
                  │ MCP Protocol
                  ▼
┌─────────────────────────────────────────────┐
│              RAG MCP Server                 │
│  ┌─────────────────────────────────────┐   │
│  │    Tools: query, list_indexes,      │   │
│  │    refresh_index, search_files      │   │
│  └─────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────────┐   │
│  │ Index Manager│  │   File Watcher   │   │
│  └──────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌──────────────────┐   │
│  │ FAISS Vector │  │ SQLite Metadata  │   │
│  │    Store     │  │  + FTS5 Search   │   │
│  └──────────────┘  └──────────────────┘   │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │ Ollama (local)   │
        │ nomic-embed-text │
        └──────────────────┘
```

## Prerequisites

1. **Python 3.10+**
2. **Ollama**: Install from https://ollama.ai
3. **nomic-embed-text model**: Run `ollama pull nomic-embed-text`

## Installation

1. Clone or download this repository:
```bash
cd /path/to/RAG
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

4. Pull the Ollama embedding model:
```bash
ollama pull nomic-embed-text
```

## Configuration

1. Copy the example config:
```bash
cp config.example.json config.json
```

2. Edit `config.json` to configure your directories:

```json
{
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
  "file_types": [".txt", ".md", ".py", ".js", ".ts", ...],
  "exclude_patterns": ["node_modules/**", ".git/**", ...],
  "auto_index": [
    {
      "name": "my-project",
      "path": "/absolute/path/to/your/project",
      "watch": true
    }
  ]
}
```

**Important**: Use absolute paths in the `auto_index` configuration.

## Usage with Claude Code

Add the server to your Claude Code MCP configuration. The location depends on your platform:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

Add this to the `mcpServers` section:

```json
{
  "mcpServers": {
    "rag": {
      "command": "python",
      "args": ["C:\\programming\\RAG\\src\\rag_server.py"],
      "env": {
        "CONFIG_PATH": "C:\\programming\\RAG\\config.json"
      }
    }
  }
}
```

**Note**: Update paths to match your installation location.

## Testing the Server

Test the server directly:

```bash
# Set config path
set CONFIG_PATH=C:\programming\RAG\config.json  # Windows
export CONFIG_PATH=/path/to/RAG/config.json     # Unix

# Run the server
python src/rag_server.py
```

The server will:
1. Connect to Ollama
2. Load or create indexes for configured directories
3. Start file watchers (if enabled)
4. Listen for MCP tool calls

## Available MCP Tools

Once connected, Claude can use these tools:

### 1. `query`
Search indexed documents using hybrid search.

**Parameters**:
- `query` (required): Search text
- `index_name` (optional): Specific index to search
- `top_k` (default: 5): Number of results
- `min_score` (default: 0.0): Minimum score threshold
- `include_keywords` (default: true): Enable keyword search

**Example**:
```
Claude internally calls: query(query="authentication flow", top_k=10)
```

### 2. `list_indexes`
List all available indexes with statistics.

### 3. `refresh_index`
Manually refresh an index by re-scanning its directory.

**Parameters**:
- `index_name` (required): Index to refresh

### 4. `get_index_info`
Get detailed information about an index.

**Parameters**:
- `index_name` (required): Index name

### 5. `search_files`
Find files by name pattern in indexed directories.

**Parameters**:
- `pattern` (required): File name pattern
- `index_name` (optional): Specific index to search

## How It Works

### Indexing Process

1. **Document Loading**: Scans configured directories for supported file types
2. **Chunking**: Splits documents into overlapping chunks (default: 512 chars with 50 char overlap)
3. **Embedding**: Generates vector embeddings using Ollama's nomic-embed-text model
4. **Storage**:
   - Vectors stored in FAISS index (fast similarity search)
   - Text and metadata stored in SQLite (keyword search via FTS5)
5. **File Watching**: Monitors files for changes and re-indexes modified files

### Query Process

1. **Query Embedding**: Converts search query to vector using Ollama
2. **Semantic Search**: FAISS finds similar vectors (cosine similarity)
3. **Keyword Search**: SQLite FTS5 performs BM25 ranking
4. **Score Fusion**: Combines scores using configurable weights (default: 70% semantic, 30% keyword)
5. **Results**: Returns top-k chunks with context

## Configuration Options

### Storage Path
Where indexes are persisted:
```json
"storage_path": "~/.rag-mcp-indexes"
```

### Ollama Settings
```json
"ollama": {
  "base_url": "http://localhost:11434",  // Ollama server URL
  "embedding_model": "nomic-embed-text",  // Model name
  "batch_size": 32                        // Embeddings per batch
}
```

### Chunking Strategy
```json
"chunking": {
  "chunk_size": 512,  // Characters per chunk
  "overlap": 50       // Overlap between chunks
}
```

### File Types
List of file extensions to index:
```json
"file_types": [".txt", ".md", ".py", ".js", ...]
```

### Exclude Patterns
Glob patterns to exclude:
```json
"exclude_patterns": [
  "node_modules/**",
  ".git/**",
  "__pycache__/**"
]
```

### Hybrid Search Weights
Balance between semantic and keyword search:
```json
"hybrid_search": {
  "semantic_weight": 0.7,   // 70% semantic
  "keyword_weight": 0.3     // 30% keyword
}
```

## Example Workflow

1. **Setup**: Configure `config.json` with your project paths
2. **Start**: Run the MCP server (automatically starts when Claude Code connects)
3. **Auto-index**: Server indexes configured directories on startup
4. **Ask Claude**: "What's the authentication implementation in my backend?"
5. **Search**: Claude calls `query` tool with your question
6. **Results**: Receives relevant code chunks from your indexed codebase
7. **Answer**: Claude uses the retrieved context to answer accurately

## Troubleshooting

### "Failed to connect to Ollama"
- Ensure Ollama is running: `ollama serve`
- Check `base_url` in config matches Ollama's address
- Verify model is installed: `ollama list`

### "No results found"
- Check index was created: Use `list_indexes` tool
- Verify directory paths are absolute and exist
- Check file types are included in `file_types`
- Review `exclude_patterns` - might be excluding needed files

### "Indexing is slow"
- Reduce `batch_size` if running on CPU
- Reduce `chunk_size` to create fewer chunks
- Exclude large binary or generated files

### File changes not detected
- Verify `watch: true` in auto_index config
- Check file type is in `file_types` list
- Restart server to reload configuration

## Performance Tips

- **CPU-only**: Ollama embeddings work on CPU but are slower. Consider using a smaller model or reducing batch size.
- **Large codebases**: Exclude build artifacts, dependencies (`node_modules`, `venv`), and generated files.
- **Chunk size**: Smaller chunks (256-512) work better for code, larger (1024) for documentation.
- **Index storage**: FAISS and SQLite files can grow large. Monitor `storage_path` disk usage.

## Development

### Project Structure
```
RAG/
├── src/
│   ├── __init__.py
│   ├── rag_server.py          # Main MCP server
│   ├── index_manager.py       # Index lifecycle
│   ├── document_processor.py  # Document loading
│   ├── chunking.py           # Text chunking
│   ├── embeddings.py         # Ollama client
│   ├── vector_store.py       # FAISS operations
│   ├── metadata_store.py     # SQLite + FTS5
│   └── file_watcher.py       # Change detection
├── config.example.json
├── requirements.txt
├── setup.py
└── README.md
```

### Running Tests
```bash
pytest tests/
```

### Logging
The server logs to stdout. Increase verbosity by editing `rag_server.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## License

MIT License - feel free to use and modify for your projects.

## Contributing

Contributions welcome! Areas for improvement:
- Additional file format loaders (PDF, DOCX)
- More chunking strategies (AST-based for code)
- Additional vector stores (Qdrant, Milvus)
- Performance optimizations
- Better error handling and recovery

## Acknowledgments

- Built on the [Model Context Protocol](https://github.com/anthropics/mcp)
- Uses [Ollama](https://ollama.ai) for local embeddings
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [SQLite FTS5](https://www.sqlite.org/fts5.html) for keyword search
