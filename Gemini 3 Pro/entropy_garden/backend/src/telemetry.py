"""
System telemetry collection for Entropy_Garden.
Non-blocking async collection of CPU, memory, and GPU metrics.
"""

import asyncio
import os
import psutil
import time
from typing import Optional, Tuple


# GPU telemetry via pynvml
_nvml_initialized = False


def init_gpu_monitoring() -> bool:
    """Initialize NVIDIA GPU monitoring. Returns True if successful."""
    global _nvml_initialized
    
    if _nvml_initialized:
        return True
    
    try:
        import pynvml
        pynvml.nvmlInit()
        _nvml_initialized = True
        return True
    except Exception as e:
        print(f"GPU monitoring unavailable: {e}")
        return False


def get_gpu_metrics() -> dict:
    """
    Get NVIDIA GPU metrics using pynvml.
    Returns empty dict if GPU not available.
    """
    if not _nvml_initialized:
        if not init_gpu_monitoring():
            return {
                "gpu_util_percent": 0.0,
                "vram_used_gb": 0.0,
                "vram_total_gb": 0.0,
                "gpu_temp_celsius": 0.0,
                "gpu_power_watts": 0.0,
            }
    
    try:
        import pynvml
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        
        # Utilization
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_util = util.gpu
        
        # Memory
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        vram_used_gb = mem.used / (1024 ** 3)
        vram_total_gb = mem.total / (1024 ** 3)
        
        # Temperature
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        
        # Power
        try:
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # mW to W
        except:
            power = 0.0
        
        return {
            "gpu_util_percent": float(gpu_util),
            "vram_used_gb": vram_used_gb,
            "vram_total_gb": vram_total_gb,
            "gpu_temp_celsius": float(temp),
            "gpu_power_watts": power,
        }
    except Exception as e:
        return {
            "gpu_util_percent": 0.0,
            "vram_used_gb": 0.0,
            "vram_total_gb": 0.0,
            "gpu_temp_celsius": 0.0,
            "gpu_power_watts": 0.0,
        }


# Track previous values for rate calculations
_prev_ctx_switches = 0
_prev_interrupts = 0
_prev_time = 0.0


def get_cpu_metrics() -> dict:
    """
    Get CPU metrics including per-core usage, load average, context switches.
    """
    global _prev_ctx_switches, _prev_interrupts, _prev_time
    
    # Per-core CPU percent (non-blocking, instant sample)
    cpu_percent = psutil.cpu_percent(interval=None, percpu=True)
    
    # Load average (1m, 5m, 15m)
    load_avg = os.getloadavg()
    
    # Context switches and interrupts (calculate rate)
    stats = psutil.cpu_stats()
    current_time = time.time()
    
    if _prev_time > 0:
        dt = current_time - _prev_time
        ctx_per_sec = (stats.ctx_switches - _prev_ctx_switches) / dt
        int_per_sec = (stats.interrupts - _prev_interrupts) / dt
    else:
        ctx_per_sec = 0.0
        int_per_sec = 0.0
    
    _prev_ctx_switches = stats.ctx_switches
    _prev_interrupts = stats.interrupts
    _prev_time = current_time
    
    return {
        "cpu_percent_per_core": cpu_percent,
        "load_average": load_avg,
        "context_switches_per_sec": ctx_per_sec,
        "interrupts_per_sec": int_per_sec,
    }


def get_memory_metrics() -> dict:
    """Get RAM usage metrics."""
    mem = psutil.virtual_memory()
    
    return {
        "ram_total_gb": mem.total / (1024 ** 3),
        "ram_used_gb": mem.used / (1024 ** 3),
        "ram_available_gb": mem.available / (1024 ** 3),
    }


def collect_all_metrics() -> dict:
    """
    Collect all system metrics in one call.
    Designed for high-frequency polling (30-60 Hz).
    """
    metrics = {}
    metrics.update(get_cpu_metrics())
    metrics.update(get_memory_metrics())
    metrics.update(get_gpu_metrics())
    metrics["timestamp"] = time.time()
    
    return metrics


async def collect_metrics_async() -> dict:
    """
    Async wrapper for metric collection.
    Runs blocking operations in thread pool.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, collect_all_metrics)


if __name__ == "__main__":
    # Test metric collection
    init_gpu_monitoring()
    
    for i in range(5):
        metrics = collect_all_metrics()
        print(f"\n--- Sample {i+1} ---")
        print(f"CPU: {[f'{c:.1f}%' for c in metrics['cpu_percent_per_core'][:4]]}...")
        print(f"Load: {metrics['load_average']}")
        print(f"RAM: {metrics['ram_used_gb']:.1f}/{metrics['ram_total_gb']:.1f} GB")
        print(f"GPU: {metrics['gpu_util_percent']:.0f}%, {metrics['vram_used_gb']:.1f}/{metrics['vram_total_gb']:.1f} GB")
        time.sleep(0.1)
