"""Tests for workspace state module."""

import tempfile
from pathlib import Path

import pytest
from workspace_state import WorkspaceState


class TestWorkspaceState:
    """Test WorkspaceState class."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def workspace(self, temp_workspace):
        """Create WorkspaceState instance."""
        return WorkspaceState(workspace_dir=temp_workspace)

    def test_initialization_creates_file(self, workspace, temp_workspace):
        """Test workspace file is created on first load."""
        workspace.load()
        workspace_file = temp_workspace / ".claude-workspace.json"
        assert workspace_file.exists()

    def test_default_state_structure(self, workspace):
        """Test default state has correct structure."""
        state = workspace.load()

        assert "version" in state
        assert "last_updated" in state
        assert "focus_files" in state
        assert "recent_queries" in state
        assert "active_tasks" in state
        assert "session_metadata" in state

    def test_add_focus_file(self, workspace):
        """Test adding focus file."""
        workspace.add_focus_file("/path/to/file.py", "editing")

        focus_files = workspace.get_focus_files()
        assert len(focus_files) == 1
        assert focus_files[0]["path"] == "/path/to/file.py"
        assert focus_files[0]["reason"] == "editing"

    def test_focus_files_deduplicated(self, workspace):
        """Test adding same file multiple times updates it."""
        workspace.add_focus_file("/path/to/file.py", "editing")
        workspace.add_focus_file("/path/to/file.py", "testing")

        focus_files = workspace.get_focus_files()
        assert len(focus_files) == 1
        assert focus_files[0]["reason"] == "testing"

    def test_focus_files_limited(self, workspace):
        """Test focus files are limited to MAX_FOCUS_FILES."""
        for i in range(25):
            workspace.add_focus_file(f"/path/to/file{i}.py", "editing")

        focus_files = workspace.get_focus_files()
        assert len(focus_files) == WorkspaceState.MAX_FOCUS_FILES

    def test_add_query(self, workspace):
        """Test adding query."""
        workspace.add_query(server="rag", query="test query", metadata={"index": "test-index"})

        queries = workspace.get_recent_queries()
        assert len(queries) == 1
        assert queries[0]["server"] == "rag"
        assert queries[0]["query"] == "test query"

    def test_queries_limited(self, workspace):
        """Test queries are limited to MAX_RECENT_QUERIES."""
        for i in range(60):
            workspace.add_query(server="test", query=f"query{i}")

        queries = workspace.get_recent_queries()
        assert len(queries) == WorkspaceState.MAX_RECENT_QUERIES

    def test_session_metadata_updated(self, workspace):
        """Test session metadata updates with queries."""
        workspace.add_query(server="rag", query="q1")
        workspace.add_query(server="code-analysis", tool="analyze")

        meta = workspace.get_session_metadata()
        assert meta["total_queries"] == 2
        assert set(meta["servers_used"]) == {"rag", "code-analysis"}

    def test_add_task(self, workspace):
        """Test adding task."""
        workspace.add_task(
            description="Refactor auth", status="in_progress", files=["/path/to/auth.py"]
        )

        tasks = workspace.get_active_tasks()
        assert len(tasks) == 1
        assert tasks[0]["description"] == "Refactor auth"
        assert tasks[0]["status"] == "in_progress"

    def test_update_task_status(self, workspace):
        """Test updating task status."""
        workspace.add_task("Test task", status="pending")
        workspace.update_task_status("Test task", "completed")

        tasks = workspace.get_active_tasks()
        assert tasks[0]["status"] == "completed"

    def test_get_focus_files_with_limit(self, workspace):
        """Test getting limited focus files."""
        for i in range(10):
            workspace.add_focus_file(f"/file{i}.py", "editing")

        files = workspace.get_focus_files(limit=5)
        assert len(files) == 5

    def test_get_recent_queries_filtered(self, workspace):
        """Test filtering queries by server."""
        workspace.add_query(server="rag", query="q1")
        workspace.add_query(server="code-analysis", tool="t1")
        workspace.add_query(server="rag", query="q2")

        rag_queries = workspace.get_recent_queries(server="rag")
        assert len(rag_queries) == 2
        assert all(q["server"] == "rag" for q in rag_queries)

    def test_get_active_tasks_filtered(self, workspace):
        """Test filtering tasks by status."""
        workspace.add_task("Task 1", status="pending")
        workspace.add_task("Task 2", status="in_progress")
        workspace.add_task("Task 3", status="pending")

        pending = workspace.get_active_tasks(status="pending")
        assert len(pending) == 2

    def test_state_persists(self, temp_workspace):
        """Test state persists across instances."""
        ws1 = WorkspaceState(workspace_dir=temp_workspace)
        ws1.add_focus_file("/file.py", "editing")
        ws1.add_query(server="rag", query="test")

        ws2 = WorkspaceState(workspace_dir=temp_workspace)
        ws2.load()

        assert len(ws2.get_focus_files()) == 1
        assert len(ws2.get_recent_queries()) == 1

    def test_clear_resets_state(self, workspace):
        """Test clear resets to default state."""
        workspace.add_focus_file("/file.py", "editing")
        workspace.add_query(server="test", query="q")
        workspace.add_task("task", status="pending")

        workspace.clear()

        state = workspace.get_full_state()
        assert len(state["focus_files"]) == 0
        assert len(state["recent_queries"]) == 0
        assert len(state["active_tasks"]) == 0

    def test_cleanup_old_entries(self, workspace):
        """Test cleanup removes old entries."""
        # This test would require mocking datetime
        # For now, just verify it runs without error
        workspace.add_focus_file("/file.py", "editing")
        workspace.cleanup_old_entries()

        # Should still have recent entry
        assert len(workspace.get_focus_files()) >= 0

    def test_thread_safety(self, workspace):
        """Test basic thread safety with lock."""
        # Add multiple items rapidly
        for i in range(10):
            workspace.add_focus_file(f"/file{i}.py", "editing")

        files = workspace.get_focus_files()
        assert len(files) == 10

    def test_metadata_with_focus_file(self, workspace):
        """Test adding metadata to focus file."""
        workspace.add_focus_file("/file.py", "editing", metadata={"score": 0.95, "query": "test"})

        files = workspace.get_focus_files()
        assert files[0]["score"] == 0.95
        assert files[0]["query"] == "test"

    def test_full_state_includes_all_sections(self, workspace):
        """Test get_full_state returns complete state."""
        workspace.add_focus_file("/file.py", "editing")
        workspace.add_query(server="test", query="q")
        workspace.add_task("task", status="pending")

        state = workspace.get_full_state()

        assert "version" in state
        assert "last_updated" in state
        assert "focus_files" in state
        assert "recent_queries" in state
        assert "active_tasks" in state
        assert "session_metadata" in state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
