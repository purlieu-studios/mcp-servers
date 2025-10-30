"""Workspace state persistence for context retention across Claude Code sessions.

Tracks focus files, recent queries, and active tasks in .claude-workspace.json
for improved context awareness across server restarts.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class WorkspaceState:
    """Manages persistent workspace state across Claude Code sessions."""

    VERSION = "1.0"
    MAX_FOCUS_FILES = 20
    MAX_RECENT_QUERIES = 50
    MAX_ACTIVE_TASKS = 10
    CLEANUP_DAYS = 7

    def __init__(self, workspace_dir: Path | None = None):
        """Initialize workspace state manager.

        Args:
            workspace_dir: Directory containing .claude-workspace.json
                          Defaults to current working directory
        """
        if workspace_dir is None:
            workspace_dir = Path.cwd()

        self.workspace_dir = Path(workspace_dir)
        self.workspace_file = self.workspace_dir / ".claude-workspace.json"
        self._lock = Lock()
        self._state: dict[str, Any] | None = None

        logger.info(f"Initialized workspace state at {self.workspace_file}")

    def _default_state(self) -> dict[str, Any]:
        """Create default workspace state."""
        return {
            "version": self.VERSION,
            "last_updated": datetime.now().isoformat(),
            "focus_files": [],
            "recent_queries": [],
            "active_tasks": [],
            "session_metadata": {
                "session_start": datetime.now().isoformat(),
                "total_queries": 0,
                "servers_used": [],
            },
        }

    def load(self) -> dict[str, Any]:
        """Load workspace state from file.

        Returns:
            Workspace state dictionary
        """
        with self._lock:
            if not self.workspace_file.exists():
                logger.info("No workspace file found, creating new state")
                self._state = self._default_state()
                self._save_unlocked()
                return self._state.copy()

            try:
                with open(self.workspace_file, encoding="utf-8") as f:
                    self._state = json.load(f)

                # Validate version
                if self._state.get("version") != self.VERSION:
                    logger.warning("Workspace version mismatch, resetting")
                    self._state = self._default_state()
                    self._save_unlocked()

                logger.debug(
                    f"Loaded workspace state with {len(self._state.get('focus_files', []))} focus files"
                )
                return self._state.copy()

            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Error loading workspace state: {e}, creating new")
                self._state = self._default_state()
                self._save_unlocked()
                return self._state.copy()

    def save(self, state: dict[str, Any] | None = None):
        """Save workspace state to file.

        Args:
            state: State to save. If None, saves current state.
        """
        with self._lock:
            if state is not None:
                self._state = state

            if self._state is None:
                self._state = self._default_state()

            self._state["last_updated"] = datetime.now().isoformat()
            self._save_unlocked()

    def _save_unlocked(self):
        """Save state without acquiring lock (internal use)."""
        if self._state is None:
            return

        try:
            with open(self.workspace_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2, ensure_ascii=False)
            logger.debug("Saved workspace state")
        except Exception as e:
            logger.error(f"Error saving workspace state: {e}")

    def add_focus_file(
        self, file_path: str, reason: str = "viewing", metadata: dict[str, Any] | None = None
    ):
        """Add file to focus list.

        Args:
            file_path: Path to file
            reason: Reason for focus (editing, testing, analyzing, etc.)
            metadata: Additional metadata
        """
        with self._lock:
            if self._state is None:
                self._state = self.load()

            focus_files = self._state.setdefault("focus_files", [])

            # Remove if already exists
            focus_files = [f for f in focus_files if f["path"] != file_path]

            # Add new entry
            entry = {
                "path": file_path,
                "last_accessed": datetime.now().isoformat(),
                "reason": reason,
            }
            if metadata:
                entry.update(metadata)

            focus_files.insert(0, entry)

            # Limit size
            self._state["focus_files"] = focus_files[: self.MAX_FOCUS_FILES]
            self._save_unlocked()

        logger.debug(f"Added focus file: {file_path} ({reason})")

    def add_query(
        self,
        server: str,
        query: str | None = None,
        tool: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Add query to recent queries.

        Args:
            server: Server name (rag, code-analysis, efcore-analysis)
            query: Query text (for rag server)
            tool: Tool name (for other servers)
            metadata: Additional metadata
        """
        with self._lock:
            if self._state is None:
                self._state = self.load()

            recent_queries = self._state.setdefault("recent_queries", [])

            entry = {"server": server, "timestamp": datetime.now().isoformat()}
            if query:
                entry["query"] = query
            if tool:
                entry["tool"] = tool
            if metadata:
                entry.update(metadata)

            recent_queries.insert(0, entry)

            # Limit size
            self._state["recent_queries"] = recent_queries[: self.MAX_RECENT_QUERIES]

            # Update session metadata
            session_meta = self._state.setdefault("session_metadata", {})
            session_meta["total_queries"] = session_meta.get("total_queries", 0) + 1

            servers_used = set(session_meta.get("servers_used", []))
            servers_used.add(server)
            session_meta["servers_used"] = sorted(servers_used)

            self._save_unlocked()

        logger.debug(f"Added query: {server} - {query or tool}")

    def add_task(
        self,
        description: str,
        status: str = "pending",
        files: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Add active task.

        Args:
            description: Task description
            status: Task status (pending, in_progress, completed)
            files: Related files
            metadata: Additional metadata
        """
        with self._lock:
            if self._state is None:
                self._state = self.load()

            active_tasks = self._state.setdefault("active_tasks", [])

            entry = {
                "description": description,
                "status": status,
                "created": datetime.now().isoformat(),
                "files": files or [],
            }
            if metadata:
                entry.update(metadata)

            active_tasks.append(entry)

            # Limit size (keep only non-completed or recent completed)
            active_tasks = [
                t
                for t in active_tasks
                if t["status"] != "completed" or self._is_recent(t.get("created"))
            ]
            self._state["active_tasks"] = active_tasks[: self.MAX_ACTIVE_TASKS]

            self._save_unlocked()

        logger.debug(f"Added task: {description} ({status})")

    def update_task_status(self, description: str, status: str):
        """Update task status.

        Args:
            description: Task description (must match existing task)
            status: New status
        """
        with self._lock:
            if self._state is None:
                self._state = self.load()

            active_tasks = self._state.get("active_tasks", [])

            for task in active_tasks:
                if task["description"] == description:
                    task["status"] = status
                    task["updated"] = datetime.now().isoformat()
                    break

            self._save_unlocked()

        logger.debug(f"Updated task status: {description} -> {status}")

    def get_focus_files(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get focus files.

        Args:
            limit: Maximum number to return

        Returns:
            List of focus file entries
        """
        with self._lock:
            if self._state is None:
                self._state = self.load()

            focus_files = self._state.get("focus_files", [])
            if limit:
                return focus_files[:limit]
            return focus_files.copy()

    def get_recent_queries(
        self, server: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Get recent queries.

        Args:
            server: Filter by server name
            limit: Maximum number to return

        Returns:
            List of query entries
        """
        with self._lock:
            if self._state is None:
                self._state = self.load()

            queries = self._state.get("recent_queries", [])

            if server:
                queries = [q for q in queries if q.get("server") == server]

            if limit:
                return queries[:limit]
            return queries.copy()

    def get_active_tasks(self, status: str | None = None) -> list[dict[str, Any]]:
        """Get active tasks.

        Args:
            status: Filter by status

        Returns:
            List of task entries
        """
        with self._lock:
            if self._state is None:
                self._state = self.load()

            tasks = self._state.get("active_tasks", [])

            if status:
                tasks = [t for t in tasks if t.get("status") == status]

            return tasks.copy()

    def get_session_metadata(self) -> dict[str, Any]:
        """Get session metadata.

        Returns:
            Session metadata dictionary
        """
        with self._lock:
            if self._state is None:
                self._state = self.load()

            return self._state.get("session_metadata", {}).copy()

    def get_full_state(self) -> dict[str, Any]:
        """Get full workspace state.

        Returns:
            Complete state dictionary
        """
        with self._lock:
            if self._state is None:
                self._state = self.load()

            return self._state.copy()

    def cleanup_old_entries(self):
        """Remove entries older than CLEANUP_DAYS."""
        with self._lock:
            if self._state is None:
                self._state = self.load()

            # Clean focus files
            focus_files = self._state.get("focus_files", [])
            self._state["focus_files"] = [
                f for f in focus_files if self._is_recent(f.get("last_accessed"))
            ]

            # Clean queries
            queries = self._state.get("recent_queries", [])
            self._state["recent_queries"] = [
                q for q in queries if self._is_recent(q.get("timestamp"))
            ]

            # Clean completed tasks
            tasks = self._state.get("active_tasks", [])
            self._state["active_tasks"] = [
                t for t in tasks if t["status"] != "completed" or self._is_recent(t.get("created"))
            ]

            self._save_unlocked()

        logger.info("Cleaned up old workspace entries")

    def clear(self):
        """Clear all workspace state."""
        with self._lock:
            self._state = self._default_state()
            self._save_unlocked()

        logger.info("Cleared workspace state")

    def _is_recent(self, timestamp_str: str | None) -> bool:
        """Check if timestamp is within CLEANUP_DAYS.

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            True if recent, False otherwise
        """
        if not timestamp_str:
            return False

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            cutoff = datetime.now() - timedelta(days=self.CLEANUP_DAYS)
            return timestamp > cutoff
        except (ValueError, TypeError):
            return False


# Global instance
_workspace_instance: WorkspaceState | None = None
_instance_lock = Lock()


def get_workspace_state(workspace_dir: Path | None = None) -> WorkspaceState:
    """Get or create global workspace state instance.

    Args:
        workspace_dir: Workspace directory (only used on first call)

    Returns:
        Global WorkspaceState instance
    """
    global _workspace_instance

    with _instance_lock:
        if _workspace_instance is None:
            _workspace_instance = WorkspaceState(workspace_dir=workspace_dir)

        return _workspace_instance
