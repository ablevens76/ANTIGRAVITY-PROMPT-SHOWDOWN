#!/usr/bin/env python3
"""
Test Dataset Generator for Compression Lab
Generates diverse test data: text, binary, structured, random
Sizes: 10MB to 500MB
"""

import os
import random
import struct
from pathlib import Path
from typing import Dict

class DatasetGenerator:
    """Generate diverse test datasets"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_text(self, size_mb: int = 10) -> bytes:
        """Generate text data with English-like patterns"""
        words = [
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'I',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'quantum', 'compression', 'algorithm', 'tensor', 'network', 'lattice',
            'parallel', 'GPU', 'CUDA', 'optimization', 'benchmark', 'performance'
        ]
        
        target_size = size_mb * 1024 * 1024
        result = []
        current_size = 0
        
        while current_size < target_size:
            sentence_len = random.randint(5, 20)
            sentence = ' '.join(random.choices(words, k=sentence_len))
            sentence = sentence.capitalize() + '. '
            result.append(sentence)
            current_size += len(sentence)
        
        return ''.join(result)[:target_size].encode('utf-8')
    
    def generate_binary(self, size_mb: int = 10) -> bytes:
        """Generate binary data with patterns (simulated executable)"""
        target_size = size_mb * 1024 * 1024
        result = bytearray(target_size)
        
        # Mix of patterns and random data
        patterns = [
            bytes([0x00] * 16),  # Null padding
            bytes([0xFF] * 16),  # All ones
            bytes(range(16)),    # Sequential
            bytes([0x90] * 16),  # NOP sled
        ]
        
        pos = 0
        while pos < target_size:
            if random.random() < 0.3:
                # Insert pattern
                pattern = random.choice(patterns)
                end = min(pos + len(pattern), target_size)
                result[pos:end] = pattern[:end-pos]
                pos = end
            else:
                # Random byte
                result[pos] = random.randint(0, 255)
                pos += 1
        
        return bytes(result)
    
    def generate_structured(self, size_mb: int = 10) -> bytes:
        """Generate structured data (JSON-like)"""
        target_size = size_mb * 1024 * 1024
        
        template = '''{"id":%d,"name":"item_%d","value":%.4f,"tags":["tag_%d","tag_%d"],"nested":{"a":%d,"b":%.2f}},\n'''
        
        result = []
        current_size = 0
        i = 0
        
        while current_size < target_size:
            entry = template % (
                i, i,
                random.uniform(0, 1000),
                i % 100, (i + 1) % 100,
                random.randint(0, 1000),
                random.uniform(0, 100)
            )
            result.append(entry)
            current_size += len(entry)
            i += 1
        
        data = '[' + ''.join(result)[:-2] + ']'
        return data[:target_size].encode('utf-8')
    
    def generate_random(self, size_mb: int = 10) -> bytes:
        """Generate purely random data (incompressible)"""
        target_size = size_mb * 1024 * 1024
        return os.urandom(target_size)
    
    def generate_quantum_circuit(self, size_mb: int = 10) -> bytes:
        """Generate quantum circuit-like data (structured floats)"""
        target_size = size_mb * 1024 * 1024
        num_floats = target_size // 4
        
        result = bytearray()
        
        for i in range(num_floats):
            # Quantum amplitude patterns
            phase = (i * 0.01) % (2 * 3.14159)
            amplitude = 0.5 + 0.5 * ((i % 256) / 255.0)
            val = amplitude * (0.5 + 0.5 * (phase / 3.14159))
            
            # Add some noise
            val += random.uniform(-0.01, 0.01)
            
            result.extend(struct.pack('f', val))
        
        return bytes(result[:target_size])
    
    def generate_all(self) -> Dict[str, bytes]:
        """Generate all test datasets"""
        datasets = {}
        
        # Small datasets (10MB)
        print("  Generating text_10mb...")
        datasets['text_10mb'] = self.generate_text(10)
        
        print("  Generating binary_10mb...")
        datasets['binary_10mb'] = self.generate_binary(10)
        
        print("  Generating structured_10mb...")
        datasets['structured_10mb'] = self.generate_structured(10)
        
        print("  Generating random_10mb...")
        datasets['random_10mb'] = self.generate_random(10)
        
        print("  Generating quantum_10mb...")
        datasets['quantum_10mb'] = self.generate_quantum_circuit(10)
        
        # Medium datasets (50MB)
        print("  Generating text_50mb...")
        datasets['text_50mb'] = self.generate_text(50)
        
        print("  Generating quantum_50mb...")
        datasets['quantum_50mb'] = self.generate_quantum_circuit(50)
        
        # Large dataset (100MB) - optional
        # Uncomment for full benchmarks
        # print("  Generating text_100mb...")
        # datasets['text_100mb'] = self.generate_text(100)
        
        return datasets
    
    def save_dataset(self, name: str, data: bytes):
        """Save dataset to file"""
        path = self.output_dir / f"{name}.bin"
        with open(path, 'wb') as f:
            f.write(data)
        return path


if __name__ == '__main__':
    gen = DatasetGenerator(Path('data'))
    datasets = gen.generate_all()
    
    print("\nGenerated datasets:")
    for name, data in datasets.items():
        print(f"  {name}: {len(data) / 1e6:.1f} MB")
