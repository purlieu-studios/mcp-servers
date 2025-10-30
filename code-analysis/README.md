# Code Analysis MCP Server

A Model Context Protocol (MCP) server that provides comprehensive code analysis capabilities including AST parsing, complexity metrics, and code quality analysis.

## Features

### Supported Languages
- **Python**: Full AST parsing with type annotations
- **JavaScript/TypeScript**: Function and class extraction
- **C#**: Method and class analysis

### Available Tools

#### 1. **parse_ast**
Parse code files and return detailed AST representation.

```json
{
  "file_path": "/path/to/file.py",
  "include_body": false
}
```

#### 2. **analyze_complexity**
Calculate cyclomatic and cognitive complexity metrics.

```json
{
  "file_path": "/path/to/file.py",
  "function_name": "my_function"  // optional
}
```

#### 3. **find_code_smells**
Detect code quality issues and anti-patterns.

```json
{
  "file_path": "/path/to/file.py",
  "severity": "medium"  // low, medium, high, or all
}
```

Detects:
- Too many parameters
- Missing docstrings
- God classes (too many methods)
- High complexity functions

#### 4. **analyze_functions**
Extract all functions with signatures, parameters, and type annotations.

```json
{
  "file_path": "/path/to/file.py"
}
```

#### 5. **analyze_classes**
Analyze class definitions, methods, properties, and inheritance.

```json
{
  "file_path": "/path/to/file.py"
}
```

#### 6. **find_dependencies**
Map import statements and file dependencies.

```json
{
  "file_path": "/path/to/file.py",
  "recursive": true  // analyze entire directory
}
```

#### 7. **get_cache_stats**
Get analysis cache performance statistics.

```json
{}
```

Returns cache hit rate, number of entries, and disk usage.

#### 8. **clear_cache**
Clear cached analysis results.

```json
{
  "older_than_days": 30  // optional: only clear old entries
}
```

### Performance Features

**Smart Caching System:**
- Automatic hash-based result caching
- ~70% reduction in repeated analysis time
- Cache automatically invalidates when files change
- Persists across sessions in `~/.code-analysis-cache/`
- All cached results include `_cached` flag

**Cache Coverage:**
- ✅ AST parsing
- ✅ Complexity analysis
- ✅ Code smell detection
- ✅ Function analysis
- ✅ Class analysis

## Installation

```bash
cd code-analysis
pip install -r requirements.txt
```

## Usage

### With Claude Code

Add to your Claude Code MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "code-analysis": {
      "command": "python",
      "args": ["-m", "src.code_analysis_server"],
      "cwd": "/path/to/code-analysis"
    }
  }
}
```

### Standalone

```bash
python -m src.code_analysis_server
```

## Examples

### Analyze Python Function Complexity

```python
# Query: "Analyze the complexity of authenticate_user function in auth.py"

# Server returns:
{
  "file_path": "/project/auth.py",
  "complexity": {
    "authenticate_user": 12,
    "high_complexity_functions": ["authenticate_user"],
    "file_complexity": 8.5
  }
}
```

### Find Code Smells

```python
# Query: "Find code quality issues in user_service.py"

# Server returns:
{
  "file_path": "/project/user_service.py",
  "code_smells": [
    {
      "type": "too_many_parameters",
      "severity": "medium",
      "function": "create_user",
      "line": 45,
      "message": "Function has 7 parameters (recommended: ≤5)",
      "suggestion": "Consider using a parameter object or builder pattern"
    },
    {
      "type": "god_class",
      "severity": "high",
      "class": "UserService",
      "line": 10,
      "message": "Class has 25 methods (recommended: ≤20)",
      "suggestion": "Consider splitting into smaller, focused classes"
    }
  ],
  "total_issues": 2
}
```

### Extract Function Information

```python
# Query: "List all functions in calculator.py with their parameters"

# Server returns:
{
  "file_path": "/project/calculator.py",
  "functions": [
    {
      "name": "add",
      "line": 5,
      "parameters": [
        {"name": "a", "type": "int", "default": null},
        {"name": "b", "type": "int", "default": null}
      ],
      "return_type": "int",
      "docstring": "Add two numbers together.",
      "is_method": false
    }
  ],
  "function_count": 8
}
```

## Architecture

```
code-analysis/
├── src/
│   ├── code_analysis_server.py   # Main MCP server
│   ├── analyzers/
│   │   ├── python_analyzer.py    # Python AST parsing
│   │   ├── javascript_analyzer.py # JS/TS analysis
│   │   └── csharp_analyzer.py    # C# analysis
│   ├── complexity.py              # Complexity metrics
│   ├── code_smells.py             # Code smell detection
│   └── dependency_analyzer.py     # Dependency mapping
├── requirements.txt
└── README.md
```

## Future Enhancements

- [ ] Add more language support (Java, Go, Rust)
- [ ] Implement proper JavaScript/TypeScript AST parsing (using esprima/babel)
- [ ] Add code duplication detection
- [ ] Implement test coverage analysis integration
- [ ] Add configurable complexity thresholds
- [ ] Support for custom code smell rules

## License

MIT
