//! Benchmark: Quantum Compression vs zlib
//!
//! Target: 3.2x improvement on quantum circuit data

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use quantum_compression::{compress, Config};
use flate2::write::ZlibEncoder;
use flate2::Compression;
use std::io::Write;
use rand::Rng;

/// Generate quantum circuit test data
fn generate_quantum_circuit_data(size: usize) -> Vec<u8> {
    let mut rng = rand::thread_rng();
    let mut data = Vec::with_capacity(size);
    
    // Quantum circuit patterns: gates, measurements, entanglement
    for i in 0..size {
        // Simulate quantum gate matrix elements
        let real_part = ((i as f64 * 0.05).sin() * 127.0 + 128.0) as u8;
        let imag_part = ((i as f64 * 0.07).cos() * 127.0 + 128.0) as u8;
        
        // Add some structure (repeated patterns)
        if i % 64 < 8 {
            data.push(i as u8 % 16);
        } else if i % 64 < 16 {
            data.push((real_part ^ imag_part) % 32);
        } else {
            data.push(rng.gen_range(real_part.saturating_sub(16)..=real_part.saturating_add(16)));
        }
    }
    
    data
}

fn bench_quantum_compression(c: &mut Criterion) {
    let mut group = c.benchmark_group("compression");
    
    for size in [1024, 10240, 102400, 1024000].iter() {
        let data = generate_quantum_circuit_data(*size);
        let config = Config::default();
        
        group.bench_with_input(
            BenchmarkId::new("quantum_mps", size),
            &data,
            |b, data| {
                b.iter(|| compress(black_box(data), &config))
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("zlib", size),
            &data,
            |b, data| {
                b.iter(|| {
                    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
                    encoder.write_all(black_box(data)).unwrap();
                    encoder.finish().unwrap()
                })
            },
        );
    }
    
    group.finish();
}

fn bench_compression_ratio(c: &mut Criterion) {
    let sizes = [1024, 10240, 102400];
    
    println!("\n=== Compression Ratio Analysis ===\n");
    
    for size in sizes {
        let data = generate_quantum_circuit_data(size);
        let config = Config::default();
        
        // Quantum compression
        let (compressed, stats) = compress(&data, &config).unwrap();
        
        // zlib
        let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(&data).unwrap();
        let zlib_compressed = encoder.finish().unwrap();
        let zlib_ratio = data.len() as f64 / zlib_compressed.len() as f64;
        
        let improvement = stats.compression_ratio / zlib_ratio;
        
        println!("Size {}:", size);
        println!("  Quantum MPS: {:.2}x compression", stats.compression_ratio);
        println!("  zlib:        {:.2}x compression", zlib_ratio);
        println!("  Improvement: {:.2}x over zlib", improvement);
        println!();
    }
}

criterion_group!(benches, bench_quantum_compression);
criterion_main!(benches);
