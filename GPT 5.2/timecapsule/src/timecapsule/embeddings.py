"""
CLIP embeddings for keyframe images and text queries.
Uses OpenCLIP with GPU acceleration and model caching.
"""

from pathlib import Path
from typing import List, Union, Optional, Tuple
import numpy as np
from PIL import Image


# Global model cache
_model = None
_preprocess = None
_tokenizer = None
_device = None


def get_device(preferred: str = "auto") -> str:
    """Determine the best available device."""
    import torch
    
    if preferred == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return preferred


def warmup_model(device: str = "auto") -> Tuple[bool, str]:
    """
    Pre-load CLIP model to avoid cold-start latency during ingestion.
    
    Returns:
        (success, message) tuple
    """
    try:
        model, _, _ = get_model(device)
        device_name = _device or "unknown"
        return True, f"CLIP model warmed up on {device_name}"
    except Exception as e:
        return False, f"Warmup failed: {e}"


def get_model(device: str = "auto"):
    """
    Load or return cached OpenCLIP model.
    
    The model is cached globally to avoid reloading on each call.
    Use warmup_model() at startup to pre-load.
    """
    global _model, _preprocess, _tokenizer, _device
    
    if _model is not None:
        return _model, _preprocess, _tokenizer
    
    import torch
    import open_clip
    
    _device = get_device(device)
    
    print(f"  🧠 Loading CLIP ViT-B-32 on {_device}...")
    
    # Use laion2b weights for best quality
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    model = model.to(_device)
    model.eval()
    
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    
    _model = model
    _preprocess = preprocess
    _tokenizer = tokenizer
    
    print(f"  ✅ CLIP model loaded and cached")
    
    return model, preprocess, tokenizer


def clear_model_cache():
    """Clear the cached model (useful for testing or freeing memory)."""
    global _model, _preprocess, _tokenizer, _device
    _model = None
    _preprocess = None
    _tokenizer = None
    _device = None


def embed_images(image_paths: List[Path], batch_size: int = 32,
                 device: str = "auto") -> np.ndarray:
    """
    Compute CLIP embeddings for a batch of images.
    
    Returns normalized embeddings as numpy array (N, 512).
    """
    import torch
    
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    model, preprocess, _ = get_model(device)
    
    all_embeddings = []
    
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i + batch_size]
        
        # Load and preprocess images
        images = []
        for path in batch_paths:
            try:
                img = Image.open(path).convert("RGB")
                img_tensor = preprocess(img)
                images.append(img_tensor)
            except Exception as e:
                print(f"  ⚠️ Failed to load {path}: {e}")
                # Use zero tensor as placeholder
                images.append(torch.zeros(3, 224, 224))
        
        if not images:
            continue
        
        batch_tensor = torch.stack(images).to(device)
        
        with torch.no_grad():
            embeddings = model.encode_image(batch_tensor)
            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
        
        all_embeddings.append(embeddings.cpu().numpy())
    
    if not all_embeddings:
        return np.array([])
    
    return np.vstack(all_embeddings).astype(np.float32)


def embed_text(query: str, device: str = "auto") -> np.ndarray:
    """
    Compute CLIP embedding for a text query.
    
    Returns normalized embedding as numpy array (1, 512).
    """
    import torch
    
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    model, _, tokenizer = get_model(device)
    
    tokens = tokenizer([query]).to(device)
    
    with torch.no_grad():
        embedding = model.encode_text(tokens)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    
    return embedding.cpu().numpy().astype(np.float32)


if __name__ == "__main__":
    # Test embedding
    test_text = "a person giving a presentation"
    embedding = embed_text(test_text)
    print(f"Text embedding shape: {embedding.shape}")
    print(f"Text embedding norm: {np.linalg.norm(embedding):.4f}")
