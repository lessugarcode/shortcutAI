"""
Right Service
SQLite-backed interaction history with search, pagination, and export support.
"""

import logging
import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from config import APP_DATA_DIR

logger = logging.getLogger(__name__)

DB_FILE = APP_DATA_DIR / "history.db"

# Thread-local storage for connections (SQLite requires same-thread usage)
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Get a thread-local database connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_FILE))
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    """Initialize the database schema."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id TEXT NOT NULL,
            content_preview TEXT,
            response TEXT,
            provider TEXT,
            model TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_interactions_action_id
        ON interactions(action_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_interactions_created_at
        ON interactions(created_at DESC)
    """)
    conn.commit()
    logger.info(f"History database initialized at {DB_FILE}")


def save_interaction(
    action_id: str,
    content_preview: str,
    response: str,
    provider: str,
    model: str,
) -> int:
    """
    Save an AI interaction to history.
    
    Returns the new row ID.
    """
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        """INSERT INTO interactions (action_id, content_preview, response, provider, model, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (action_id, content_preview[:500] if content_preview else "", response, provider, model, now),
    )
    conn.commit()
    return cursor.lastrowid


def get_history(limit: int = 50, offset: int = 0) -> list[dict]:
    """
    Get recent interaction history, newest first.
    """
    conn = _get_conn()
    rows = conn.execute(
        """SELECT id, action_id, content_preview, 
                  substr(response, 1, 500) as response_preview,
                  provider, model, created_at
           FROM interactions
           ORDER BY created_at DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    ).fetchall()
    return [dict(row) for row in rows]


def search_history(query: str, limit: int = 50) -> list[dict]:
    """
    Full-text search across content_preview and response.
    Uses LIKE for simplicity (SQLite FTS optional).
    """
    conn = _get_conn()
    search_term = f"%{query}%"
    rows = conn.execute(
        """SELECT id, action_id, content_preview,
                  substr(response, 1, 500) as response_preview,
                  provider, model, created_at
           FROM interactions
           WHERE content_preview LIKE ? OR response LIKE ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (search_term, search_term, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def get_interaction_by_id(interaction_id: int) -> Optional[dict]:
    """
    Get a single interaction by ID, including full response.
    """
    conn = _get_conn()
    row = conn.execute(
        """SELECT id, action_id, content_preview, response, provider, model, created_at
           FROM interactions WHERE id = ?""",
        (interaction_id,),
    ).fetchone()
    if row:
        return dict(row)
    return None


def delete_interaction(interaction_id: int) -> bool:
    """
    Delete a single interaction by ID.
    Returns True if deleted, False if not found.
    """
    conn = _get_conn()
    cursor = conn.execute(
        "DELETE FROM interactions WHERE id = ?",
        (interaction_id,),
    )
    conn.commit()
    return cursor.rowcount > 0


def get_interactions_by_ids(interaction_ids: list[int]) -> list[dict]:
    """
    Get multiple interactions by ID list, including full responses.
    Used for export.
    """
    conn = _get_conn()
    placeholders = ",".join("?" * len(interaction_ids))
    rows = conn.execute(
        f"""SELECT id, action_id, content_preview, response, provider, model, created_at
            FROM interactions
            WHERE id IN ({placeholders})
            ORDER BY created_at DESC""",
        interaction_ids,
    ).fetchall()
    return [dict(row) for row in rows]


# Initialize DB on module load
try:
    init_db()
except Exception as e:
    logger.warning(f"Failed to initialize history DB (may be read-only): {e}")
