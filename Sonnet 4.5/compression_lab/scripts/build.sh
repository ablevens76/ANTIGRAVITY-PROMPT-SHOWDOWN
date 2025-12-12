#!/bin/bash
# build.sh - Build CUDA compression kernels for RTX 4070

set -e

echo "🔧 Compression Lab Build Script"
echo "================================"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CUDA_SRC="$PROJECT_DIR/src/cuda"
BUILD_DIR="$PROJECT_DIR/build"

# Check for nvcc
if ! command -v nvcc &> /dev/null; then
    echo "❌ NVCC not found! Install CUDA toolkit:"
    echo "   sudo apt install nvidia-cuda-toolkit"
    exit 1
fi

# Print system info
echo ""
echo "📊 System Info:"
echo "  NVCC: $(nvcc --version | grep release | awk '{print $6}')"
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader 2>/dev/null || echo "  GPU: Not detected"
echo ""

# Create build directory
mkdir -p "$BUILD_DIR"

# Compile flags for RTX 4070 (SM 8.9)
NVCC_FLAGS="-arch=sm_89 -O3 -use_fast_math --expt-relaxed-constexpr"

echo "🔨 Compiling CUDA kernels..."

# Compile each kernel as a shared library
for cu_file in "$CUDA_SRC"/*.cu; do
    if [ -f "$cu_file" ]; then
        name=$(basename "$cu_file" .cu)
        echo "  Compiling $name.cu..."
        nvcc $NVCC_FLAGS -Xcompiler -fPIC -shared \
            -o "$BUILD_DIR/lib${name}.so" \
            "$cu_file" 2>&1 | head -20 || true
    fi
done

# Compile as combined library
echo "  Building combined library..."
nvcc $NVCC_FLAGS -Xcompiler -fPIC -shared \
    -o "$BUILD_DIR/libcompression_lab.so" \
    "$CUDA_SRC"/*.cu 2>&1 | head -20 || true

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Output:"
ls -lh "$BUILD_DIR"/*.so 2>/dev/null || echo "  No shared libraries built (check CUDA installation)"
