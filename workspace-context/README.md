# Workspace Context MCP Server

Intelligent context prediction and file recommendations based on workspace state, access patterns, and code dependencies.

## Features

- **Smart Recommendations**: Predict relevant files based on current work context
- **Dependency Analysis**: Map file relationships through imports and references
- **Pattern Detection**: Learn from access patterns to suggest files
- **Context Prediction**: Forecast next files you'll likely need
- **Access Analytics**: Understand usage trends and patterns
- **Context Summary**: High-level overview of workspace state

## Available Tools (6)

### 1. `get_context_recommendations`
Get intelligent file recommendations based on current work.

**Parameters:**
- `limit`: Maximum recommendations (default: 10)
- `include_dependencies`: Include dependency-based recs (default: true)
- `include_patterns`: Include pattern-based recs (default: true)

**Returns**: Ranked list of recommended files with scores and reasons

### 2. `get_related_files`
Find files related to a specific file.

**Parameters:**
- `file_path`: Path to file (required)
- `relationship_type`: Type of relationship
  - `imports`: Files imported by this file
  - `imported_by`: Files that import this file
  - `co_accessed`: Files accessed together
  - `all`: All relationships (default)

**Returns**: List of related files with relationship types

### 3. `get_access_patterns`
Analyze file access patterns and trends.

**Returns**: Statistics including:
- Most accessed files
- Access frequency by time of day
- Average files per session

### 4. `build_dependency_map`
Build dependency map for Python files in workspace.

**Parameters:**
- `root_path`: Root directory to scan (default: current directory)

**Returns**: Map of files to their dependencies

### 5. `predict_next_files`
Predict likely next files to access.

**Parameters:**
- `current_file`: Current file being worked on (optional)
- `limit`: Maximum predictions (default: 5)

**Returns**: Predictions with confidence scores

### 6. `get_context_summary`
Get high-level summary of workspace context.

**Returns**: Overview including:
- Focus file count
- Active task count
- Primary file types
- Server usage statistics
- Current focus areas

## How It Works

### Scoring Algorithm

Recommendations are scored by combining multiple factors:

1. **Recency Score (30% weight)**
   - Recent files scored higher
   - Normalized by access order

2. **Dependency Score (40% weight)**
   - Files imported by focus files
   - Files that import focus files
   - Higher score for direct imports

3. **Pattern Score (30% weight)**
   - Files frequently accessed together
   - Time proximity detection (<1 hour = strong correlation)
   - Frequency-based boosting

### Caching Strategy

- **Dependency Cache**: File import analysis cached per file
- **Pattern Cache**: Access patterns cached for 5 minutes
- **Invalidation**: Cache automatically rebuilt on TTL expiry

### Context Analysis

The analyzer examines:
- Workspace state (focus files, queries, tasks)
- File access timestamps and patterns
- Python import statements (AST parsing)
- Co-access patterns (temporal proximity)
- File type distribution

## Use Cases

### Proactive Context Loading
```
"What files should I look at next?"
→ Returns predictions based on current work
```

### Dependency Navigation
```
"Show me files related to auth.py"
→ Maps imports, reverse deps, co-accessed files
```

### Pattern Discovery
```
"What are my access patterns?"
→ Shows most-used files, time-of-day trends
```

### Smart Context
```
"Give me a context summary"
→ Overview of focus, tasks, file types, activity
```

## Installation

```bash
cd workspace-context
pip install -r requirements.txt
```

## Usage

Add to Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "workspace-context": {
      "command": "python",
      "args": ["-m", "src.workspace_context_server"],
      "cwd": "/path/to/workspace-context"
    }
  }
}
```

## Testing

```bash
pytest tests/ -v --cov=src
```

## Integration

Works with:
- **Workspace State**: Reads focus files, queries, tasks
- **Session Memory**: Enhances recommendations with session history
- **Query History**: Uses past queries for pattern detection

## Performance

- **Recommendations**: <50ms for typical workspace
- **Dependency Map**: <200ms for 100 Python files
- **Pattern Analysis**: <100ms with caching
- **Memory**: ~5MB for typical workspace state

## Examples

### Get Smart Recommendations
```
"Show me recommended files"
→ Returns top 10 files you should look at based on:
  - Recent focus files
  - Related dependencies
  - Co-access patterns
```

### Navigate Dependencies
```
"What files does main.py import?"
→ Shows all import dependencies with resolution
```

### Understand Patterns
```
"When do I work on frontend files?"
→ Access pattern analysis by hour
```

### Predict Next Steps
```
"I'm working on auth.py, what's next?"
→ Predicts files with confidence scores
```

## Algorithm Details

### Co-Access Detection
Files accessed within 1 hour are considered co-accessed:
- Score = 1.0 - (time_diff_seconds / 3600)
- Bidirectional relationship
- Accumulated across multiple sessions

### Import Resolution
Python imports resolved to file paths:
1. Relative to source file directory
2. Relative to workspace root
3. Package `__init__.py` detection

### Frequent File Detection
Files accessed ≥3 times marked as frequent:
- Boosts recommendation confidence
- Used in pattern-based scoring

## Limitations

- **Python-focused**: Dependency mapping works best with Python files
- **Local imports**: Only resolves local project imports, not stdlib/external
- **Pattern learning**: Requires usage history to build patterns
- **File access**: Recommendations based on read access, not modifications

## Future Enhancements

- Multi-language support (JavaScript, TypeScript, etc.)
- Semantic code analysis for better relationships
- Machine learning for prediction improvement
- Integration with git history
- Cross-repository context sharing
