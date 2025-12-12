"""
CLI entry points for TimeCapsule.
"""

import click
from pathlib import Path


@click.group()
@click.version_option()
def main():
    """TimeCapsule - GPU-accelerated video search."""
    pass


@main.command()
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def doctor(json_output: bool):
    """Check GPU, CUDA, FFmpeg, CT2 status and compute backend."""
    from timecapsule.doctor import print_doctor_report
    print_doctor_report(json_output=json_output)


@main.command()
def warmup():
    """Pre-load CLIP and Whisper models to avoid cold-start latency."""
    import time
    
    click.echo("🔥 Warming up models...")
    
    # Warmup CLIP
    start = time.time()
    click.echo("  Loading CLIP model...")
    from timecapsule.embeddings import warmup_model
    success, msg = warmup_model()
    clip_time = time.time() - start
    if success:
        click.echo(f"  ✅ CLIP ready ({clip_time:.1f}s)")
    else:
        click.echo(f"  ⚠️ CLIP: {msg}")
    
    # Warmup FAISS index
    click.echo("  Loading FAISS index...")
    from timecapsule.indexer import ensure_index_loaded
    has_data = ensure_index_loaded()
    if has_data:
        click.echo("  ✅ FAISS index loaded with data")
    else:
        click.echo("  ℹ️ FAISS index empty (no videos ingested yet)")
    
    click.echo("\n✅ Warmup complete - first search will be fast!")


@main.command()
@click.argument("video_folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--workers", "-w", default=1, help="Number of parallel workers")
def ingest(video_folder: Path, workers: int):
    """Ingest videos from a folder."""
    from timecapsule.ingest import run_ingest
    run_ingest(video_folder, workers=workers)


@main.command()
@click.argument("query")
@click.option("--topk", "-k", default=10, help="Number of results to return")
def search(query: str, topk: int):
    """Search indexed videos with natural language."""
    from timecapsule.search import run_search
    results = run_search(query, topk=topk)
    
    if not results:
        click.echo("No results found.")
        return
    
    click.echo(f"\n🔍 Top {len(results)} results for: '{query}'\n")
    for i, r in enumerate(results, 1):
        click.echo(f"{i}. [{r['score']:.2f}] {r['video_path']}")
        click.echo(f"   ⏱️  {r['timestamp']:.1f}s")
        if r.get("transcript"):
            click.echo(f"   💬 {r['transcript'][:60]}...")
        click.echo()


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind")
@click.option("--port", "-p", default=8000, help="Port to bind")
def serve(host: str, port: int):
    """Launch the web UI server."""
    import uvicorn
    from timecapsule.server import app
    
    click.echo(f"🚀 Starting TimeCapsule server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


@main.command()
@click.option("--port", "-p", default=8000, help="Port for server")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
def demo(port: int, no_browser: bool):
    """Run full demo: doctor → warmup → generate samples → ingest → serve."""
    import subprocess
    import webbrowser
    import time
    import os
    
    project_root = Path(__file__).parent.parent.parent
    sample_dir = project_root / "sample_videos"
    
    click.echo("=" * 60)
    click.echo("🎬 TimeCapsule Demo")
    click.echo("=" * 60)
    
    # Step 1: Doctor
    click.echo("\n📋 Step 1/5: System check...")
    from timecapsule.doctor import print_doctor_report
    results = print_doctor_report()
    
    if not results.get("ffmpeg_available"):
        click.echo("❌ Demo cannot proceed without FFmpeg")
        return
    
    # Step 2: Check espeak-ng
    click.echo("\n🗣️ Step 2/5: Checking TTS...")
    if not results.get("espeak_available"):
        click.echo("❌ espeak-ng not found. Install with: sudo apt install espeak-ng")
        return
    click.echo("✅ espeak-ng available")
    
    # Step 3: Generate samples
    click.echo("\n🎥 Step 3/5: Generating sample videos...")
    script_path = project_root / "scripts" / "generate_sample.sh"
    if script_path.exists():
        result = subprocess.run(
            ["bash", str(script_path), str(sample_dir)],
            cwd=str(project_root),
            capture_output=False
        )
        if result.returncode != 0:
            click.echo("❌ Sample generation failed")
            return
    else:
        click.echo(f"⚠️ Script not found: {script_path}")
        return
    
    # Step 4: Warmup + Ingest
    click.echo("\n🔥 Step 4/5: Warming up and ingesting...")
    from timecapsule.embeddings import warmup_model
    warmup_model()
    
    from timecapsule.ingest import run_ingest
    run_ingest(sample_dir)
    
    # Step 5: Launch server
    click.echo("\n🚀 Step 5/5: Launching server...")
    click.echo(f"\n{'=' * 60}")
    click.echo(f"🎉 Demo ready at http://127.0.0.1:{port}")
    click.echo("   Try searching: 'python programming' or 'machine learning'")
    click.echo(f"{'=' * 60}\n")
    
    if not no_browser:
        # Give server a moment to start
        import threading
        def open_browser():
            time.sleep(2)
            webbrowser.open(f"http://127.0.0.1:{port}")
        threading.Thread(target=open_browser, daemon=True).start()
    
    import uvicorn
    from timecapsule.server import app
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
