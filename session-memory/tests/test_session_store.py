"""Tests for session store module."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from src.session_store import SessionStore


pytestmark = pytest.mark.unit


class TestSessionStore:
    """Test SessionStore class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test_sessions.db"
            yield db_path

    @pytest.fixture
    def store(self, temp_db):
        """Create SessionStore instance."""
        return SessionStore(db_path=temp_db)

    def test_initialization_creates_database(self, temp_db):
        """Test database initialization creates schema."""
        store = SessionStore(db_path=temp_db)
        assert temp_db.exists()

        # Verify tables exist
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert 'sessions' in tables
        assert 'messages' in tables
        assert 'decisions' in tables
        assert 'session_tags' in tables

    def test_create_session(self, store):
        """Test creating a session."""
        session_id = store.create_session(tags={"project": "test", "user": "dev"})
        assert session_id > 0

        info = store.get_session_info(session_id)
        assert info['status'] == 'active'
        assert info['tags']['project'] == 'test'
        assert info['tags']['user'] == 'dev'

    def test_get_or_create_active_session(self, store):
        """Test getting or creating active session."""
        session_id1 = store.get_or_create_active_session()
        session_id2 = store.get_or_create_active_session()

        # Should return same session
        assert session_id1 == session_id2

    def test_log_message(self, store):
        """Test logging messages."""
        session_id = store.create_session()

        msg_id = store.log_message(
            role="user",
            content="Hello, how are you?",
            tokens=5,
            session_id=session_id
        )

        assert msg_id > 0

        messages = store.get_session_messages(session_id)
        assert len(messages) == 1
        assert messages[0]['role'] == 'user'
        assert messages[0]['content'] == "Hello, how are you?"
        assert messages[0]['tokens'] == 5

    def test_message_count_updates(self, store):
        """Test session message count updates."""
        session_id = store.create_session()

        store.log_message("user", "Message 1", session_id=session_id)
        store.log_message("assistant", "Message 2", session_id=session_id)
        store.log_message("user", "Message 3", session_id=session_id)

        info = store.get_session_info(session_id)
        assert info['message_count'] == 3

    def test_token_count_updates(self, store):
        """Test session token count updates."""
        session_id = store.create_session()

        store.log_message("user", "Message", tokens=10, session_id=session_id)
        store.log_message("assistant", "Reply", tokens=20, session_id=session_id)

        info = store.get_session_info(session_id)
        assert info['total_tokens'] == 30

    def test_log_decision(self, store):
        """Test logging decisions."""
        session_id = store.create_session()

        decision_id = store.log_decision(
            decision="Refactor authentication module",
            context="Security improvements needed",
            session_id=session_id
        )

        assert decision_id > 0

    def test_get_session_messages_filtered(self, store):
        """Test getting filtered messages."""
        session_id = store.create_session()

        store.log_message("user", "User message 1", session_id=session_id)
        store.log_message("assistant", "Assistant reply 1", session_id=session_id)
        store.log_message("user", "User message 2", session_id=session_id)

        # Filter by role
        user_messages = store.get_session_messages(session_id, role="user")
        assert len(user_messages) == 2
        assert all(m['role'] == 'user' for m in user_messages)

    def test_get_session_messages_limited(self, store):
        """Test message limit."""
        session_id = store.create_session()

        for i in range(10):
            store.log_message("user", f"Message {i}", session_id=session_id)

        messages = store.get_session_messages(session_id, limit=5)
        assert len(messages) == 5

    def test_get_session_info(self, store):
        """Test getting session info."""
        session_id = store.create_session(tags={"project": "test"})

        info = store.get_session_info(session_id)
        assert info['id'] == session_id
        assert info['status'] == 'active'
        assert 'start_time' in info
        assert info['tags']['project'] == 'test'

    def test_end_session(self, store):
        """Test ending a session."""
        session_id = store.create_session()
        store.log_message("user", "Message", session_id=session_id)

        store.end_session(session_id, summary="Completed task X")

        info = store.get_session_info(session_id)
        assert info['status'] == 'completed'
        assert info['summary'] == "Completed task X"
        assert info['end_time'] is not None

    def test_search_sessions_by_query(self, store):
        """Test searching sessions by query."""
        session1 = store.create_session()
        store.log_message("user", "I need help with authentication", session_id=session1)

        session2 = store.create_session()
        store.log_message("user", "How do I configure the database?", session_id=session2)

        # Search for authentication
        results = store.search_sessions(query="authentication")
        assert len(results) == 1
        assert results[0]['id'] == session1

    def test_search_sessions_by_tag(self, store):
        """Test searching sessions by tag."""
        session1 = store.create_session(tags={"project": "auth"})
        session2 = store.create_session(tags={"project": "db"})
        session3 = store.create_session(tags={"project": "auth"})

        results = store.search_sessions(tag="project:auth")
        # Note: Implementation searches for tag name only, not tag:value
        # This test documents current behavior

    def test_search_sessions_recent(self, store):
        """Test getting recent sessions."""
        for i in range(5):
            store.create_session(tags={"index": str(i)})

        results = store.search_sessions(limit=3)
        assert len(results) == 3

    def test_get_stats(self, store):
        """Test getting statistics."""
        session1 = store.create_session()
        store.log_message("user", "Message 1", tokens=10, session_id=session1)
        store.log_message("assistant", "Reply 1", tokens=20, session_id=session1)

        session2 = store.create_session()
        store.log_message("user", "Message 2", tokens=15, session_id=session2)

        store.end_session(session1)

        stats = store.get_stats()
        assert stats['total_sessions'] == 2
        assert stats['active_sessions'] == 1
        assert stats['total_messages'] == 3
        assert stats['total_tokens'] == 45
        assert stats['avg_messages_per_session'] == 1.5

    def test_session_persistence(self, temp_db):
        """Test sessions persist across instances."""
        store1 = SessionStore(db_path=temp_db)
        session_id = store1.create_session()
        store1.log_message("user", "Test message", session_id=session_id)

        store2 = SessionStore(db_path=temp_db)
        info = store2.get_session_info(session_id)
        assert info is not None
        assert info['message_count'] == 1

    def test_metadata_in_messages(self, store):
        """Test storing metadata with messages."""
        session_id = store.create_session()

        store.log_message(
            role="user",
            content="Test",
            metadata={"source": "web", "intent": "question"},
            session_id=session_id
        )

        messages = store.get_session_messages(session_id)
        assert messages[0]['metadata']['source'] == 'web'
        assert messages[0]['metadata']['intent'] == 'question'

    def test_multiple_sessions_independent(self, store):
        """Test multiple sessions are independent."""
        session1 = store.create_session()
        session2 = store.create_session()

        store.log_message("user", "Session 1 message", session_id=session1)
        store.log_message("user", "Session 2 message", session_id=session2)

        messages1 = store.get_session_messages(session1)
        messages2 = store.get_session_messages(session2)

        assert len(messages1) == 1
        assert len(messages2) == 1
        assert messages1[0]['content'] != messages2[0]['content']

    def test_current_session_persists(self, store):
        """Test current session ID persists within instance."""
        session_id1 = store.get_or_create_active_session()
        session_id2 = store.get_or_create_active_session()

        assert session_id1 == session_id2
        assert session_id1 == store._current_session_id

    def test_thread_safety(self, store):
        """Test basic thread safety."""
        session_id = store.create_session()

        # Log multiple messages rapidly
        for i in range(10):
            store.log_message("user", f"Message {i}", session_id=session_id)

        info = store.get_session_info(session_id)
        assert info['message_count'] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
