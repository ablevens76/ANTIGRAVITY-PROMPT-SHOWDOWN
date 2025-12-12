"""
Entropy score calculation for Entropy_Garden.
Computes a normalized 0.0-1.0 "chaos" score from system metrics.
"""

from typing import Dict, List
from statistics import mean


def compute_entropy_score(metrics: dict, weights: dict = None) -> float:
    """
    Compute a weighted entropy score from system metrics.
    
    Higher entropy = more system activity/chaos.
    
    Args:
        metrics: Dictionary containing system telemetry
        weights: Optional custom weights for each component
        
    Returns:
        Normalized entropy score between 0.0 and 1.0
    """
    if weights is None:
        weights = {
            "cpu": 0.25,
            "load": 0.1,
            "ctx": 0.1,
            "mem": 0.2,
            "gpu": 0.25,
            "vram": 0.1,
        }
    
    # Normalize each metric to 0-1 range
    components = []
    
    # CPU usage (average across cores)
    cpu_cores = metrics.get("cpu_percent_per_core", [0])
    if cpu_cores:
        cpu_normalized = mean(cpu_cores) / 100.0
        components.append(("cpu", weights.get("cpu", 0) * cpu_normalized))
    
    # Load average (normalized to core count)
    load_avg = metrics.get("load_average", (0, 0, 0))
    if isinstance(load_avg, (list, tuple)) and len(load_avg) >= 1:
        import os
        cpu_count = os.cpu_count() or 1
        load_normalized = min(load_avg[0] / cpu_count, 1.0)
        components.append(("load", weights.get("load", 0) * load_normalized))
    
    # Context switches (normalized to ~100k/sec as "high")
    ctx_switches = metrics.get("context_switches_per_sec", 0)
    ctx_normalized = min(ctx_switches / 100000.0, 1.0)
    components.append(("ctx", weights.get("ctx", 0) * ctx_normalized))
    
    # Memory usage
    ram_total = metrics.get("ram_total_gb", 1)
    ram_used = metrics.get("ram_used_gb", 0)
    if ram_total > 0:
        mem_normalized = ram_used / ram_total
        components.append(("mem", weights.get("mem", 0) * mem_normalized))
    
    # GPU utilization
    gpu_util = metrics.get("gpu_util_percent", 0)
    gpu_normalized = gpu_util / 100.0
    components.append(("gpu", weights.get("gpu", 0) * gpu_normalized))
    
    # VRAM usage
    vram_total = metrics.get("vram_total_gb", 1)
    vram_used = metrics.get("vram_used_gb", 0)
    if vram_total > 0:
        vram_normalized = vram_used / vram_total
        components.append(("vram", weights.get("vram", 0) * vram_normalized))
    
    # Sum weighted components and normalize
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    
    entropy = sum(value for _, value in components) / total_weight
    
    # Clamp to valid range
    return max(0.0, min(1.0, entropy))


def get_dominant_metric(metrics: dict) -> str:
    """
    Determine which metric is currently most dominant.
    Useful for visual emphasis in the frontend.
    """
    scores = {}
    
    # CPU
    cpu_cores = metrics.get("cpu_percent_per_core", [0])
    scores["cpu"] = mean(cpu_cores) if cpu_cores else 0
    
    # Memory
    ram_total = metrics.get("ram_total_gb", 1)
    ram_used = metrics.get("ram_used_gb", 0)
    scores["memory"] = (ram_used / ram_total * 100) if ram_total > 0 else 0
    
    # GPU
    scores["gpu"] = metrics.get("gpu_util_percent", 0)
    
    return max(scores.keys(), key=lambda k: scores[k])


if __name__ == "__main__":
    # Test entropy calculation
    test_metrics = {
        "cpu_percent_per_core": [45.0, 50.0, 30.0, 60.0],
        "load_average": (2.5, 2.0, 1.8),
        "context_switches_per_sec": 50000,
        "ram_total_gb": 64.0,
        "ram_used_gb": 24.0,
        "gpu_util_percent": 35.0,
        "vram_total_gb": 12.0,
        "vram_used_gb": 3.5,
    }
    
    score = compute_entropy_score(test_metrics)
    dominant = get_dominant_metric(test_metrics)
    
    print(f"Entropy Score: {score:.3f}")
    print(f"Dominant Metric: {dominant}")
