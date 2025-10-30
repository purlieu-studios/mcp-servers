# MCP Servers Collection - Claude Guide

This repository contains 3 specialized MCP servers providing 18 tools for intelligent code analysis, database optimization, and semantic search.

## 🎯 Available Servers

### 1. RAG Server (5 tools)
Intelligent document search with hybrid semantic + keyword retrieval.
- [Full Documentation](./rag/claude.md)

### 2. Code Analysis Server (6 tools)
AST parsing, complexity analysis, and code quality detection.
- [Full Documentation](./code-analysis/claude.md)

### 3. EF Core Analysis Server (7 tools)
Entity Framework Core analysis, optimization, and migration support.
- [Full Documentation](./efcore-analysis/claude.md)

---

## 📚 All Available Tools (18 total)

### RAG Server Tools

#### `query`
Search across indexed codebases using hybrid semantic + keyword search.
```json
{
  "query": "authentication logic",
  "index_name": "my-project",
  "top_k": 5,
  "min_score": 0.5
}
```

#### `list_indexes`
List all available indexes with statistics.

#### `refresh_index`
Manually refresh an index to pick up file changes.

#### `get_index_info`
Get detailed information about a specific index.

#### `search_files`
Find files by name pattern within an index.

---

### Code Analysis Server Tools

#### `parse_ast`
Parse code files and return detailed AST structure (Python full support).
```json
{
  "file_path": "/path/to/file.py",
  "include_body": false
}
```

#### `analyze_complexity`
Calculate cyclomatic and cognitive complexity metrics.
```json
{
  "file_path": "/path/to/file.py",
  "function_name": "process_data"
}
```

#### `find_code_smells`
Detect code quality issues and anti-patterns.
```json
{
  "file_path": "/path/to/file.py",
  "severity": "medium"
}
```

#### `analyze_functions`
Extract all functions with signatures, parameters, and types.

#### `analyze_classes`
Analyze class definitions, methods, and inheritance.

#### `find_dependencies`
Map import statements and dependencies.
```json
{
  "file_path": "/path/to/project",
  "recursive": true
}
```

---

### EF Core Analysis Server Tools

#### `analyze_dbcontext`
Inspect DbContext class structure and configuration.
```json
{
  "file_path": "/path/to/ApplicationDbContext.cs"
}
```

#### `analyze_entity`
Deep analysis of entity models with relationships.
```json
{
  "file_path": "/path/to/User.cs",
  "entity_name": "User"
}
```

#### `generate_migration`
Generate EF Core migration code from model changes.
```json
{
  "old_model_path": "/path/to/User.old.cs",
  "new_model_path": "/path/to/User.cs",
  "migration_name": "AddUserEmail"
}
```

#### `analyze_linq`
Analyze LINQ queries for optimization opportunities.

#### `suggest_indexes`
AI-powered database index recommendations.
```json
{
  "project_path": "/path/to/project",
  "dbcontext_name": "ApplicationDbContext"
}
```

#### `validate_model`
Validate entity models for EF Core configuration issues.

#### `find_relationships`
Map all entity relationships in a project.

---

## 💡 Common Usage Patterns

### Finding Code
```
"Search my codebase for authentication-related code"
→ Uses RAG query tool with semantic understanding

"Find all functions that handle user input validation"
→ Uses RAG query + analyze_functions tools
```

### Code Quality
```
"Analyze UserService.py for code smells"
→ Uses find_code_smells tool

"What's the complexity of the authenticate function?"
→ Uses analyze_complexity tool
```

### Database Optimization
```
"Analyze my DbContext and suggest improvements"
→ Uses analyze_dbcontext + suggest_indexes tools

"Check if my User entity is properly configured"
→ Uses validate_model tool
```

### Understanding Code Structure
```
"Show me all the classes in this file and their methods"
→ Uses analyze_classes tool

"What are the dependencies of this module?"
→ Uses find_dependencies tool
```

---

## 🔧 Setup

Each server needs to be configured in your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "rag": {
      "command": "python",
      "args": ["-m", "src.rag_server"],
      "cwd": "C:\\path\\to\\mcp-servers\\rag",
      "env": {
        "CONFIG_PATH": "C:\\path\\to\\mcp-servers\\rag\\config.json"
      }
    },
    "code-analysis": {
      "command": "python",
      "args": ["-m", "src.code_analysis_server"],
      "cwd": "C:\\path\\to\\mcp-servers\\code-analysis"
    },
    "efcore-analysis": {
      "command": "python",
      "args": ["-m", "src.efcore_server"],
      "cwd": "C:\\path\\to\\mcp-servers\\efcore-analysis"
    }
  }
}
```

---

## 🎓 Best Practices

### For RAG Server
- Create separate indexes for different projects
- Use semantic search for concept-based queries
- Use keyword search for exact matches
- Combine both with hybrid search for best results

### For Code Analysis
- Start with code smell detection for quick wins
- Use complexity analysis to identify refactoring candidates
- Parse AST when you need detailed structure information
- Run dependency analysis to understand module relationships

### For EF Core Analysis
- Always validate models before deploying migrations
- Use LINQ analysis to catch N+1 queries early
- Generate indexes based on actual query patterns
- Validate relationships to prevent runtime errors

---

## 📊 Tool Selection Guide

**Want to search code?** → RAG Server
**Want to analyze code quality?** → Code Analysis Server
**Want to optimize database/EF Core?** → EF Core Analysis Server

**Need complexity metrics?** → `analyze_complexity`
**Need to find issues?** → `find_code_smells` or `validate_model`
**Need structure info?** → `parse_ast`, `analyze_functions`, `analyze_classes`
**Need performance help?** → `analyze_linq`, `suggest_indexes`

---

## 🔗 Quick Links

- [RAG Server Details](./rag/claude.md)
- [Code Analysis Details](./code-analysis/claude.md)
- [EF Core Analysis Details](./efcore-analysis/claude.md)
- [Main README](./README.md)

---

**When in doubt, ask! I can help you choose the right tool for your task.**
