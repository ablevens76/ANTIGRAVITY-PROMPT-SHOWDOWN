"""
FastAPI server with web UI for TimeCapsule.
"""

from pathlib import Path
from typing import Optional
import asyncio
import os

from fastapi import FastAPI, Query, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

from timecapsule.database import get_connection, get_video_stats, get_all_videos
from timecapsule.search import run_search
from timecapsule.ingest import run_ingest, find_videos

# App setup
app = FastAPI(title="TimeCapsule", version="0.1.0")

# Static files
STATIC_DIR = Path(__file__).parent.parent.parent / "static"
DATA_DIR = Path(__file__).parent.parent.parent / "data"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Ingest status
ingest_status = {
    "running": False,
    "progress": 0,
    "total": 0,
    "current_video": None,
    "message": "Idle"
}


class IngestRequest(BaseModel):
    folder: str
    whisper_model: str = "base"
    keyframe_interval: float = 2.0


class SearchRequest(BaseModel):
    query: str
    topk: int = 10


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI."""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return html_path.read_text()
    return """
    <!DOCTYPE html>
    <html>
    <head><title>TimeCapsule</title></head>
    <body>
        <h1>TimeCapsule</h1>
        <p>Static files not found. Please ensure static/index.html exists.</p>
        <p>API available at /docs</p>
    </body>
    </html>
    """


@app.get("/api/stats")
async def get_stats():
    """Get database statistics."""
    try:
        conn = get_connection()
        stats = get_video_stats(conn)
        conn.close()
        return stats
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/videos")
async def list_videos():
    """List all indexed videos."""
    try:
        conn = get_connection()
        videos = get_all_videos(conn)
        conn.close()
        return {"videos": videos}
    except Exception as e:
        return {"error": str(e), "videos": []}


@app.get("/api/search")
async def search(q: str = Query(..., min_length=1), topk: int = 10):
    """Search indexed videos."""
    try:
        results = run_search(q, topk=topk)
        return {"query": q, "results": results}
    except Exception as e:
        return {"query": q, "results": [], "error": str(e)}


@app.post("/api/ingest")
async def start_ingest(request: IngestRequest, background_tasks: BackgroundTasks):
    """Start video ingestion."""
    global ingest_status
    
    if ingest_status["running"]:
        return {"error": "Ingestion already in progress"}
    
    folder = Path(request.folder)
    if not folder.exists():
        return {"error": f"Folder not found: {folder}"}
    
    videos = find_videos(folder)
    if not videos:
        return {"error": "No videos found in folder"}
    
    ingest_status = {
        "running": True,
        "progress": 0,
        "total": len(videos),
        "current_video": None,
        "message": "Starting..."
    }
    
    background_tasks.add_task(
        run_ingest_background,
        folder,
        request.whisper_model,
        request.keyframe_interval
    )
    
    return {"status": "started", "video_count": len(videos)}


async def run_ingest_background(folder: Path, whisper_model: str, keyframe_interval: float):
    """Run ingestion in background."""
    global ingest_status
    
    try:
        # Run synchronously (transcription is already optimized)
        run_ingest(folder, whisper_model=whisper_model, keyframe_interval=keyframe_interval)
        ingest_status["message"] = "Complete!"
    except Exception as e:
        ingest_status["message"] = f"Error: {e}"
    finally:
        ingest_status["running"] = False


@app.get("/api/ingest/status")
async def get_ingest_status():
    """Get current ingestion status."""
    return ingest_status


@app.get("/thumbnail/{filename:path}")
async def serve_thumbnail(filename: str):
    """Serve a thumbnail image."""
    thumb_path = DATA_DIR / "thumbnails" / filename
    if not thumb_path.exists():
        # Try as absolute path
        thumb_path = Path(filename)
    
    if thumb_path.exists():
        return FileResponse(thumb_path)
    raise HTTPException(status_code=404, detail="Thumbnail not found")


@app.get("/video")
async def serve_video(path: str):
    """Serve a video file for playback."""
    video_path = Path(path)
    if video_path.exists():
        return FileResponse(video_path, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Video not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
