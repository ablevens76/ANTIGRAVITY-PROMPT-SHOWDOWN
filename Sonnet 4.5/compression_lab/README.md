# Compression Lab

Self-optimizing GPU compression algorithm research for RTX 4070.

## Overview

Three CUDA-accelerated compression algorithms:
1. **Arithmetic Coding** - Parallel entropy estimation + range encoding
2. **LZ77 Parallel** - Hash-based matching with sliding window
3. **E8 Lattice** - Novel E8 root pattern recognition (research)

## Quick Start

```bash
# Install dependencies
pip install flask

# Run benchmarks
cd scripts
chmod +x *.sh
./run_benchmarks.sh

# View dashboard
cd ../dashboard
python3 server.py
# Open http://localhost:8080
```

## Project Structure

```
compression_lab/
├── src/cuda/
│   ├── common.cuh           # CUDA utilities
│   ├── arithmetic_coding.cu # Range encoder
│   ├── lz77_parallel.cu     # LZ77 with hash
│   └── e8_lattice.cu        # E8 pattern matching
├── benchmarks/
│   ├── harness.py           # Benchmark runner
│   └── dataset_gen.py       # Test data generator
├── dashboard/
│   ├── index.html           # D3.js/Chart.js UI
│   └── server.py            # Flask API
├── scripts/
│   ├── build.sh             # CUDA compiler
│   └── run_benchmarks.sh    # Full suite runner
└── results/
    └── benchmarks.db        # SQLite database
```

## Hardware Requirements

| Component | Requirement |
|-----------|-------------|
| GPU | RTX 4070 or better (SM 8.9+) |
| VRAM | 12GB |
| RAM | 64GB (for large datasets) |
| CUDA | 11.0+ |

## Algorithms

### Arithmetic Coding (SM 8.9)
- Block-parallel frequency counting
- Prefix sum for CDF
- Range encoding with renormalization
- **Best for**: High compression on text

### LZ77 Parallel
- Hash table for 3-byte sequences
- Parallel match finding (64-chain limit)
- Token encoding: literal or (length, offset)
- **Best for**: Balanced speed/ratio

### E8 Lattice (Research)
- 240 E8 root vectors for pattern matching
- Maps 64-byte blocks to 8D vectors
- Quantized residual encoding
- **Best for**: Structured/scientific data

## Performance Targets

- Throughput: >10 GB/s
- VRAM: <85% utilization
- Temperature: <75°C

## License

MIT
