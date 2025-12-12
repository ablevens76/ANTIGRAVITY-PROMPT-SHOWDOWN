# TimeCapsule Benchmark Report

## System Specifications

| Component | Value |
|-----------|-------|
| **GPU** | NVIDIA GeForce RTX 4070 (12GB VRAM) |
| **CUDA** | 11.8 |
| **PyTorch** | 2.0.1+cu118 |
| **Python** | 3.9.19 |
| **FFmpeg** | 4.4.2 |
| **OS** | Pop!_OS (Ubuntu-based) |
| **RAM** | 64GB |

## Ingestion Benchmark

| Metric | Value |
|--------|-------|
| **Videos Processed** | 2 |
| **Total Duration** | 18 seconds of video |
| **Total Ingestion Time** | 26.1 seconds |
| **Keyframes Extracted** | 9 |
| **CLIP Embeddings** | 9 vectors (512-dim) |

### Per-Video Timing

| Video | Duration | Keyframes | Embedding Time | Total |
|-------|----------|-----------|----------------|-------|
| programming_sample.mp4 | 8s | 4 | ~0.7s | ~25s* |
| sample_video.mp4 | 10s | 5 | ~0.8s | ~1s |

*First video includes CLIP model loading (~24s cold start)

## Embedding Throughput

| Metric | Value |
|--------|-------|
| **CLIP Model** | ViT-B-32 (laion2b_s34b_b79k) |
| **Cold Start** | ~24 seconds (model download + load) |
| **Warm Throughput** | ~6 frames/second |
| **GPU Memory Usage** | ~2GB VRAM |

## Search Performance

| Metric | Value |
|--------|-------|
| **Index Size** | 9 vectors |
| **Search Latency** | <10ms |
| **FAISS Backend** | IndexFlatIP (CPU) |

## Transcription

Transcription was not benchmarked in this run because the synthetic test videos lacked audio tracks. With real videos containing speech:

| Metric | Expected Value |
|--------|----------------|
| **Model** | faster-whisper base |
| **Device** | CUDA (GPU accelerated) |
| **Expected Speed** | ~10-30x realtime on RTX 4070 |

## Test Suite

```
======================== 11 passed in 0.83s ========================
```

| Test Category | Tests | Status |
|---------------|-------|--------|
| Database operations | 6 | ✅ Passed |
| FAISS indexing | 5 | ✅ Passed |

## Reproducibility

### Quick Demo Command

```bash
cd GPT\ 5.2/timecapsule

# Generate sample videos
bash scripts/generate_sample.sh ./sample_videos

# Run doctor
timecapsule doctor

# Ingest
python -c "from timecapsule.ingest import run_ingest; from pathlib import Path; run_ingest(Path('./sample_videos'))"

# Serve
python -m timecapsule.server
# Open http://localhost:8000
```

### Docker (optional)

```bash
# docker-compose.yml not yet created - manual install required
pip install -e .
```

## Notes

1. **GPU Detection**: Successfully detected RTX 4070 with CUDA 11.8
2. **Compute Backend**: CUDA (GPU acceleration enabled)
3. **CLIP Loading**: First run downloads ~400MB model weights
4. **FAISS**: Using CPU version for simplicity; GPU version available
