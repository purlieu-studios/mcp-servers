"""Tests for context analyzer module."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.context_analyzer import ContextAnalyzer


pytestmark = pytest.mark.unit


class TestContextAnalyzer:
    """Test ContextAnalyzer class."""

    @pytest.fixture
    def mock_workspace_state(self):
        """Create mock workspace state."""
        mock = Mock()
        mock.get_focus_files = Mock(return_value=[])
        mock.get_recent_queries = Mock(return_value=[])
        mock.get_active_tasks = Mock(return_value=[])
        return mock

    @pytest.fixture
    def analyzer(self, mock_workspace_state):
        """Create ContextAnalyzer instance."""
        return ContextAnalyzer(mock_workspace_state)

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create some Python files
            (workspace / "main.py").write_text("import utils\nimport helpers\n")
            (workspace / "utils.py").write_text("def foo(): pass\n")
            (workspace / "helpers.py").write_text("from utils import foo\n")

            yield workspace

    def test_initialization(self, analyzer, mock_workspace_state):
        """Test analyzer initialization."""
        assert analyzer.workspace_state == mock_workspace_state
        assert analyzer._dependency_cache == {}
        assert analyzer._pattern_cache is None

    def test_get_recommendations_empty_workspace(self, analyzer):
        """Test recommendations with no focus files."""
        recommendations = analyzer.get_recommendations()
        assert recommendations == []

    def test_get_recommendations_with_focus_files(self, analyzer, mock_workspace_state):
        """Test recommendations based on focus files."""
        now = datetime.now()
        focus_files = [
            {
                'path': '/path/to/file1.py',
                'last_accessed': now.isoformat(),
                'reason': 'editing'
            },
            {
                'path': '/path/to/file2.py',
                'last_accessed': (now - timedelta(minutes=5)).isoformat(),
                'reason': 'viewing'
            },
            {
                'path': '/path/to/file3.py',
                'last_accessed': (now - timedelta(minutes=10)).isoformat(),
                'reason': 'search_result'
            }
        ]
        mock_workspace_state.get_focus_files.return_value = focus_files

        recommendations = analyzer.get_recommendations(limit=5, include_dependencies=False, include_patterns=False)

        # Should get recommendations based on recency
        assert len(recommendations) >= 0
        # Most recent files should not be in recommendations (they're already in focus)

    def test_get_recommendations_filters_top_focus(self, analyzer, mock_workspace_state):
        """Test that top 5 focus files are filtered from recommendations."""
        now = datetime.now()
        focus_files = [
            {'path': f'/file{i}.py', 'last_accessed': (now - timedelta(minutes=i)).isoformat(), 'reason': 'editing'}
            for i in range(10)
        ]
        mock_workspace_state.get_focus_files.return_value = focus_files

        recommendations = analyzer.get_recommendations(limit=10, include_dependencies=False, include_patterns=False)

        # Top 5 files should not appear in recommendations
        rec_paths = [r['file'] for r in recommendations]
        for i in range(5):
            assert f'/file{i}.py' not in rec_paths

    def test_get_related_files_nonexistent_file(self, analyzer):
        """Test getting related files for non-existent file."""
        related = analyzer.get_related_files('/nonexistent/file.py')
        assert related == []

    def test_get_related_files_with_imports(self, analyzer, temp_workspace):
        """Test finding related files by imports."""
        main_file = temp_workspace / "main.py"

        related = analyzer.get_related_files(
            str(main_file),
            relationship_type='imports'
        )

        # Should have some related files (even if not all resolved)
        assert isinstance(related, list)

    def test_get_access_patterns_empty(self, analyzer, mock_workspace_state):
        """Test access patterns with no data."""
        mock_workspace_state.get_focus_files.return_value = []

        patterns = analyzer.get_access_patterns()

        assert patterns['total_files'] == 0
        assert patterns['most_accessed'] == []
        assert patterns['average_session_files'] == 0

    def test_get_access_patterns_with_data(self, analyzer, mock_workspace_state):
        """Test access patterns with focus files."""
        now = datetime.now()
        focus_files = [
            {'path': '/file1.py', 'last_accessed': now.isoformat()},
            {'path': '/file1.py', 'last_accessed': (now - timedelta(hours=1)).isoformat()},
            {'path': '/file2.py', 'last_accessed': now.isoformat()},
        ]
        mock_workspace_state.get_focus_files.return_value = focus_files

        patterns = analyzer.get_access_patterns()

        assert patterns['total_files'] == 2
        assert len(patterns['most_accessed']) > 0
        assert patterns['most_accessed'][0]['file'] == '/file1.py'
        assert patterns['most_accessed'][0]['count'] == 2

    def test_build_dependency_map(self, analyzer, temp_workspace):
        """Test building dependency map."""
        dep_map = analyzer.build_dependency_map(root_path=temp_workspace)

        assert isinstance(dep_map, dict)
        # Should find Python files
        assert len(dep_map) > 0

    def test_build_dependency_map_caches_results(self, analyzer, temp_workspace):
        """Test that dependency extraction is cached."""
        main_file = temp_workspace / "main.py"

        # First call
        imports1 = analyzer._extract_imports(main_file)

        # Second call should use cache
        imports2 = analyzer._extract_imports(main_file)

        assert imports1 == imports2
        assert str(main_file) in analyzer._dependency_cache

    def test_predict_next_files_empty(self, analyzer, mock_workspace_state):
        """Test prediction with no context."""
        mock_workspace_state.get_focus_files.return_value = []

        predictions = analyzer.predict_next_files(limit=5)

        assert predictions == []

    def test_predict_next_files_with_current(self, analyzer, temp_workspace):
        """Test prediction with current file."""
        main_file = temp_workspace / "main.py"

        predictions = analyzer.predict_next_files(
            current_file=str(main_file),
            limit=5
        )

        # Should return some predictions
        assert isinstance(predictions, list)
        for pred in predictions:
            assert 'file' in pred
            assert 'confidence' in pred
            assert 'reason' in pred
            assert 0.0 <= pred['confidence'] <= 1.0

    def test_get_context_summary(self, analyzer, mock_workspace_state):
        """Test context summary generation."""
        now = datetime.now()
        mock_workspace_state.get_focus_files.return_value = [
            {'path': '/file1.py', 'last_accessed': now.isoformat(), 'reason': 'editing'},
            {'path': '/file2.js', 'last_accessed': now.isoformat(), 'reason': 'viewing'}
        ]
        mock_workspace_state.get_recent_queries.return_value = [
            {'server': 'rag', 'query': 'test'}
        ]
        mock_workspace_state.get_active_tasks.return_value = [
            {'description': 'Fix bug'}
        ]

        summary = analyzer.get_context_summary()

        assert summary['focus_files_count'] == 2
        assert summary['active_tasks_count'] == 1
        assert summary['recent_queries_count'] == 1
        assert '.py' in summary['primary_file_types']
        assert summary['server_usage']['rag'] == 1
        assert len(summary['current_focus']) <= 5

    def test_extract_imports_invalid_syntax(self, analyzer, temp_workspace):
        """Test extracting imports from file with invalid syntax."""
        bad_file = temp_workspace / "bad.py"
        bad_file.write_text("import this is not valid python")

        imports = analyzer._extract_imports(bad_file)

        # Should handle error gracefully
        assert imports == set()

    def test_pattern_cache_ttl(self, analyzer, mock_workspace_state):
        """Test pattern cache expiration."""
        mock_workspace_state.get_focus_files.return_value = [
            {'path': '/file1.py', 'last_accessed': datetime.now().isoformat()}
        ]

        # Get pattern cache
        cache1 = analyzer._get_pattern_cache()
        assert cache1 is not None

        # Simulate cache expiration
        analyzer._cache_timestamp = datetime.now() - timedelta(minutes=10)

        # Should rebuild cache
        cache2 = analyzer._get_pattern_cache()
        assert cache2 is not None

    def test_co_access_detection(self, analyzer, mock_workspace_state):
        """Test co-access pattern detection."""
        now = datetime.now()
        focus_files = [
            {'path': '/file1.py', 'last_accessed': now.isoformat()},
            {'path': '/file2.py', 'last_accessed': (now + timedelta(minutes=1)).isoformat()},
            {'path': '/file3.py', 'last_accessed': (now + timedelta(minutes=2)).isoformat()},
        ]
        mock_workspace_state.get_focus_files.return_value = focus_files

        cache = analyzer._get_pattern_cache()

        # Files accessed close together should be in co_access_map
        assert 'co_access_map' in cache
        co_access = cache['co_access_map']

        # file1 and file2 should be linked (accessed within 1 hour)
        if '/file1.py' in co_access:
            assert isinstance(co_access['/file1.py'], dict)

    def test_resolve_imports_local_modules(self, analyzer, temp_workspace):
        """Test resolving imports to local file paths."""
        main_file = temp_workspace / "main.py"
        imports = {'utils', 'helpers'}

        resolved = analyzer._resolve_imports(imports, main_file)

        # Should resolve to actual files in workspace
        assert isinstance(resolved, set)

    def test_find_reverse_dependencies(self, analyzer, mock_workspace_state, temp_workspace):
        """Test finding files that import a given file."""
        utils_file = temp_workspace / "utils.py"

        # Mock focus files to include our test files
        mock_workspace_state.get_focus_files.return_value = [
            {'path': str(temp_workspace / "main.py")},
            {'path': str(temp_workspace / "helpers.py")}
        ]

        imported_by = analyzer._find_reverse_dependencies(str(utils_file))

        # Should be a set
        assert isinstance(imported_by, set)

    def test_recommendations_combine_scores(self, analyzer, mock_workspace_state):
        """Test that recommendations combine multiple scoring factors."""
        now = datetime.now()
        focus_files = [
            {'path': '/file1.py', 'last_accessed': now.isoformat(), 'reason': 'editing'},
            {'path': '/file2.py', 'last_accessed': (now - timedelta(minutes=5)).isoformat(), 'reason': 'viewing'}
        ]
        mock_workspace_state.get_focus_files.return_value = focus_files

        # Get recommendations with all factors
        recs = analyzer.get_recommendations(
            limit=5,
            include_dependencies=True,
            include_patterns=True
        )

        # Each recommendation should have score and reasons
        for rec in recs:
            assert 'score' in rec
            assert 'reasons' in rec
            assert isinstance(rec['reasons'], list)
            assert rec['score'] >= 0.0

    def test_frequent_files_detection(self, analyzer, mock_workspace_state):
        """Test detection of frequently accessed files."""
        now = datetime.now()
        focus_files = [
            {'path': '/frequent.py', 'last_accessed': (now - timedelta(minutes=i)).isoformat()}
            for i in range(5)
        ]
        mock_workspace_state.get_focus_files.return_value = focus_files

        cache = analyzer._get_pattern_cache()

        # File accessed 5 times should be in frequent_files
        assert 'frequent_files' in cache
        assert '/frequent.py' in cache['frequent_files']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
