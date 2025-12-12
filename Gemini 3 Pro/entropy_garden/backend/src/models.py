"""
Data models for Entropy_Garden telemetry.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Tuple
import time


@dataclass
class EntropyEvent:
    """
    Normalized entropy event containing all system telemetry metrics.
    Streamed via WebSocket at 30-60 Hz.
    """
    # Timestamp
    timestamp: float = field(default_factory=time.time)
    
    # Computed entropy score (0.0 - 1.0)
    entropy_score: float = 0.0
    
    # CPU metrics
    cpu_percent_per_core: List[float] = field(default_factory=list)
    load_average: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    context_switches_per_sec: float = 0.0
    interrupts_per_sec: float = 0.0
    
    # Memory metrics
    ram_total_gb: float = 0.0
    ram_used_gb: float = 0.0
    ram_available_gb: float = 0.0
    
    # GPU metrics
    gpu_util_percent: float = 0.0
    vram_used_gb: float = 0.0
    vram_total_gb: float = 0.0
    gpu_temp_celsius: float = 0.0
    gpu_power_watts: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)


@dataclass
class MappingConfig:
    """
    Configuration for how metrics map to visual properties.
    """
    mode: str = "balanced"  # "cpu_heavy", "gpu_heavy", "balanced"
    intensity: float = 1.0  # 0.0 - 2.0
    
    @property
    def weights(self) -> dict:
        """Get metric weights based on mapping mode."""
        if self.mode == "cpu_heavy":
            return {
                "cpu": 0.5,
                "load": 0.15,
                "ctx": 0.1,
                "mem": 0.1,
                "gpu": 0.1,
                "vram": 0.05,
            }
        elif self.mode == "gpu_heavy":
            return {
                "cpu": 0.15,
                "load": 0.05,
                "ctx": 0.05,
                "mem": 0.15,
                "gpu": 0.4,
                "vram": 0.2,
            }
        else:  # balanced
            return {
                "cpu": 0.25,
                "load": 0.1,
                "ctx": 0.1,
                "mem": 0.2,
                "gpu": 0.25,
                "vram": 0.1,
            }
