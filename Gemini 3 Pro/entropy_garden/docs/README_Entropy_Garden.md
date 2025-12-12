# Entropy_Garden Documentation

## Overview

**Entropy_Garden** is a high-performance real-time telemetry dashboard that visualizes system metrics as an animated E8 lattice projection.

The E8 lattice is an 8-dimensional mathematical structure with exceptional symmetry. This visualization projects its 240 root vectors into 3D space, where each vertex responds in real-time to CPU, GPU, memory, and other system entropy metrics.

---

## Architecture

```
┌─────────────────┐     WebSocket     ┌─────────────────┐
│   Backend       │ ◀──────────────── │   Frontend      │
│   (FastAPI)     │      60 Hz        │   (Three.js)    │
│                 │                   │                 │
│ • Telemetry     │                   │ • E8 Lattice    │
│ • Entropy Score │                   │ • 240 Vertices  │
│ • GPU/CPU/RAM   │                   │ • 144 FPS       │
└─────────────────┘                   └─────────────────┘
```

---

## E8 Lattice Construction

The E8 root system consists of 240 vectors in 8D space:

### Type 1: 112 Roots
All permutations of `(±1, ±1, 0, 0, 0, 0, 0, 0)`:
- Choose 2 positions from 8: C(8,2) = 28 combinations
- Each position can be ±1: 4 sign combinations
- Total: 28 × 4 = 112 roots

### Type 2: 128 Roots
All vectors `(±½, ±½, ±½, ±½, ±½, ±½, ±½, ±½)` with an **even number of minus signs**:
- 256 total sign combinations
- 128 have even number of minus signs

### 8D → 3D Projection
We use a deterministic orthogonal projection based on golden-ratio rotations:
1. Create rotation matrices in planes (0,4), (1,5), (2,6)
2. Use angles π/φ, π/φ², π/φ³ where φ is golden ratio
3. Extract 3 orthogonal directions as projection basis
4. Normalize resulting 3D positions to unit sphere

---

## Entropy Score Calculation

The entropy score (0.0 - 1.0) is computed from weighted metrics:

| Metric | Weight (Balanced) | Normalization |
|--------|-------------------|---------------|
| CPU Usage | 0.25 | avg(cores) / 100 |
| Load Average | 0.10 | load_1m / cpu_count |
| Context Switches | 0.10 | switches / 100,000 |
| Memory Usage | 0.20 | used / total |
| GPU Utilization | 0.25 | util / 100 |
| VRAM Usage | 0.10 | used / total |

---

## Metric-to-Visual Mapping

| Metric | Visual Property |
|--------|-----------------|
| Entropy Score | Vertex pulsing amplitude |
| CPU | Color saturation |
| GPU | Color hue shift (green → red) |
| Memory | Vertex position wobble |
| Intensity Setting | Overall effect multiplier |

### Mapping Modes

- **Balanced**: Equal weight to CPU, GPU, memory
- **CPU Heavy**: 60% weight to CPU metrics
- **GPU Heavy**: 60% weight to GPU metrics

---

## Running the Dashboard

### Quick Start
```bash
./start_garden.sh
```
Opens http://localhost:5173 automatically.

### Manual Start
```bash
# Terminal 1: Backend
cd backend
pip install -e .
uvicorn src.main:app --port 8080

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/snapshot` | GET | One-shot metrics JSON |
| `/ws/entropy` | WS | Real-time 60 Hz stream |
| `/config/mapping` | GET/POST | Mapping mode config |

---

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| FPS | 144 | TBD |
| Frame Time | ~6.9ms | TBD |
| VRAM | < 4GB | TBD |
| RAM | < 8GB | TBD |

See `Optimization_Log.md` for iteration history.
