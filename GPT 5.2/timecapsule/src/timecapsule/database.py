"""
SQLite database operations for TimeCapsule.
Stores video metadata, transcript segments, and embedding mappings.
"""

import sqlite3
from pathlib import Path
from typing import Optional
import json

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "timecapsule.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get database connection, creating tables if needed."""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    # Create tables
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            duration REAL,
            width INTEGER,
            height INTEGER,
            fps REAL,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        );
        
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );
        
        CREATE TABLE IF NOT EXISTS keyframes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            thumbnail_path TEXT,
            embedding_id INTEGER,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_transcripts_video ON transcripts(video_id);
        CREATE INDEX IF NOT EXISTS idx_transcripts_text ON transcripts(text);
        CREATE INDEX IF NOT EXISTS idx_keyframes_video ON keyframes(video_id);
    """)
    
    conn.commit()
    return conn


def add_video(conn: sqlite3.Connection, path: str, duration: float = None,
              width: int = None, height: int = None, fps: float = None) -> int:
    """Add a video to the database, returning its ID."""
    cursor = conn.execute("""
        INSERT OR REPLACE INTO videos (path, filename, duration, width, height, fps, status)
        VALUES (?, ?, ?, ?, ?, ?, 'processing')
    """, (path, Path(path).name, duration, width, height, fps))
    conn.commit()
    return cursor.lastrowid


def add_transcript_segment(conn: sqlite3.Connection, video_id: int,
                           start_time: float, end_time: float, text: str):
    """Add a transcript segment."""
    conn.execute("""
        INSERT INTO transcripts (video_id, start_time, end_time, text)
        VALUES (?, ?, ?, ?)
    """, (video_id, start_time, end_time, text))
    conn.commit()


def add_keyframe(conn: sqlite3.Connection, video_id: int, timestamp: float,
                 thumbnail_path: str = None, embedding_id: int = None) -> int:
    """Add a keyframe, returning its ID."""
    cursor = conn.execute("""
        INSERT INTO keyframes (video_id, timestamp, thumbnail_path, embedding_id)
        VALUES (?, ?, ?, ?)
    """, (video_id, timestamp, thumbnail_path, embedding_id))
    conn.commit()
    return cursor.lastrowid


def update_keyframe_embedding(conn: sqlite3.Connection, keyframe_id: int, embedding_id: int):
    """Update keyframe with embedding ID."""
    conn.execute("""
        UPDATE keyframes SET embedding_id = ? WHERE id = ?
    """, (embedding_id, keyframe_id))
    conn.commit()


def mark_video_complete(conn: sqlite3.Connection, video_id: int):
    """Mark video as fully processed."""
    conn.execute("""
        UPDATE videos SET status = 'complete' WHERE id = ?
    """, (video_id,))
    conn.commit()


def search_transcripts(conn: sqlite3.Connection, query: str, limit: int = 20) -> list:
    """Search transcript segments for matching text."""
    # Simple LIKE search (could upgrade to FTS5)
    cursor = conn.execute("""
        SELECT t.*, v.path as video_path, v.filename
        FROM transcripts t
        JOIN videos v ON t.video_id = v.id
        WHERE t.text LIKE ?
        ORDER BY t.start_time
        LIMIT ?
    """, (f"%{query}%", limit))
    return [dict(row) for row in cursor.fetchall()]


def get_keyframe_by_embedding_id(conn: sqlite3.Connection, embedding_id: int) -> Optional[dict]:
    """Get keyframe info by embedding ID."""
    cursor = conn.execute("""
        SELECT k.*, v.path as video_path, v.filename
        FROM keyframes k
        JOIN videos v ON k.video_id = v.id
        WHERE k.embedding_id = ?
    """, (embedding_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_all_videos(conn: sqlite3.Connection) -> list:
    """Get all indexed videos."""
    cursor = conn.execute("SELECT * FROM videos ORDER BY ingested_at DESC")
    return [dict(row) for row in cursor.fetchall()]


def get_video_stats(conn: sqlite3.Connection) -> dict:
    """Get database statistics."""
    stats = {}
    
    cursor = conn.execute("SELECT COUNT(*) FROM videos")
    stats["video_count"] = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM transcripts")
    stats["transcript_segments"] = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM keyframes")
    stats["keyframe_count"] = cursor.fetchone()[0]
    
    return stats
