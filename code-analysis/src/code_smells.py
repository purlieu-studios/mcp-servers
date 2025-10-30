"""Code smell detection."""

from pathlib import Path
from typing import Any


async def detect_code_smells(
    file_path: Path, analyzer: Any, min_severity: str = "all"
) -> list[dict[str, Any]]:
    """Detect code smells and quality issues."""

    smells = []

    # Analyze functions for code smells
    functions = await analyzer.analyze_functions(file_path)

    for func in functions:
        # Long function check
        param_count = len(func.get("parameters", []))
        if param_count > 5:
            smells.append(
                {
                    "type": "too_many_parameters",
                    "severity": "medium",
                    "function": func["name"],
                    "line": func.get("line"),
                    "message": f"Function has {param_count} parameters (recommended: ≤5)",
                    "suggestion": "Consider using a parameter object or builder pattern",
                }
            )

        # Check for missing docstrings (Python)
        if analyzer.language == "python":
            if not func.get("docstring"):
                smells.append(
                    {
                        "type": "missing_docstring",
                        "severity": "low",
                        "function": func["name"],
                        "line": func.get("line"),
                        "message": "Function is missing docstring",
                        "suggestion": "Add a docstring to explain the function's purpose",
                    }
                )

    # Analyze classes for code smells
    classes = await analyzer.analyze_classes(file_path)

    for cls in classes:
        method_count = len(cls.get("methods", []))

        # Too many methods (God class)
        if method_count > 20:
            smells.append(
                {
                    "type": "god_class",
                    "severity": "high",
                    "class": cls["name"],
                    "line": cls.get("line"),
                    "message": f"Class has {method_count} methods (recommended: ≤20)",
                    "suggestion": "Consider splitting into smaller, focused classes",
                }
            )

    # Filter by severity
    if min_severity != "all":
        severity_levels = {"low": 1, "medium": 2, "high": 3}
        min_level = severity_levels.get(min_severity, 0)
        smells = [s for s in smells if severity_levels.get(s["severity"], 0) >= min_level]

    return smells
