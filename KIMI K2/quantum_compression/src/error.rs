//! Error types for quantum compression

use thiserror::Error;

#[derive(Error, Debug)]
pub enum CompressionError {
    #[error("Input data too small: {0} bytes (minimum: 64)")]
    InputTooSmall(usize),
    
    #[error("Tensor decomposition failed: {0}")]
    TensorDecomposition(String),
    
    #[error("Huffman encoding failed: {0}")]
    HuffmanEncoding(String),
    
    #[error("Decompression failed: data corrupted")]
    DecompressionFailed,
    
    #[error("VRAM allocation failed: requested {requested} bytes, available {available}")]
    VramAllocation { requested: usize, available: usize },
    
    #[error("GPU not available")]
    GpuNotAvailable,
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, CompressionError>;
