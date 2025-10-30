"""Code complexity analysis."""

from pathlib import Path
from typing import Any


async def calculate_complexity(
    file_path: Path, analyzer: Any, function_name: str | None = None
) -> dict[str, Any]:
    """Calculate code complexity metrics."""

    if hasattr(analyzer, "calculate_cyclomatic_complexity"):
        # Use analyzer-specific complexity calculation
        complexities = await analyzer.calculate_cyclomatic_complexity(file_path, function_name)
    else:
        # Fallback to basic complexity
        functions = await analyzer.analyze_functions(file_path)
        complexities = {}

        for func in functions:
            # Basic heuristic: lines of code / decisions
            complexities[func["name"]] = {
                "cyclomatic": 1,  # Placeholder
                "cognitive": 1,  # Placeholder
            }

    # Calculate overall file complexity
    if isinstance(complexities, dict) and complexities:
        avg_complexity = (
            sum(complexities.values()) / len(complexities)
            if isinstance(list(complexities.values())[0], int)
            else 1
        )

        return {
            "file_complexity": avg_complexity,
            "function_complexities": complexities,
            "high_complexity_functions": [
                name
                for name, score in complexities.items()
                if (isinstance(score, int) and score > 10)
                or (isinstance(score, dict) and score.get("cyclomatic", 0) > 10)
            ],
        }

    return {
        "file_complexity": 0,
        "function_complexities": complexities,
        "high_complexity_functions": [],
    }
