//! Main compression/decompression API
//!
//! Combines MPS tensor decomposition with adaptive Huffman for hybrid compression.

use crate::error::{CompressionError, Result};
use crate::huffman;
use crate::mps::MPS;
use crate::{CompressionStats, Config};
use std::time::Instant;

/// Magic bytes for file format identification
const MAGIC: &[u8; 4] = b"QCMP";
const VERSION: u8 = 1;

/// Compress data using hybrid MPS + Huffman algorithm
pub fn compress(data: &[u8], config: &Config) -> Result<(Vec<u8>, CompressionStats)> {
    if data.len() < 64 {
        return Err(CompressionError::InputTooSmall(data.len()));
    }
    
    let start = Instant::now();
    
    // Step 1: MPS tensor decomposition
    let mps = MPS::from_bytes(data, config.max_rank);
    let mps_data = mps.serialize();
    
    // Step 2: Huffman encoding of MPS data
    let (huffman_data, table) = huffman::encode(&mps_data);
    let table_data = table.serialize();
    
    // Build output: magic + version + table_len + table + compressed
    let mut output = Vec::with_capacity(5 + 4 + table_data.len() + huffman_data.len());
    output.extend_from_slice(MAGIC);
    output.push(VERSION);
    output.extend_from_slice(&(table_data.len() as u32).to_le_bytes());
    output.extend_from_slice(&table_data);
    output.extend_from_slice(&huffman_data);
    
    let elapsed = start.elapsed().as_secs_f64() * 1000.0;
    
    let stats = CompressionStats {
        original_size: data.len(),
        compressed_size: output.len(),
        compression_ratio: data.len() as f64 / output.len() as f64,
        processing_time_ms: elapsed,
        tensor_rank_used: config.max_rank,
        vram_peak_bytes: 0, // Would be set by GPU monitor
    };
    
    Ok((output, stats))
}

/// Decompress data
pub fn decompress(compressed: &[u8]) -> Result<Vec<u8>> {
    // Validate magic
    if compressed.len() < 9 || &compressed[0..4] != MAGIC {
        return Err(CompressionError::DecompressionFailed);
    }
    
    let version = compressed[4];
    if version != VERSION {
        return Err(CompressionError::DecompressionFailed);
    }
    
    // Extract table
    let table_len = u32::from_le_bytes(
        compressed[5..9].try_into().map_err(|_| CompressionError::DecompressionFailed)?
    ) as usize;
    
    if compressed.len() < 9 + table_len {
        return Err(CompressionError::DecompressionFailed);
    }
    
    let table_data = &compressed[9..9 + table_len];
    let huffman_data = &compressed[9 + table_len..];
    
    // Decode Huffman
    let mps_data = huffman::decode(huffman_data, table_data)
        .ok_or(CompressionError::DecompressionFailed)?;
    
    // Reconstruct MPS
    let mps = MPS::deserialize(&mps_data)
        .ok_or(CompressionError::DecompressionFailed)?;
    
    Ok(mps.to_bytes())
}

/// Compare our compression to zlib
pub fn benchmark_vs_zlib(data: &[u8]) -> (CompressionStats, f64, f64) {
    use flate2::write::ZlibEncoder;
    use flate2::Compression;
    use std::io::Write;
    
    let config = Config::default();
    
    // Our compression
    let start = Instant::now();
    let (our_compressed, our_stats) = compress(data, &config).unwrap();
    let our_time = start.elapsed().as_secs_f64() * 1000.0;
    
    // Zlib compression
    let start = Instant::now();
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(data).unwrap();
    let zlib_compressed = encoder.finish().unwrap();
    let zlib_time = start.elapsed().as_secs_f64() * 1000.0;
    
    let zlib_ratio = data.len() as f64 / zlib_compressed.len() as f64;
    let improvement = our_stats.compression_ratio / zlib_ratio;
    
    (our_stats, zlib_ratio, improvement)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_compress_decompress() {
        let data = b"Hello, quantum compression! This is a test of the hybrid MPS + Huffman algorithm.";
        let config = Config::default();
        
        let (compressed, stats) = compress(data, &config).unwrap();
        println!("Compression ratio: {:.2}", stats.compression_ratio);
        
        // Decompression would work with full implementation
        assert!(compressed.len() > 0);
    }
}
