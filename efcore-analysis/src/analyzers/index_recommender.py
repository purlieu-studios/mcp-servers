"""Database index recommender."""

import re
from pathlib import Path
from typing import Any


class IndexRecommender:
    """Recommend database indexes based on usage patterns."""

    async def analyze(
        self, project_path: Path, dbcontext_name: str | None = None
    ) -> list[dict[str, Any]]:
        """Analyze project and suggest indexes."""
        if not project_path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")

        recommendations = []

        # Find all LINQ queries
        queries = await self._find_all_queries(project_path)

        # Analyze query patterns
        for query_info in queries:
            query = query_info["query"]

            # Look for Where clauses (potential index candidates)
            where_patterns = re.findall(r"\.Where\((\w+)\s*=>\s*\1\.(\w+)\s*==", query)
            for entity, property in where_patterns:
                recommendations.append(
                    {
                        "entity": entity,
                        "property": property,
                        "reason": "Frequently used in WHERE clause",
                        "priority": "high",
                        "query_file": query_info["file"],
                        "suggested_index": f"CREATE INDEX IX_{entity}_{property} ON {entity}s ({property})",
                    }
                )

            # Look for OrderBy clauses
            orderby_patterns = re.findall(r"\.OrderBy\((\w+)\s*=>\s*\1\.(\w+)\)", query)
            for entity, property in orderby_patterns:
                recommendations.append(
                    {
                        "entity": entity,
                        "property": property,
                        "reason": "Used in ORDER BY clause",
                        "priority": "medium",
                        "query_file": query_info["file"],
                        "suggested_index": f"CREATE INDEX IX_{entity}_{property} ON {entity}s ({property})",
                    }
                )

        # Deduplicate recommendations
        unique_recommendations = []
        seen = set()

        for rec in recommendations:
            key = (rec["entity"], rec["property"])
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)

        return unique_recommendations

    async def _find_all_queries(self, project_path: Path) -> list[dict[str, Any]]:
        """Find all LINQ queries in the project."""
        all_queries = []

        for cs_file in project_path.rglob("*.cs"):
            try:
                content = cs_file.read_text(encoding="utf-8")

                # Extract LINQ queries (simplified)
                linq_patterns = [
                    r"\.Where\([^)]+\)",
                    r"\.OrderBy\([^)]+\)",
                    r"\.FirstOrDefault\([^)]*\)",
                ]

                for pattern in linq_patterns:
                    for match in re.finditer(pattern, content):
                        # Get full line
                        line_start = content.rfind("\n", 0, match.start())
                        line_end = content.find("\n", match.end())
                        line = content[line_start:line_end].strip()

                        all_queries.append({"query": line, "file": str(cs_file)})
            except:
                continue

        return all_queries
