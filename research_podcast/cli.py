"""
Command-line interface for the Research Paper Podcast Generator.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from research_podcast.core.pipeline import run_pipeline
from research_podcast.models.settings import Settings
from research_podcast.utils.logging import configure_logging

app = typer.Typer(
    help="Convert research papers to podcast-style audio content",
    add_completion=False
)

log = configure_logging()

@app.command()
def convert(
    pdf: Path = typer.Argument(
        ...,
        exists=True,
        help="Path to the research paper PDF"
    ),
    model: str = typer.Option(
        "mistral:latest",
        help="Ollama model to use (must be already pulled)"
    ),
    temperature: float = typer.Option(
        0.7,
        help="Temperature for text generation (0.0-1.0)"
    ),
    output_dir: Path = typer.Option(
        "outputs",
        help="Root directory for output files"
    ),
    voice_prompts: Optional[Path] = typer.Option(
        None,
        help="JSON file mapping speakers to WAV files for voice cloning"
    ),
    host: str = typer.Option(
        "localhost", 
        help="Ollama server host"
    ),
    port: int = typer.Option(
        11434, 
        help="Ollama server port"
    ),
):
    """
    Convert a research paper PDF into an engaging podcast with realistic TTS voices
    using Ollama for inference and Dia for speech synthesis.
    """
    try:
        # Configure settings
        cfg_kwargs = {
            "pdf_path": pdf,
            "model_name": model,
            "temperature": temperature,
            "host": host,
            "port": port,
            "output_root": output_dir,
        }
        
        # Load voice prompts if provided
        if voice_prompts and voice_prompts.exists():
            try:
                with open(voice_prompts, encoding="utf-8") as f:
                    voice_map = json.load(f)
                cfg_kwargs["voice_prompts"] = {k: Path(v) for k, v in voice_map.items()}
                log.info(f"Loaded voice prompts: {list(voice_map.keys())}")
            except Exception as e:
                log.error(f"Error loading voice prompts: {e}")
                raise typer.Abort()
        
        # Initialize settings and run pipeline
        settings = Settings(**cfg_kwargs)
        results = run_pipeline(settings)
        
        # Print final results
        if "mp3_path" in results:
            log.info(f"✅ Success! Final MP3 at {results['mp3_path']}")
        else:
            log.warning("⚠️ Process completed with issues. Check logs for details.")
        
    except Exception as e:
        log.error(f"Pipeline failed: {e}")
        raise typer.Abort()

@app.command()
def version():
    """Display the current version of the package."""
    from research_podcast import __version__
    print(f"Research Paper Podcast Generator v{__version__}")

if __name__ == "__main__":
    app()