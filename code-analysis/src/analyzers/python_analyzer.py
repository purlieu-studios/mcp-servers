"""Python code analyzer using AST."""

import ast
from pathlib import Path
from typing import Any


class PythonAnalyzer:
    """Analyzer for Python code files."""

    def __init__(self):
        self.language = "python"

    async def parse_file(self, file_path: Path, include_body: bool = False) -> dict[str, Any]:
        """Parse Python file and return AST structure."""
        content = file_path.read_text(encoding="utf-8")

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            return {"error": f"Syntax error: {e.msg}", "line": e.lineno, "offset": e.offset}

        return {
            "type": "Module",
            "body": [self._node_to_dict(node, include_body) for node in tree.body],
        }

    async def analyze_functions(self, file_path: Path) -> list[dict[str, Any]]:
        """Extract all functions and their signatures."""
        content = file_path.read_text(encoding="utf-8")

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return []

        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "async": isinstance(node, ast.AsyncFunctionDef),
                    "parameters": self._extract_parameters(node),
                    "return_type": self._extract_type_annotation(node.returns),
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                    "docstring": ast.get_docstring(node),
                    "is_method": self._is_method(node, tree),
                }
                functions.append(func_info)

        return functions

    async def analyze_classes(self, file_path: Path) -> list[dict[str, Any]]:
        """Extract all classes and their structure."""
        content = file_path.read_text(encoding="utf-8")

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return []

        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [self._get_base_name(b) for b in node.bases],
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                    "docstring": ast.get_docstring(node),
                    "methods": [],
                    "properties": [],
                }

                # Extract methods and properties
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "line": item.lineno,
                            "is_static": any(
                                self._get_decorator_name(d) == "staticmethod"
                                for d in item.decorator_list
                            ),
                            "is_class_method": any(
                                self._get_decorator_name(d) == "classmethod"
                                for d in item.decorator_list
                            ),
                            "is_property": any(
                                self._get_decorator_name(d) == "property"
                                for d in item.decorator_list
                            ),
                            "parameters": self._extract_parameters(item),
                            "return_type": self._extract_type_annotation(item.returns),
                        }

                        if method_info["is_property"]:
                            class_info["properties"].append(method_info)
                        else:
                            class_info["methods"].append(method_info)

                classes.append(class_info)

        return classes

    def _node_to_dict(self, node: ast.AST, include_body: bool = False) -> dict[str, Any]:
        """Convert AST node to dictionary."""
        node_dict = {"type": node.__class__.__name__, "line": getattr(node, "lineno", None)}

        if isinstance(node, ast.FunctionDef):
            node_dict.update(
                {
                    "name": node.name,
                    "parameters": self._extract_parameters(node),
                    "return_type": self._extract_type_annotation(node.returns),
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                }
            )
            if include_body:
                node_dict["body"] = [self._node_to_dict(n, include_body) for n in node.body]

        elif isinstance(node, ast.ClassDef):
            node_dict.update(
                {
                    "name": node.name,
                    "bases": [self._get_base_name(b) for b in node.bases],
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                }
            )
            if include_body:
                node_dict["body"] = [self._node_to_dict(n, include_body) for n in node.body]

        elif isinstance(node, ast.Import):
            node_dict["names"] = [alias.name for alias in node.names]

        elif isinstance(node, ast.ImportFrom):
            node_dict.update({"module": node.module, "names": [alias.name for alias in node.names]})

        elif isinstance(node, ast.Assign):
            node_dict["targets"] = [self._get_node_name(t) for t in node.targets]

        elif isinstance(node, ast.AnnAssign):
            node_dict.update(
                {
                    "target": self._get_node_name(node.target),
                    "annotation": self._extract_type_annotation(node.annotation),
                }
            )

        return node_dict

    def _extract_parameters(self, func_node: ast.FunctionDef) -> list[dict[str, Any]]:
        """Extract function parameters with type annotations."""
        params = []

        args = func_node.args

        # Regular arguments
        for i, arg in enumerate(args.args):
            param = {
                "name": arg.arg,
                "type": self._extract_type_annotation(arg.annotation),
                "default": None,
            }

            # Check if this arg has a default value
            default_offset = len(args.args) - len(args.defaults)
            if i >= default_offset:
                default_idx = i - default_offset
                param["default"] = (
                    ast.unparse(args.defaults[default_idx])
                    if default_idx < len(args.defaults)
                    else None
                )

            params.append(param)

        # *args
        if args.vararg:
            params.append(
                {
                    "name": f"*{args.vararg.arg}",
                    "type": self._extract_type_annotation(args.vararg.annotation),
                    "default": None,
                }
            )

        # **kwargs
        if args.kwarg:
            params.append(
                {
                    "name": f"**{args.kwarg.arg}",
                    "type": self._extract_type_annotation(args.kwarg.annotation),
                    "default": None,
                }
            )

        return params

    def _extract_type_annotation(self, annotation: ast.AST | None) -> str | None:
        """Extract type annotation as string."""
        if annotation is None:
            return None

        try:
            return ast.unparse(annotation)
        except:
            return str(annotation)

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        else:
            return ast.unparse(decorator)

    def _get_base_name(self, base: ast.AST) -> str:
        """Get base class name."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{self._get_node_name(base.value)}.{base.attr}"
        else:
            return ast.unparse(base)

    def _get_node_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        else:
            try:
                return ast.unparse(node)
            except:
                return str(node)

    def _is_method(self, func_node: ast.FunctionDef, tree: ast.Module) -> bool:
        """Check if function is a method (inside a class)."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if func_node in node.body:
                    return True
        return False

    async def calculate_cyclomatic_complexity(
        self, file_path: Path, function_name: str | None = None
    ) -> dict[str, int]:
        """Calculate cyclomatic complexity."""
        content = file_path.read_text(encoding="utf-8")

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return {}

        complexities = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if function_name and node.name != function_name:
                    continue

                complexity = self._calculate_complexity_for_node(node)
                complexities[node.name] = complexity

        return complexities

    def _calculate_complexity_for_node(self, node: ast.FunctionDef) -> int:
        """Calculate complexity for a single function node."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points add to complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each boolean operator adds complexity
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1

        return complexity
