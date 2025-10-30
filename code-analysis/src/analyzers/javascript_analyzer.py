"""JavaScript/TypeScript code analyzer."""

import re
from pathlib import Path
from typing import Any


class JavaScriptAnalyzer:
    """Analyzer for JavaScript and TypeScript code files."""

    def __init__(self):
        self.language = "javascript"

    async def parse_file(self, file_path: Path, include_body: bool = False) -> dict[str, Any]:
        """Parse JavaScript/TypeScript file (simplified regex-based parsing)."""
        content = file_path.read_text(encoding="utf-8")

        # Extract basic structure
        functions = self._extract_functions(content)
        classes = self._extract_classes(content)
        imports = self._extract_imports(content)

        return {"functions": functions, "classes": classes, "imports": imports}

    async def analyze_functions(self, file_path: Path) -> list[dict[str, Any]]:
        """Extract all functions."""
        content = file_path.read_text(encoding="utf-8")
        return self._extract_functions(content)

    async def analyze_classes(self, file_path: Path) -> list[dict[str, Any]]:
        """Extract all classes."""
        content = file_path.read_text(encoding="utf-8")
        return self._extract_classes(content)

    def _extract_functions(self, content: str) -> list[dict[str, Any]]:
        """Extract function definitions using regex."""
        functions = []

        # Match various function declarations
        patterns = [
            # function name(...) or async function name(...)
            r"(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
            # const name = (...) => or const name = async (...) =>
            r"const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>",
            # name: (...) => (object methods)
            r"(\w+)\s*:\s*(?:async\s+)?\(([^)]*)\)\s*=>",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                name = match.group(1)
                params = match.group(2).strip()

                func_info = {
                    "name": name,
                    "parameters": [p.strip() for p in params.split(",") if p.strip()],
                    "line": content[: match.start()].count("\n") + 1,
                    "async": "async" in match.group(0),
                }
                functions.append(func_info)

        return functions

    def _extract_classes(self, content: str) -> list[dict[str, Any]]:
        """Extract class definitions using regex."""
        classes = []

        # Match class declarations
        class_pattern = r"class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{"

        for match in re.finditer(class_pattern, content):
            name = match.group(1)
            base = match.group(2)

            class_info = {
                "name": name,
                "line": content[: match.start()].count("\n") + 1,
                "extends": base,
                "methods": [],
            }

            # Try to extract methods (simplified)
            # This would need proper AST parsing for accuracy
            class_info["methods"] = self._extract_class_methods(content, match.end())

            classes.append(class_info)

        return classes

    def _extract_class_methods(self, content: str, class_start: int) -> list[dict[str, Any]]:
        """Extract methods from a class (simplified)."""
        # This is a simplified version - would need proper parsing
        methods = []
        method_pattern = r"(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*{"

        # Look for methods in class body (very simplified)
        class_body = content[class_start : class_start + 5000]  # Arbitrary limit

        for match in re.finditer(method_pattern, class_body):
            if match.group(1) not in ["if", "while", "for", "switch"]:  # Filter keywords
                methods.append(
                    {
                        "name": match.group(1),
                        "parameters": [p.strip() for p in match.group(2).split(",") if p.strip()],
                    }
                )

        return methods

    def _extract_imports(self, content: str) -> list[dict[str, Any]]:
        """Extract import statements."""
        imports = []

        # Match import statements
        import_patterns = [
            r'import\s+(.+?)\s+from\s+[\'"](.+?)[\'"]',
            r'import\s+[\'"](.+?)[\'"]',
            r'require\([\'"](.+?)[\'"]\)',
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                imports.append(
                    {
                        "module": match.group(match.lastindex)
                        if match.lastindex
                        else match.group(1),
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

        return imports
