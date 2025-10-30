"""File watcher for automatic index refresh."""

import logging
import time
from pathlib import Path
from typing import Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class IndexFileHandler(FileSystemEventHandler):
    """Handles file system events for index refresh."""

    def __init__(self, directory: Path, file_types: Set[str],
                 on_change_callback: Callable, debounce_seconds: float = 2.0):
        self.directory = directory
        self.file_types = file_types
        self.on_change_callback = on_change_callback
        self.debounce_seconds = debounce_seconds
        self.pending_changes = set()
        self.last_event_time = 0

    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event."""
        if event.is_directory:
            return

        # Check if file type is relevant
        path = Path(event.src_path)
        if path.suffix not in self.file_types:
            return

        # Add to pending changes
        self.pending_changes.add(str(path))

        # Debounce: only trigger callback if enough time has passed
        current_time = time.time()
        if current_time - self.last_event_time >= self.debounce_seconds:
            self._trigger_callback()

    def _trigger_callback(self):
        """Trigger the callback with pending changes."""
        if not self.pending_changes:
            return

        logger.info(f"Detected {len(self.pending_changes)} file changes")
        self.last_event_time = time.time()

        try:
            self.on_change_callback(self.directory)
        except Exception as e:
            logger.error(f"Error in change callback: {e}")
        finally:
            self.pending_changes.clear()


class FileWatcher:
    """Watches directories for changes and triggers index refresh."""

    def __init__(self):
        self.observer = Observer()
        self.handlers = {}

    def watch_directory(self, directory: str, file_types: Set[str],
                        on_change: Callable):
        """Start watching a directory for changes.

        Args:
            directory: Directory to watch
            file_types: Set of file extensions to monitor
            on_change: Callback function(directory) to call on changes
        """
        directory_path = Path(directory).expanduser().resolve()

        if not directory_path.exists():
            logger.error(f"Cannot watch non-existent directory: {directory}")
            return

        # Create handler
        handler = IndexFileHandler(
            directory=directory_path,
            file_types=file_types,
            on_change_callback=on_change
        )

        # Schedule watching
        self.observer.schedule(handler, str(directory_path), recursive=True)
        self.handlers[str(directory_path)] = handler

        logger.info(f"Started watching directory: {directory}")

    def start(self):
        """Start the file watcher."""
        self.observer.start()
        logger.info("File watcher started")

    def stop(self):
        """Stop the file watcher."""
        self.observer.stop()
        self.observer.join()
        logger.info("File watcher stopped")

    def is_alive(self) -> bool:
        """Check if watcher is running."""
        return self.observer.is_alive()
