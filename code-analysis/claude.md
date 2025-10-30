# Code Analysis Server - Claude Guide

Comprehensive code analysis with AST parsing, complexity metrics, and code quality detection for Python, JavaScript/TypeScript, and C#.

## 🎯 What This Server Does

Analyzes your code to provide:
- **AST Structure**: Detailed abstract syntax tree parsing (Python)
- **Complexity Metrics**: Cyclomatic and cognitive complexity
- **Code Smells**: Quality issues and anti-patterns
- **Function Analysis**: Signatures, parameters, and types
- **Class Analysis**: Structure, methods, and inheritance
- **Dependency Mapping**: Import and module relationships

## 🔧 Available Tools (6)

### 1. `parse_ast` - Get AST Structure

Parse code files and return detailed AST representation.

**Best For:** Python files (full AST support)
**Also Works:** JavaScript/TypeScript, C# (simplified parsing)

**Parameters:**
```json
{
  "file_path": "/path/to/file.py",
  "include_body": false                      // Include function bodies in AST
}
```

**Returns:**
```json
{
  "file_path": "/path/to/file.py",
  "language": "python",
  "ast": {
    "type": "Module",
    "body": [
      {
        "type": "FunctionDef",
        "name": "calculate_total",
        "line": 5,
        "parameters": [
          {"name": "items", "type": "list[Item]", "default": null},
          {"name": "discount", "type": "float", "default": "0.0"}
        ],
        "return_type": "float",
        "decorators": [],
        "is_async": false
      },
      {
        "type": "ClassDef",
        "name": "ShoppingCart",
        "line": 15,
        "bases": ["BaseCart"],
        "decorators": []
      }
    ]
  }
}
```

**Example Usage:**
```
"Parse calculator.py and show me the AST structure"
"What's the structure of my auth module?"
"Show me all the classes and functions in this file"
```

**Tips:**
- Use `include_body: false` for high-level structure
- Use `include_body: true` to see implementation details
- Works best with Python for full type annotation support

---

### 2. `analyze_complexity` - Calculate Complexity

Calculate cyclomatic and cognitive complexity metrics.

**Parameters:**
```json
{
  "file_path": "/path/to/file.py",
  "function_name": "process_order"          // Optional: specific function
}
```

**Returns:**
```json
{
  "file_path": "/path/to/file.py",
  "complexity": {
    "file_complexity": 8.5,
    "function_complexities": {
      "process_order": 15,
      "validate_items": 6,
      "calculate_total": 3
    },
    "high_complexity_functions": ["process_order"]
  }
}
```

**Example Usage:**
```
"What's the complexity of the authenticate_user function?"
"Analyze complexity in user_service.py"
"Which functions in this file are too complex?"
```

**Complexity Guidelines:**
- **1-5**: Simple, easy to test
- **6-10**: Moderate, acceptable
- **11-20**: Complex, consider refactoring
- **21+**: Very complex, should refactor

---

### 3. `find_code_smells` - Detect Quality Issues

Detect code smells and anti-patterns.

**Parameters:**
```json
{
  "file_path": "/path/to/file.py",
  "severity": "medium"                       // low, medium, high, or all
}
```

**Returns:**
```json
{
  "file_path": "/path/to/file.py",
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
    },
    {
      "type": "missing_docstring",
      "severity": "low",
      "function": "helper_function",
      "line": 102,
      "message": "Function is missing docstring",
      "suggestion": "Add a docstring to explain the function's purpose"
    }
  ],
  "total_issues": 3
}
```

**Detected Code Smells:**
- **Too Many Parameters**: Functions with > 5 parameters
- **God Class**: Classes with > 20 methods
- **Missing Docstrings**: Functions without documentation (Python)
- **High Complexity**: Functions with cyclomatic complexity > 10

**Example Usage:**
```
"Find code smells in UserService.py"
"Check for quality issues in my auth module"
"What needs to be refactored in this file?"
```

**Severity Levels:**
- **Low**: Minor issues, nice to fix
- **Medium**: Should address soon
- **High**: Important to fix

---

### 4. `analyze_functions` - Extract Functions

Extract all functions with complete signatures, parameters, and types.

**Parameters:**
```json
{
  "file_path": "/path/to/file.py"
}
```

**Returns:**
```json
{
  "file_path": "/path/to/file.py",
  "functions": [
    {
      "name": "calculate_discount",
      "line": 15,
      "async": false,
      "parameters": [
        {"name": "price", "type": "float", "default": null},
        {"name": "percent", "type": "int", "default": "10"}
      ],
      "return_type": "float",
      "decorators": ["cached_property"],
      "docstring": "Calculate discount based on price and percentage.",
      "is_method": false
    },
    {
      "name": "__init__",
      "line": 25,
      "async": false,
      "parameters": [
        {"name": "self", "type": null, "default": null},
        {"name": "name", "type": "str", "default": null}
      ],
      "return_type": null,
      "decorators": [],
      "docstring": null,
      "is_method": true
    }
  ],
  "function_count": 12
}
```

**Example Usage:**
```
"List all functions in calculator.py"
"What are the function signatures in auth.py?"
"Show me all async functions in this file"
```

**Use Cases:**
- Understanding API surface
- Documenting function signatures
- Finding functions with specific patterns
- Reviewing parameter types

---

### 5. `analyze_classes` - Extract Classes

Analyze class definitions, methods, properties, and inheritance.

**Parameters:**
```json
{
  "file_path": "/path/to/file.py"
}
```

**Returns:**
```json
{
  "file_path": "/path/to/file.py",
  "classes": [
    {
      "name": "ShoppingCart",
      "line": 10,
      "bases": ["BaseCart", "Serializable"],
      "decorators": ["dataclass"],
      "docstring": "Represents a user's shopping cart.",
      "methods": [
        {
          "name": "add_item",
          "line": 20,
          "is_static": false,
          "is_class_method": false,
          "is_property": false,
          "parameters": [
            {"name": "self", "type": null, "default": null},
            {"name": "item", "type": "Item", "default": null}
          ],
          "return_type": "None"
        }
      ],
      "properties": [
        {
          "name": "total",
          "line": 45,
          "is_property": true,
          "return_type": "float"
        }
      ]
    }
  ],
  "class_count": 1
}
```

**Example Usage:**
```
"Show me all classes in models.py"
"What methods does the User class have?"
"Analyze the class hierarchy in this file"
```

**Use Cases:**
- Understanding class structure
- Reviewing inheritance patterns
- Finding properties vs methods
- Documenting class APIs

---

### 6. `find_dependencies` - Map Dependencies

Map import statements and file dependencies.

**Parameters:**
```json
{
  "file_path": "/path/to/file.py",
  "recursive": true                          // Analyze entire directory
}
```

**Returns:**
```json
{
  "path": "/path/to/project",
  "dependencies": {
    "file": "/path/to/project/auth.py",
    "imports": [
      "flask",
      "sqlalchemy",
      "bcrypt",
      "./models",
      "./database"
    ],
    "external_packages": [
      "flask",
      "sqlalchemy",
      "bcrypt"
    ],
    "local_imports": [
      "./models",
      "./database"
    ]
  }
}
```

**Example Usage:**
```
"What dependencies does auth.py have?"
"Map all imports in my project"
"Which external packages does this module use?"
```

**Use Cases:**
- Understanding module dependencies
- Finding circular imports
- Auditing external dependencies
- Planning refactoring

---

## 🎯 Supported Languages

### Python (Full Support)
- ✅ Complete AST parsing with `ast` module
- ✅ Type annotations
- ✅ Decorators
- ✅ Async functions
- ✅ Docstrings
- ✅ Complexity calculation

### JavaScript/TypeScript (Regex-based)
- ✅ Function extraction
- ✅ Class extraction
- ✅ Import statements
- ⚠️ Limited to regex patterns (no full AST)

### C# (Regex-based)
- ✅ Method extraction
- ✅ Class extraction
- ✅ Property detection
- ✅ Using statements
- ⚠️ Limited to regex patterns (no full AST)

---

## 💡 Common Workflows

### Code Review Workflow
```
1. "Find code smells in UserService.py"
   → Identifies quality issues

2. "What's the complexity of the problematic functions?"
   → Measures complexity metrics

3. "Show me the function signatures"
   → Reviews parameters and types
```

### Refactoring Workflow
```
1. "Analyze complexity in payment_processor.py"
   → Finds complex functions

2. "Parse AST to see the structure"
   → Understands current organization

3. "Show me all dependencies"
   → Plans impact of changes
```

### Documentation Workflow
```
1. "List all public functions in api.py"
   → Gets API surface

2. "Analyze classes in models.py"
   → Documents class structure

3. "Find functions missing docstrings"
   → Identifies documentation gaps
```

---

## 🎓 Best Practices

### When to Use Each Tool

**`parse_ast`**
- Need detailed code structure
- Understanding complex logic
- Preparing for major refactoring

**`analyze_complexity`**
- Code review
- Identifying refactoring candidates
- Setting quality gates

**`find_code_smells`**
- Quick quality check
- Pre-commit reviews
- Learning code quality patterns

**`analyze_functions`**
- API documentation
- Understanding public interfaces
- Finding specific patterns

**`analyze_classes`**
- OOP design review
- Inheritance analysis
- Class responsibility evaluation

**`find_dependencies`**
- Module decoupling
- Dependency audits
- Circular import detection

---

## 📊 Interpreting Results

### Complexity Scores
```
1-5:   ✅ Excellent - simple and maintainable
6-10:  👍 Good - acceptable complexity
11-15: ⚠️  Warning - consider refactoring
16-20: 🔴 High - should refactor
21+:   💀 Critical - must refactor
```

### Code Smell Severity
```
Low:    💡 Nice to fix, improves quality
Medium: ⚠️  Should address, affects maintainability
High:   🔴 Important to fix, impacts reliability
```

### Function Parameter Count
```
0-3:  ✅ Ideal
4-5:  👍 Acceptable
6-7:  ⚠️  Too many, use parameter object
8+:   🔴 Way too many, definitely refactor
```

---

## 🐛 Troubleshooting

### "No analyzer available for this file type"
- Check file extension (.py, .js, .ts, .cs)
- Verify file is supported language

### "Syntax error in parsing"
- File has syntax errors
- Try fixing code syntax first
- Check for encoding issues

### Python analysis very detailed, others not
- Python uses full AST parsing
- JS/TS/C# use regex-based extraction
- For better JS/TS analysis, consider using Roslyn or Babel in future

---

## 🔗 Related Resources

- [README](./README.md) - Full documentation
- [Main MCP Guide](../claude.md) - All servers

---

**Need help choosing the right analysis?**
- Simple overview → `analyze_functions` or `analyze_classes`
- Quality check → `find_code_smells`
- Deep dive → `parse_ast`
- Metrics → `analyze_complexity`
- Relationships → `find_dependencies`
