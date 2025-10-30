"""Session memory storage for conversation history and context retention.

Tracks conversation messages, session boundaries, and key decisions to maintain
context across Claude Code restarts.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class SessionStore:
    """SQLite-based session memory storage."""

    def __init__(self, db_path: Path | None = None):
        """Initialize session store.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.claude-session-memory.db
        """
        if db_path is None:
            db_path = Path.home() / ".claude-session-memory.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._current_session_id: int | None = None

        self._init_database()
        logger.info(f"Initialized session store at {self.db_path}")

    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT DEFAULT 'active',
                    summary TEXT,
                    message_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0
                )
            """)

            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tokens INTEGER DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)

            # Decisions table (for tracking key decisions/actions)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    decision TEXT NOT NULL,
                    context TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)

            # Session tags table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    value TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time DESC)"
            )

            conn.commit()
        finally:
            conn.close()

    def create_session(self, tags: dict[str, str] | None = None) -> int:
        """Create a new session.

        Args:
            tags: Optional tags for the session

        Returns:
            Session ID
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO sessions (start_time, status)
                    VALUES (?, 'active')
                """,
                    (datetime.now().isoformat(),),
                )
                session_id = cursor.lastrowid

                # Add tags if provided
                if tags:
                    for tag, value in tags.items():
                        conn.execute(
                            """
                            INSERT INTO session_tags (session_id, tag, value)
                            VALUES (?, ?, ?)
                        """,
                            (session_id, tag, value),
                        )

                conn.commit()
                self._current_session_id = session_id
                logger.info(f"Created new session: {session_id}")
                return session_id
            finally:
                conn.close()

    def get_or_create_active_session(self) -> int:
        """Get current active session or create new one.

        Returns:
            Session ID
        """
        with self._lock:
            if self._current_session_id is not None:
                return self._current_session_id

            conn = sqlite3.connect(self.db_path)
            try:
                # Check for recent active session (within last 30 minutes)
                cutoff = (datetime.now() - timedelta(minutes=30)).isoformat()
                cursor = conn.execute(
                    """
                    SELECT id FROM sessions
                    WHERE status = 'active' AND start_time > ?
                    ORDER BY start_time DESC LIMIT 1
                """,
                    (cutoff,),
                )
                row = cursor.fetchone()

                if row:
                    self._current_session_id = row[0]
                    logger.info(f"Resuming session: {self._current_session_id}")
                else:
                    # Create new session
                    cursor = conn.execute(
                        """
                        INSERT INTO sessions (start_time, status)
                        VALUES (?, 'active')
                    """,
                        (datetime.now().isoformat(),),
                    )
                    self._current_session_id = cursor.lastrowid
                    conn.commit()
                    logger.info(f"Created new session: {self._current_session_id}")

                return self._current_session_id
            finally:
                conn.close()

    def log_message(
        self,
        role: str,
        content: str,
        tokens: int = 0,
        metadata: dict[str, Any] | None = None,
        session_id: int | None = None,
    ) -> int:
        """Log a conversation message.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            tokens: Token count
            metadata: Additional metadata
            session_id: Session ID (uses current if not specified)

        Returns:
            Message ID
        """
        if session_id is None:
            session_id = self.get_or_create_active_session()

        conn = sqlite3.connect(self.db_path)
        try:
            metadata_json = json.dumps(metadata) if metadata else None

            cursor = conn.execute(
                """
                INSERT INTO messages (session_id, role, content, timestamp, tokens, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (session_id, role, content, datetime.now().isoformat(), tokens, metadata_json),
            )

            message_id = cursor.lastrowid

            # Update session stats
            conn.execute(
                """
                UPDATE sessions
                SET message_count = message_count + 1,
                    total_tokens = total_tokens + ?
                WHERE id = ?
            """,
                (tokens, session_id),
            )

            conn.commit()
            logger.debug(f"Logged message {message_id} to session {session_id}")
            return message_id
        finally:
            conn.close()

    def log_decision(
        self, decision: str, context: str | None = None, session_id: int | None = None
    ) -> int:
        """Log a key decision or action.

        Args:
            decision: Decision description
            context: Additional context
            session_id: Session ID (uses current if not specified)

        Returns:
            Decision ID
        """
        if session_id is None:
            session_id = self.get_or_create_active_session()

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                INSERT INTO decisions (session_id, decision, context, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (session_id, decision, context, datetime.now().isoformat()),
            )

            conn.commit()
            decision_id = cursor.lastrowid
            logger.debug(f"Logged decision {decision_id} to session {session_id}")
            return decision_id
        finally:
            conn.close()

    def get_session_messages(
        self, session_id: int | None = None, limit: int | None = None, role: str | None = None
    ) -> list[dict[str, Any]]:
        """Get messages from a session.

        Args:
            session_id: Session ID (uses current if not specified)
            limit: Maximum number of messages
            role: Filter by role

        Returns:
            List of message dictionaries
        """
        if session_id is None:
            session_id = self.get_or_create_active_session()

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM messages WHERE session_id = ?"
            params = [session_id]

            if role:
                query += " AND role = ?"
                params.append(role)

            query += " ORDER BY timestamp DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            messages = []
            for row in rows:
                msg = {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                    "tokens": row["tokens"],
                }
                if row["metadata"]:
                    msg["metadata"] = json.loads(row["metadata"])
                messages.append(msg)

            return messages
        finally:
            conn.close()

    def get_session_info(self, session_id: int | None = None) -> dict[str, Any] | None:
        """Get session information.

        Args:
            session_id: Session ID (uses current if not specified)

        Returns:
            Session information dictionary or None
        """
        if session_id is None:
            session_id = self._current_session_id or self.get_or_create_active_session()

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM sessions WHERE id = ?
            """,
                (session_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            # Get tags
            cursor = conn.execute(
                """
                SELECT tag, value FROM session_tags WHERE session_id = ?
            """,
                (session_id,),
            )
            tags = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "id": row["id"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "status": row["status"],
                "summary": row["summary"],
                "message_count": row["message_count"],
                "total_tokens": row["total_tokens"],
                "tags": tags,
            }
        finally:
            conn.close()

    def search_sessions(
        self, query: str | None = None, tag: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search sessions.

        Args:
            query: Search query (searches messages and decisions)
            tag: Filter by tag
            limit: Maximum results

        Returns:
            List of session info dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            if query:
                # Search in messages and decisions
                cursor = conn.execute(
                    """
                    SELECT DISTINCT s.* FROM sessions s
                    LEFT JOIN messages m ON s.id = m.session_id
                    LEFT JOIN decisions d ON s.id = d.session_id
                    WHERE m.content LIKE ? OR d.decision LIKE ?
                    ORDER BY s.start_time DESC LIMIT ?
                """,
                    (f"%{query}%", f"%{query}%", limit),
                )
            elif tag:
                # Filter by tag
                cursor = conn.execute(
                    """
                    SELECT s.* FROM sessions s
                    JOIN session_tags st ON s.id = st.session_id
                    WHERE st.tag = ?
                    ORDER BY s.start_time DESC LIMIT ?
                """,
                    (tag, limit),
                )
            else:
                # Return recent sessions
                cursor = conn.execute(
                    """
                    SELECT * FROM sessions
                    ORDER BY start_time DESC LIMIT ?
                """,
                    (limit,),
                )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def end_session(self, session_id: int | None = None, summary: str | None = None):
        """End a session.

        Args:
            session_id: Session ID (uses current if not specified)
            summary: Optional session summary
        """
        if session_id is None:
            session_id = self._current_session_id

        if session_id is None:
            return

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                UPDATE sessions
                SET end_time = ?, status = 'completed', summary = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), summary, session_id),
            )
            conn.commit()

            if session_id == self._current_session_id:
                self._current_session_id = None

            logger.info(f"Ended session: {session_id}")
        finally:
            conn.close()

    def get_stats(self) -> dict[str, Any]:
        """Get session statistics.

        Returns:
            Statistics dictionary
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
                    SUM(message_count) as total_messages,
                    SUM(total_tokens) as total_tokens,
                    AVG(message_count) as avg_messages_per_session
                FROM sessions
            """)
            row = cursor.fetchone()

            return {
                "total_sessions": row[0] or 0,
                "active_sessions": row[1] or 0,
                "total_messages": row[2] or 0,
                "total_tokens": row[3] or 0,
                "avg_messages_per_session": round(row[4], 2) if row[4] else 0,
                "db_path": str(self.db_path),
            }
        finally:
            conn.close()


# Global instance
_store_instance: SessionStore | None = None
_instance_lock = Lock()


def get_session_store(db_path: Path | None = None) -> SessionStore:
    """Get or create global session store instance.

    Args:
        db_path: Database path (only used on first call)

    Returns:
        Global SessionStore instance
    """
    global _store_instance

    with _instance_lock:
        if _store_instance is None:
            _store_instance = SessionStore(db_path=db_path)

        return _store_instance
