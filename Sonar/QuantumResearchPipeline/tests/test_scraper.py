"""
Tests for arxiv_scraper.py
"""
import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from arxiv_scraper import get_topological_papers


class TestTopologicalPaperSelection:
    """Test paper selection for quantum simulation."""
    
    def test_select_topological_keywords(self):
        """Test that papers with topological keywords are prioritized."""
        papers = [
            {"title": "Generic Paper", "abstract": "Nothing special here"},
            {"title": "Toric Code Implementation", "abstract": "Surface code study"},
            {"title": "Anyon Braiding in Majorana Fermions", "abstract": "Topological qubits"},
        ]
        
        selected = get_topological_papers(papers, n=2)
        assert len(selected) == 2
        # Papers with topological keywords should be selected
        assert any("toric" in p["title"].lower() for p in selected)
        assert any("anyon" in p["title"].lower() for p in selected)
    
    def test_select_fewer_papers(self):
        """Test selection when fewer papers available than requested."""
        papers = [
            {"title": "Only Paper", "abstract": "Single entry"},
        ]
        
        selected = get_topological_papers(papers, n=3)
        assert len(selected) == 1
    
    def test_empty_papers_list(self):
        """Test handling of empty paper list."""
        selected = get_topological_papers([], n=3)
        assert len(selected) == 0
    
    def test_keyword_in_abstract(self):
        """Test that keywords in abstract are also detected."""
        papers = [
            {"title": "Generic Title", "abstract": "This paper discusses topological protection"},
        ]
        
        selected = get_topological_papers(papers, n=1)
        assert len(selected) == 1


class TestMetadataIntegrity:
    """Test metadata file handling."""
    
    def test_metadata_file_exists(self):
        """Check if metadata.json was created by scraper run."""
        metadata_path = Path(__file__).parent.parent / "papers" / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                data = json.load(f)
            assert isinstance(data, list)
            if len(data) > 0:
                assert "title" in data[0]
                assert "authors" in data[0]
                assert "abstract" in data[0]
