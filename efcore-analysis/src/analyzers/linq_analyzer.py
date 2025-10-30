"""LINQ query analyzer."""

import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List


class LinqAnalyzer:
    """Analyze LINQ queries for optimization opportunities."""

    async def analyze(self, file_path: Path) -> Dict[str, Any]:
        """Analyze LINQ queries in a file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding='utf-8')

        # Extract LINQ queries
        queries = self._extract_linq_queries(content)

        # Analyze each query
        analyzed_queries = []
        issues = []

        for query in queries:
            analysis = self._analyze_query(query)
            analyzed_queries.append(analysis)

            if analysis.get("issues"):
                issues.extend(analysis["issues"])

        return {
            "total_queries": len(queries),
            "analyzed_queries": analyzed_queries,
            "issues": issues,
            "total_issues": len(issues)
        }

    def _extract_linq_queries(self, content: str) -> List[str]:
        """Extract LINQ queries from content."""
        queries = []

        # Match common LINQ patterns
        patterns = [
            r'\.Where\([^)]+\)',
            r'\.Select\([^)]+\)',
            r'\.FirstOrDefault\([^)]*\)',
            r'\.ToList\(\)',
            r'\.Include\([^)]+\)',
            r'\.OrderBy\([^)]+\)',
            r'\.GroupBy\([^)]+\)',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                # Get context (line)
                line_start = content.rfind('\n', 0, match.start())
                line_end = content.find('\n', match.end())
                line = content[line_start:line_end].strip()

                if line not in queries:
                    queries.append(line)

        return queries

    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze a single LINQ query."""
        analysis = {
            "query": query,
            "issues": [],
            "suggestions": []
        }

        # Check for N+1 query problem
        if '.Include(' not in query and any(nav in query for nav in ['Navigation', 'Related']):
            analysis["issues"].append({
                "type": "potential_n_plus_1",
                "severity": "high",
                "message": "Potential N+1 query problem detected",
                "suggestion": "Consider using .Include() to eager load related entities"
            })

        # Check for missing ToListAsync/ToArrayAsync
        if '.ToList()' in query:
            analysis["issues"].append({
                "type": "sync_execution",
                "severity": "medium",
                "message": "Using synchronous ToList()",
                "suggestion": "Consider using ToListAsync() for async execution"
            })

        # Check for Select after Where (optimization)
        if '.Select(' in query and '.Where(' in query:
            select_pos = query.find('.Select(')
            where_pos = query.find('.Where(')

            if select_pos < where_pos:
                analysis["suggestions"].append({
                    "type": "optimization",
                    "message": "Consider placing Where before Select for better performance"
                })

        # Check for FirstOrDefault without Where
        if '.FirstOrDefault()' in query and '.Where(' not in query:
            analysis["suggestions"].append({
                "type": "optimization",
                "message": "Consider using FirstOrDefault(predicate) instead of Where().FirstOrDefault()"
            })

        return analysis
