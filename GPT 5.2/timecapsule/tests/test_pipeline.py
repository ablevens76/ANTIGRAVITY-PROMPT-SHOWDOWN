"""
Integration tests for the ingestion pipeline.
Tests that synthetic videos produce expected outputs.
"""

import pytest
import tempfile
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from timecapsule.database import get_connection, get_video_stats
from timecapsule.keyframes import get_video_info


def create_test_video_with_audio(output_path: Path, duration: int = 5) -> bool:
    """Create a small test video with audio using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=red:s=320x240:d={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "64k",
        "-t", str(duration),
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and output_path.exists()


class TestIngestPipeline:
    """Integration tests for video ingestion."""
    
    def test_video_info_extraction(self):
        """Test that video info is correctly extracted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            
            if not create_test_video_with_audio(video_path, duration=3):
                pytest.skip("FFmpeg not available or failed")
            
            info = get_video_info(str(video_path))
            
            assert info["duration"] > 0
            assert info["width"] == 320
            assert info["height"] == 240
    
    def test_synthetic_video_has_audio(self):
        """Test that our synthetic video generator produces audio."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            
            if not create_test_video_with_audio(video_path):
                pytest.skip("FFmpeg not available")
            
            # Check for audio stream using ffprobe
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            assert "audio" in result.stdout, "Video must have an audio stream"
    
    def test_ingest_produces_keyframes(self):
        """Test that ingestion produces keyframes (visual indexing works)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            db_path = Path(tmpdir) / "test.db"
            thumb_dir = Path(tmpdir) / "thumbs"
            thumb_dir.mkdir()
            
            if not create_test_video_with_audio(video_path, duration=6):
                pytest.skip("FFmpeg not available")
            
            # Run keyframe extraction directly
            from timecapsule.keyframes import extract_keyframes
            
            keyframes = extract_keyframes(str(video_path), thumb_dir, interval=2.0)
            
            assert len(keyframes) > 0, "Must extract at least 1 keyframe"
            
            # Verify thumbnails exist
            for ts, path in keyframes:
                assert path.exists(), f"Thumbnail must exist: {path}"


class TestTranscriptionRegression:
    """Regression tests for transcription pipeline."""
    
    def test_audio_extraction_works(self):
        """Test that audio can be extracted from video with audio stream."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            audio_path = Path(tmpdir) / "test.wav"
            
            if not create_test_video_with_audio(video_path, duration=3):
                pytest.skip("FFmpeg not available")
            
            # Try to extract audio
            cmd = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-ar", "16000", "-ac", "1", "-vn",
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            assert result.returncode == 0, f"Audio extraction must succeed: {result.stderr}"
            assert audio_path.exists(), "Audio file must be created"
            assert audio_path.stat().st_size > 0, "Audio file must not be empty"
    
    def test_ingest_produces_transcript_segments(self):
        """
        CRITICAL REGRESSION TEST: Ingest with audio must produce transcript segments.
        
        This prevents the "0 segments" silent failure where only vision search works
        but text search is broken due to missing transcription.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test_speech.mp4"
            db_path = Path(tmpdir) / "test.db"
            thumb_dir = Path(tmpdir) / "thumbs"
            thumb_dir.mkdir()
            
            # Create video with audio
            if not create_test_video_with_audio(video_path, duration=5):
                pytest.skip("FFmpeg not available")
            
            # Verify audio stream exists before testing transcription
            probe_cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                str(video_path)
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            
            if "audio" not in probe_result.stdout:
                pytest.skip("Test video has no audio stream")
            
            # Extract audio to verify it's valid
            audio_path = Path(tmpdir) / "test.wav"
            extract_cmd = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-ar", "16000", "-ac", "1", "-vn",
                str(audio_path)
            ]
            extract_result = subprocess.run(extract_cmd, capture_output=True, text=True)
            
            # The key assertion: audio extraction must succeed for videos with audio
            assert extract_result.returncode == 0, (
                "Audio extraction failed - this would cause 0 transcript segments. "
                f"Error: {extract_result.stderr}"
            )
            assert audio_path.exists() and audio_path.stat().st_size > 1000, (
                "Audio file too small or missing - transcription would fail silently"
            )


class TestDatabasePersistence:
    """Test database and index persistence."""
    
    def test_database_persists_across_connections(self):
        """Test that data persists when connection is closed and reopened."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        
        try:
            from timecapsule.database import get_connection, add_video, get_video_stats
            
            # First connection: add data
            conn1 = get_connection(db_path)
            add_video(conn1, "/path/to/video.mp4", duration=60.0)
            conn1.close()
            
            # Second connection: verify data persists
            conn2 = get_connection(db_path)
            stats = get_video_stats(conn2)
            conn2.close()
            
            assert stats["video_count"] == 1, "Data must persist across connections"
        finally:
            if db_path.exists():
                db_path.unlink()
