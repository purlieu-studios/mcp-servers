# Quick Start Guide

Get your RAG MCP server running in 5 minutes!

## Step 1: Install Ollama

Download and install Ollama from https://ollama.ai

**Windows**: Download the installer
**macOS**: `brew install ollama`
**Linux**: `curl -fsSL https://ollama.com/install.sh | sh`

## Step 2: Start Ollama and Pull Model

```bash
# Start Ollama (if not already running)
ollama serve

# In a new terminal, pull the embedding model
ollama pull nomic-embed-text
```

## Step 3: Install RAG MCP Server

```bash
cd C:\programming\RAG  # Or your installation path

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Step 4: Configure Your Indexes

Copy and edit the configuration:

```bash
cp config.example.json config.json
```

Edit `config.json` and update the `auto_index` section:

```json
{
  "auto_index": [
    {
      "name": "my-project",
      "path": "C:\\Users\\YourName\\projects\\my-project",
      "watch": true
    }
  ]
}
```

**Important**: Use absolute paths, not relative paths!

## Step 5: Test the Server

```bash
# Windows
set CONFIG_PATH=C:\programming\RAG\config.json
python src\rag_server.py

# Unix
export CONFIG_PATH=/path/to/RAG/config.json
python src/rag_server.py
```

You should see:
```
INFO - Successfully connected to Ollama with model nomic-embed-text
INFO - Auto-indexing: my-project from /path/to/project
INFO - Loaded 150 documents from /path/to/project
INFO - Indexing complete: {'files_indexed': 150, 'chunks_created': 1245}
INFO - RAG server initialized successfully
```

## Step 6: Configure Claude Code

Edit your Claude Code config file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

Add the MCP server:

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

## Step 7: Restart Claude Code

Restart Claude Code to load the MCP server.

## Step 8: Test It!

In Claude Code, try asking:
- "What files are indexed?" (Claude will use `list_indexes` tool)
- "Search for authentication code" (Claude will use `query` tool)
- "Find all .py files" (Claude will use `search_files` tool)

## Common Issues

### Ollama not connecting
- Make sure Ollama is running: `ollama serve`
- Check `base_url` in config.json: `http://localhost:11434`

### No files indexed
- Verify paths are absolute
- Check file extensions are in `file_types` list
- Review `exclude_patterns` - might be excluding your files

### Server not appearing in Claude Code
- Check JSON syntax in claude_desktop_config.json
- Verify paths in MCP config are correct
- Look at Claude Code logs for errors

## Next Steps

- Add more directories to `auto_index`
- Customize `chunk_size` and `overlap` for your content
- Adjust `hybrid_search` weights for better results
- Enable `watch: true` for automatic updates

## Getting Help

- Check README.md for detailed documentation
- Review logs for error messages
- Ensure Ollama model is downloaded: `ollama list`
