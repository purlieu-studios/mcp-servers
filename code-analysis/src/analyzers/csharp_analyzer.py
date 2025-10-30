"""C# code analyzer."""

import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional


class CSharpAnalyzer:
    """Analyzer for C# code files."""

    def __init__(self):
        self.language = "csharp"

    async def parse_file(self, file_path: Path, include_body: bool = False) -> Dict[str, Any]:
        """Parse C# file (simplified regex-based parsing)."""
        content = file_path.read_text(encoding='utf-8')

        classes = self._extract_classes(content)
        methods = self._extract_methods(content)
        usings = self._extract_usings(content)

        return {
            "classes": classes,
            "methods": methods,
            "usings": usings
        }

    async def analyze_functions(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract all methods."""
        content = file_path.read_text(encoding='utf-8')
        return self._extract_methods(content)

    async def analyze_classes(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract all classes."""
        content = file_path.read_text(encoding='utf-8')
        return self._extract_classes(content)

    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        classes = []

        # Match class declarations
        class_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:abstract\s+|sealed\s+|static\s+)?class\s+(\w+)(?:\s*:\s*([^{]+))?'

        for match in re.finditer(class_pattern, content):
            name = match.group(1)
            inheritance = match.group(2).strip() if match.group(2) else None

            class_info = {
                "name": name,
                "line": content[:match.start()].count('\n') + 1,
                "inherits_from": inheritance,
                "methods": [],
                "properties": []
            }

            # Extract methods and properties (simplified)
            class_body_start = content.find('{', match.end())
            if class_body_start != -1:
                class_info["methods"] = self._extract_class_methods(content, class_body_start)
                class_info["properties"] = self._extract_properties(content, class_body_start)

            classes.append(class_info)

        return classes

    def _extract_methods(self, content: str) -> List[Dict[str, Any]]:
        """Extract method definitions."""
        methods = []

        # Match method declarations
        method_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:static\s+|virtual\s+|override\s+|async\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)'

        for match in re.finditer(method_pattern, content):
            return_type = match.group(1)
            name = match.group(2)
            params = match.group(3).strip()

            # Skip if it looks like a keyword
            if name.lower() in ['if', 'while', 'for', 'foreach', 'switch', 'catch']:
                continue

            method_info = {
                "name": name,
                "return_type": return_type,
                "parameters": self._parse_parameters(params),
                "line": content[:match.start()].count('\n') + 1,
                "async": 'async' in match.group(0)
            }
            methods.append(method_info)

        return methods

    def _extract_class_methods(self, content: str, class_start: int) -> List[Dict[str, Any]]:
        """Extract methods from a class."""
        # Simplified - would need proper parsing for accuracy
        return []

    def _extract_properties(self, content: str, class_start: int) -> List[Dict[str, Any]]:
        """Extract properties from a class."""
        properties = []

        # Match property declarations (simplified)
        prop_pattern = r'(?:public\s+|private\s+|protected\s+)?(\w+)\s+(\w+)\s*{\s*get;?\s*set;?\s*}'

        for match in re.finditer(prop_pattern, content[class_start:class_start+10000]):
            properties.append({
                "name": match.group(2),
                "type": match.group(1)
            })

        return properties

    def _extract_usings(self, content: str) -> List[str]:
        """Extract using statements."""
        usings = []

        using_pattern = r'using\s+([^;]+);'

        for match in re.finditer(using_pattern, content):
            usings.append(match.group(1).strip())

        return usings

    def _parse_parameters(self, params_str: str) -> List[Dict[str, str]]:
        """Parse method parameters."""
        if not params_str.strip():
            return []

        parameters = []
        for param in params_str.split(','):
            parts = param.strip().split()
            if len(parts) >= 2:
                parameters.append({
                    "type": ' '.join(parts[:-1]),
                    "name": parts[-1]
                })

        return parameters
