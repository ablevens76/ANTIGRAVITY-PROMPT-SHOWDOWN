"""
Keyframe extraction from videos using FFmpeg.
"""

import subprocess
import json
from pathlib import Path
from typing import List, Tuple
from PIL import Image


def get_video_info(video_path: str) -> dict:
    """Get video metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    
    data = json.loads(result.stdout)
    
    # Find video stream
    video_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break
    
    info = {
        "duration": float(data.get("format", {}).get("duration", 0)),
        "width": video_stream.get("width") if video_stream else None,
        "height": video_stream.get("height") if video_stream else None,
        "fps": None,
    }
    
    # Parse FPS
    if video_stream and "r_frame_rate" in video_stream:
        fps_parts = video_stream["r_frame_rate"].split("/")
        if len(fps_parts) == 2 and int(fps_parts[1]) != 0:
            info["fps"] = int(fps_parts[0]) / int(fps_parts[1])
    
    return info


def extract_keyframes(video_path: str, output_dir: Path, 
                      interval: float = 2.0,
                      max_frames: int = 100) -> List[Tuple[float, Path]]:
    """
    Extract keyframes at regular intervals.
    
    Args:
        video_path: Path to video file
        output_dir: Directory to save thumbnails
        interval: Seconds between frames
        max_frames: Maximum number of frames to extract
        
    Returns:
        List of (timestamp, thumbnail_path) tuples
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video_name = Path(video_path).stem
    
    # Get video duration
    info = get_video_info(video_path)
    duration = info["duration"]
    
    # Calculate frame timestamps
    timestamps = []
    t = 0.0
    while t < duration and len(timestamps) < max_frames:
        timestamps.append(t)
        t += interval
    
    print(f"  🎞️ Extracting {len(timestamps)} keyframes...")
    
    results = []
    for i, ts in enumerate(timestamps):
        output_path = output_dir / f"{video_name}_{i:04d}.jpg"
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(ts),
            "-i", video_path,
            "-vframes", "1",
            "-vf", "scale=224:224:force_original_aspect_ratio=decrease,pad=224:224:(ow-iw)/2:(oh-ih)/2",
            "-q:v", "5",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and output_path.exists():
            results.append((ts, output_path))
    
    print(f"  ✅ Extracted {len(results)} keyframes")
    
    return results


def load_image_for_clip(image_path: Path) -> Image.Image:
    """Load and prepare image for CLIP processing."""
    img = Image.open(image_path).convert("RGB")
    return img


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        output_dir = Path("./test_keyframes")
        
        info = get_video_info(video_path)
        print(f"Video info: {info}")
        
        frames = extract_keyframes(video_path, output_dir)
        for ts, path in frames[:5]:
            print(f"  {ts:.1f}s -> {path}")
