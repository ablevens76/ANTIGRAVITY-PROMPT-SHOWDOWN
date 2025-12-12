"""
FAISS vector index for fast similarity search.
"""

from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

# Default index path
DEFAULT_INDEX_PATH = Path(__file__).parent.parent.parent / "data" / "faiss.index"


class FAISSIndex:
    """FAISS index wrapper for cosine similarity search."""
    
    def __init__(self, dimension: int = 512):
        import faiss
        
        self.dimension = dimension
        # Inner product index (for normalized vectors = cosine similarity)
        self.index = faiss.IndexFlatIP(dimension)
        self.id_map = []  # Maps FAISS internal IDs to our keyframe IDs
    
    def add(self, embeddings: np.ndarray, ids: List[int]):
        """Add embeddings with corresponding IDs."""
        if len(embeddings) == 0:
            return
        
        embeddings = embeddings.astype(np.float32)
        
        # Ensure normalized
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-8)
        
        self.index.add(embeddings)
        self.id_map.extend(ids)
    
    def search(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for similar embeddings.
        
        Returns list of (keyframe_id, score) tuples.
        """
        if self.index.ntotal == 0:
            return []
        
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        
        # Normalize query
        norm = np.linalg.norm(query_embedding)
        query_embedding = query_embedding / (norm + 1e-8)
        
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, (idx, score) in enumerate(zip(indices[0], distances[0])):
            if idx >= 0 and idx < len(self.id_map):
                keyframe_id = self.id_map[idx]
                results.append((keyframe_id, float(score)))
        
        return results
    
    def save(self, path: Optional[Path] = None):
        """Save index to disk."""
        import faiss
        
        if path is None:
            path = DEFAULT_INDEX_PATH
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(path))
        
        # Save ID map
        id_map_path = path.with_suffix(".ids.npy")
        np.save(str(id_map_path), np.array(self.id_map))
        
        print(f"  💾 Saved index ({self.index.ntotal} vectors) to {path}")
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "FAISSIndex":
        """Load index from disk."""
        import faiss
        
        if path is None:
            path = DEFAULT_INDEX_PATH
        
        path = Path(path)
        
        if not path.exists():
            print(f"  ⚠️ Index not found at {path}, creating new")
            return cls()
        
        index = faiss.read_index(str(path))
        
        instance = cls(dimension=index.d)
        instance.index = index
        
        # Load ID map
        id_map_path = path.with_suffix(".ids.npy")
        if id_map_path.exists():
            instance.id_map = np.load(str(id_map_path)).tolist()
        
        print(f"  📂 Loaded index ({index.ntotal} vectors) from {path}")
        
        return instance
    
    @property
    def size(self) -> int:
        """Number of vectors in the index."""
        return self.index.ntotal


# Global index instance
_index: Optional[FAISSIndex] = None


def get_index() -> FAISSIndex:
    """Get or load the global FAISS index from disk."""
    global _index
    
    if _index is None:
        _index = FAISSIndex.load()
    
    return _index


def reload_index(path: Optional[Path] = None) -> FAISSIndex:
    """
    Force reload the index from disk.
    
    Useful after external modifications or to ensure fresh state.
    """
    global _index
    _index = FAISSIndex.load(path)
    return _index


def ensure_index_loaded() -> bool:
    """
    Ensure the FAISS index is loaded (for cold-start warmup).
    
    Returns True if index exists and was loaded, False if new empty index.
    """
    index = get_index()
    return index.size > 0


def save_index():
    """Save the global index to disk."""
    global _index
    
    if _index is not None:
        _index.save()


def clear_index():
    """Clear the global index (does not delete files)."""
    global _index
    _index = None


if __name__ == "__main__":
    # Test index
    index = FAISSIndex(dimension=512)
    
    # Add some random vectors
    embeddings = np.random.randn(10, 512).astype(np.float32)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    index.add(embeddings, list(range(10)))
    
    # Search
    query = np.random.randn(512).astype(np.float32)
    results = index.search(query.reshape(1, -1), k=5)
    
    print("Search results:")
    for id, score in results:
        print(f"  ID {id}: {score:.4f}")
