"""Context analyzer for intelligent file recommendation and pattern detection.

Analyzes workspace state, access patterns, and file relationships to provide
proactive context recommendations.
"""

import ast
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """Analyzes workspace context for intelligent file recommendations."""

    def __init__(self, workspace_state):
        """Initialize context analyzer.

        Args:
            workspace_state: WorkspaceState instance
        """
        self.workspace_state = workspace_state
        self._dependency_cache: Dict[str, Set[str]] = {}
        self._pattern_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None
        self.CACHE_TTL_MINUTES = 5

    def get_recommendations(
        self,
        limit: int = 10,
        include_dependencies: bool = True,
        include_patterns: bool = True
    ) -> List[Dict[str, Any]]:
        """Get file recommendations based on current context.

        Args:
            limit: Maximum recommendations
            include_dependencies: Include dependency-based recommendations
            include_patterns: Include pattern-based recommendations

        Returns:
            List of recommendation dictionaries with scores
        """
        recommendations = {}

        # Get focus files
        focus_files = self.workspace_state.get_focus_files(limit=20)
        if not focus_files:
            return []

        focus_paths = [f['path'] for f in focus_files]

        # Score by recency (most recent = highest score)
        for idx, file_info in enumerate(focus_files):
            path = file_info['path']
            recency_score = 1.0 - (idx / len(focus_files))  # 1.0 to 0.0

            if path not in recommendations:
                recommendations[path] = {
                    'file': path,
                    'score': 0.0,
                    'reasons': []
                }

            recommendations[path]['score'] += recency_score * 0.3
            recommendations[path]['reasons'].append(
                f"Recently accessed ({file_info.get('reason', 'unknown')})"
            )

        # Add dependency-based recommendations
        if include_dependencies:
            dep_recs = self._get_dependency_recommendations(focus_paths)
            for path, score in dep_recs.items():
                if path not in recommendations:
                    recommendations[path] = {
                        'file': path,
                        'score': 0.0,
                        'reasons': []
                    }
                recommendations[path]['score'] += score * 0.4
                recommendations[path]['reasons'].append('Related by imports/dependencies')

        # Add pattern-based recommendations
        if include_patterns:
            pattern_recs = self._get_pattern_recommendations(focus_paths)
            for path, score in pattern_recs.items():
                if path not in recommendations:
                    recommendations[path] = {
                        'file': path,
                        'score': 0.0,
                        'reasons': []
                    }
                recommendations[path]['score'] += score * 0.3
                recommendations[path]['reasons'].append('Frequently accessed together')

        # Sort by score and return top N
        sorted_recs = sorted(
            recommendations.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        # Filter out files that are already in top focus
        top_focus = set(focus_paths[:5])
        filtered_recs = [r for r in sorted_recs if r['file'] not in top_focus]

        return filtered_recs[:limit]

    def get_related_files(
        self,
        file_path: str,
        relationship_type: str = 'all'
    ) -> List[Dict[str, Any]]:
        """Find files related to a specific file.

        Args:
            file_path: Path to file
            relationship_type: Type of relationship ('imports', 'imported_by', 'co_accessed', 'all')

        Returns:
            List of related file dictionaries
        """
        path = Path(file_path)
        if not path.exists():
            return []

        related = {}

        # Import dependencies
        if relationship_type in ('imports', 'all'):
            imports = self._extract_imports(path)
            for imp in imports:
                related[imp] = {
                    'file': imp,
                    'relationship': 'imports',
                    'strength': 1.0
                }

        # Reverse dependencies (files that import this one)
        if relationship_type in ('imported_by', 'all'):
            imported_by = self._find_reverse_dependencies(file_path)
            for imp in imported_by:
                if imp not in related:
                    related[imp] = {
                        'file': imp,
                        'relationship': 'imported_by',
                        'strength': 0.9
                    }

        # Co-accessed files (files accessed in same sessions)
        if relationship_type in ('co_accessed', 'all'):
            co_accessed = self._find_co_accessed_files(file_path)
            for co_file, score in co_accessed.items():
                if co_file not in related:
                    related[co_file] = {
                        'file': co_file,
                        'relationship': 'co_accessed',
                        'strength': score
                    }

        return list(related.values())

    def get_access_patterns(self) -> Dict[str, Any]:
        """Analyze file access patterns.

        Returns:
            Dictionary with pattern statistics
        """
        focus_files = self.workspace_state.get_focus_files(limit=100)

        if not focus_files:
            return {
                'total_files': 0,
                'most_accessed': [],
                'access_by_hour': {},
                'average_session_files': 0
            }

        # Count file access frequency
        file_counts = Counter(f['path'] for f in focus_files)

        # Analyze access times
        access_by_hour = defaultdict(int)
        for file_info in focus_files:
            try:
                timestamp = datetime.fromisoformat(file_info['last_accessed'])
                hour = timestamp.hour
                access_by_hour[hour] += 1
            except (ValueError, KeyError):
                continue

        # Get most accessed files
        most_accessed = [
            {'file': path, 'count': count}
            for path, count in file_counts.most_common(10)
        ]

        return {
            'total_files': len(file_counts),
            'most_accessed': most_accessed,
            'access_by_hour': dict(access_by_hour),
            'average_session_files': len(focus_files) / max(1, len(file_counts))
        }

    def build_dependency_map(
        self,
        root_path: Optional[Path] = None
    ) -> Dict[str, List[str]]:
        """Build dependency map for Python files in workspace.

        Args:
            root_path: Root directory to scan (defaults to cwd)

        Returns:
            Dictionary mapping files to their dependencies
        """
        if root_path is None:
            root_path = Path.cwd()

        dependency_map = {}

        # Find all Python files
        python_files = list(root_path.rglob('*.py'))

        for py_file in python_files:
            try:
                imports = self._extract_imports(py_file)
                if imports:
                    dependency_map[str(py_file)] = list(imports)
            except Exception as e:
                logger.debug(f"Error analyzing {py_file}: {e}")
                continue

        return dependency_map

    def predict_next_files(
        self,
        current_file: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Predict likely next files to access.

        Args:
            current_file: Current file being worked on (optional)
            limit: Maximum predictions

        Returns:
            List of prediction dictionaries with confidence scores
        """
        if current_file:
            # Get related files to current file
            related = self.get_related_files(current_file, relationship_type='all')

            # Combine with access patterns
            patterns = self._get_pattern_cache()
            predictions = []

            for rel in related[:limit * 2]:
                confidence = rel['strength']

                # Boost confidence if file is frequently accessed
                if rel['file'] in patterns.get('frequent_files', set()):
                    confidence *= 1.2

                predictions.append({
                    'file': rel['file'],
                    'confidence': min(1.0, confidence),
                    'reason': f"Related by {rel['relationship']}"
                })

            return sorted(predictions, key=lambda x: x['confidence'], reverse=True)[:limit]
        else:
            # Use general recommendations
            recs = self.get_recommendations(limit=limit)
            return [
                {
                    'file': r['file'],
                    'confidence': r['score'],
                    'reason': ', '.join(r['reasons'])
                }
                for r in recs
            ]

    def get_context_summary(self) -> Dict[str, Any]:
        """Get high-level context summary.

        Returns:
            Context summary dictionary
        """
        focus_files = self.workspace_state.get_focus_files(limit=20)
        recent_queries = self.workspace_state.get_recent_queries(limit=10)
        active_tasks = self.workspace_state.get_active_tasks()

        # Analyze file types
        file_extensions = Counter()
        for file_info in focus_files:
            path = Path(file_info['path'])
            file_extensions[path.suffix] += 1

        # Analyze query servers
        server_usage = Counter(q.get('server', 'unknown') for q in recent_queries)

        return {
            'focus_files_count': len(focus_files),
            'active_tasks_count': len(active_tasks),
            'recent_queries_count': len(recent_queries),
            'primary_file_types': dict(file_extensions.most_common(5)),
            'server_usage': dict(server_usage),
            'current_focus': focus_files[:5] if focus_files else [],
            'recommendations_available': len(self.get_recommendations(limit=5))
        }

    # Private helper methods

    def _get_dependency_recommendations(
        self,
        focus_paths: List[str]
    ) -> Dict[str, float]:
        """Get recommendations based on file dependencies."""
        recommendations = {}

        for path in focus_paths[:10]:  # Limit to top 10 focus files
            try:
                file_path = Path(path)
                if not file_path.exists() or file_path.suffix != '.py':
                    continue

                # Get imports from this file
                imports = self._extract_imports(file_path)
                for imp in imports:
                    if imp not in recommendations:
                        recommendations[imp] = 0.0
                    recommendations[imp] += 0.5  # Base score for being imported

                # Get files that import this file
                imported_by = self._find_reverse_dependencies(path)
                for imp in imported_by:
                    if imp not in recommendations:
                        recommendations[imp] = 0.0
                    recommendations[imp] += 0.3  # Lower score for reverse dependency

            except Exception as e:
                logger.debug(f"Error getting dependencies for {path}: {e}")
                continue

        return recommendations

    def _get_pattern_recommendations(
        self,
        focus_paths: List[str]
    ) -> Dict[str, float]:
        """Get recommendations based on access patterns."""
        patterns = self._get_pattern_cache()
        recommendations = {}

        # Files frequently accessed together
        co_access = patterns.get('co_access_map', {})

        for path in focus_paths[:5]:  # Top 5 focus files
            if path in co_access:
                for co_file, score in co_access[path].items():
                    if co_file not in recommendations:
                        recommendations[co_file] = 0.0
                    recommendations[co_file] += score

        return recommendations

    def _extract_imports(self, file_path: Path) -> Set[str]:
        """Extract import statements from Python file."""
        if str(file_path) in self._dependency_cache:
            return self._dependency_cache[str(file_path)]

        imports = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)

            # Try to resolve to file paths
            resolved_imports = self._resolve_imports(imports, file_path)
            self._dependency_cache[str(file_path)] = resolved_imports

            return resolved_imports

        except Exception as e:
            logger.debug(f"Error parsing {file_path}: {e}")
            return set()

    def _resolve_imports(
        self,
        imports: Set[str],
        source_file: Path
    ) -> Set[str]:
        """Resolve import module names to file paths."""
        resolved = set()

        for imp in imports:
            # Convert module path to file path
            # e.g., "foo.bar.baz" -> "foo/bar/baz.py"
            module_path = imp.replace('.', '/')

            # Try different resolutions
            candidates = [
                source_file.parent / f"{module_path}.py",
                source_file.parent / module_path / "__init__.py",
                Path.cwd() / f"{module_path}.py",
                Path.cwd() / module_path / "__init__.py",
            ]

            for candidate in candidates:
                if candidate.exists():
                    resolved.add(str(candidate))
                    break

        return resolved

    def _find_reverse_dependencies(self, file_path: str) -> Set[str]:
        """Find files that import the given file."""
        imported_by = set()
        target_path = Path(file_path)

        # Search in workspace for files that might import this one
        focus_files = self.workspace_state.get_focus_files(limit=50)

        for file_info in focus_files:
            try:
                path = Path(file_info['path'])
                if not path.exists() or path.suffix != '.py':
                    continue

                imports = self._extract_imports(path)
                if str(target_path) in imports:
                    imported_by.add(str(path))

            except Exception as e:
                logger.debug(f"Error checking {file_info['path']}: {e}")
                continue

        return imported_by

    def _find_co_accessed_files(self, file_path: str) -> Dict[str, float]:
        """Find files frequently accessed together with given file."""
        patterns = self._get_pattern_cache()
        co_access = patterns.get('co_access_map', {})

        return co_access.get(file_path, {})

    def _get_pattern_cache(self) -> Dict[str, Any]:
        """Get or build pattern cache."""
        # Check if cache is still valid
        if self._pattern_cache and self._cache_timestamp:
            age = datetime.now() - self._cache_timestamp
            if age < timedelta(minutes=self.CACHE_TTL_MINUTES):
                return self._pattern_cache

        # Rebuild cache
        focus_files = self.workspace_state.get_focus_files(limit=100)

        # Build co-access map (files accessed close together in time)
        co_access_map = defaultdict(lambda: defaultdict(float))

        for i, file1 in enumerate(focus_files):
            path1 = file1['path']
            time1 = datetime.fromisoformat(file1['last_accessed'])

            for file2 in focus_files[i+1:i+11]:  # Look at next 10 files
                path2 = file2['path']
                time2 = datetime.fromisoformat(file2['last_accessed'])

                # Calculate time proximity score
                time_diff = abs((time1 - time2).total_seconds())
                if time_diff < 3600:  # Within 1 hour
                    score = 1.0 - (time_diff / 3600)
                    co_access_map[path1][path2] += score
                    co_access_map[path2][path1] += score

        # Get frequently accessed files
        file_counts = Counter(f['path'] for f in focus_files)
        frequent_files = {path for path, count in file_counts.items() if count >= 3}

        self._pattern_cache = {
            'co_access_map': {k: dict(v) for k, v in co_access_map.items()},
            'frequent_files': frequent_files,
            'total_analyzed': len(focus_files)
        }
        self._cache_timestamp = datetime.now()

        return self._pattern_cache
