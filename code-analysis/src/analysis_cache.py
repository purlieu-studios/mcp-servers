"""Analysis result caching system for Code Analysis Server.

Caches analysis results based on file content hash to prevent
repeated analysis of unchanged files.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AnalysisCache:
    """Cache for analysis results with file hash-based invalidation."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize cache with storage directory.

        Args:
            cache_dir: Directory for cache storage. Defaults to ~/.code-analysis-cache
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".code-analysis-cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"hits": 0, "misses": 0, "saves": 0}
        logger.info(f"Initialized analysis cache at {self.cache_dir}")

    def _hash_file(self, file_path: Path) -> str:
        """Calculate MD5 hash of file contents.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of file contents
        """
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""

    def _cache_key(self, file_path: Path, analysis_type: str) -> str:
        """Generate cache key from file path, type, and content hash.

        Args:
            file_path: Path to source file
            analysis_type: Type of analysis (complexity, smells, ast, etc.)

        Returns:
            Cache key string
        """
        file_hash = self._hash_file(file_path)
        # Use file name + hash to make keys readable but unique
        return f"{file_path.name}_{analysis_type}_{file_hash}"

    def _cache_file_path(self, cache_key: str) -> Path:
        """Get file path for cache entry.

        Args:
            cache_key: Cache key

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def get(self, file_path: Path, analysis_type: str) -> dict[str, Any] | None:
        """Get cached analysis result if available.

        Args:
            file_path: Path to source file
            analysis_type: Type of analysis

        Returns:
            Cached result dict or None if not found/invalid
        """
        if not file_path.exists():
            return None

        cache_key = self._cache_key(file_path, analysis_type)
        cache_file = self._cache_file_path(cache_key)

        if not cache_file.exists():
            self.stats["misses"] += 1
            logger.debug(f"Cache miss: {cache_key}")
            return None

        try:
            with open(cache_file) as f:
                cached_data = json.load(f)

            # Verify cache metadata
            if "cached_at" not in cached_data or "result" not in cached_data:
                logger.warning(f"Invalid cache format: {cache_key}")
                cache_file.unlink()  # Remove invalid cache
                self.stats["misses"] += 1
                return None

            self.stats["hits"] += 1
            logger.debug(f"Cache hit: {cache_key}")
            return cached_data["result"]

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error reading cache {cache_key}: {e}")
            # Remove corrupt cache file
            try:
                cache_file.unlink()
            except Exception:
                pass
            self.stats["misses"] += 1
            return None

    def set(self, file_path: Path, analysis_type: str, result: dict[str, Any]):
        """Store analysis result in cache.

        Args:
            file_path: Path to source file
            analysis_type: Type of analysis
            result: Analysis result to cache
        """
        if not file_path.exists():
            return

        cache_key = self._cache_key(file_path, analysis_type)
        cache_file = self._cache_file_path(cache_key)

        try:
            cache_data = {
                "file_path": str(file_path),
                "analysis_type": analysis_type,
                "cached_at": datetime.now().isoformat(),
                "result": result,
            }

            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

            self.stats["saves"] += 1
            logger.debug(f"Cached result: {cache_key}")

        except Exception as e:
            logger.error(f"Error saving cache {cache_key}: {e}")

    def clear(self, older_than_days: int | None = None):
        """Clear cache entries.

        Args:
            older_than_days: If specified, only clear entries older than this many days
        """
        cleared = 0
        cutoff_date = None

        if older_than_days is not None:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                if cutoff_date:
                    # Check file modification time
                    mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if mod_time > cutoff_date:
                        continue

                cache_file.unlink()
                cleared += 1

            except Exception as e:
                logger.error(f"Error clearing cache file {cache_file}: {e}")

        logger.info(f"Cleared {cleared} cache entries")
        return cleared

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache stats including hits, misses, hit rate, size
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        # Calculate cache size
        cache_files = list(self.cache_dir.glob("*.json"))
        cache_size_bytes = sum(f.stat().st_size for f in cache_files)
        cache_size_mb = cache_size_bytes / (1024 * 1024)

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "saves": self.stats["saves"],
            "hit_rate_percent": round(hit_rate, 2),
            "cache_entries": len(cache_files),
            "cache_size_mb": round(cache_size_mb, 2),
            "cache_dir": str(self.cache_dir),
        }


# Global cache instance
_cache_instance: AnalysisCache | None = None


def get_cache() -> AnalysisCache:
    """Get or create global cache instance.

    Returns:
        Global AnalysisCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AnalysisCache()
    return _cache_instance
