//! Quantum Compression Library
//!
//! Hybrid compression using Matrix Product States (MPS) tensor networks
//! combined with adaptive Huffman coding, optimized for RTX 4070.

pub mod mps;
pub mod huffman;
pub mod compress;
pub mod error;

pub use compress::{compress, decompress};
pub use error::CompressionError;

/// Configuration for the compression algorithm
#[derive(Debug, Clone)]
pub struct Config {
    /// Maximum tensor rank for MPS decomposition
    pub max_rank: usize,
    /// Chunk size for parallel processing (bytes)
    pub chunk_size: usize,
    /// Use GPU acceleration if available
    pub use_gpu: bool,
    /// VRAM budget in bytes (default: 10GB of 12GB)
    pub vram_budget: usize,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            max_rank: 64,
            chunk_size: 1024 * 1024, // 1MB chunks
            use_gpu: true,
            vram_budget: 10 * 1024 * 1024 * 1024, // 10GB
        }
    }
}

/// Compression statistics
#[derive(Debug, Clone, serde::Serialize)]
pub struct CompressionStats {
    pub original_size: usize,
    pub compressed_size: usize,
    pub compression_ratio: f64,
    pub processing_time_ms: f64,
    pub tensor_rank_used: usize,
    pub vram_peak_bytes: usize,
}

impl CompressionStats {
    pub fn new(original: usize, compressed: usize, time_ms: f64) -> Self {
        Self {
            original_size: original,
            compressed_size: compressed,
            compression_ratio: original as f64 / compressed as f64,
            processing_time_ms: time_ms,
            tensor_rank_used: 0,
            vram_peak_bytes: 0,
        }
    }
}
