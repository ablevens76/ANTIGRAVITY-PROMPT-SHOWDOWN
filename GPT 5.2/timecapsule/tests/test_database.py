"""Tests for database operations."""

import pytest
import tempfile
from pathlib import Path
import sqlite3

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from timecapsule.database import (
    get_connection, add_video, add_transcript_segment,
    add_keyframe, get_video_stats, search_transcripts
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    conn = get_connection(db_path)
    yield conn, db_path
    
    conn.close()
    if db_path.exists():
        db_path.unlink()


class TestDatabase:
    def test_create_tables(self, temp_db):
        """Test that tables are created correctly."""
        conn, _ = temp_db
        
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        
        assert "videos" in tables
        assert "transcripts" in tables
        assert "keyframes" in tables
    
    def test_add_video(self, temp_db):
        """Test adding a video."""
        conn, _ = temp_db
        
        video_id = add_video(conn, "/path/to/video.mp4", duration=60.0)
        
        assert video_id is not None
        assert video_id > 0
        
        cursor = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row["path"] == "/path/to/video.mp4"
        assert row["duration"] == 60.0
    
    def test_add_transcript_segment(self, temp_db):
        """Test adding transcript segments."""
        conn, _ = temp_db
        
        video_id = add_video(conn, "/path/to/video.mp4")
        add_transcript_segment(conn, video_id, 0.0, 5.0, "Hello world")
        add_transcript_segment(conn, video_id, 5.0, 10.0, "This is a test")
        
        cursor = conn.execute(
            "SELECT * FROM transcripts WHERE video_id = ?", (video_id,)
        )
        rows = cursor.fetchall()
        
        assert len(rows) == 2
        assert rows[0]["text"] == "Hello world"
    
    def test_add_keyframe(self, temp_db):
        """Test adding keyframes."""
        conn, _ = temp_db
        
        video_id = add_video(conn, "/path/to/video.mp4")
        kf_id = add_keyframe(conn, video_id, 5.0, "/path/to/thumb.jpg")
        
        assert kf_id is not None
        
        cursor = conn.execute("SELECT * FROM keyframes WHERE id = ?", (kf_id,))
        row = cursor.fetchone()
        
        assert row["timestamp"] == 5.0
        assert row["thumbnail_path"] == "/path/to/thumb.jpg"
    
    def test_get_stats(self, temp_db):
        """Test getting statistics."""
        conn, _ = temp_db
        
        # Add some data
        video_id = add_video(conn, "/path/to/video.mp4")
        add_transcript_segment(conn, video_id, 0.0, 5.0, "Test")
        add_keyframe(conn, video_id, 2.5)
        
        stats = get_video_stats(conn)
        
        assert stats["video_count"] == 1
        assert stats["transcript_segments"] == 1
        assert stats["keyframe_count"] == 1
    
    def test_search_transcripts(self, temp_db):
        """Test transcript search."""
        conn, _ = temp_db
        
        video_id = add_video(conn, "/path/to/video.mp4")
        add_transcript_segment(conn, video_id, 0.0, 5.0, "Hello world")
        add_transcript_segment(conn, video_id, 5.0, 10.0, "Python programming")
        
        # Search for "world"
        results = search_transcripts(conn, "world")
        assert len(results) == 1
        assert "Hello" in results[0]["text"]
        
        # Search for "Python"
        results = search_transcripts(conn, "Python")
        assert len(results) == 1
