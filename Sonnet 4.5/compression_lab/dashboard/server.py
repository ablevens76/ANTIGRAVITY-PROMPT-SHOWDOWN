#!/usr/bin/env python3
"""
Flask server for Compression Lab Dashboard
Serves HTML and provides API for benchmark data
"""

import subprocess
import threading
from pathlib import Path
from flask import Flask, jsonify, send_from_directory

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'benchmarks'))

from harness import BenchmarkDatabase, GPUMonitor, CompressionBenchmark
from dataset_gen import DatasetGenerator

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DB = PROJECT_ROOT / 'results' / 'benchmarks.db'

db = BenchmarkDatabase(RESULTS_DB)
gpu_monitor = GPUMonitor()


@app.route('/')
def index():
    """Serve dashboard HTML"""
    return send_from_directory(Path(__file__).parent, 'index.html')


@app.route('/api/results')
def get_results():
    """Get benchmark results"""
    results = db.get_all_results()
    return jsonify(results)


@app.route('/api/gpu')
def get_gpu():
    """Get current GPU metrics"""
    metrics = gpu_monitor.get_metrics()
    return jsonify(metrics)


@app.route('/api/run', methods=['POST'])
def run_benchmarks():
    """Start benchmark run in background"""
    def run_in_background():
        gen = DatasetGenerator(PROJECT_ROOT / 'data')
        datasets = gen.generate_all()
        
        benchmark = CompressionBenchmark()
        benchmark.run_all(datasets)
    
    thread = threading.Thread(target=run_in_background)
    thread.start()
    
    return jsonify({'status': 'started'})


@app.route('/api/summary')
def get_summary():
    """Get summary statistics"""
    results = db.get_all_results()
    
    summary = {}
    for algo in ['arithmetic', 'lz77', 'e8_lattice']:
        algo_results = [r for r in results if r['algorithm'] == algo]
        if algo_results:
            summary[algo] = {
                'avg_ratio': sum(r['compression_ratio'] for r in algo_results) / len(algo_results),
                'avg_throughput': sum(r['throughput_gbps'] for r in algo_results) / len(algo_results),
                'count': len(algo_results)
            }
    
    return jsonify(summary)


def main():
    print("=" * 60)
    print("Compression Lab Dashboard")
    print("=" * 60)
    print(f"\nServing at http://localhost:8080")
    print("Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=8080, debug=False)


if __name__ == '__main__':
    main()
