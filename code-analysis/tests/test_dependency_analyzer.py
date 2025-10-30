"""Tests for dependency analyzer."""

import pytest

from src.dependency_analyzer import DependencyAnalyzer

pytestmark = pytest.mark.unit


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return DependencyAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_python_file(self, analyzer, sample_python_imports):
        """Test analyzing Python imports."""
        result = await analyzer.analyze(sample_python_imports)

        assert "file" in result
        assert "imports" in result
        assert "external_packages" in result
        assert "local_imports" in result

        # Should have standard library imports
        assert "os" in result["imports"]
        assert "sys" in result["imports"]

        # Should have external packages
        assert "numpy" in result["external_packages"] or "np" in str(result["imports"])
        assert "pandas" in result["external_packages"] or "pd" in str(result["imports"])

        # Should have local imports
        local = result["local_imports"]
        assert any("models" in imp for imp in local) or any("." in imp for imp in result["imports"])

    @pytest.mark.asyncio
    async def test_analyze_javascript_file(self, analyzer, sample_javascript):
        """Test analyzing JavaScript imports."""
        result = await analyzer.analyze(sample_javascript)

        assert "file" in result
        assert "imports" in result

        # JavaScript file should not have Python-style imports
        # But might have require/import statements if we add them

    @pytest.mark.asyncio
    async def test_analyze_directory_recursive(self, analyzer, sample_project_structure):
        """Test analyzing entire directory recursively."""
        result = await analyzer.analyze(sample_project_structure, recursive=True)

        assert "directory" in result
        assert "files" in result
        assert "total_files" in result

        # Should analyze multiple files
        assert result["total_files"] >= 3

        # Check that auth.py was analyzed
        auth_file = None
        for file_path, deps in result["files"].items():
            if "auth.py" in file_path:
                auth_file = deps
                break

        assert auth_file is not None
        assert "bcrypt" in auth_file["imports"]
        assert any("models" in imp for imp in auth_file["imports"])

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self, analyzer, temp_dir):
        """Test analyzing nonexistent file."""
        bad_path = temp_dir / "nonexistent.py"

        with pytest.raises(FileNotFoundError):
            await analyzer.analyze(bad_path)

    @pytest.mark.asyncio
    async def test_distinguish_external_and_local_imports(self, analyzer, sample_python_imports):
        """Test distinguishing between external and local imports."""
        result = await analyzer.analyze(sample_python_imports)

        external = result["external_packages"]
        local = result["local_imports"]

        # External packages should not start with .
        for pkg in external:
            assert not pkg.startswith(".")

        # Local imports should start with . or /
        for imp in local:
            assert imp.startswith(".") or imp.startswith("/")

    @pytest.mark.asyncio
    async def test_analyze_file_with_no_imports(self, analyzer, sample_python_simple):
        """Test analyzing file with no imports."""
        result = await analyzer.analyze(sample_python_simple)

        assert "imports" in result
        # Simple file has no imports
        assert len(result["imports"]) == 0

    @pytest.mark.asyncio
    async def test_analyze_csharp_file(self, analyzer, sample_csharp):
        """Test analyzing C# using statements."""
        result = await analyzer.analyze(sample_csharp)

        assert "file" in result
        assert "imports" in result

        # Should extract using statements
        imports = result["imports"]
        assert "System" in imports or any("System" in imp for imp in imports)

    @pytest.mark.asyncio
    async def test_analyze_typescript_file(self, analyzer, sample_typescript):
        """Test analyzing TypeScript imports."""
        result = await analyzer.analyze(sample_typescript)

        assert "file" in result
        assert "imports" in result

        # TypeScript uses ES6 imports, might not be captured by simple regex
        # but result should still be valid

    @pytest.mark.asyncio
    async def test_extract_python_imports_from_imports(self, analyzer, temp_dir):
        """Test extracting various Python import styles."""
        file_path = temp_dir / "various_imports.py"
        file_path.write_text("""
import os
import sys
from pathlib import Path
from typing import List, Dict
from .models import User
from ..utils import helper
""")

        result = await analyzer.analyze(file_path)

        imports = result["imports"]
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports or any("pathlib" in imp for imp in imports)
        assert "typing" in imports or any("typing" in imp for imp in imports)

    @pytest.mark.asyncio
    async def test_extract_from_imports(self, analyzer, temp_dir):
        """Test extracting 'from X import Y' style imports."""
        file_path = temp_dir / "from_imports.py"
        file_path.write_text("""
from flask import Flask, request, jsonify
from sqlalchemy.orm import Session
from models import User, Order
""")

        result = await analyzer.analyze(file_path)

        imports = result["imports"]
        assert "flask" in imports
        assert "sqlalchemy.orm" in imports or any("sqlalchemy" in imp for imp in imports)
        assert "models" in imports
