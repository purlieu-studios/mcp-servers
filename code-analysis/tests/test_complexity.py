"""Tests for complexity analysis."""
import pytest
from pathlib import Path
from src.complexity import calculate_complexity
from src.analyzers.python_analyzer import PythonAnalyzer


pytestmark = pytest.mark.unit


class TestComplexityAnalysis:
    """Test complexity calculation."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return PythonAnalyzer()

    @pytest.mark.asyncio
    async def test_calculate_complexity_simple_file(self, analyzer, sample_python_simple):
        """Test complexity calculation for simple functions."""
        result = await calculate_complexity(sample_python_simple, analyzer)

        assert "file_complexity" in result
        assert "function_complexities" in result
        assert "high_complexity_functions" in result

        # Simple file should have low complexity
        assert result["file_complexity"] < 5

        # Should have complexities for both functions
        assert "greet" in result["function_complexities"]
        assert "add" in result["function_complexities"]

        # No functions should be high complexity
        assert len(result["high_complexity_functions"]) == 0

    @pytest.mark.asyncio
    async def test_calculate_complexity_complex_file(self, analyzer, sample_python_complex):
        """Test complexity calculation for complex functions."""
        result = await calculate_complexity(sample_python_complex, analyzer)

        assert "file_complexity" in result
        assert result["file_complexity"] >= 3  # Should be moderately complex

        # Should identify complex_function as high complexity
        assert "complex_function" in result["function_complexities"]
        assert result["function_complexities"]["complex_function"] >= 9

        # Verify high complexity detection (threshold may vary)
        assert "high_complexity_functions" in result

    @pytest.mark.asyncio
    async def test_calculate_complexity_specific_function(self, analyzer, sample_python_complex):
        """Test complexity calculation for a specific function."""
        result = await calculate_complexity(
            sample_python_complex,
            analyzer,
            function_name="complex_function"
        )

        assert "function_complexities" in result
        assert "complex_function" in result["function_complexities"]

    @pytest.mark.asyncio
    async def test_empty_file_complexity(self, analyzer, temp_dir):
        """Test complexity of empty file."""
        empty_file = temp_dir / "empty.py"
        empty_file.write_text("")

        result = await calculate_complexity(empty_file, analyzer)

        assert result["file_complexity"] == 0
        assert result["function_complexities"] == {}
        assert result["high_complexity_functions"] == []

    @pytest.mark.asyncio
    async def test_complexity_with_loops_and_conditionals(self, analyzer, temp_dir):
        """Test complexity calculation with loops and conditionals."""
        file_path = temp_dir / "loops.py"
        file_path.write_text('''
def process_items(items):
    """Process items with loops and conditionals."""
    result = []

    for item in items:
        if item.is_valid:
            if item.priority > 5:
                result.append(item.process())
            elif item.priority > 0:
                result.append(item.defer())
        else:
            continue

    while len(result) > 100:
        result.pop(0)

    return result
''')

        result = await calculate_complexity(file_path, analyzer)

        assert "process_items" in result["function_complexities"]
        # Should have moderate complexity due to nested conditions and loops
        assert result["function_complexities"]["process_items"] >= 5
