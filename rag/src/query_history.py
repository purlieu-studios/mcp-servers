"""Query history tracking for RAG server.

Tracks all queries and their results for session replay and context retention.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class QueryHistory:
    """SQLite-based query history tracker."""

    def __init__(self, db_path: Path | None = None):
        """Initialize query history with SQLite database.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.rag-query-history.db
        """
        if db_path is None:
            db_path = Path.home() / ".rag-query-history.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        logger.info(f"Initialized query history at {self.db_path}")

    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    index_name TEXT,
                    top_k INTEGER DEFAULT 5,
                    min_score REAL DEFAULT 0.0,
                    include_keywords BOOLEAN DEFAULT TRUE,
                    result_count INTEGER,
                    results TEXT,  -- JSON array of results
                    timestamp TEXT NOT NULL,
                    duration_ms INTEGER
                )
            """)

            # Create indexes for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON query_history(timestamp DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query
                ON query_history(query)
            """)

            conn.commit()
        finally:
            conn.close()

    def save_query(
        self,
        query: str,
        results: list[dict[str, Any]],
        index_name: str | None = None,
        top_k: int = 5,
        min_score: float = 0.0,
        include_keywords: bool = True,
        duration_ms: int | None = None,
    ) -> int:
        """Save a query and its results to history.

        Args:
            query: Query text
            results: List of result dictionaries
            index_name: Name of index searched
            top_k: Number of results requested
            min_score: Minimum score threshold
            include_keywords: Whether keyword search was included
            duration_ms: Query execution time in milliseconds

        Returns:
            ID of the saved query
        """
        timestamp = datetime.now().isoformat()
        results_json = json.dumps(results)
        result_count = len(results)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                INSERT INTO query_history
                (query, index_name, top_k, min_score, include_keywords,
                 result_count, results, timestamp, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    query,
                    index_name,
                    top_k,
                    min_score,
                    include_keywords,
                    result_count,
                    results_json,
                    timestamp,
                    duration_ms,
                ),
            )
            conn.commit()
            query_id = cursor.lastrowid

            logger.debug(f"Saved query {query_id}: '{query}' with {result_count} results")
            return query_id
        finally:
            conn.close()

    def get_history(
        self, limit: int = 20, index_name: str | None = None, include_results: bool = False
    ) -> list[dict[str, Any]]:
        """Get recent query history.

        Args:
            limit: Maximum number of queries to return
            index_name: Filter by index name
            include_results: Include full result sets in output

        Returns:
            List of query history entries
        """
        query_sql = """
            SELECT id, query, index_name, top_k, min_score, include_keywords,
                   result_count, timestamp, duration_ms
        """

        if include_results:
            query_sql = """
                SELECT id, query, index_name, top_k, min_score, include_keywords,
                       result_count, results, timestamp, duration_ms
            """

        if index_name:
            query_sql += """
                FROM query_history
                WHERE index_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params = (index_name, limit)
        else:
            query_sql += """
                FROM query_history
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params = (limit,)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query_sql, params)
            rows = cursor.fetchall()

            history = []
            for row in rows:
                entry = {
                    "id": row["id"],
                    "query": row["query"],
                    "index_name": row["index_name"],
                    "top_k": row["top_k"],
                    "min_score": row["min_score"],
                    "include_keywords": bool(row["include_keywords"]),
                    "result_count": row["result_count"],
                    "timestamp": row["timestamp"],
                    "duration_ms": row["duration_ms"],
                }

                if include_results:
                    entry["results"] = json.loads(row["results"])

                history.append(entry)

            return history
        finally:
            conn.close()

    def get_query_by_id(self, query_id: int) -> dict[str, Any] | None:
        """Get a specific query by ID.

        Args:
            query_id: Query ID

        Returns:
            Query entry with full results, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, query, index_name, top_k, min_score, include_keywords,
                       result_count, results, timestamp, duration_ms
                FROM query_history
                WHERE id = ?
            """,
                (query_id,),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "id": row["id"],
                "query": row["query"],
                "index_name": row["index_name"],
                "top_k": row["top_k"],
                "min_score": row["min_score"],
                "include_keywords": bool(row["include_keywords"]),
                "result_count": row["result_count"],
                "results": json.loads(row["results"]),
                "timestamp": row["timestamp"],
                "duration_ms": row["duration_ms"],
            }
        finally:
            conn.close()

    def search_history(self, search_term: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search query history by query text.

        Args:
            search_term: Term to search for in queries
            limit: Maximum number of results

        Returns:
            List of matching query history entries
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, query, index_name, top_k, min_score, include_keywords,
                       result_count, timestamp, duration_ms
                FROM query_history
                WHERE query LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (f"%{search_term}%", limit),
            )
            rows = cursor.fetchall()

            return [
                {
                    "id": row["id"],
                    "query": row["query"],
                    "index_name": row["index_name"],
                    "top_k": row["top_k"],
                    "min_score": row["min_score"],
                    "include_keywords": bool(row["include_keywords"]),
                    "result_count": row["result_count"],
                    "timestamp": row["timestamp"],
                    "duration_ms": row["duration_ms"],
                }
                for row in rows
            ]
        finally:
            conn.close()

    def get_stats(self) -> dict[str, Any]:
        """Get query history statistics.

        Returns:
            Statistics about query history
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_queries,
                    AVG(result_count) as avg_results,
                    AVG(duration_ms) as avg_duration_ms,
                    MAX(timestamp) as last_query_time
                FROM query_history
            """)
            row = cursor.fetchone()

            # Get query count by index
            cursor = conn.execute("""
                SELECT index_name, COUNT(*) as count
                FROM query_history
                GROUP BY index_name
                ORDER BY count DESC
            """)
            index_stats = {row[0] or "all": row[1] for row in cursor.fetchall()}

            return {
                "total_queries": row[0],
                "avg_results_per_query": round(row[1], 2) if row[1] else 0,
                "avg_duration_ms": round(row[2], 2) if row[2] else 0,
                "last_query_time": row[3],
                "queries_by_index": index_stats,
                "db_path": str(self.db_path),
            }
        finally:
            conn.close()

    def clear_history(self, older_than_days: int | None = None) -> int:
        """Clear query history.

        Args:
            older_than_days: Only clear queries older than N days

        Returns:
            Number of queries deleted
        """
        conn = sqlite3.connect(self.db_path)
        try:
            if older_than_days is None:
                cursor = conn.execute("DELETE FROM query_history")
                deleted = cursor.rowcount
                conn.commit()
            else:
                from datetime import timedelta

                cutoff_date = (datetime.now() - timedelta(days=older_than_days)).isoformat()

                cursor = conn.execute(
                    "DELETE FROM query_history WHERE timestamp < ?", (cutoff_date,)
                )
                deleted = cursor.rowcount
                conn.commit()

            logger.info(f"Cleared {deleted} query history entries")
            return deleted
        finally:
            conn.close()


# Global instance
_history_instance: QueryHistory | None = None


def get_query_history() -> QueryHistory:
    """Get or create global query history instance.

    Returns:
        Global QueryHistory instance
    """
    global _history_instance
    if _history_instance is None:
        _history_instance = QueryHistory()
    return _history_instance
