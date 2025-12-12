#!/bin/bash
# build_popos.sh - PopOS! specific build script for Quantum Compression
# Optimized for RTX 4070 (Ada Lovelace, SM 8.9)

set -e

echo "🔧 Quantum Compression Build Script for Pop!_OS"
echo "================================================"
echo ""

# System info
echo "📊 System Information:"
echo "  CPU: $(lscpu | grep 'Model name' | cut -d':' -f2 | xargs)"
echo "  RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo ""

# Rust version
echo "🦀 Rust Version:"
rustc --version
cargo --version
echo ""

# CUDA check
echo "🎮 CUDA Check:"
if command -v nvcc &> /dev/null; then
    echo "  NVCC: $(nvcc --version | grep release | awk '{print $6}')"
else
    echo "  NVCC: Not found (CUDA kernels disabled)"
fi

if command -v nvidia-smi &> /dev/null; then
    echo "  Driver: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader)"
    echo "  VRAM: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader)"
fi
echo ""

# Set native CPU flags
export RUSTFLAGS="-C target-cpu=native -C opt-level=3"

# CUDA compute capability for RTX 4070 (Ada Lovelace)
export CUDA_ARCH="sm_89"

echo "⚙️  Build Configuration:"
echo "  RUSTFLAGS: $RUSTFLAGS"
echo "  CUDA_ARCH: $CUDA_ARCH"
echo ""

# Clean previous build
echo "🧹 Cleaning previous build..."
cargo clean 2>/dev/null || true

# Build release
echo "🔨 Building release..."
time cargo build --release

# Run tests
echo "🧪 Running tests..."
cargo test --release

# Build benchmarks
echo "📈 Building benchmarks..."
cargo build --release --benches

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Output:"
ls -lh target/release/libquantum_compression.* 2>/dev/null || echo "  Library not found (expected for lib crate)"

# VRAM utilization check
echo ""
echo "🎮 GPU Memory Status:"
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv 2>/dev/null || echo "N/A"
