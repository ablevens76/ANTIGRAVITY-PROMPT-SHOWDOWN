"""
Audio transcription using faster-whisper with GPU acceleration.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
import os


def extract_audio(video_path: str, output_path: Optional[str] = None) -> str:
    """Extract audio from video file using ffmpeg."""
    if output_path is None:
        # Create temp file
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
    
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-ar", "16000",  # 16kHz sample rate (Whisper expects this)
        "-ac", "1",      # Mono
        "-vn",           # No video
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    
    return output_path


def transcribe_audio(audio_path: str, model_size: str = "base", 
                     device: str = "auto") -> List[Tuple[float, float, str]]:
    """
    Transcribe audio file using faster-whisper.
    
    Returns list of (start_time, end_time, text) tuples.
    """
    from faster_whisper import WhisperModel
    import torch
    
    # Determine device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    compute_type = "float16" if device == "cuda" else "int8"
    
    print(f"  🎤 Loading Whisper {model_size} on {device}...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    
    print(f"  🎤 Transcribing...")
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    results = []
    for segment in segments:
        results.append((segment.start, segment.end, segment.text.strip()))
    
    print(f"  ✅ Transcribed {len(results)} segments ({info.duration:.1f}s audio)")
    
    return results


def transcribe_video(video_path: str, model_size: str = "base",
                     device: str = "auto") -> List[Tuple[float, float, str]]:
    """
    Complete transcription pipeline: extract audio and transcribe.
    Cleans up temp audio file after.
    """
    print(f"  📼 Extracting audio from {Path(video_path).name}...")
    audio_path = extract_audio(video_path)
    
    try:
        segments = transcribe_audio(audio_path, model_size=model_size, device=device)
        return segments
    finally:
        # Clean up temp audio
        if Path(audio_path).exists():
            Path(audio_path).unlink()


if __name__ == "__main__":
    # Test with a sample video
    import sys
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        segments = transcribe_video(video_path)
        for start, end, text in segments[:5]:
            print(f"[{start:.1f}-{end:.1f}] {text}")
