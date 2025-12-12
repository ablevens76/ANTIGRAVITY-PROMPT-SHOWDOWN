"""Tests for search functionality."""

import pytest
import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from timecapsule.indexer import FAISSIndex


class TestFAISSIndex:
    def test_create_index(self):
        """Test index creation."""
        index = FAISSIndex(dimension=512)
        assert index.size == 0
    
    def test_add_embeddings(self):
        """Test adding embeddings to index."""
        index = FAISSIndex(dimension=512)
        
        # Create random embeddings
        embeddings = np.random.randn(10, 512).astype(np.float32)
        ids = list(range(10))
        
        index.add(embeddings, ids)
        
        assert index.size == 10
    
    def test_search(self):
        """Test searching the index."""
        index = FAISSIndex(dimension=512)
        
        # Create random embeddings
        embeddings = np.random.randn(10, 512).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        ids = list(range(10))
        
        index.add(embeddings, ids)
        
        # Search with first embedding (should find itself as top match)
        results = index.search(embeddings[0:1], k=5)
        
        assert len(results) == 5
        # First result should be the query itself (or very close)
        assert results[0][0] == 0 or results[0][1] > 0.99
    
    def test_search_returns_correct_shape(self):
        """Test search returns correct number of results."""
        index = FAISSIndex(dimension=512)
        
        embeddings = np.random.randn(5, 512).astype(np.float32)
        index.add(embeddings, [100, 200, 300, 400, 500])
        
        # Request more than available
        results = index.search(embeddings[0:1], k=10)
        
        assert len(results) <= 5
        
        # Check IDs are from our list
        result_ids = [r[0] for r in results]
        for rid in result_ids:
            assert rid in [100, 200, 300, 400, 500]
    
    def test_empty_search(self):
        """Test searching empty index."""
        index = FAISSIndex(dimension=512)
        
        query = np.random.randn(1, 512).astype(np.float32)
        results = index.search(query, k=5)
        
        assert len(results) == 0
