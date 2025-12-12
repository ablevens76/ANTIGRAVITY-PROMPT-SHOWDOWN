"""
Search engine combining FAISS visual search and transcript text search.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from timecapsule.database import get_connection, search_transcripts, get_keyframe_by_embedding_id
from timecapsule.embeddings import embed_text
from timecapsule.indexer import get_index


def run_search(query: str, topk: int = 10, 
               visual_weight: float = 0.6,
               text_weight: float = 0.4) -> List[Dict[str, Any]]:
    """
    Search indexed videos using both visual and text matching.
    
    Args:
        query: Natural language search query
        topk: Number of results to return
        visual_weight: Weight for visual (CLIP) results
        text_weight: Weight for transcript matches
        
    Returns:
        List of result dicts with video_path, timestamp, score, thumbnail, transcript
    """
    results = []
    seen_timestamps = set()  # Deduplicate by video+timestamp
    
    # Visual search with CLIP
    try:
        query_embedding = embed_text(query)
        index = get_index()
        
        if index.size > 0:
            visual_results = index.search(query_embedding, k=topk * 2)
            
            conn = get_connection()
            for keyframe_id, score in visual_results:
                keyframe = get_keyframe_by_embedding_id(conn, keyframe_id)
                if keyframe:
                    key = (keyframe["video_path"], round(keyframe["timestamp"], 1))
                    if key not in seen_timestamps:
                        seen_timestamps.add(key)
                        results.append({
                            "video_path": keyframe["video_path"],
                            "filename": keyframe["filename"],
                            "timestamp": keyframe["timestamp"],
                            "thumbnail": keyframe.get("thumbnail_path"),
                            "score": score * visual_weight,
                            "transcript": None,
                            "source": "visual"
                        })
            conn.close()
    except Exception as e:
        print(f"⚠️ Visual search failed: {e}")
    
    # Text search in transcripts
    try:
        conn = get_connection()
        transcript_results = search_transcripts(conn, query, limit=topk * 2)
        conn.close()
        
        for t in transcript_results:
            key = (t["video_path"], round(t["start_time"], 1))
            if key not in seen_timestamps:
                seen_timestamps.add(key)
                # Simple scoring based on match length
                score = min(1.0, len(query) / max(len(t["text"]), 1)) * text_weight
                results.append({
                    "video_path": t["video_path"],
                    "filename": t["filename"],
                    "timestamp": t["start_time"],
                    "thumbnail": None,
                    "score": score,
                    "transcript": t["text"],
                    "source": "transcript"
                })
    except Exception as e:
        print(f"⚠️ Text search failed: {e}")
    
    # Sort by score and limit
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:topk]
    
    return results


def search_visual_only(query: str, topk: int = 10) -> List[Dict[str, Any]]:
    """Search using only CLIP visual embeddings."""
    query_embedding = embed_text(query)
    index = get_index()
    
    if index.size == 0:
        return []
    
    visual_results = index.search(query_embedding, k=topk)
    
    results = []
    conn = get_connection()
    
    for keyframe_id, score in visual_results:
        keyframe = get_keyframe_by_embedding_id(conn, keyframe_id)
        if keyframe:
            results.append({
                "video_path": keyframe["video_path"],
                "filename": keyframe["filename"],
                "timestamp": keyframe["timestamp"],
                "thumbnail": keyframe.get("thumbnail_path"),
                "score": float(score),
                "transcript": None,
                "source": "visual"
            })
    
    conn.close()
    return results


if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "person talking"
    
    results = run_search(query, topk=5)
    
    print(f"\nSearch results for: '{query}'")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['score']:.2f}] {r['filename']} @ {r['timestamp']:.1f}s")
        if r["transcript"]:
            print(f"   💬 {r['transcript'][:60]}...")
