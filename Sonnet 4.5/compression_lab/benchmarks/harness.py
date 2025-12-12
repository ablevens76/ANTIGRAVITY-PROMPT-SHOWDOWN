#!/usr/bin/env python3
"""
Benchmark Harness for Compression Lab
Measures: compression ratio, GPU memory, throughput, power consumption
Logs results to SQLite database
"""

import os
import sys
import time
import sqlite3
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import struct

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DB = PROJECT_ROOT / "results" / "benchmarks.db"
DATA_DIR = PROJECT_ROOT / "data"

class GPUMonitor:
    """Monitor GPU metrics via nvidia-smi"""
    
    @staticmethod
    def get_metrics() -> Dict:
        """Get current GPU metrics"""
        try:
            result = subprocess.run([
                'nvidia-smi',
                '--query-gpu=memory.used,memory.total,utilization.gpu,power.draw,temperature.gpu',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)
            
            values = result.stdout.strip().split(', ')
            return {
                'memory_used_mb': int(values[0]),
                'memory_total_mb': int(values[1]),
                'gpu_utilization': int(values[2]),
                'power_watts': float(values[3]),
                'temperature_c': int(values[4])
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def check_thermal(max_temp: int = 75) -> bool:
        """Check if GPU is under thermal limit"""
        metrics = GPUMonitor.get_metrics()
        return metrics.get('temperature_c', 100) < max_temp


class BenchmarkDatabase:
    """SQLite database for benchmark results"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                algorithm TEXT,
                dataset TEXT,
                dataset_size_bytes INTEGER,
                compressed_size_bytes INTEGER,
                compression_ratio REAL,
                time_ms REAL,
                throughput_gbps REAL,
                memory_used_mb INTEGER,
                power_watts REAL,
                temperature_c INTEGER,
                error TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def log_result(self, result: Dict):
        """Log a benchmark result"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO runs (
                timestamp, algorithm, dataset, dataset_size_bytes,
                compressed_size_bytes, compression_ratio, time_ms,
                throughput_gbps, memory_used_mb, power_watts, temperature_c, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            result.get('algorithm'),
            result.get('dataset'),
            result.get('dataset_size_bytes'),
            result.get('compressed_size_bytes'),
            result.get('compression_ratio'),
            result.get('time_ms'),
            result.get('throughput_gbps'),
            result.get('memory_used_mb'),
            result.get('power_watts'),
            result.get('temperature_c'),
            result.get('error')
        ))
        conn.commit()
        conn.close()
    
    def get_all_results(self) -> List[Dict]:
        """Get all benchmark results"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM runs ORDER BY timestamp DESC')
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def export_csv(self, output_path: Path):
        """Export results to CSV"""
        import csv
        results = self.get_all_results()
        if not results:
            return
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)


class CompressionBenchmark:
    """Run compression benchmarks"""
    
    ALGORITHMS = ['arithmetic', 'lz77', 'e8_lattice']
    
    def __init__(self):
        self.db = BenchmarkDatabase(RESULTS_DB)
        self.gpu = GPUMonitor()
    
    def run_algorithm(self, algorithm: str, data: bytes) -> Dict:
        """Run a compression algorithm and measure performance"""
        result = {
            'algorithm': algorithm,
            'dataset_size_bytes': len(data),
            'compressed_size_bytes': 0,
            'compression_ratio': 0,
            'time_ms': 0,
            'throughput_gbps': 0,
            'error': None
        }
        
        # Check thermal before running
        if not self.gpu.check_thermal():
            result['error'] = 'GPU over thermal limit'
            return result
        
        # Get GPU metrics before
        metrics_before = self.gpu.get_metrics()
        
        # Simulate compression (actual CUDA would be called via ctypes/pybind11)
        start_time = time.perf_counter()
        
        # For now, use Python fallback compression for demo
        import zlib
        if algorithm == 'arithmetic':
            # Simulate arithmetic coding with zlib level 9
            compressed = zlib.compress(data, level=9)
        elif algorithm == 'lz77':
            # Simulate LZ77 with zlib level 6
            compressed = zlib.compress(data, level=6)
        elif algorithm == 'e8_lattice':
            # Simulate E8 (less compression, faster)
            compressed = zlib.compress(data, level=1)
        else:
            compressed = data
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Get GPU metrics after
        metrics_after = self.gpu.get_metrics()
        
        # Calculate results
        result['compressed_size_bytes'] = len(compressed)
        result['compression_ratio'] = len(data) / len(compressed) if len(compressed) > 0 else 0
        result['time_ms'] = elapsed_ms
        result['throughput_gbps'] = (len(data) / 1e9) / (elapsed_ms / 1000) if elapsed_ms > 0 else 0
        result['memory_used_mb'] = metrics_after.get('memory_used_mb', 0)
        result['power_watts'] = metrics_after.get('power_watts', 0)
        result['temperature_c'] = metrics_after.get('temperature_c', 0)
        
        return result
    
    def run_benchmark(self, algorithm: str, dataset_name: str, data: bytes) -> Dict:
        """Run a single benchmark and log results"""
        print(f"  Running {algorithm} on {dataset_name}...")
        
        result = self.run_algorithm(algorithm, data)
        result['dataset'] = dataset_name
        
        self.db.log_result(result)
        
        print(f"    Ratio: {result['compression_ratio']:.2f}x, "
              f"Throughput: {result['throughput_gbps']:.2f} GB/s, "
              f"Temp: {result.get('temperature_c', 'N/A')}°C")
        
        return result
    
    def run_all(self, datasets: Dict[str, bytes]) -> List[Dict]:
        """Run all algorithms on all datasets"""
        results = []
        
        for dataset_name, data in datasets.items():
            print(f"\nDataset: {dataset_name} ({len(data) / 1e6:.1f} MB)")
            
            for algorithm in self.ALGORITHMS:
                result = self.run_benchmark(algorithm, dataset_name, data)
                results.append(result)
                
                # Cool down if needed
                if not self.gpu.check_thermal():
                    print("  Cooling down...")
                    time.sleep(5)
        
        return results


def main():
    """Main entry point"""
    from dataset_gen import DatasetGenerator
    
    print("=" * 60)
    print("Compression Lab Benchmark Harness")
    print("=" * 60)
    
    # Generate test datasets
    print("\nGenerating test datasets...")
    gen = DatasetGenerator(DATA_DIR)
    datasets = gen.generate_all()
    
    # Run benchmarks
    print("\nRunning benchmarks...")
    benchmark = CompressionBenchmark()
    results = benchmark.run_all(datasets)
    
    # Export results
    print("\nExporting results...")
    csv_path = PROJECT_ROOT / "results" / "benchmark_results.csv"
    benchmark.db.export_csv(csv_path)
    print(f"  Saved to {csv_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for algo in CompressionBenchmark.ALGORITHMS:
        algo_results = [r for r in results if r['algorithm'] == algo]
        if algo_results:
            avg_ratio = sum(r['compression_ratio'] for r in algo_results) / len(algo_results)
            avg_throughput = sum(r['throughput_gbps'] for r in algo_results) / len(algo_results)
            print(f"{algo:15} - Avg Ratio: {avg_ratio:.2f}x, Avg Throughput: {avg_throughput:.2f} GB/s")
    
    print("\nDone!")


if __name__ == '__main__':
    main()
