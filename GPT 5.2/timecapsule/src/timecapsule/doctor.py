"""
System diagnostics for TimeCapsule.
Checks GPU, CUDA, FFmpeg, CT2 version, and compute backend availability.
"""

import json
import shutil
import subprocess
import sys
from packaging import version


def check_ct2_cuda_compatibility() -> dict:
    """
    Check CTranslate2 version compatibility with CUDA.
    
    CT2 4.5+ requires CUDA 12.3+ and cuDNN 9.
    Running CT2 >= 4.5 on CUDA 11.x will fail silently or crash.
    """
    result = {
        "ctranslate2_version": None,
        "ctranslate2_available": False,
        "cuda_compatible": True,
        "warning": None,
    }
    
    try:
        import ctranslate2
        result["ctranslate2_version"] = ctranslate2.__version__
        result["ctranslate2_available"] = True
        
        # Check for incompatible version on CUDA 11.x
        import torch
        if torch.cuda.is_available():
            cuda_ver = torch.version.cuda
            ct2_ver = version.parse(ctranslate2.__version__)
            
            # CT2 4.5+ needs CUDA 12.3+ and cuDNN 9
            if ct2_ver >= version.parse("4.5.0"):
                if cuda_ver and cuda_ver.startswith("11"):
                    result["cuda_compatible"] = False
                    result["warning"] = (
                        f"ctranslate2 {ctranslate2.__version__} requires CUDA 12.3+, "
                        f"but CUDA {cuda_ver} detected. GPU transcription may fail. "
                        "Pin ctranslate2<4.5 for CUDA 11.x support."
                    )
    except ImportError:
        pass
    except Exception as e:
        result["warning"] = f"CT2 check failed: {e}"
    
    return result


def run_doctor() -> dict:
    """Run system diagnostics and return status dict."""
    results = {
        "python_version": sys.version,
        "torch_available": False,
        "torch_version": None,
        "cuda_available": False,
        "cuda_version": None,
        "gpu_name": None,
        "gpu_memory": None,
        "ffmpeg_available": False,
        "ffmpeg_path": None,
        "espeak_available": False,
        "compute_backend": "cpu",
    }
    
    # Check PyTorch
    try:
        import torch
        results["torch_available"] = True
        results["torch_version"] = torch.__version__
        results["cuda_available"] = torch.cuda.is_available()
        
        if torch.cuda.is_available():
            results["cuda_version"] = torch.version.cuda
            results["gpu_name"] = torch.cuda.get_device_name(0)
            results["gpu_memory"] = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB"
            results["compute_backend"] = "cuda"
    except ImportError:
        pass
    
    # Check CTranslate2 compatibility
    ct2_info = check_ct2_cuda_compatibility()
    results.update({
        "ctranslate2_version": ct2_info["ctranslate2_version"],
        "ctranslate2_cuda_compatible": ct2_info["cuda_compatible"],
        "ctranslate2_warning": ct2_info["warning"],
    })
    
    # Check FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        results["ffmpeg_available"] = True
        results["ffmpeg_path"] = ffmpeg_path
    
    # Check espeak-ng for TTS
    espeak_path = shutil.which("espeak-ng") or shutil.which("espeak")
    results["espeak_available"] = espeak_path is not None
    
    return results


def print_doctor_report(json_output: bool = False) -> dict:
    """Print formatted doctor report to console."""
    results = run_doctor()
    
    if json_output:
        print(json.dumps(results, indent=2))
        return results
    
    print("=" * 60)
    print("🏥 TimeCapsule Doctor - System Diagnostics")
    print("=" * 60)
    
    # Python
    print(f"\n📦 Python: {results['python_version'].split()[0]}")
    
    # PyTorch
    print("\n🔥 PyTorch:")
    if results["torch_available"]:
        print(f"   Version: {results['torch_version']}")
        print(f"   CUDA Available: {'✅ Yes' if results['cuda_available'] else '❌ No'}")
        if results["cuda_available"]:
            print(f"   CUDA Version: {results['cuda_version']}")
    else:
        print("   ❌ Not installed")
    
    # GPU
    print("\n🎮 GPU:")
    if results["gpu_name"]:
        print(f"   Device: {results['gpu_name']}")
        print(f"   Memory: {results['gpu_memory']}")
    else:
        print("   ❌ No CUDA GPU detected")
    
    # CTranslate2 (Whisper backend)
    print("\n🎤 CTranslate2 (Whisper):")
    if results.get("ctranslate2_version"):
        print(f"   Version: {results['ctranslate2_version']}")
        if results.get("ctranslate2_warning"):
            print(f"   ⚠️  {results['ctranslate2_warning']}")
        elif results.get("ctranslate2_cuda_compatible"):
            print("   ✅ CUDA compatible")
    else:
        print("   ℹ️ Not loaded yet")
    
    # nvidia-smi
    print("\n📊 nvidia-smi:")
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                print(f"   {line}")
        else:
            print("   ❌ nvidia-smi failed")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("   ❌ nvidia-smi not available")
    
    # FFmpeg
    print("\n🎬 FFmpeg:")
    if results["ffmpeg_available"]:
        print(f"   ✅ Found: {results['ffmpeg_path']}")
    else:
        print("   ❌ Not found in PATH")
    
    # espeak-ng
    print("\n🗣️ espeak-ng (TTS):")
    if results["espeak_available"]:
        print("   ✅ Available for sample generation")
    else:
        print("   ⚠️ Not found - install with: sudo apt install espeak-ng")
    
    # Compute backend
    print("\n⚡ Compute Backend:")
    backend = results["compute_backend"].upper()
    icon = "🚀" if backend == "CUDA" else "🐢"
    print(f"   {icon} {backend}")
    
    print("\n" + "=" * 60)
    
    # Summary
    all_good = (
        results["torch_available"] and
        results["ffmpeg_available"]
    )
    
    if all_good and results["cuda_available"]:
        if results.get("ctranslate2_warning"):
            print("⚠️  GPU ready but CT2/CUDA version mismatch detected!")
        else:
            print("✅ All systems GO! GPU acceleration enabled.")
    elif all_good:
        print("⚠️  System ready, but running in CPU mode (slower).")
    else:
        missing = []
        if not results["torch_available"]:
            missing.append("PyTorch")
        if not results["ffmpeg_available"]:
            missing.append("FFmpeg")
        print(f"❌ Missing: {', '.join(missing)}")
    
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    import sys
    json_mode = "--json" in sys.argv
    print_doctor_report(json_output=json_mode)
