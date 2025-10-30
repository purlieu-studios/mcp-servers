"""Dependency analysis for code files."""

import re
from pathlib import Path
from typing import Any


class DependencyAnalyzer:
    """Analyze file dependencies and imports."""

    async def analyze(self, file_path: Path, recursive: bool = False) -> dict[str, Any]:
        """Analyze dependencies for a file or directory."""

        if not file_path.exists():
            raise FileNotFoundError(f"Path does not exist: {file_path}")

        if file_path.is_file():
            return await self._analyze_file(file_path)
        elif file_path.is_dir() and recursive:
            return await self._analyze_directory(file_path)
        else:
            return {"error": "Invalid path or recursive not enabled for directory"}

    async def _analyze_file(self, file_path: Path) -> dict[str, Any]:
        """Analyze dependencies for a single file."""
        content = file_path.read_text(encoding="utf-8")
        ext = file_path.suffix

        dependencies = {"file": str(file_path), "imports": [], "dependencies": []}

        # Python imports
        if ext == ".py":
            dependencies["imports"] = self._extract_python_imports(content)

        # JavaScript/TypeScript imports
        elif ext in [".js", ".ts", ".jsx", ".tsx"]:
            dependencies["imports"] = self._extract_js_imports(content)

        # C# usings
        elif ext == ".cs":
            dependencies["imports"] = self._extract_csharp_usings(content)

        # Group by type
        dependencies["external_packages"] = [
            imp
            for imp in dependencies["imports"]
            if not imp.startswith(".") and not imp.startswith("/")
        ]

        dependencies["local_imports"] = [
            imp for imp in dependencies["imports"] if imp.startswith(".") or imp.startswith("/")
        ]

        return dependencies

    async def _analyze_directory(self, directory: Path) -> dict[str, Any]:
        """Analyze dependencies for all files in a directory."""
        all_dependencies = {}

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in [
                ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".cs",
            ]:
                file_deps = await self._analyze_file(file_path)
                all_dependencies[str(file_path)] = file_deps

        return {
            "directory": str(directory),
            "files": all_dependencies,
            "total_files": len(all_dependencies),
        }

    def _extract_python_imports(self, content: str) -> list[str]:
        """Extract Python imports."""
        imports = []

        # import x
        for match in re.finditer(r"^import\s+([^\s]+)", content, re.MULTILINE):
            imports.append(match.group(1))

        # from x import y
        for match in re.finditer(r"^from\s+([^\s]+)\s+import", content, re.MULTILINE):
            imports.append(match.group(1))

        return imports

    def _extract_js_imports(self, content: str) -> list[str]:
        """Extract JavaScript/TypeScript imports."""
        imports = []

        # import ... from 'x'
        for match in re.finditer(r'import\s+.+\s+from\s+[\'"](.+?)[\'"]', content):
            imports.append(match.group(1))

        # import 'x'
        for match in re.finditer(r'import\s+[\'"](.+?)[\'"]', content):
            imports.append(match.group(1))

        # require('x')
        for match in re.finditer(r'require\([\'"](.+?)[\'"]\)', content):
            imports.append(match.group(1))

        return imports

    def _extract_csharp_usings(self, content: str) -> list[str]:
        """Extract C# using statements."""
        usings = []

        for match in re.finditer(r"using\s+([^;]+);", content):
            usings.append(match.group(1).strip())

        return usings
