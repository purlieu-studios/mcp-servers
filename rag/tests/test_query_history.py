"""Tests for query history module."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from src.query_history import QueryHistory


pytestmark = pytest.mark.unit


class TestQueryHistory:
    """Test QueryHistory class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test_history.db"
            yield db_path
            # Force close any lingering connections on Windows
            import gc
            gc.collect()

    @pytest.fixture
    def history(self, temp_db):
        """Create QueryHistory instance with temporary database."""
        hist = QueryHistory(db_path=temp_db)
        yield hist
        # Ensure all connections are closed
        import gc
        gc.collect()

    @pytest.fixture
    def sample_results(self):
        """Create sample query results."""
        return [
            {
                'index': 'test-index',
                'file': '/path/to/file1.py',
                'text': 'def authenticate_user(username, password):\n    ...',
                'score': 0.95,
                'location': '100-200'
            },
            {
                'index': 'test-index',
                'file': '/path/to/file2.py',
                'text': 'class UserAuth:\n    ...',
                'score': 0.87,
                'location': '50-150'
            }
        ]

    def test_initialization_creates_database(self, temp_db):
        """Test database initialization creates schema."""
        history = QueryHistory(db_path=temp_db)
        assert temp_db.exists()

        # Verify schema was created
        import sqlite3
        import gc
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='query_history'"
            )
            assert cursor.fetchone() is not None

        # Force cleanup of connections
        del history
        gc.collect()

    def test_save_query_stores_data(self, history, sample_results):
        """Test saving query stores all data correctly."""
        query_id = history.save_query(
            query="authentication logic",
            results=sample_results,
            index_name="test-index",
            top_k=5,
            min_score=0.5,
            include_keywords=True,
            duration_ms=150
        )

        assert query_id > 0

        # Retrieve and verify
        entry = history.get_query_by_id(query_id)
        assert entry is not None
        assert entry['query'] == "authentication logic"
        assert entry['index_name'] == "test-index"
        assert entry['top_k'] == 5
        assert entry['min_score'] == 0.5
        assert entry['include_keywords'] is True
        assert entry['result_count'] == 2
        assert entry['duration_ms'] == 150
        assert len(entry['results']) == 2

    def test_get_history_returns_recent_queries(self, history, sample_results):
        """Test get_history returns queries in reverse chronological order."""
        # Save multiple queries
        history.save_query("query 1", sample_results, index_name="index1")
        history.save_query("query 2", sample_results, index_name="index2")
        history.save_query("query 3", sample_results, index_name="index1")

        # Get history
        result = history.get_history(limit=10)

        assert len(result) == 3
        assert result[0]['query'] == "query 3"  # Most recent first
        assert result[1]['query'] == "query 2"
        assert result[2]['query'] == "query 1"

    def test_get_history_limits_results(self, history, sample_results):
        """Test get_history respects limit parameter."""
        # Save 5 queries
        for i in range(5):
            history.save_query(f"query {i}", sample_results)

        # Request only 3
        result = history.get_history(limit=3)
        assert len(result) == 3

    def test_get_history_filters_by_index(self, history, sample_results):
        """Test get_history filters by index name."""
        history.save_query("query 1", sample_results, index_name="index1")
        history.save_query("query 2", sample_results, index_name="index2")
        history.save_query("query 3", sample_results, index_name="index1")

        # Filter by index1
        result = history.get_history(index_name="index1")
        assert len(result) == 2
        assert all(entry['index_name'] == "index1" for entry in result)

    def test_get_history_excludes_results_by_default(self, history, sample_results):
        """Test get_history excludes full results unless requested."""
        history.save_query("test query", sample_results)

        # Without include_results
        result = history.get_history()
        assert 'results' not in result[0]

        # With include_results
        result = history.get_history(include_results=True)
        assert 'results' in result[0]
        assert len(result[0]['results']) == 2

    def test_get_query_by_id_returns_full_data(self, history, sample_results):
        """Test get_query_by_id returns complete query data."""
        query_id = history.save_query("test query", sample_results, duration_ms=100)

        entry = history.get_query_by_id(query_id)
        assert entry is not None
        assert entry['id'] == query_id
        assert entry['query'] == "test query"
        assert 'results' in entry
        assert len(entry['results']) == 2

    def test_get_query_by_id_returns_none_for_invalid_id(self, history):
        """Test get_query_by_id returns None for non-existent query."""
        entry = history.get_query_by_id(9999)
        assert entry is None

    def test_search_history_finds_matching_queries(self, history, sample_results):
        """Test search_history finds queries by search term."""
        history.save_query("authentication logic", sample_results)
        history.save_query("database connection", sample_results)
        history.save_query("user authentication", sample_results)

        # Search for "auth"
        results = history.search_history("auth")
        assert len(results) == 2
        assert all("auth" in entry['query'].lower() for entry in results)

    def test_search_history_is_case_insensitive(self, history, sample_results):
        """Test search_history is case insensitive."""
        history.save_query("Authentication Logic", sample_results)

        results = history.search_history("authentication")
        assert len(results) == 1

        results = history.search_history("AUTHENTICATION")
        assert len(results) == 1

    def test_get_stats_returns_accurate_statistics(self, history, sample_results):
        """Test get_stats returns correct statistics."""
        # Save queries with different result counts
        history.save_query("query 1", sample_results[:1], duration_ms=100)
        history.save_query("query 2", sample_results, duration_ms=200)
        history.save_query("query 3", sample_results, duration_ms=150, index_name="index1")

        stats = history.get_stats()

        assert stats['total_queries'] == 3
        assert stats['avg_results_per_query'] == pytest.approx(1.67, 0.1)
        assert stats['avg_duration_ms'] == pytest.approx(150.0, 0.1)
        assert 'last_query_time' in stats
        assert 'queries_by_index' in stats

    def test_get_stats_handles_empty_history(self, history):
        """Test get_stats handles empty database."""
        stats = history.get_stats()

        assert stats['total_queries'] == 0
        assert stats['avg_results_per_query'] == 0
        assert stats['avg_duration_ms'] == 0

    def test_clear_history_removes_all_entries(self, history, sample_results):
        """Test clear_history removes all queries."""
        # Save multiple queries
        history.save_query("query 1", sample_results)
        history.save_query("query 2", sample_results)
        history.save_query("query 3", sample_results)

        # Clear all
        deleted = history.clear_history()
        assert deleted == 3

        # Verify empty
        result = history.get_history()
        assert len(result) == 0

    def test_clear_history_with_age_filter(self, history, sample_results):
        """Test clear_history with age filter removes only old entries."""
        # This test requires time manipulation or mocking
        # For now, we'll test that the function runs without error
        history.save_query("recent query", sample_results)

        # Clear entries older than 30 days (should not delete recent query)
        deleted = history.clear_history(older_than_days=30)
        assert deleted == 0

        # Verify query still exists
        result = history.get_history()
        assert len(result) == 1

    def test_results_stored_as_json(self, history, sample_results):
        """Test results are properly serialized and deserialized."""
        query_id = history.save_query("test", sample_results)

        entry = history.get_query_by_id(query_id)
        results = entry['results']

        # Verify structure is preserved
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]['file'] == sample_results[0]['file']
        assert results[0]['score'] == sample_results[0]['score']

    def test_multiple_indexes_tracked_in_stats(self, history, sample_results):
        """Test statistics track queries by index."""
        history.save_query("q1", sample_results, index_name="index1")
        history.save_query("q2", sample_results, index_name="index1")
        history.save_query("q3", sample_results, index_name="index2")
        history.save_query("q4", sample_results)  # No index (all)

        stats = history.get_stats()
        by_index = stats['queries_by_index']

        assert by_index['index1'] == 2
        assert by_index['index2'] == 1
        assert by_index['all'] == 1

    def test_timestamp_format_is_iso(self, history, sample_results):
        """Test timestamps are stored in ISO format."""
        query_id = history.save_query("test", sample_results)

        entry = history.get_query_by_id(query_id)
        timestamp = entry['timestamp']

        # Should be parseable as datetime
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

    def test_query_history_persists_across_instances(self, temp_db, sample_results):
        """Test query history persists between instances."""
        # Create first instance and save query
        history1 = QueryHistory(db_path=temp_db)
        query_id = history1.save_query("persistent query", sample_results)

        # Create second instance (simulates restart)
        history2 = QueryHistory(db_path=temp_db)
        entry = history2.get_query_by_id(query_id)

        assert entry is not None
        assert entry['query'] == "persistent query"

    def test_handles_empty_results(self, history):
        """Test saving query with no results."""
        query_id = history.save_query("no results", [], index_name="test")

        entry = history.get_query_by_id(query_id)
        assert entry['result_count'] == 0
        assert len(entry['results']) == 0

    def test_handles_none_index_name(self, history, sample_results):
        """Test handling queries without index name."""
        query_id = history.save_query("query", sample_results, index_name=None)

        entry = history.get_query_by_id(query_id)
        assert entry['index_name'] is None

    def test_handles_none_duration(self, history, sample_results):
        """Test handling queries without duration measurement."""
        query_id = history.save_query("query", sample_results, duration_ms=None)

        entry = history.get_query_by_id(query_id)
        assert entry['duration_ms'] is None
