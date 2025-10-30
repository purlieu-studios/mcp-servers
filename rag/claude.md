# RAG Server - Claude Guide

Intelligent document search using hybrid semantic + keyword retrieval powered by FAISS vector search and SQLite FTS5.

## 🎯 What This Server Does

The RAG (Retrieval Augmented Generation) server indexes your code and documents, then allows you to search them using:
- **Semantic search**: Understands meaning and context (via Ollama embeddings)
- **Keyword search**: Traditional text matching (via SQLite FTS5 with BM25)
- **Hybrid search**: Combines both for optimal results

## 🔧 Available Tools (5)

### 1. `query` - Search Indexed Content

Search across your indexed codebase using hybrid semantic + keyword search.

**Parameters:**
```json
{
  "query": "authentication logic",           // What to search for
  "index_name": "my-project",                // Optional: specific index
  "top_k": 5,                                // Optional: number of results (default: 5)
  "min_score": 0.5,                          // Optional: minimum relevance score
  "include_keywords": true                   // Optional: include keyword matches
}
```

**Returns:**
```json
{
  "results": [
    {
      "text": "def authenticate_user(username, password):\n    ...",
      "file_path": "/project/auth.py",
      "score": 0.87,
      "start_char": 145,
      "end_char": 645
    }
  ],
  "index_name": "my-project",
  "total_results": 5
}
```

**Example Usage:**
```
"Search my codebase for authentication logic"
"Find code related to database connections"
"Show me all error handling code"
```

**Tips:**
- Use natural language for semantic search ("how users log in")
- Use specific terms for keyword search ("authenticate_user function")
- Adjust `top_k` based on how many results you want
- Use `min_score` to filter low-relevance results

---

### 2. `list_indexes` - Show All Indexes

Get a list of all available indexes with their statistics.

**Parameters:** None

**Returns:**
```json
{
  "indexes": [
    {
      "name": "my-project",
      "file_count": 234,
      "chunk_count": 1892,
      "vector_count": 1892,
      "size_mb": 45.3
    },
    {
      "name": "documentation",
      "file_count": 45,
      "chunk_count": 312,
      "vector_count": 312,
      "size_mb": 8.7
    }
  ]
}
```

**Example Usage:**
```
"What indexes are available?"
"Show me all my indexed projects"
```

---

### 3. `refresh_index` - Update Index

Manually refresh an index to pick up file changes.

**Parameters:**
```json
{
  "index_name": "my-project"
}
```

**Returns:**
```json
{
  "index_name": "my-project",
  "files_added": 3,
  "files_updated": 5,
  "files_removed": 1,
  "total_files": 237
}
```

**Example Usage:**
```
"Refresh the my-project index"
"Update the documentation index with new files"
```

**Note:** If file watching is enabled, this happens automatically. Use this for manual refreshes.

---

### 4. `get_index_info` - Detailed Index Information

Get comprehensive information about a specific index.

**Parameters:**
```json
{
  "index_name": "my-project"
}
```

**Returns:**
```json
{
  "name": "my-project",
  "directory": "/path/to/project",
  "statistics": {
    "file_count": 234,
    "chunk_count": 1892,
    "vector_count": 1892,
    "total_size_bytes": 47519232
  },
  "configuration": {
    "chunk_size": 512,
    "overlap": 50,
    "file_types": [".py", ".js", ".md", ".txt"]
  },
  "files": [
    "/path/to/project/auth.py",
    "/path/to/project/database.py",
    "..."
  ]
}
```

**Example Usage:**
```
"Give me details about the my-project index"
"What files are in the documentation index?"
```

---

### 5. `search_files` - Find Files by Name

Search for files by name pattern within an index.

**Parameters:**
```json
{
  "pattern": "*.py",                         // Glob pattern
  "index_name": "my-project"                 // Optional: specific index
}
```

**Returns:**
```json
{
  "files": [
    "/path/to/project/auth.py",
    "/path/to/project/database.py",
    "/path/to/project/models.py"
  ],
  "total_files": 3,
  "index_name": "my-project"
}
```

**Example Usage:**
```
"Find all Python files in my-project"
"Show me all markdown files"
"List JavaScript files in the index"
```

---

## 💡 Usage Examples

### Basic Search
```
You: "Search my codebase for user authentication"

Uses: query tool with hybrid search
Returns: Relevant code chunks from auth.py, user_service.py, etc.
```

### Finding Specific Code
```
You: "Find the function that validates email addresses"

Uses: query tool with semantic understanding
Returns: Code chunks containing email validation logic
```

### Exploring a Feature
```
You: "Show me all code related to payment processing"

Uses: query tool with high top_k
Returns: Multiple chunks covering payment flows
```

### Understanding Coverage
```
You: "What's in my documentation index?"

Uses: get_index_info tool
Returns: Full list of indexed documentation files
```

---

## 🎯 How Hybrid Search Works

The RAG server combines two search methods:

### Semantic Search (70% weight by default)
- Uses Ollama embeddings (nomic-embed-text, 768 dimensions)
- Understands meaning and context
- Finds conceptually similar code
- Stored in FAISS vector index

**Good for:**
- Conceptual queries ("error handling")
- Natural language questions
- Finding similar code patterns

### Keyword Search (30% weight by default)
- Uses SQLite FTS5 with BM25 ranking
- Traditional text matching
- Exact term matching
- Fast and precise

**Good for:**
- Specific function names
- Exact error messages
- Unique identifiers

### Combined Results
Scores from both methods are merged using configurable weights, giving you the best of both worlds.

---

## ⚙️ Configuration

The RAG server uses `config.json` for configuration:

```json
{
  "storage_path": "C:\\Users\\user\\.rag-mcp-indexes",
  "ollama": {
    "base_url": "http://localhost:11434",
    "model": "nomic-embed-text",
    "batch_size": 32
  },
  "chunking": {
    "chunk_size": 512,
    "overlap": 50
  },
  "indexes": [
    {
      "name": "my-project",
      "path": "C:\\projects\\my-project",
      "description": "Main project codebase",
      "watch": true,
      "file_types": [".py", ".js", ".ts", ".md"],
      "exclude_patterns": ["node_modules/", ".git/", "*.min.js"]
    }
  ]
}
```

**Key Settings:**
- `chunk_size`: Characters per chunk (512 recommended for code)
- `overlap`: Characters of overlap between chunks
- `watch`: Enable real-time file watching
- `file_types`: Which files to index
- `exclude_patterns`: Patterns to ignore

---

## 🚀 Performance Tips

### For Best Search Results
1. Use natural language for concepts
2. Use specific terms for exact matches
3. Increase `top_k` if you need more results
4. Adjust `min_score` to filter noise

### For Fast Indexing
1. Exclude unnecessary directories (`node_modules`, `.git`)
2. Limit file types to what you need
3. Use appropriate `chunk_size` (smaller = more chunks = slower)

### For Large Codebases
1. Create separate indexes for different parts
2. Use `watch: false` if manual refresh is okay
3. Consider larger `chunk_size` (up to 1024)

---

## 🔍 Query Best Practices

### Good Queries
✅ "authentication logic"
✅ "error handling in API calls"
✅ "database connection code"
✅ "user validation functions"

### Less Effective Queries
❌ "code" (too vague)
❌ "stuff" (not specific)
❌ Single characters or very short terms

### Pro Tips
- Be specific about what you're looking for
- Include context when helpful ("API authentication" vs just "auth")
- Use technical terms the code likely contains
- Try both broad and specific queries

---

## 🐛 Troubleshooting

### No Results Found
- Check if the index contains the file
- Try a broader query
- Lower `min_score` threshold
- Verify index is up to date (use `refresh_index`)

### Results Not Relevant
- Increase `min_score` to filter low-quality matches
- Use more specific query terms
- Check if the right files are indexed

### Slow Search
- Reduce `top_k` value
- Check if file watching is causing re-indexing
- Consider splitting large indexes

---

## 📊 Index Statistics

Check index health with `get_index_info`:
- **file_count**: Number of indexed files
- **chunk_count**: Number of text chunks
- **vector_count**: Number of embeddings (should equal chunk_count)
- **total_size_bytes**: Index size on disk

Healthy indexes have vector_count == chunk_count

---

## 🔗 Related Resources

- [RAG README](./README.md) - Full documentation
- [Quick Start Guide](./QUICKSTART.md) - Setup in 5 minutes
- [Setup Instructions](./SETUP_INSTRUCTIONS.md) - Detailed setup

---

**Need help? Just ask! I can help you:**
- Find the right query terms
- Understand search results
- Optimize index configuration
- Troubleshoot issues
