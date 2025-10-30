# Contributing to MCP Servers

Thank you for your interest in contributing! This document provides guidelines and best practices for contributing to this project.

## 📏 Code Size Limits

**⚠️ Important: Pull requests should be ≤500 lines of code (LOC)**

### Why 500 LOC?

- **Easier to review**: Smaller PRs get reviewed faster and more thoroughly
- **Less risky**: Smaller changes are easier to test and less likely to introduce bugs
- **Better for rollbacks**: If issues arise, smaller commits are easier to revert
- **Focus**: Encourages focused, single-purpose changes

### What Counts Towards the Limit?

**Included in count:**
- Source code changes (`.py`, `.js`, `.ts`, `.cs`, etc.)
- Logic and implementation changes

**Excluded from count:**
- Test files (`test_*.py`, `*.test.js`, etc.)
- Documentation files (`.md`, `.txt`, docstrings)
- Configuration files (`config.json`, `pytest.ini`, etc.)
- Auto-generated code
- Package manager files (`requirements.txt`, `package.json`)
- Line deletions

### Checking Your LOC

Before creating a PR, check your line count:

```bash
# Check total changes
git diff --stat origin/main...HEAD

# Check code-only changes (excluding tests/docs)
git diff origin/main...HEAD -- '*.py' ':!tests/' ':!**/test_*.py' | wc -l
```

### What If I Need More Than 500 LOC?

If your change legitimately requires more than 500 LOC:

1. **Split into multiple PRs**: Break your work into logical, incremental PRs
2. **Justify in PR description**: Explain why it can't be split
3. **Get pre-approval**: Discuss with maintainers before submitting large PRs

**Valid reasons for exceeding 500 LOC:**
- New server/module with comprehensive tests (but consider incremental addition)
- Database migration with auto-generated schema
- Third-party library integration requiring boilerplate
- Major refactoring (but try to split into phases)

**Not valid reasons:**
- "It was easier to do it all at once"
- Multiple unrelated features bundled together
- Mixing refactoring with new features

## 🚀 Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/mcp-servers.git
cd mcp-servers
```

### 2. Set Up Development Environment

For each server you're working on:

```bash
# Code Analysis Server
cd code-analysis
pip install -r requirements.txt
pip install -e .

# EF Core Analysis Server
cd efcore-analysis
pip install -r requirements.txt
pip install -e .

# RAG Server
cd rag
pip install -r requirements.txt
pip install -e .
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

## 📝 Development Workflow

### 1. Make Your Changes

- **Keep it focused**: One feature/fix per PR
- **Keep it small**: ≤500 LOC of production code
- **Write tests**: All new code needs tests
- **Update docs**: Keep documentation in sync

### 2. Run Tests

```bash
# Run tests for the server you modified
cd <server-directory>
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src --cov-report=term
```

**Requirements:**
- All tests must pass
- Code coverage must be ≥80% for changed files
- No new warnings or errors

### 3. Check Code Quality

```bash
# Format code (if using black)
black src/ tests/

# Lint code (if using flake8)
flake8 src/ tests/

# Type checking (if using mypy)
mypy src/
```

### 4. Commit Your Changes

**Commit message format:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/updates
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build process, dependencies

**Examples:**

```bash
git commit -m "feat(rag): add semantic search caching

Implemented LRU cache for frequently searched queries to improve
response time by ~40% on repeated searches.

Closes #42"
```

```bash
git commit -m "fix(efcore): handle missing DbContext file

Added FileNotFoundError handling in DbContextAnalyzer to gracefully
handle missing files instead of crashing.

Fixes #123"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub using the PR template.

## 🧪 Testing Guidelines

### Test Requirements

- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Test tool interactions and workflows
- **Coverage**: Maintain ≥80% coverage for changed code

### Test Structure

```python
"""Tests for <module_name>."""

import pytest
from src.module import Function


pytestmark = pytest.mark.unit  # or pytest.mark.integration


class TestFunction:
    """Test Function class."""

    def test_basic_functionality(self):
        """Test basic use case."""
        result = Function().do_thing()
        assert result == expected

    def test_error_handling(self):
        """Test error scenarios."""
        with pytest.raises(ValueError):
            Function().do_invalid_thing()
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_module.py

# Specific test
pytest tests/test_module.py::TestClass::test_method

# With coverage
pytest --cov=src --cov-report=html

# Integration tests only
pytest -m integration

# Unit tests only
pytest -m unit
```

## 📚 Documentation Guidelines

### What to Document

1. **README updates**: If you change functionality or add features
2. **CLAUDE.md guides**: If you modify MCP tools or APIs
3. **Docstrings**: All public functions, classes, methods
4. **Code comments**: Complex logic, non-obvious decisions
5. **Type hints**: All function signatures (Python)

### Docstring Format (Python)

```python
def calculate_complexity(code: str, function_name: Optional[str] = None) -> Dict[str, Any]:
    """Calculate cyclomatic complexity for code.

    Args:
        code: Source code to analyze
        function_name: Specific function to analyze (optional)

    Returns:
        Dictionary with complexity metrics:
        - file_complexity: Overall file complexity
        - function_complexities: Per-function complexity scores
        - high_complexity_functions: List of functions over threshold

    Raises:
        SyntaxError: If code has syntax errors
        ValueError: If function_name not found

    Example:
        >>> result = calculate_complexity("def foo(): pass")
        >>> result['file_complexity']
        1
    """
```

## 🔍 Code Review Process

### What Reviewers Look For

1. **Size**: Is it ≤500 LOC? If not, is it justified?
2. **Tests**: Are there adequate tests? Do they pass?
3. **Coverage**: Is coverage maintained?
4. **Quality**: Is code clean, readable, maintainable?
5. **Documentation**: Are docs updated?
6. **Focus**: Does PR address one thing well?

### Addressing Feedback

- Respond to all comments
- Make requested changes
- Mark conversations as resolved when addressed
- Be open to suggestions

## 🎯 Best Practices

### Code Style

- **Python**: Follow PEP 8
- **JavaScript/TypeScript**: Follow standard.js or project conventions
- **Line length**: ≤100 characters
- **Imports**: Group stdlib, third-party, local
- **Naming**: Descriptive names, avoid abbreviations

### Error Handling

```python
# Good: Specific exceptions with context
try:
    result = parse_code(file_path)
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    raise
except SyntaxError as e:
    logger.error(f"Syntax error in {file_path}: {e}")
    return {"error": "invalid_syntax", "details": str(e)}

# Bad: Bare except
try:
    result = parse_code(file_path)
except:
    return None
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed debugging information")
logger.info("Informational messages")
logger.warning("Warning messages")
logger.error("Error messages")

# Include context
logger.error(f"Failed to parse {file_path}: {error}")
```

### Type Hints

```python
from typing import Optional, List, Dict, Any

def process_items(
    items: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, int]:
    """Process items and return counts."""
    ...
```

## 🤖 AI-Assisted Development

If you used AI tools (like Claude Code, Copilot, etc.) to help with development:

1. **Review all AI-generated code**: Don't blindly accept suggestions
2. **Test thoroughly**: AI can make mistakes
3. **Validate against standards**: Ensure code follows project conventions
4. **Disclose in PR**: Check the "AI-Assisted Development" box in PR template

## 🐛 Reporting Bugs

### Before Reporting

1. Check if it's already reported in [Issues](https://github.com/purlieu-studios/mcp-servers/issues)
2. Verify it's reproducible with latest main branch
3. Check if it's a known limitation

### Bug Report Template

**Title:** Clear, concise description

**Description:**
- What happened?
- What did you expect to happen?
- Steps to reproduce

**Environment:**
- OS: (Windows/Linux/macOS)
- Python version: (3.10/3.11/3.12)
- Server: (code-analysis/efcore-analysis/rag)

**Logs/Screenshots:**
Include relevant error messages or screenshots

## 💡 Feature Requests

### Before Requesting

1. Check [Issues](https://github.com/purlieu-studios/mcp-servers/issues) for existing requests
2. Consider if it fits the project scope
3. Think about backward compatibility

### Feature Request Template

**Title:** Clear feature description

**Problem:**
What problem does this solve?

**Proposed Solution:**
How would this feature work?

**Alternatives:**
What other solutions did you consider?

**Additional Context:**
Any other relevant information

## 📋 Release Process

Releases are handled by maintainers:

1. All PRs merged to `main`
2. Version bump when appropriate
3. Release notes generated
4. Tagged release created
5. CI/CD deploys automatically

## 📞 Getting Help

- **Questions**: Open a [Discussion](https://github.com/purlieu-studios/mcp-servers/discussions)
- **Bugs**: Open an [Issue](https://github.com/purlieu-studios/mcp-servers/issues)
- **Chat**: Join our community (if available)

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing! 🎉**

Questions? Open an issue or discussion!
