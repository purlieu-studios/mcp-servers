"""Pytest configuration and shared fixtures for RAG server tests."""
import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator
import pytest
import numpy as np


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_texts() -> list[str]:
    """Sample text documents for testing."""
    return [
        "This is a simple test document about machine learning.",
        "Python is a great programming language for data science.",
        "Vector databases are useful for similarity search.",
        "Natural language processing helps computers understand text.",
        "Machine learning models can be trained on large datasets.",
    ]


@pytest.fixture
def sample_code_python() -> str:
    """Sample Python code for testing."""
    return '''
def calculate_fibonacci(n: int) -> list[int]:
    """Calculate Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib


class Calculator:
    """A simple calculator class."""

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b
'''


@pytest.fixture
def sample_code_javascript() -> str:
    """Sample JavaScript code for testing."""
    return '''
function fetchUserData(userId) {
    return fetch(`/api/users/${userId}`)
        .then(response => response.json())
        .then(data => {
            console.log('User data:', data);
            return data;
        })
        .catch(error => {
            console.error('Error fetching user:', error);
            throw error;
        });
}

class UserManager {
    constructor() {
        this.users = new Map();
    }

    addUser(id, name) {
        this.users.set(id, { id, name });
    }

    getUser(id) {
        return this.users.get(id);
    }
}
'''


@pytest.fixture
def sample_markdown() -> str:
    """Sample Markdown document for testing."""
    return '''# Documentation Guide

## Introduction

This is a comprehensive guide to using the RAG system.

### Features

- Semantic search using embeddings
- Keyword search with BM25
- Hybrid search combining both approaches

### Installation

```bash
pip install -r requirements.txt
```

### Usage

To use the system:

1. Configure your index
2. Add documents
3. Query for results

## Advanced Topics

### Vector Databases

Vector databases store embeddings efficiently and allow fast similarity search.

### Chunking Strategies

Different chunking strategies work better for different document types.
'''


@pytest.fixture
def sample_files(temp_dir: Path) -> dict[str, Path]:
    """Create sample files for testing."""
    files = {}

    # Python file
    py_file = temp_dir / "test.py"
    py_file.write_text('''
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
''')
    files['python'] = py_file

    # JavaScript file
    js_file = temp_dir / "test.js"
    js_file.write_text('''
console.log("Hello, World!");
''')
    files['javascript'] = js_file

    # Markdown file
    md_file = temp_dir / "README.md"
    md_file.write_text('''# Test Project

This is a test project.

## Features

- Feature 1
- Feature 2
''')
    files['markdown'] = md_file

    # Text file
    txt_file = temp_dir / "notes.txt"
    txt_file.write_text('''These are some notes.
Line 2 of notes.
Line 3 of notes.
''')
    files['text'] = txt_file

    return files


@pytest.fixture
def mock_embeddings() -> np.ndarray:
    """Generate mock embeddings for testing."""
    np.random.seed(42)
    return np.random.rand(5, 768).astype('float32')


@pytest.fixture
def normalized_mock_embeddings(mock_embeddings: np.ndarray) -> np.ndarray:
    """Generate normalized mock embeddings for testing."""
    norms = np.linalg.norm(mock_embeddings, axis=1, keepdims=True)
    return (mock_embeddings / norms).astype('float32')
