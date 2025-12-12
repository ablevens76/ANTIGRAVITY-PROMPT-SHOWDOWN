"""
FastAPI backend for Entropy_Garden.
Provides WebSocket streaming and REST endpoints for system telemetry.
"""

import asyncio
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from src.telemetry import collect_all_metrics, init_gpu_monitoring
from src.entropy import compute_entropy_score, get_dominant_metric
from src.models import EntropyEvent, MappingConfig


# Configuration
STREAM_HZ = 60  # Target updates per second
STREAM_INTERVAL = 1.0 / STREAM_HZ


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize GPU monitoring on startup."""
    print("🌿 Entropy Garden Backend Starting...")
    init_gpu_monitoring()
    print(f"📡 WebSocket streaming at {STREAM_HZ} Hz")
    yield
    print("🌿 Entropy Garden Backend Shutting Down...")


app = FastAPI(
    title="Entropy Garden Backend",
    version="0.1.0",
    lifespan=lifespan
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Current mapping configuration (shared state)
current_mapping = MappingConfig()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "entropy_garden"}


@app.get("/snapshot")
async def get_snapshot():
    """
    One-shot JSON snapshot of all metrics.
    """
    metrics = collect_all_metrics()
    entropy_score = compute_entropy_score(metrics, current_mapping.weights)
    
    event = EntropyEvent(
        timestamp=metrics["timestamp"],
        entropy_score=entropy_score,
        cpu_percent_per_core=metrics["cpu_percent_per_core"],
        load_average=metrics["load_average"],
        context_switches_per_sec=metrics["context_switches_per_sec"],
        interrupts_per_sec=metrics["interrupts_per_sec"],
        ram_total_gb=metrics["ram_total_gb"],
        ram_used_gb=metrics["ram_used_gb"],
        ram_available_gb=metrics["ram_available_gb"],
        gpu_util_percent=metrics["gpu_util_percent"],
        vram_used_gb=metrics["vram_used_gb"],
        vram_total_gb=metrics["vram_total_gb"],
        gpu_temp_celsius=metrics["gpu_temp_celsius"],
        gpu_power_watts=metrics["gpu_power_watts"],
    )
    
    return event.to_dict()


@app.post("/config/mapping")
async def set_mapping(mode: str = "balanced", intensity: float = 1.0):
    """Set the metric-to-visual mapping configuration."""
    global current_mapping
    current_mapping = MappingConfig(mode=mode, intensity=intensity)
    return {"status": "ok", "mode": mode, "intensity": intensity}


@app.get("/config/mapping")
async def get_mapping():
    """Get current mapping configuration."""
    return {"mode": current_mapping.mode, "intensity": current_mapping.intensity}


@app.websocket("/ws/entropy")
async def websocket_entropy(websocket: WebSocket):
    """
    WebSocket endpoint for real-time entropy streaming.
    Streams EntropyEvent data at 60 Hz.
    """
    await websocket.accept()
    print(f"📡 Client connected: {websocket.client}")
    
    try:
        while True:
            start_time = time.time()
            
            # Collect metrics
            metrics = collect_all_metrics()
            entropy_score = compute_entropy_score(metrics, current_mapping.weights)
            dominant = get_dominant_metric(metrics)
            
            # Build event
            event_data = {
                "timestamp": metrics["timestamp"],
                "entropy_score": entropy_score,
                "dominant_metric": dominant,
                "intensity": current_mapping.intensity,
                "cpu_percent_per_core": metrics["cpu_percent_per_core"],
                "load_average": list(metrics["load_average"]),
                "context_switches_per_sec": metrics["context_switches_per_sec"],
                "ram_used_gb": metrics["ram_used_gb"],
                "ram_total_gb": metrics["ram_total_gb"],
                "gpu_util_percent": metrics["gpu_util_percent"],
                "vram_used_gb": metrics["vram_used_gb"],
                "vram_total_gb": metrics["vram_total_gb"],
                "gpu_temp_celsius": metrics["gpu_temp_celsius"],
            }
            
            # Send to client
            await websocket.send_json(event_data)
            
            # Maintain target frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, STREAM_INTERVAL - elapsed)
            await asyncio.sleep(sleep_time)
            
    except WebSocketDisconnect:
        print(f"📡 Client disconnected: {websocket.client}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
