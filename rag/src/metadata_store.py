"""SQLite-based metadata and keyword search store."""

import sqlite3
import logging
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class MetadataStore:
    """SQLite store for document metadata and full-text search."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Connect to SQLite database."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # Enable foreign key constraints
        self.conn.execute('PRAGMA foreign_keys = ON')

    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()

        # Files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                file_type TEXT,
                hash TEXT,
                size INTEGER,
                modified REAL,
                indexed_at REAL DEFAULT (strftime('%s', 'now'))
            )
        ''')

        # Chunks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                start_char INTEGER,
                end_char INTEGER,
                embedding_id INTEGER,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        ''')

        # Full-text search virtual table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                text,
                content=chunks,
                content_rowid=id
            )
        ''')

        # Triggers to keep FTS in sync
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text);
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                DELETE FROM chunks_fts WHERE rowid = old.id;
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                DELETE FROM chunks_fts WHERE rowid = old.id;
                INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text);
            END
        ''')

        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON chunks(file_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)')

        self.conn.commit()

    def add_file(self, file_path: str, file_type: str, content: str, size: int, modified: float) -> int:
        """Add or update a file in the database.

        Returns:
            file_id
        """
        # Calculate hash
        file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

        cursor = self.conn.cursor()

        # Check if file exists
        cursor.execute('SELECT id, hash FROM files WHERE path = ?', (file_path,))
        row = cursor.fetchone()

        if row:
            file_id, existing_hash = row
            if existing_hash == file_hash:
                # File unchanged
                return file_id

            # File changed, delete old chunks
            cursor.execute('DELETE FROM chunks WHERE file_id = ?', (file_id,))

            # Update file metadata
            cursor.execute('''
                UPDATE files SET hash = ?, size = ?, modified = ?, indexed_at = strftime('%s', 'now')
                WHERE id = ?
            ''', (file_hash, size, modified, file_id))
        else:
            # New file
            cursor.execute('''
                INSERT INTO files (path, file_type, hash, size, modified)
                VALUES (?, ?, ?, ?, ?)
            ''', (file_path, file_type, file_hash, size, modified))
            file_id = cursor.lastrowid

        self.conn.commit()
        return file_id

    def add_chunk(self, file_id: int, text: str, start_char: int, end_char: int, embedding_id: int) -> int:
        """Add a chunk to the database.

        Returns:
            chunk_id
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO chunks (file_id, text, start_char, end_char, embedding_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (file_id, text, start_char, end_char, embedding_id))

        chunk_id = cursor.lastrowid
        self.conn.commit()
        return chunk_id

    def get_chunk(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """Get chunk by ID."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.*, f.path as file_path
            FROM chunks c
            JOIN files f ON c.file_id = f.id
            WHERE c.id = ?
        ''', (chunk_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def search_text(self, query: str, limit: int = 10) -> List[Tuple[int, float]]:
        """Full-text search for chunks.

        Returns:
            List of (chunk_id, bm25_score) tuples
        """
        cursor = self.conn.cursor()

        # Use FTS5 BM25 scoring
        cursor.execute('''
            SELECT rowid, bm25(chunks_fts) as score
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
            ORDER BY score
            LIMIT ?
        ''', (query, limit))

        results = []
        for row in cursor.fetchall():
            # BM25 scores are negative (higher is better)
            # Normalize to 0-1 range approximately
            chunk_id = row[0]
            score = max(0, 1.0 + (row[1] / 10.0))  # Simple normalization
            results.append((chunk_id, score))

        return results

    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata by path."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM files WHERE path = ?', (file_path,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all indexed files."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM files ORDER BY path')
        return [dict(row) for row in cursor.fetchall()]

    def delete_file(self, file_path: str):
        """Delete a file and its chunks."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM files WHERE path = ?', (file_path,))
        self.conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        cursor = self.conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM files')
        file_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM chunks')
        chunk_count = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(size) FROM files')
        total_size = cursor.fetchone()[0] or 0

        return {
            'file_count': file_count,
            'chunk_count': chunk_count,
            'total_size_bytes': total_size,
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
