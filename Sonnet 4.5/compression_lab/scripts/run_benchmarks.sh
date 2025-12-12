#!/bin/bash
# run_benchmarks.sh - Run full benchmark suite

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Compression Lab Benchmark Runner"
echo "===================================="
echo ""

# Check GPU
echo "📊 GPU Status:"
nvidia-smi --query-gpu=name,memory.used,memory.total,temperature.gpu --format=csv,noheader
echo ""

# Check thermal
TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader)
if [ "$TEMP" -gt 75 ]; then
    echo "⚠️ GPU temperature high ($TEMP°C). Waiting to cool down..."
    sleep 30
fi

# Run benchmarks
echo "🔬 Starting benchmarks..."
echo ""

cd benchmarks
python3 harness.py

echo ""
echo "📈 Results saved to results/benchmarks.db"
echo "📄 CSV export at results/benchmark_results.csv"
echo ""
echo "🌐 To view dashboard:"
echo "   cd dashboard && python3 server.py"
echo "   Open http://localhost:8080"
