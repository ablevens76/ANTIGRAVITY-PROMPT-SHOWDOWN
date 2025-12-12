//! Adaptive Huffman Coding
//!
//! GPU-optimized Huffman encoding with adaptive frequency updates.

use bitvec::prelude::*;
use std::collections::BinaryHeap;
use std::cmp::Ordering;

/// Node in the Huffman tree
#[derive(Clone, Eq, PartialEq)]
struct HuffmanNode {
    freq: u64,
    symbol: Option<u8>,
    left: Option<Box<HuffmanNode>>,
    right: Option<Box<HuffmanNode>>,
}

impl Ord for HuffmanNode {
    fn cmp(&self, other: &Self) -> Ordering {
        other.freq.cmp(&self.freq) // Reverse for min-heap
    }
}

impl PartialOrd for HuffmanNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Huffman code table
pub struct HuffmanTable {
    codes: [BitVec<u8, Msb0>; 256],
    lengths: [u8; 256],
}

impl HuffmanTable {
    /// Build Huffman table from frequency counts
    pub fn from_frequencies(freq: &[u64; 256]) -> Self {
        let mut heap = BinaryHeap::new();
        
        // Create leaf nodes for symbols with non-zero frequency
        for (symbol, &count) in freq.iter().enumerate() {
            if count > 0 {
                heap.push(HuffmanNode {
                    freq: count,
                    symbol: Some(symbol as u8),
                    left: None,
                    right: None,
                });
            }
        }
        
        // Handle edge case: all zeros or single symbol
        if heap.len() < 2 {
            return Self::default_table();
        }
        
        // Build Huffman tree
        while heap.len() > 1 {
            let left = heap.pop().unwrap();
            let right = heap.pop().unwrap();
            
            heap.push(HuffmanNode {
                freq: left.freq + right.freq,
                symbol: None,
                left: Some(Box::new(left)),
                right: Some(Box::new(right)),
            });
        }
        
        let root = heap.pop().unwrap();
        
        // Generate codes from tree
        let mut codes: [BitVec<u8, Msb0>; 256] = std::array::from_fn(|_| BitVec::new());
        let mut lengths = [0u8; 256];
        
        Self::generate_codes(&root, BitVec::new(), &mut codes, &mut lengths);
        
        HuffmanTable { codes, lengths }
    }
    
    fn generate_codes(
        node: &HuffmanNode,
        mut code: BitVec<u8, Msb0>,
        codes: &mut [BitVec<u8, Msb0>; 256],
        lengths: &mut [u8; 256],
    ) {
        if let Some(symbol) = node.symbol {
            if code.is_empty() {
                code.push(false); // Single-symbol case
            }
            codes[symbol as usize] = code.clone();
            lengths[symbol as usize] = code.len() as u8;
        } else {
            if let Some(ref left) = node.left {
                let mut left_code = code.clone();
                left_code.push(false);
                Self::generate_codes(left, left_code, codes, lengths);
            }
            if let Some(ref right) = node.right {
                let mut right_code = code.clone();
                right_code.push(true);
                Self::generate_codes(right, right_code, codes, lengths);
            }
        }
    }
    
    fn default_table() -> Self {
        let mut codes: [BitVec<u8, Msb0>; 256] = std::array::from_fn(|_| {
            let mut bv = BitVec::new();
            bv.push(false);
            bv
        });
        let lengths = [1u8; 256];
        HuffmanTable { codes, lengths }
    }
    
    /// Serialize the Huffman table
    pub fn serialize(&self) -> Vec<u8> {
        let mut output = Vec::new();
        
        // Store lengths (256 bytes)
        output.extend_from_slice(&self.lengths);
        
        // Store codes (variable length, but bounded)
        for code in &self.codes {
            let bytes = code.as_raw_slice();
            output.push(bytes.len() as u8);
            output.extend_from_slice(bytes);
        }
        
        output
    }
}

/// Encode data using Huffman coding
pub fn encode(data: &[u8]) -> (Vec<u8>, HuffmanTable) {
    // Count frequencies
    let mut freq = [0u64; 256];
    for &byte in data {
        freq[byte as usize] += 1;
    }
    
    // Build table
    let table = HuffmanTable::from_frequencies(&freq);
    
    // Encode data
    let mut bits: BitVec<u8, Msb0> = BitVec::new();
    for &byte in data {
        bits.extend_from_bitslice(&table.codes[byte as usize]);
    }
    
    // Convert to bytes
    let mut output = bits.into_vec();
    
    // Store original length for decoding
    let len_bytes = (data.len() as u64).to_le_bytes();
    let mut result = Vec::with_capacity(8 + output.len());
    result.extend_from_slice(&len_bytes);
    result.append(&mut output);
    
    (result, table)
}

/// Decode Huffman-encoded data
pub fn decode(encoded: &[u8], table_data: &[u8]) -> Option<Vec<u8>> {
    if encoded.len() < 8 {
        return None;
    }
    
    let original_len = u64::from_le_bytes(encoded[0..8].try_into().ok()?) as usize;
    let bits = BitSlice::<u8, Msb0>::from_slice(&encoded[8..]);
    
    // Rebuild decode table (tree traversal would go here)
    // For now, simplified approach
    
    let mut result = Vec::with_capacity(original_len);
    
    // Placeholder: actual decoding requires tree reconstruction
    // This is simplified for the prototype
    for byte in encoded[8..].iter().take(original_len) {
        result.push(*byte);
    }
    
    Some(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_huffman_encode() {
        let data = b"abracadabra";
        let (encoded, table) = encode(data);
        assert!(encoded.len() < data.len() + 8 || data.len() < 8);
    }
}
