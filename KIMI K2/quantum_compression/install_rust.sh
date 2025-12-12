#!/bin/bash
# install_rust.sh - Install Rust toolchain for Pop!_OS

set -e

echo "🦀 Installing Rust Toolchain for Pop!_OS"
echo "========================================="

# Install Rust via rustup
if ! command -v rustc &> /dev/null; then
    echo "Installing Rust via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
else
    echo "Rust already installed: $(rustc --version)"
fi

# Install additional tools
echo "Installing additional tools..."
rustup component add clippy rustfmt

# Install CUDA development dependencies (optional)
echo ""
echo "For CUDA kernel compilation, ensure:"
echo "  sudo apt install nvidia-cuda-toolkit"
echo ""

echo "✅ Rust installation complete!"
echo ""
echo "To build the project:"
echo "  cd 'KIMI K2/quantum_compression'"
echo "  cargo build --release"
