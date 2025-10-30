"""Integration tests for Code Analysis MCP Server."""

import asyncio
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def mock_server_context():
    """Mock MCP server context."""
    with patch("src.code_analysis_server.server") as mock_server:
        yield mock_server


class TestCodeAnalysisIntegration:
    """Integration tests for MCP tools."""

    @pytest.mark.asyncio
    async def test_parse_ast_tool_python(self, sample_python_complex):
        """Test parse_ast tool with Python file."""
        from src.code_analysis_server import handle_parse_ast

        result = await handle_parse_ast(
            {"file_path": str(sample_python_complex), "include_body": False}
        )

        assert "file_path" in result
        assert "language" in result
        assert "ast" in result
        assert result["language"] == "python"
        assert result["ast"]["type"] == "Module"

    @pytest.mark.asyncio
    async def test_parse_ast_tool_with_body(self, sample_python_simple):
        """Test parse_ast tool including function bodies."""
        from src.code_analysis_server import handle_parse_ast

        result = await handle_parse_ast(
            {"file_path": str(sample_python_simple), "include_body": True}
        )

        assert result["language"] == "python"
        # With body should have more detailed AST

    @pytest.mark.asyncio
    async def test_parse_ast_nonexistent_file(self):
        """Test parse_ast with nonexistent file."""
        from src.code_analysis_server import handle_parse_ast

        with pytest.raises(FileNotFoundError):
            await handle_parse_ast({"file_path": "/nonexistent/file.py"})

    @pytest.mark.asyncio
    async def test_parse_ast_unsupported_extension(self, temp_dir):
        """Test parse_ast with unsupported file type."""
        from src.code_analysis_server import handle_parse_ast

        unsupported = temp_dir / "file.xyz"
        unsupported.write_text("some content")

        with pytest.raises(ValueError, match="No analyzer available"):
            await handle_parse_ast({"file_path": str(unsupported)})

    @pytest.mark.asyncio
    async def test_analyze_complexity_tool(self, sample_python_complex):
        """Test analyze_complexity tool."""
        from src.code_analysis_server import handle_analyze_complexity

        result = await handle_analyze_complexity({"file_path": str(sample_python_complex)})

        assert "file_path" in result
        assert "complexity" in result
        assert "function_complexities" in result["complexity"]
        assert "high_complexity_functions" in result["complexity"]

        # Should identify complex_function or have complexity data
        func_complexities = result["complexity"]["function_complexities"]
        assert "complex_function" in func_complexities
        assert func_complexities["complex_function"] >= 9

    @pytest.mark.asyncio
    async def test_analyze_complexity_specific_function(self, sample_python_complex):
        """Test analyze_complexity for specific function."""
        from src.code_analysis_server import handle_analyze_complexity

        result = await handle_analyze_complexity(
            {"file_path": str(sample_python_complex), "function_name": "complex_function"}
        )

        assert "complexity" in result
        complexities = result["complexity"]["function_complexities"]
        assert "complex_function" in complexities

    @pytest.mark.asyncio
    async def test_find_code_smells_tool(self, sample_python_code_smells):
        """Test find_code_smells tool."""
        from src.code_analysis_server import handle_find_code_smells

        result = await handle_find_code_smells(
            {"file_path": str(sample_python_code_smells), "severity": "all"}
        )

        assert "file_path" in result
        assert "code_smells" in result
        assert "total_issues" in result

        # Should find multiple issues
        assert result["total_issues"] >= 3

        # Should have various smell types
        smell_types = {smell["type"] for smell in result["code_smells"]}
        assert "too_many_parameters" in smell_types
        assert "god_class" in smell_types

    @pytest.mark.asyncio
    async def test_find_code_smells_severity_filter(self, sample_python_code_smells):
        """Test find_code_smells with severity filtering."""
        from src.code_analysis_server import handle_find_code_smells

        result = await handle_find_code_smells(
            {"file_path": str(sample_python_code_smells), "severity": "high"}
        )

        # Should only have high severity issues
        for smell in result["code_smells"]:
            assert smell["severity"] == "high"

    @pytest.mark.asyncio
    async def test_analyze_functions_tool(self, sample_python_complex):
        """Test analyze_functions tool."""
        from src.code_analysis_server import handle_analyze_functions

        result = await handle_analyze_functions({"file_path": str(sample_python_complex)})

        assert "file_path" in result
        assert "functions" in result
        assert "function_count" in result

        # Should extract multiple functions
        assert result["function_count"] >= 2

        # Should have some functions extracted
        functions = result["functions"]
        assert len(functions) >= 2

    @pytest.mark.asyncio
    async def test_analyze_classes_tool(self, sample_python_complex):
        """Test analyze_classes tool."""
        from src.code_analysis_server import handle_analyze_classes

        result = await handle_analyze_classes({"file_path": str(sample_python_complex)})

        assert "file_path" in result
        assert "classes" in result
        assert "class_count" in result

        # Should extract classes
        assert result["class_count"] >= 2

        # Should have User and UserService classes
        class_names = [c["name"] for c in result["classes"]]
        assert "User" in class_names
        assert "UserService" in class_names

    @pytest.mark.asyncio
    async def test_find_dependencies_tool_single_file(self, sample_python_imports):
        """Test find_dependencies tool for single file."""
        from src.code_analysis_server import handle_find_dependencies

        result = await handle_find_dependencies(
            {"file_path": str(sample_python_imports), "recursive": False}
        )

        assert "path" in result
        assert "dependencies" in result

        deps = result["dependencies"]
        assert "imports" in deps
        assert "external_packages" in deps
        assert "local_imports" in deps

    @pytest.mark.asyncio
    async def test_find_dependencies_tool_recursive(self, sample_project_structure):
        """Test find_dependencies tool recursively."""
        from src.code_analysis_server import handle_find_dependencies

        result = await handle_find_dependencies(
            {"file_path": str(sample_project_structure), "recursive": True}
        )

        assert "path" in result
        assert "dependencies" in result

        # Should analyze multiple files
        deps = result["dependencies"]
        assert "total_files" in deps
        assert deps["total_files"] >= 3

    @pytest.mark.asyncio
    async def test_end_to_end_code_quality_check(self, sample_python_complex):
        """E2E test: Complete code quality analysis."""
        from src.code_analysis_server import (
            handle_analyze_complexity,
            handle_analyze_functions,
            handle_find_code_smells,
        )

        # Step 1: Analyze complexity
        complexity_result = await handle_analyze_complexity(
            {"file_path": str(sample_python_complex)}
        )

        # Verify we got complexity data
        func_complexities = complexity_result["complexity"]["function_complexities"]
        assert len(func_complexities) > 0

        # Find high complexity function
        high_complexity_funcs = [name for name, comp in func_complexities.items() if comp >= 9]
        assert len(high_complexity_funcs) > 0

        # Step 2: Find code smells
        smells_result = await handle_find_code_smells(
            {
                "file_path": str(sample_python_complex),
                "severity": "low",  # Use "low" to capture more issues
            }
        )

        # Verify we got a result (may or may not have issues depending on detection)
        assert "total_issues" in smells_result
        assert "code_smells" in smells_result

        # Step 3: Analyze functions to get details
        functions_result = await handle_analyze_functions({"file_path": str(sample_python_complex)})

        # Find the problematic function
        complex_func = next(
            (f for f in functions_result["functions"] if f["name"] in high_complexity_funcs), None
        )
        assert complex_func is not None

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, sample_python_complex, sample_python_simple):
        """Test running multiple tools concurrently."""
        from src.code_analysis_server import (
            handle_analyze_complexity,
            handle_analyze_functions,
            handle_find_code_smells,
        )

        # Run tools concurrently
        tasks = [
            handle_analyze_complexity({"file_path": str(sample_python_complex)}),
            handle_find_code_smells({"file_path": str(sample_python_complex), "severity": "all"}),
            handle_analyze_functions({"file_path": str(sample_python_simple)}),
        ]

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_javascript_file_analysis(self, sample_javascript):
        """E2E test: Analyze JavaScript file."""
        from src.code_analysis_server import handle_analyze_functions, handle_parse_ast

        # Parse AST (simplified for JavaScript)
        ast_result = await handle_parse_ast(
            {"file_path": str(sample_javascript), "include_body": False}
        )

        assert ast_result["language"] == "javascript"
        assert "functions" in ast_result["ast"]

        # Analyze functions
        funcs_result = await handle_analyze_functions({"file_path": str(sample_javascript)})

        assert funcs_result["function_count"] >= 3
        func_names = [f["name"] for f in funcs_result["functions"]]
        assert "calculateTotal" in func_names or "fetchUserData" in func_names

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_csharp_file_analysis(self, sample_csharp):
        """E2E test: Analyze C# file."""
        from src.code_analysis_server import handle_analyze_classes, handle_analyze_functions

        # Analyze functions
        funcs_result = await handle_analyze_functions({"file_path": str(sample_csharp)})

        assert funcs_result["function_count"] >= 2

        # Analyze classes
        classes_result = await handle_analyze_classes({"file_path": str(sample_csharp)})

        assert classes_result["class_count"] >= 2
        class_names = [c["name"] for c in classes_result["classes"]]
        assert "User" in class_names or "UserService" in class_names
