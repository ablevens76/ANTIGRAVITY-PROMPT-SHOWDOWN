#!/bin/bash
# Entropy Garden - One-Click Launcher
# Starts backend and frontend, opens browser automatically

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "🌿 ═══════════════════════════════════════════════════════════"
echo "   Entropy Garden - E8 Lattice Telemetry Dashboard"
echo "🌿 ═══════════════════════════════════════════════════════════"

# Check dependencies
echo ""
echo "📦 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found"
    exit 1
fi

echo "✅ Python: $(python3 --version)"
echo "✅ Node: $(node --version)"

# Install backend dependencies
echo ""
echo "📦 Installing backend dependencies..."
cd "$BACKEND_DIR"
pip install -e . --quiet 2>/dev/null || pip install fastapi uvicorn psutil pynvml --quiet

# Install frontend dependencies
echo ""
echo "📦 Installing frontend dependencies..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    npm install --silent
fi

# Kill any existing processes on our ports
echo ""
echo "🔄 Checking for existing processes..."
pkill -f "uvicorn.*8080" 2>/dev/null || true
pkill -f "vite.*5173" 2>/dev/null || true
sleep 1

# Start backend
echo ""
echo "🚀 Starting backend server (port 8080)..."
cd "$BACKEND_DIR"
python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8080 --log-level warning &
BACKEND_PID=$!
sleep 2

# Verify backend started
if ! curl -s http://localhost:8080/ > /dev/null; then
    echo "❌ Backend failed to start"
    exit 1
fi
echo "✅ Backend running at http://localhost:8080"

# Start frontend
echo ""
echo "🎨 Starting frontend dev server (port 5173)..."
cd "$FRONTEND_DIR"
npm run dev -- --host 127.0.0.1 &
FRONTEND_PID=$!
sleep 3

echo ""
echo "🌿 ═══════════════════════════════════════════════════════════"
echo "   Entropy Garden is ready!"
echo "🌿 ═══════════════════════════════════════════════════════════"
echo ""
echo "   📊 Backend API:  http://localhost:8080"
echo "   🎨 Frontend UI:  http://localhost:5173"
echo "   📡 WebSocket:    ws://localhost:8080/ws/entropy"
echo ""
echo "   Press Ctrl+C to stop all services"
echo "🌿 ═══════════════════════════════════════════════════════════"

# Open browser (if available)
if command -v xdg-open &> /dev/null; then
    sleep 1
    xdg-open "http://localhost:5173" 2>/dev/null &
fi

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down Entropy Garden..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "👋 Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait
