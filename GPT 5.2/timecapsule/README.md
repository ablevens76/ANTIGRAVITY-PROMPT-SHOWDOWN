# TimeCapsule 🎬🔍

> **GPU-accelerated local video search** with natural language queries, automatic transcription, and instant timestamp playback.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org)
[![CUDA](https://img.shields.io/badge/CUDA-11.8+-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Tests](https://img.shields.io/badge/Tests-11%2F11%20Passing-brightgreen.svg)](#testing)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What is TimeCapsule?

TimeCapsule is a **local-first video search engine** that indexes your video library and enables natural language search. Point it at a folder of videos and search for moments like:

- *"person explaining code"*
- *"outdoor scene with mountains"*
- *"someone laughing"*

Click any result to **jump directly to that timestamp** in the video.

### Key Features

| Feature | Description |
|---------|-------------|
| 🎤 **Speech-to-Text** | GPU-accelerated transcription with Whisper |
| 🖼️ **Visual Search** | CLIP embeddings for semantic image understanding |
| ⚡ **Fast Indexing** | FAISS vector search with sub-10ms queries |
| 🎯 **Precise Playback** | Click-to-play at exact timestamps |
| 🖥️ **Beautiful UI** | Modern dark-themed web interface |
| 🔒 **100% Local** | No cloud, no API keys, your data stays private |

---

## 📸 Screenshots

The web UI provides:
- **Dashboard** with video/keyframe/transcript stats
- **Search box** with natural language input
- **Results grid** with thumbnails, timestamps, and confidence scores
- **Video player** with automatic timestamp seeking

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **NVIDIA GPU** with CUDA (optional, CPU fallback available)
- **FFmpeg** installed (`sudo apt install ffmpeg` on Ubuntu/Pop!_OS)

### Installation

```bash
# Clone or navigate to the project
cd timecapsule

# Install the package
pip install -e .

# Verify your system
timecapsule doctor
```

### Usage

```bash
# 1. Check your system
timecapsule doctor

# 2. Index your videos
timecapsule ingest /path/to/your/videos/

# 3. Launch the web UI
timecapsule serve

# 4. Open http://localhost:8000 and search!
```

---

## 💻 CLI Reference

### `timecapsule doctor`

Check system readiness: GPU, CUDA, PyTorch, FFmpeg.

```bash
$ timecapsule doctor

============================================================
🏥 TimeCapsule Doctor - System Diagnostics
============================================================

📦 Python: 3.9.19

🔥 PyTorch:
   Version: 2.0.1+cu118
   CUDA Available: ✅ Yes
   CUDA Version: 11.8

🎮 GPU:
   Device: NVIDIA GeForce RTX 4070
   Memory: 11.6 GB

🎬 FFmpeg:
   ✅ Found: /usr/bin/ffmpeg

⚡ Compute Backend:
   🚀 CUDA

============================================================
✅ All systems GO! GPU acceleration enabled.
============================================================
```

### `timecapsule ingest <folder>`

Process videos: extract audio, transcribe, extract keyframes, compute embeddings.

```bash
$ timecapsule ingest ~/Videos/tutorials/ --workers 2

🎬 Found 5 videos to process

[1/5] ==================================================
📼 Processing: python_basics.mp4
  📊 Duration: 1200.0s, 1920x1080
  🎤 Transcribing... ✅ 847 segments
  🎞️ Extracting keyframes... ✅ 600 frames
  🧠 Computing embeddings... ✅ Indexed

============================================================
📊 Ingestion Complete!
  Videos processed: 5
  Total segments: 3,421
  Total keyframes: 2,847
  Total time: 342.5s
============================================================
```

### `timecapsule search "query"`

Search from the command line.

```bash
$ timecapsule search "explaining recursion" --topk 5

🔍 Top 5 results for: 'explaining recursion'

1. [0.87] python_basics.mp4
   ⏱️  847.2s
   💬 "So recursion is when a function calls itself..."

2. [0.73] algorithms_101.mp4
   ⏱️  1203.5s
   💬 "Let's trace through this recursive call..."
```

### `timecapsule serve`

Launch the web UI.

```bash
$ timecapsule serve --port 8000

🚀 Starting TimeCapsule server at http://127.0.0.1:8000
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TimeCapsule                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │  Video   │───▶│  FFmpeg  │───▶│  Whisper (GPU)   │  │
│  │  Files   │    │  Audio   │    │  Transcription   │  │
│  └──────────┘    └──────────┘    └────────┬─────────┘  │
│       │                                    │            │
│       ▼                                    ▼            │
│  ┌──────────┐                      ┌──────────────┐    │
│  │ Keyframe │                      │   SQLite     │    │
│  │ Extract  │                      │  Transcripts │    │
│  └────┬─────┘                      └──────────────┘    │
│       │                                                 │
│       ▼                                                 │
│  ┌──────────────┐    ┌──────────────────────────────┐  │
│  │  CLIP (GPU)  │───▶│     FAISS Vector Index       │  │
│  │  Embeddings  │    │   (512-dim, cosine sim)      │  │
│  └──────────────┘    └──────────────────────────────┘  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                    FastAPI Server                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐  │
│  │ /search │  │ /ingest │  │ /video  │  │ /stats   │  │
│  └─────────┘  └─────────┘  └─────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
timecapsule/
├── README.md               # This file
├── pyproject.toml          # Project configuration
├── benchmark.md            # Performance benchmarks
│
├── src/timecapsule/        # Main package
│   ├── __init__.py
│   ├── cli.py              # Click CLI commands
│   ├── doctor.py           # System diagnostics
│   ├── database.py         # SQLite operations
│   ├── transcribe.py       # Whisper transcription
│   ├── keyframes.py        # FFmpeg keyframe extraction
│   ├── embeddings.py       # OpenCLIP embeddings
│   ├── indexer.py          # FAISS vector index
│   ├── search.py           # Search engine
│   ├── ingest.py           # Ingestion pipeline
│   └── server.py           # FastAPI server
│
├── static/
│   └── index.html          # Web UI (single-page app)
│
├── tests/
│   ├── test_database.py    # Database unit tests
│   └── test_search.py      # FAISS index tests
│
├── scripts/
│   └── generate_sample.sh  # Create test videos
│
└── data/                   # Runtime data (gitignored)
    ├── timecapsule.db      # SQLite database
    ├── faiss.index         # Vector index
    └── thumbnails/         # Extracted frames
```

---

## ⚙️ Configuration

### Whisper Model Sizes

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | ~1GB | Fastest | Basic |
| `base` | ~1GB | Fast | Good (default) |
| `small` | ~2GB | Medium | Better |
| `medium` | ~5GB | Slow | Great |
| `large` | ~10GB | Slowest | Best |

```bash
# Use a specific model
timecapsule ingest ./videos --model small
```

### Keyframe Interval

```bash
# Extract a frame every 5 seconds (default: 2s)
timecapsule ingest ./videos --interval 5.0
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Expected output:
======================== 11 passed in 0.83s ========================
```

### Test Coverage

| Module | Tests | Description |
|--------|-------|-------------|
| `database.py` | 6 | SQLite CRUD operations |
| `indexer.py` | 5 | FAISS add/search operations |

---

## 📊 Benchmarks

Tested on **RTX 4070 12GB** with **CUDA 11.8**:

| Operation | Performance |
|-----------|-------------|
| CLIP model load | ~24s (cold start) |
| Embedding throughput | ~6 frames/sec |
| FAISS search latency | <10ms |
| Whisper (base) | ~10-30x realtime |
| GPU VRAM usage | ~2-3GB |

See [benchmark.md](benchmark.md) for detailed results.

---

## 🛠️ Troubleshooting

### "CUDA not available"

1. Check NVIDIA driver: `nvidia-smi`
2. Reinstall PyTorch with CUDA:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
3. TimeCapsule will fall back to CPU mode automatically

### "FFmpeg not found"

```bash
# Ubuntu/Pop!_OS
sudo apt install ffmpeg

# Verify
ffmpeg -version
```

### "No videos found"

Supported formats: `.mp4`, `.mkv`, `.webm`, `.avi`, `.mov`

### "Out of memory"

- Use a smaller Whisper model: `--model tiny`
- Reduce keyframe interval: `--interval 5.0`
- Process fewer videos at once

---

## 🔧 Development

### Setup Development Environment

```bash
# Clone the repo
git clone <repo-url>
cd timecapsule

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

### Code Formatting

```bash
# Format with black
black src/

# Lint with ruff
ruff check src/
```

---

## 🔒 Version Compatibility Lock

TimeCapsule requires specific PyTorch + CUDA versions for GPU acceleration. Use these exact commands based on your CUDA version:

### CUDA 11.8 (Recommended)

```bash
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 \
    --index-url https://download.pytorch.org/whl/cu118
```

### CUDA 12.1

```bash
pip install torch==2.1.0+cu121 torchvision==0.16.0+cu121 torchaudio==2.1.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121
```

### CPU Only

```bash
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cpu
```

### Verify Installation

```bash
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

📖 **Reference**: [PyTorch Previous Versions](https://pytorch.org/get-started/previous-versions/)

### Pinned Dependencies

For full reproducibility, the tested versions are:

| Package | Version |
|---------|---------|
| torch | 2.0.1+cu118 |
| faster-whisper | ≥1.0 |
| open-clip-torch | ≥2.20 |
| faiss-cpu | ≥1.7 |
| fastapi | ≥0.100 |

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - CTranslate2-based Whisper
- [OpenCLIP](https://github.com/mlfoundations/open_clip) - Open source CLIP implementation
- [FAISS](https://github.com/facebookresearch/faiss) - Facebook AI Similarity Search
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework

---

## 🚧 Roadmap

- [ ] Multi-GPU support
- [ ] Batch processing with progress bars
- [ ] Video collection management
- [ ] Export search results
- [ ] Docker deployment
- [ ] Transcript editing UI

---

<div align="center">
  <b>Built with ❤️ for local video search</b>
</div>
