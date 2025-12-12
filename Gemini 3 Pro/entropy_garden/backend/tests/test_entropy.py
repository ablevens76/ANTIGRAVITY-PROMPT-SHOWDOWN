"""
Unit tests for entropy score calculation.
"""

import pytest
from src.entropy import compute_entropy_score, get_dominant_metric


class TestEntropyScore:
    def test_zero_activity(self):
        """Test entropy score with minimal activity."""
        metrics = {
            "cpu_percent_per_core": [0.0, 0.0, 0.0, 0.0],
            "load_average": (0.0, 0.0, 0.0),
            "context_switches_per_sec": 0,
            "ram_total_gb": 64.0,
            "ram_used_gb": 0.0,
            "gpu_util_percent": 0.0,
            "vram_total_gb": 12.0,
            "vram_used_gb": 0.0,
        }
        score = compute_entropy_score(metrics)
        assert score == 0.0
    
    def test_max_activity(self):
        """Test entropy score with maximum activity."""
        metrics = {
            "cpu_percent_per_core": [100.0, 100.0, 100.0, 100.0],
            "load_average": (24.0, 24.0, 24.0),  # 24-core system fully loaded
            "context_switches_per_sec": 200000,
            "ram_total_gb": 64.0,
            "ram_used_gb": 64.0,
            "gpu_util_percent": 100.0,
            "vram_total_gb": 12.0,
            "vram_used_gb": 12.0,
        }
        score = compute_entropy_score(metrics)
        assert 0.9 <= score <= 1.0
    
    def test_partial_activity(self):
        """Test entropy score with partial activity."""
        metrics = {
            "cpu_percent_per_core": [50.0, 50.0, 50.0, 50.0],
            "load_average": (2.0, 2.0, 2.0),
            "context_switches_per_sec": 50000,
            "ram_total_gb": 64.0,
            "ram_used_gb": 32.0,
            "gpu_util_percent": 50.0,
            "vram_total_gb": 12.0,
            "vram_used_gb": 6.0,
        }
        score = compute_entropy_score(metrics)
        assert 0.3 <= score <= 0.7
    
    def test_custom_weights(self):
        """Test entropy score with custom weights."""
        metrics = {
            "cpu_percent_per_core": [100.0],
            "load_average": (0.0, 0.0, 0.0),
            "context_switches_per_sec": 0,
            "ram_total_gb": 64.0,
            "ram_used_gb": 0.0,
            "gpu_util_percent": 0.0,
            "vram_total_gb": 12.0,
            "vram_used_gb": 0.0,
        }
        
        # CPU-heavy weights
        cpu_heavy_weights = {"cpu": 1.0, "load": 0, "ctx": 0, "mem": 0, "gpu": 0, "vram": 0}
        score = compute_entropy_score(metrics, cpu_heavy_weights)
        assert score == 1.0
    
    def test_score_in_valid_range(self):
        """Test that score is always between 0 and 1."""
        import random
        
        for _ in range(100):
            metrics = {
                "cpu_percent_per_core": [random.uniform(0, 100) for _ in range(8)],
                "load_average": (random.uniform(0, 10), random.uniform(0, 10), random.uniform(0, 10)),
                "context_switches_per_sec": random.uniform(0, 200000),
                "ram_total_gb": 64.0,
                "ram_used_gb": random.uniform(0, 64),
                "gpu_util_percent": random.uniform(0, 100),
                "vram_total_gb": 12.0,
                "vram_used_gb": random.uniform(0, 12),
            }
            score = compute_entropy_score(metrics)
            assert 0.0 <= score <= 1.0


class TestDominantMetric:
    def test_cpu_dominant(self):
        """Test detection of CPU as dominant metric."""
        metrics = {
            "cpu_percent_per_core": [90.0, 90.0],
            "ram_total_gb": 64.0,
            "ram_used_gb": 10.0,
            "gpu_util_percent": 10.0,
        }
        assert get_dominant_metric(metrics) == "cpu"
    
    def test_gpu_dominant(self):
        """Test detection of GPU as dominant metric."""
        metrics = {
            "cpu_percent_per_core": [10.0, 10.0],
            "ram_total_gb": 64.0,
            "ram_used_gb": 10.0,
            "gpu_util_percent": 95.0,
        }
        assert get_dominant_metric(metrics) == "gpu"
