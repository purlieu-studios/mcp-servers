"""Tests for analysis cache module."""

import pytest
import json
import tempfile
from pathlib import Path
from src.analysis_cache import AnalysisCache


pytestmark = pytest.mark.unit


class TestAnalysisCache:
    """Test AnalysisCache class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance with temporary directory."""
        return AnalysisCache(cache_dir=temp_cache_dir)

    @pytest.fixture
    def sample_file(self, temp_cache_dir):
        """Create a sample Python file for testing."""
        file_path = temp_cache_dir / "sample.py"
        file_path.write_text("def hello():\n    return 'world'\n")
        return file_path

    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initialization creates directory."""
        cache = AnalysisCache(cache_dir=temp_cache_dir / "new_cache")
        assert cache.cache_dir.exists()
        assert cache.stats == {"hits": 0, "misses": 0, "saves": 0}

    def test_cache_miss_returns_none(self, cache, sample_file):
        """Test cache miss returns None."""
        result = cache.get(sample_file, "complexity")
        assert result is None
        assert cache.stats["misses"] == 1
        assert cache.stats["hits"] == 0

    def test_cache_hit_returns_result(self, cache, sample_file):
        """Test cache hit returns stored result."""
        # Store result
        test_result = {"complexity": 5, "functions": ["hello"]}
        cache.set(sample_file, "complexity", test_result)

        # Retrieve result
        cached = cache.get(sample_file, "complexity")
        assert cached == test_result
        assert cache.stats["hits"] == 1
        assert cache.stats["saves"] == 1

    def test_cache_invalidates_on_file_change(self, cache, sample_file):
        """Test cache invalidates when file content changes."""
        # Store result for original file
        test_result = {"complexity": 5}
        cache.set(sample_file, "complexity", test_result)

        # Verify cache hit
        cached = cache.get(sample_file, "complexity")
        assert cached == test_result

        # Modify file
        sample_file.write_text("def goodbye():\n    return 'world'\n")

        # Should be cache miss now
        cached_after_change = cache.get(sample_file, "complexity")
        assert cached_after_change is None
        assert cache.stats["misses"] == 1

    def test_different_analysis_types_cached_separately(self, cache, sample_file):
        """Test different analysis types have separate cache entries."""
        complexity_result = {"complexity": 5}
        smells_result = {"smells": []}

        cache.set(sample_file, "complexity", complexity_result)
        cache.set(sample_file, "smells", smells_result)

        assert cache.get(sample_file, "complexity") == complexity_result
        assert cache.get(sample_file, "smells") == smells_result

    def test_cache_persists_to_disk(self, temp_cache_dir, sample_file):
        """Test cache persists between instances."""
        # Create first cache instance and store result
        cache1 = AnalysisCache(cache_dir=temp_cache_dir)
        test_result = {"complexity": 10}
        cache1.set(sample_file, "complexity", test_result)

        # Create second cache instance (simulates restart)
        cache2 = AnalysisCache(cache_dir=temp_cache_dir)
        cached = cache2.get(sample_file, "complexity")

        assert cached == test_result

    def test_get_stats_returns_correct_data(self, cache, sample_file):
        """Test get_stats returns accurate statistics."""
        # Make some cache operations
        cache.get(sample_file, "complexity")  # miss
        cache.set(sample_file, "complexity", {"result": 1})  # save
        cache.get(sample_file, "complexity")  # hit
        cache.get(sample_file, "smells")  # miss

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["saves"] == 1
        assert stats["hit_rate_percent"] == 33.33
        assert stats["cache_entries"] >= 1
        assert "cache_dir" in stats

    def test_clear_cache_removes_all_entries(self, cache, sample_file):
        """Test clear_cache removes all entries."""
        # Store multiple results
        cache.set(sample_file, "complexity", {"result": 1})
        cache.set(sample_file, "smells", {"result": 2})

        stats_before = cache.get_stats()
        assert stats_before["cache_entries"] >= 2

        # Clear cache
        cleared = cache.clear()
        assert cleared >= 2

        stats_after = cache.get_stats()
        assert stats_after["cache_entries"] == 0

    def test_clear_cache_with_age_filter(self, temp_cache_dir, sample_file):
        """Test clear_cache with age filter."""
        cache = AnalysisCache(cache_dir=temp_cache_dir)

        # Create a cache entry
        cache.set(sample_file, "complexity", {"result": 1})

        # Clear entries older than 30 days (should not clear recent entry)
        cleared = cache.clear(older_than_days=30)
        assert cleared == 0

        stats = cache.get_stats()
        assert stats["cache_entries"] == 1

    def test_cache_handles_missing_file(self, cache, temp_cache_dir):
        """Test cache handles non-existent files gracefully."""
        missing_file = temp_cache_dir / "nonexistent.py"

        # Should return None without error
        result = cache.get(missing_file, "complexity")
        assert result is None

        # Should not crash when setting
        cache.set(missing_file, "complexity", {"result": 1})

    def test_cache_handles_corrupt_cache_file(self, cache, sample_file, temp_cache_dir):
        """Test cache handles corrupted cache files."""
        # Create a valid cache entry
        cache.set(sample_file, "complexity", {"result": 1})

        # Corrupt the cache file
        cache_files = list(temp_cache_dir.glob("*.json"))
        assert len(cache_files) >= 1

        with open(cache_files[0], 'w') as f:
            f.write("invalid json {{{")

        # Should handle corruption gracefully
        result = cache.get(sample_file, "complexity")
        assert result is None
        assert cache.stats["misses"] == 1

    def test_cache_key_includes_file_content_hash(self, cache, sample_file):
        """Test cache key changes when file content changes."""
        # Get initial cache key
        key1 = cache._cache_key(sample_file, "complexity")

        # Modify file
        sample_file.write_text("def modified():\n    pass\n")

        # Get new cache key
        key2 = cache._cache_key(sample_file, "complexity")

        # Keys should be different
        assert key1 != key2

    def test_multiple_files_cached_independently(self, cache, temp_cache_dir):
        """Test multiple files are cached independently."""
        file1 = temp_cache_dir / "file1.py"
        file2 = temp_cache_dir / "file2.py"

        file1.write_text("def func1(): pass")
        file2.write_text("def func2(): pass")

        result1 = {"complexity": 1}
        result2 = {"complexity": 2}

        cache.set(file1, "complexity", result1)
        cache.set(file2, "complexity", result2)

        assert cache.get(file1, "complexity") == result1
        assert cache.get(file2, "complexity") == result2

    def test_cache_stats_hit_rate_calculation(self, cache, sample_file):
        """Test cache hit rate calculation is accurate."""
        # Store a result
        cache.set(sample_file, "complexity", {"result": 1})

        # 3 hits, 2 misses = 60% hit rate
        cache.get(sample_file, "complexity")  # hit
        cache.get(sample_file, "complexity")  # hit
        cache.get(sample_file, "complexity")  # hit
        cache.get(sample_file, "smells")  # miss
        cache.get(sample_file, "ast")  # miss

        stats = cache.get_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats["hit_rate_percent"] == 60.0
