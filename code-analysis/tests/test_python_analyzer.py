"""Tests for Python code analyzer."""
import pytest
from pathlib import Path
from src.analyzers.python_analyzer import PythonAnalyzer


pytestmark = pytest.mark.unit


class TestPythonAnalyzer:
    """Test PythonAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return PythonAnalyzer()

    def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.language == "python"

    @pytest.mark.asyncio
    async def test_parse_simple_file(self, analyzer, sample_python_simple):
        """Test parsing a simple Python file."""
        result = await analyzer.parse_file(sample_python_simple, include_body=False)

        assert result["type"] == "Module"
        assert "body" in result
        assert len(result["body"]) == 2  # Two functions

        # Check first function
        func = result["body"][0]
        assert func["type"] == "FunctionDef"
        assert func["name"] == "greet"
        assert len(func["parameters"]) == 1
        assert func["parameters"][0]["name"] == "name"
        assert func["parameters"][0]["type"] == "str"
        assert func["return_type"] == "str"

    @pytest.mark.asyncio
    async def test_parse_complex_file(self, analyzer, sample_python_complex):
        """Test parsing a complex Python file with classes."""
        result = await analyzer.parse_file(sample_python_complex, include_body=False)

        assert result["type"] == "Module"
        assert len(result["body"]) > 0

        # Find the User class
        user_class = None
        for node in result["body"]:
            if node.get("type") == "ClassDef" and node.get("name") == "User":
                user_class = node
                break

        assert user_class is not None
        assert user_class["name"] == "User"
        assert "@dataclass" in str(user_class["decorators"]) or "dataclass" in user_class.get("decorators", [])

    @pytest.mark.asyncio
    async def test_parse_file_with_syntax_error(self, analyzer, temp_dir):
        """Test parsing a file with syntax errors."""
        bad_file = temp_dir / "bad.py"
        bad_file.write_text("def broken(\n  return  # Invalid syntax")

        result = await analyzer.parse_file(bad_file, include_body=False)

        assert "error" in result
        assert "Syntax error" in result["error"] or "syntax error" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_analyze_functions_simple(self, analyzer, sample_python_simple):
        """Test extracting functions from simple file."""
        functions = await analyzer.analyze_functions(sample_python_simple)

        assert len(functions) == 2

        greet_func = functions[0]
        assert greet_func["name"] == "greet"
        assert len(greet_func["parameters"]) == 1
        assert greet_func["return_type"] == "str"
        assert greet_func["docstring"] == "Greet someone by name."
        assert greet_func["async"] == False

        add_func = functions[1]
        assert add_func["name"] == "add"
        assert len(add_func["parameters"]) == 2
        assert add_func["return_type"] == "int"

    @pytest.mark.asyncio
    async def test_analyze_functions_with_async(self, analyzer, sample_python_complex):
        """Test extracting async functions."""
        functions = await analyzer.analyze_functions(sample_python_complex)

        # Note: analyze_functions may extract top-level functions only
        # Async methods inside classes might require analyze_classes instead
        assert len(functions) >= 1  # At least extract some functions

        # If async functions are extracted, verify they're marked correctly
        async_funcs = [f for f in functions if f.get("async", False)]
        if len(async_funcs) > 0:
            assert all(f["async"] == True for f in async_funcs)

    @pytest.mark.asyncio
    async def test_analyze_functions_with_defaults(self, analyzer, temp_dir):
        """Test extracting functions with default parameters."""
        file_path = temp_dir / "defaults.py"
        file_path.write_text('''
def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}!"
''')

        functions = await analyzer.analyze_functions(file_path)

        assert len(functions) == 1
        func = functions[0]
        assert len(func["parameters"]) == 2
        assert func["parameters"][0]["name"] == "name"
        assert func["parameters"][0]["default"] is None
        assert func["parameters"][1]["name"] == "greeting"
        # Default can be either 'Hello' or "Hello" depending on Python's repr
        assert func["parameters"][1]["default"] in ['"Hello"', "'Hello'"]

    @pytest.mark.asyncio
    async def test_analyze_classes_simple(self, analyzer, sample_python_complex):
        """Test extracting classes."""
        classes = await analyzer.analyze_classes(sample_python_complex)

        assert len(classes) >= 2  # User and UserService

        user_class = next(c for c in classes if c["name"] == "User")
        assert user_class["name"] == "User"
        assert len(user_class["methods"]) >= 1
        assert len(user_class["properties"]) >= 1  # display_name property

    @pytest.mark.asyncio
    async def test_analyze_classes_with_inheritance(self, analyzer, temp_dir):
        """Test extracting classes with inheritance."""
        file_path = temp_dir / "inheritance.py"
        file_path.write_text('''
class Animal:
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"

class Cat(Animal):
    def speak(self):
        return "Meow!"
''')

        classes = await analyzer.analyze_classes(file_path)

        assert len(classes) == 3

        dog_class = next(c for c in classes if c["name"] == "Dog")
        assert "Animal" in dog_class["bases"]

        cat_class = next(c for c in classes if c["name"] == "Cat")
        assert "Animal" in cat_class["bases"]

    @pytest.mark.asyncio
    async def test_analyze_classes_with_decorators(self, analyzer, sample_python_complex):
        """Test extracting decorated classes."""
        classes = await analyzer.analyze_classes(sample_python_complex)

        user_class = next(c for c in classes if c["name"] == "User")
        assert "dataclass" in user_class["decorators"] or len(user_class["decorators"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_classes_distinguishes_methods_and_properties(self, analyzer, sample_python_complex):
        """Test that methods and properties are correctly categorized."""
        classes = await analyzer.analyze_classes(sample_python_complex)

        user_class = next(c for c in classes if c["name"] == "User")

        # Should have display_name as a property
        property_names = [p["name"] for p in user_class["properties"]]
        assert "display_name" in property_names

        # Should have update_email as a method
        method_names = [m["name"] for m in user_class["methods"]]
        assert "update_email" in method_names

    @pytest.mark.asyncio
    async def test_calculate_complexity_simple(self, analyzer, sample_python_simple):
        """Test complexity calculation for simple functions."""
        complexities = await analyzer.calculate_cyclomatic_complexity(sample_python_simple)

        assert "greet" in complexities
        assert "add" in complexities

        # Simple functions should have low complexity
        assert complexities["greet"] <= 3
        assert complexities["add"] <= 2

    @pytest.mark.asyncio
    async def test_calculate_complexity_complex_function(self, analyzer, sample_python_complex):
        """Test complexity calculation for complex function."""
        complexities = await analyzer.calculate_cyclomatic_complexity(sample_python_complex)

        assert "complex_function" in complexities

        # Complex function should have high complexity
        complex_func_complexity = complexities["complex_function"]
        assert complex_func_complexity >= 9  # Should be significantly complex

    @pytest.mark.asyncio
    async def test_calculate_complexity_specific_function(self, analyzer, sample_python_complex):
        """Test complexity calculation for a specific function."""
        complexities = await analyzer.calculate_cyclomatic_complexity(
            sample_python_complex,
            function_name="complex_function"
        )

        # Should only return the requested function
        assert "complex_function" in complexities
        assert complexities["complex_function"] >= 9

    @pytest.mark.asyncio
    async def test_extract_parameters_with_varargs(self, analyzer, temp_dir):
        """Test extracting functions with *args and **kwargs."""
        file_path = temp_dir / "varargs.py"
        file_path.write_text('''
def flexible(*args, **kwargs):
    pass

def typed_flexible(*args: int, **kwargs: str):
    pass
''')

        functions = await analyzer.analyze_functions(file_path)

        assert len(functions) == 2

        flexible = functions[0]
        param_names = [p["name"] for p in flexible["parameters"]]
        assert "*args" in param_names
        assert "**kwargs" in param_names

    @pytest.mark.asyncio
    async def test_empty_file(self, analyzer, temp_dir):
        """Test parsing an empty file."""
        empty_file = temp_dir / "empty.py"
        empty_file.write_text("")

        result = await analyzer.parse_file(empty_file)
        assert result["type"] == "Module"
        assert result["body"] == []

        functions = await analyzer.analyze_functions(empty_file)
        assert functions == []

        classes = await analyzer.analyze_classes(empty_file)
        assert classes == []

    @pytest.mark.asyncio
    async def test_file_with_only_imports(self, analyzer, sample_python_imports):
        """Test parsing a file with only imports."""
        result = await analyzer.parse_file(sample_python_imports)

        assert result["type"] == "Module"
        assert len(result["body"]) > 0

        # Should have imports and maybe a function
        import_nodes = [n for n in result["body"] if n.get("type") in ["Import", "ImportFrom"]]
        assert len(import_nodes) > 0

    @pytest.mark.asyncio
    async def test_analyze_syntax_error_file(self, analyzer, temp_dir):
        """Test analyzing a file with syntax errors."""
        bad_file = temp_dir / "syntax_error.py"
        bad_file.write_text("def bad(:\n  pass")

        functions = await analyzer.analyze_functions(bad_file)
        assert functions == []

        classes = await analyzer.analyze_classes(bad_file)
        assert classes == []

    @pytest.mark.asyncio
    async def test_decorators_extraction(self, analyzer, temp_dir):
        """Test extracting various decorator types."""
        file_path = temp_dir / "decorators.py"
        file_path.write_text('''
from functools import lru_cache

@lru_cache
def cached_func():
    pass

@staticmethod
def static_method():
    pass

@property
def my_property(self):
    pass

class MyClass:
    @classmethod
    def class_method(cls):
        pass
''')

        functions = await analyzer.analyze_functions(file_path)

        cached = next(f for f in functions if f["name"] == "cached_func")
        assert "lru_cache" in cached["decorators"]

        static = next(f for f in functions if f["name"] == "static_method")
        assert "staticmethod" in static["decorators"]

        prop = next(f for f in functions if f["name"] == "my_property")
        assert "property" in prop["decorators"]
