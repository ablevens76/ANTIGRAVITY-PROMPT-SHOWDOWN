#!/usr/bin/env python3
"""
AGENT 1: arXivScraper
Scrapes quantum computing + photonic compression papers from arXiv (2024-2025).
"""

import json
from pathlib import Path

import arxiv
import requests

# Configuration
SEARCH_QUERY = "quantum computing photonic compression"
MAX_RESULTS = 20
TOP_PDFS = 5
OUTPUT_DIR = Path(__file__).parent / "papers"


def scrape_arxiv_papers():
    """Scrape papers matching quantum computing photonic compression."""
    print("=" * 60)
    print("🔬 AGENT 1: arXivScraper - STARTING")
    print("=" * 60)
    print(f"Query: '{SEARCH_QUERY}'")
    print(f"Max Results: {MAX_RESULTS}")
    print("Date Range: 2024-2025")
    print("-" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Search arXiv
    client = arxiv.Client()
    search = arxiv.Search(
        query=SEARCH_QUERY,
        max_results=MAX_RESULTS,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    for i, result in enumerate(client.results(search)):
        # Filter for 2024-2025 papers
        pub_year = result.published.year
        if pub_year < 2024:
            continue

        paper = {
            "id": result.entry_id.split("/")[-1],
            "title": result.title,
            "authors": [a.name for a in result.authors],
            "abstract": result.summary,
            "published": result.published.isoformat(),
            "updated": result.updated.isoformat() if result.updated else None,
            "categories": result.categories,
            "pdf_url": result.pdf_url,
            "primary_category": result.primary_category,
            "relevance_score": MAX_RESULTS - i,  # Higher score = more relevant
        }
        papers.append(paper)
        print(f"  [{len(papers):02d}] {paper['title'][:60]}...")

    print(f"\n📊 Found {len(papers)} papers from 2024-2025")

    # Save metadata
    metadata_path = OUTPUT_DIR / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(papers, f, indent=2)
    print(f"💾 Saved metadata to {metadata_path}")

    # Download top PDFs
    print(f"\n📥 Downloading top {TOP_PDFS} PDFs...")
    top_papers = sorted(papers, key=lambda x: x["relevance_score"], reverse=True)[:TOP_PDFS]

    for i, paper in enumerate(top_papers, 1):
        pdf_path = OUTPUT_DIR / f"{paper['id'].replace('/', '_')}.pdf"
        if not pdf_path.exists():
            try:
                response = requests.get(paper["pdf_url"], timeout=30)
                response.raise_for_status()
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
                print(f"  ✅ [{i}/{TOP_PDFS}] Downloaded: {paper['title'][:50]}...")
            except Exception as e:
                print(f"  ❌ [{i}/{TOP_PDFS}] Failed: {paper['title'][:50]}... ({e})")
        else:
            print(f"  ⏭️ [{i}/{TOP_PDFS}] Already exists: {pdf_path.name}")

    print("\n" + "=" * 60)
    print("🔬 AGENT 1: arXivScraper - COMPLETE")
    print("=" * 60)

    return papers


def get_topological_papers(papers, n=3):
    """Select papers most likely about topological quantum computing."""
    keywords = ["topological", "toric", "anyon", "surface code", "braiding", "majorana"]

    scored = []
    for paper in papers:
        score = sum(
            1
            for kw in keywords
            if kw.lower() in paper["title"].lower() or kw.lower() in paper["abstract"].lower()
        )
        scored.append((score, paper))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [p for s, p in scored[:n]]

    if len(selected) < n:
        # Fill with highest relevance papers if not enough topological ones
        remaining = [p for p in papers if p not in selected]
        selected.extend(remaining[: n - len(selected)])

    return selected


if __name__ == "__main__":
    papers = scrape_arxiv_papers()

    print("\n📌 Top 3 papers for quantum simulation:")
    topological = get_topological_papers(papers, n=3)
    for i, p in enumerate(topological, 1):
        print(f"  {i}. {p['title'][:70]}...")

    # Save selected papers for Agent 3
    with open(OUTPUT_DIR / "selected_for_simulation.json", "w") as f:
        json.dump(topological, f, indent=2)
