"""
Video ingestion pipeline: transcribe, extract keyframes, compute embeddings, index.
"""

from pathlib import Path
from typing import List, Optional
import time

from timecapsule.database import (
    get_connection, add_video, add_transcript_segment,
    add_keyframe, update_keyframe_embedding, mark_video_complete
)
from timecapsule.transcribe import transcribe_video
from timecapsule.keyframes import extract_keyframes, get_video_info
from timecapsule.embeddings import embed_images
from timecapsule.indexer import get_index, save_index


SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi", ".mov"}


def find_videos(folder: Path) -> List[Path]:
    """Find all supported video files in folder."""
    videos = []
    for ext in SUPPORTED_EXTENSIONS:
        videos.extend(folder.glob(f"*{ext}"))
        videos.extend(folder.glob(f"*{ext.upper()}"))
    return sorted(videos)


def ingest_video(video_path: Path, thumbnail_dir: Path,
                 whisper_model: str = "base",
                 keyframe_interval: float = 2.0) -> dict:
    """
    Ingest a single video: transcribe, extract keyframes, compute embeddings.
    
    Returns timing stats dict.
    """
    stats = {
        "video": video_path.name,
        "transcribe_time": 0,
        "keyframe_time": 0,
        "embed_time": 0,
        "total_time": 0,
        "segments": 0,
        "keyframes": 0,
    }
    
    total_start = time.time()
    
    conn = get_connection()
    
    # Get video info
    print(f"\n📼 Processing: {video_path.name}")
    try:
        info = get_video_info(str(video_path))
        print(f"  📊 Duration: {info['duration']:.1f}s, {info['width']}x{info['height']}")
    except Exception as e:
        print(f"  ⚠️ Could not get video info: {e}")
        info = {"duration": 0, "width": None, "height": None, "fps": None}
    
    # Add video to DB
    video_id = add_video(
        conn, str(video_path),
        duration=info.get("duration"),
        width=info.get("width"),
        height=info.get("height"),
        fps=info.get("fps")
    )
    
    # Transcribe
    t_start = time.time()
    try:
        segments = transcribe_video(str(video_path), model_size=whisper_model)
        for start, end, text in segments:
            add_transcript_segment(conn, video_id, start, end, text)
        stats["segments"] = len(segments)
    except Exception as e:
        print(f"  ⚠️ Transcription failed: {e}")
        segments = []
    stats["transcribe_time"] = time.time() - t_start
    
    # Extract keyframes
    t_start = time.time()
    try:
        keyframes = extract_keyframes(
            str(video_path), thumbnail_dir,
            interval=keyframe_interval
        )
        
        keyframe_ids = []
        keyframe_paths = []
        for ts, thumb_path in keyframes:
            kf_id = add_keyframe(conn, video_id, ts, str(thumb_path))
            keyframe_ids.append(kf_id)
            keyframe_paths.append(thumb_path)
        
        stats["keyframes"] = len(keyframes)
    except Exception as e:
        print(f"  ⚠️ Keyframe extraction failed: {e}")
        keyframe_ids = []
        keyframe_paths = []
    stats["keyframe_time"] = time.time() - t_start
    
    # Compute embeddings
    t_start = time.time()
    if keyframe_paths:
        try:
            print(f"  🧠 Computing CLIP embeddings for {len(keyframe_paths)} frames...")
            embeddings = embed_images(keyframe_paths)
            
            # Add to FAISS index
            index = get_index()
            index.add(embeddings, keyframe_ids)
            
            # Update keyframe records with embedding IDs
            for i, kf_id in enumerate(keyframe_ids):
                update_keyframe_embedding(conn, kf_id, kf_id)
            
            print(f"  ✅ Indexed {len(embeddings)} embeddings")
        except Exception as e:
            print(f"  ⚠️ Embedding failed: {e}")
    stats["embed_time"] = time.time() - t_start
    
    # Mark complete
    mark_video_complete(conn, video_id)
    conn.close()
    
    stats["total_time"] = time.time() - total_start
    
    print(f"  ⏱️ Total time: {stats['total_time']:.1f}s")
    
    return stats


def run_ingest(folder: Path, workers: int = 1,
               whisper_model: str = "base",
               keyframe_interval: float = 2.0):
    """
    Ingest all videos from a folder.
    
    Args:
        folder: Path to folder containing videos
        workers: Number of parallel workers (currently sequential)
        whisper_model: Whisper model size (tiny/base/small/medium/large)
        keyframe_interval: Seconds between keyframe extraction
    """
    folder = Path(folder)
    
    if not folder.exists():
        print(f"❌ Folder not found: {folder}")
        return
    
    videos = find_videos(folder)
    
    if not videos:
        print(f"❌ No videos found in {folder}")
        print(f"   Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
        return
    
    print(f"🎬 Found {len(videos)} videos to process")
    
    # Thumbnail directory
    thumbnail_dir = Path(__file__).parent.parent.parent / "data" / "thumbnails"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    all_stats = []
    
    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] {'='*50}")
        stats = ingest_video(
            video, thumbnail_dir,
            whisper_model=whisper_model,
            keyframe_interval=keyframe_interval
        )
        all_stats.append(stats)
    
    # Save index
    save_index()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Ingestion Complete!")
    print("="*60)
    
    total_time = sum(s["total_time"] for s in all_stats)
    total_segments = sum(s["segments"] for s in all_stats)
    total_keyframes = sum(s["keyframes"] for s in all_stats)
    
    print(f"  Videos processed: {len(all_stats)}")
    print(f"  Total segments: {total_segments}")
    print(f"  Total keyframes: {total_keyframes}")
    print(f"  Total time: {total_time:.1f}s")
    
    return all_stats


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
        run_ingest(folder)
    else:
        print("Usage: python -m timecapsule.ingest <video_folder>")
