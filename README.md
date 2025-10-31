# MCP Servers Collection

![Tests](https://github.com/purlieu-studios/mcp-servers/actions/workflows/test.yml/badge.svg)
[![codecov](https://codecov.io/gh/purlieu-studios/mcp-servers/branch/main/graph/badge.svg)](https://codecov.io/gh/purlieu-studios/mcp-servers)

A comprehensive collection of Model Context Protocol (MCP) servers for code analysis, database management, intelligent document search, AI-powered task planning, and context-aware workspace intelligence.

## 🚀 Available Servers

### 1. **RAG Server** - Intelligent Document Search 🔍
**Path**: `./rag/` | **Status**: ✅ Production Ready (118 tests passing, 54% coverage)

Production-ready semantic search with hybrid retrieval (vector + keyword).

**Features:**
- 🧠 Semantic search using Ollama embeddings (nomic-embed-text, 768-dim)
- 📊 Hybrid search combining FAISS vector similarity + SQLite FTS5 BM25
- 📁 Real-time file watching with automatic index refresh
- 🎯 Multi-index support with independent configurations
- 💾 Persistent indexes with caching
- 🔧 5 MCP Tools: query, list_indexes, refresh_index, get_index_info, search_files

[📖 Full Documentation](./rag/README.md) | [⚡ Quick Start](./rag/QUICKSTART.md)

---

### 2. **Code Analysis Server** - AST & Quality Analysis 🔬
**Path**: `./code-analysis/` | **Status**: ✅ Production Ready (62 tests passing, 82% coverage)

Comprehensive code analysis with AST parsing, complexity metrics, and code smell detection.

**Features:**
- 🌳 Full AST parsing for Python with type annotations
- 📊 Cyclomatic & cognitive complexity analysis
- 👃 Code smell detection (long methods, god classes, missing docstrings)
- 🔗 Dependency mapping and import analysis
- 📝 Function & class extraction with complete signatures
- 🎯 Supports: **Python**, JavaScript/TypeScript, C#

**6 Analysis Tools:**
- `parse_ast` - Detailed AST representation
- `analyze_complexity` - Complexity metrics per function
- `find_code_smells` - Quality issue detection
- `analyze_functions` - Extract all functions with signatures
- `analyze_classes` - Class structure analysis
- `find_dependencies` - Map imports and dependencies

[📖 Documentation](./code-analysis/README.md)

---

### 3. **EF Core Analysis Server** - Database & ORM Intelligence 🗄️
**Path**: `./efcore-analysis/` | **Status**: ✅ Production Ready (75 tests passing, 76% coverage)

Specialized Entity Framework Core analysis, optimization, and migration support.

**Features:**
- 🏗️ DbContext inspection and configuration analysis
- 📋 Entity model validation with relationship mapping
- 🔄 Automatic migration code generation from model diffs
- ⚡ LINQ query optimization suggestions (N+1 detection, async recommendations)
- 📈 AI-powered database index recommendations
- ✅ Model validation for common EF Core configuration issues

**7 Analysis Tools:**
- `analyze_dbcontext` - Inspect DbContext structure and config
- `analyze_entity` - Deep entity model analysis with relationships
- `generate_migration` - Generate migration Up/Down code
- `analyze_linq` - Optimize LINQ queries
- `suggest_indexes` - Recommend database indexes from query patterns
- `validate_model` - Find configuration issues
- `find_relationships` - Map complete entity relationship graph

[📖 Documentation](./efcore-analysis/README.md)

---

### 4. **Task Generator Server** - AI Project Planning 🎯
**Path**: `./task-generator/` | **Status**: ✅ Production Ready (14 tests passing, 55% coverage)

AI-powered project planning and task breakdown with LOC estimation.

**Features:**
- 🤖 Smart task generation from natural language descriptions
- 📋 Template system for common patterns (MCP servers, APIs, databases, testing)
- 📊 Complexity analysis with LOC and time estimates
- 🔄 Plan refinement capabilities (remove, split, modify tasks)
- 💡 Commit planning with 500 LOC limit respect
- 🔗 Automatic dependency tracking

**4 Planning Tools:**
- `generate_task_plan` - Convert descriptions into structured task plans
- `refine_task_plan` - Adjust plans with modifications
- `estimate_complexity` - Analyze project scope and effort
- `list_templates` - Show available task templates

[📖 Documentation](./task-generator/README.md)

---

### 5. **Workspace Context Server** - Smart File Recommendations 🧠
**Path**: `./workspace-context/` | **Status**: ✅ Production Ready (20 tests passing, 50% coverage)

Intelligent context prediction and file recommendations based on workspace state.

**Features:**
- 🎯 Smart file recommendations based on current work context
- 🔗 Dependency analysis through import mapping
- 📈 Pattern detection from access history
- 🔮 Next-file prediction with confidence scores
- 📊 Access analytics and usage trends
- 📝 High-level workspace context summary

**6 Context Tools:**
- `get_context_recommendations` - Get ranked file suggestions
- `get_related_files` - Find dependencies and relationships
- `get_access_patterns` - Analyze file usage trends
- `build_dependency_map` - Map Python project dependencies
- `predict_next_files` - Predict likely next files to access
- `get_context_summary` - Workspace state overview

[📖 Documentation](./workspace-context/README.md)

---

### 6. **Session Memory Server** - Conversation Tracking 💬
**Path**: `./session-memory/` | **Status**: ✅ Production Ready (20 tests passing, 51% coverage)

Tracks conversation history and session context across restarts.

**Features:**
- 💾 Persistent conversation logging with SQLite storage
- 🔄 Automatic session management (30min inactivity = new session)
- 📌 Decision logging for key actions and choices
- 🔍 Full-text search across past conversations
- 📊 Session statistics and token usage tracking
- 🔗 Integration with workspace state

**7 Memory Tools:**
- `log_message` - Track conversation messages
- `get_session_history` - Retrieve session conversations
- `get_current_session` - Get active session info
- `search_sessions` - Search past conversations
- `log_decision` - Record key decisions
- `end_session` - Close session with summary
- `get_session_stats` - View memory usage statistics

[📖 Documentation](./session-memory/README.md)

---

## 📦 Installation

Each server can be installed independently:

```bash
# RAG Server
cd rag && pip install -r requirements.txt

# Code Analysis Server
cd code-analysis && pip install -r requirements.txt

# EF Core Analysis Server
cd efcore-analysis && pip install -r requirements.txt

# Task Generator Server
cd task-generator && pip install -r requirements.txt

# Workspace Context Server
cd workspace-context && pip install -r requirements.txt

# Session Memory Server
cd session-memory && pip install -r requirements.txt
```

## 🔧 Claude Code Configuration

Add servers to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rag": {
      "command": "python",
      "args": ["-m", "src.rag_server"],
      "cwd": "C:\\programming\\mcp-servers\\rag",
      "env": {
        "CONFIG_PATH": "C:\\programming\\mcp-servers\\rag\\config.json"
      }
    },
    "code-analysis": {
      "command": "python",
      "args": ["-m", "src.code_analysis_server"],
      "cwd": "C:\\programming\\mcp-servers\\code-analysis"
    },
    "efcore-analysis": {
      "command": "python",
      "args": ["-m", "src.efcore_server"],
      "cwd": "C:\\programming\\mcp-servers\\efcore-analysis"
    },
    "task-generator": {
      "command": "python",
      "args": ["-m", "src.task_generator_server"],
      "cwd": "C:\\programming\\mcp-servers\\task-generator"
    },
    "workspace-context": {
      "command": "python",
      "args": ["-m", "src.workspace_context_server"],
      "cwd": "C:\\programming\\mcp-servers\\workspace-context"
    },
    "session-memory": {
      "command": "python",
      "args": ["-m", "src.session_memory_server"],
      "cwd": "C:\\programming\\mcp-servers\\session-memory"
    }
  }
}
```

## 🎯 Quick Examples

### RAG Server - Semantic Code Search
```
Query: "Find all authentication-related code in my project"

→ Searches using semantic understanding + keywords
→ Returns relevant code chunks with file paths and scores
→ Supports multiple indexes simultaneously
```

### Code Analysis - Quality Check
```
Query: "Analyze UserService.py for code smells"

Returns:
✓ Too many parameters (7 > 5) → Use parameter object
✓ Missing docstrings → Add documentation
✓ High complexity (cyclomatic: 15) → Refactor method
```

### EF Core - Database Optimization
```
Query: "Analyze my DbContext and suggest database indexes"

Returns:
✓ Index on Users.Email (used in 15 WHERE clauses) - HIGH PRIORITY
✓ Index on Orders.OrderDate (used in 8 ORDER BY) - MEDIUM
✓ Missing primary key on UserProfile entity - CRITICAL
✓ N+1 query in UserRepository.GetWithOrders() - FIX NEEDED
```

## 📊 Project Statistics

- **Total MCP Servers:** 6
- **Total MCP Tools:** 37 (5 + 8 + 7 + 4 + 6 + 7)
- **Total Tests:** 300+ passing across all servers
- **Lines of Code:** ~8,500+
- **Average Coverage:** 64% across all servers
- **Languages Supported:** Python, JavaScript/TypeScript, C#

## 📁 Repository Structure

```
mcp-servers/
├── README.md                    # This file
├── rag/                         # RAG Server
│   ├── src/
│   │   ├── rag_server.py
│   │   ├── index_manager.py
│   │   ├── vector_store.py
│   │   ├── embeddings.py
│   │   ├── metadata_store.py
│   │   └── ...
│   ├── tests/                   # 107 passing tests
│   ├── config.json
│   ├── README.md
│   └── QUICKSTART.md
├── code-analysis/               # Code Analysis Server
│   ├── src/
│   │   ├── code_analysis_server.py
│   │   └── analyzers/
│   │       ├── python_analyzer.py
│   │       ├── javascript_analyzer.py
│   │       └── csharp_analyzer.py
│   └── README.md
└── efcore-analysis/             # EF Core Analysis Server
    ├── src/
    │   ├── efcore_server.py
    │   └── analyzers/
    │       ├── dbcontext_analyzer.py
    │       ├── entity_analyzer.py
    │       ├── migration_analyzer.py
    │       ├── linq_analyzer.py
    │       └── index_recommender.py
    └── README.md
```

## 🛠️ Technology Stack

- **MCP SDK:** Model Context Protocol for Claude Code integration
- **Vector Search:** FAISS (Facebook AI Similarity Search)
- **Embeddings:** Ollama (nomic-embed-text, 768-dimensional)
- **Full-Text Search:** SQLite FTS5 with BM25 ranking
- **AST Parsing:** Python `ast` module for code analysis
- **Testing:** pytest, pytest-asyncio, pytest-cov, pytest-mock

## 🧪 Testing

Comprehensive test coverage for the RAG server:

```bash
cd rag && python -m pytest tests/ -v --cov=src
```

**Test Results:**
- ✅ 107 tests passing
- ⏭️ 5 tests skipped (platform-specific)
- 📊 88% code coverage
- 🎯 Covers: chunking, embeddings, vector store, metadata store, document processing

## 🗺️ Roadmap

### Completed ✅
- [x] RAG Server with hybrid search
- [x] Comprehensive RAG test suite (unit + integration)
- [x] Code Analysis Server (Python AST + multi-language)
- [x] EF Core Analysis Server (DbContext + LINQ + migrations)
- [x] Task Generator Server (AI-powered project planning)
- [x] Workspace Context Server (smart file recommendations)
- [x] Session Memory Server (conversation tracking)
- [x] Pre-commit hooks (ruff, file checks)
- [x] CI/CD pipeline (GitHub Actions)

### In Progress 🚧
- [ ] Code-analysis CI hanging fix
- [ ] Integration tests for server files
- [ ] AST-based code chunking for RAG
- [ ] Query result caching for RAG

### Planned 📋
- [ ] Project Structure Server
- [ ] Git Operations Server
- [ ] More language support (Java, Go, Rust)
- [ ] Visual relationship diagrams (Mermaid/PlantUML)
- [ ] Performance profiling integration
- [ ] GPU embedding support
- [ ] Distributed indexing

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

- **📏 Size Limit**: PRs should be ≤500 lines of production code
- **🧪 Tests Required**: All changes need tests (≥80% coverage)
- **📝 Documentation**: Update docs for any API/tool changes
- **✅ CI Passing**: All tests must pass in CI

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

### Quick Start for Contributors

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/mcp-servers.git
cd mcp-servers

# Create a branch
git checkout -b feature/your-feature

# Make changes, add tests, run tests
cd <server-directory>
pytest tests/ -v

# Commit and push
git commit -m "feat: your feature description"
git push origin feature/your-feature

# Create PR using the template
```

## 📚 Learn More

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude Code Documentation](https://claude.com/claude-code)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Contributing Guidelines](./CONTRIBUTING.md)

## 📁 Project Structure

Each server is self-contained and follows this structure:
- `src/` - Source code
- `README.md` - Comprehensive documentation
- `requirements.txt` - Python dependencies
- `tests/` - Test suite with ≥80% coverage
- `CLAUDE.md` - Claude-specific usage guide

## 💡 Requirements

- **Python:** 3.10+
- **Claude Code:** For MCP integration
- **Ollama:** Required for RAG server (nomic-embed-text model)
- **Server-specific deps:** See individual `requirements.txt` files

## 📝 License

MIT License - see individual server directories for details.

---

**Built with ❤️ for Claude Code** | Last Updated: 2025-10-29
