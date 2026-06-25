"""SQLite connection, schema initialization, and lightweight migrations."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from server import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    file_type TEXT NOT NULL DEFAULT 'md',
    content_hash TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    note_id TEXT,
    message TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _migrate_notes(conn: sqlite3.Connection) -> None:
    """Upgrade legacy notes table (pre multi-user API) to current schema."""
    cols = _table_columns(conn, "notes")
    if not cols:
        return

    if "user_id" not in cols:
        conn.execute(
            "ALTER TABLE notes ADD COLUMN user_id TEXT NOT NULL DEFAULT ''"
        )
    if "content" not in cols:
        conn.execute(
            "ALTER TABLE notes ADD COLUMN content TEXT NOT NULL DEFAULT ''"
        )
    if "updated_at" not in cols:
        conn.execute(
            "ALTER TABLE notes ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"
        )
        conn.execute(
            "UPDATE notes SET updated_at = created_at WHERE updated_at = ''"
        )

    conn.execute("DELETE FROM notes WHERE user_id = ''")


def init_db() -> None:
    """Create tables and apply migrations on application startup."""
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    try:
        conn.executescript(_SCHEMA)
        _migrate_notes(conn)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_notes_user_content_hash "
            "ON notes(user_id, content_hash)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_updated "
            "ON tasks(user_id, updated_at DESC)"
        )
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_conn():
    """Yield a connection with row factory for dict-like access."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
