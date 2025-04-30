"""
Main pipeline for the Research Paper Podcast Generator.
"""

import json
import sys
from datetime import datetime
from typing import Dict

from research_podcast.core.audio import DIA_AVAILABLE, encode_mp3, generate_audio
from research_podcast.core.dialogue import (
    enhance_dialogue_script,
    generate_dialogue_script,
    get_pdf_summary,
)
from research_podcast.core.ollama import is_ollama_running
from research_podcast.core.pdf import extract_text_from_pdf
from research_podcast.models.settings import Settings
from research_podcast.utils.logging import configure_logging

log = configure_logging()

def run_pipeline(settings: Settings) -> Dict:
    """
    Execute the main podcast generation pipeline.
    
    Args:
        settings: Configuration settings
        
    Returns:
        Dictionary of results for each step
    """
    results = {}
    
    # Step 1: Check if Ollama is running
    if not is_ollama_running(settings.host, settings.port):
        log.error(f"Ollama server is not running at {settings.host}:{settings.port}")
        log.error("Please start Ollama with: ollama serve")
        sys.exit(1)
    
    # Step 2: Extract text from PDF
    try:
        pdf_text = extract_text_from_pdf(settings.pdf_path)
        results["pdf_extraction"] = "success"
    except Exception as e:
        log.error(f"Failed to extract PDF text: {e}")
        results["pdf_extraction"] = f"error: {str(e)}"
        return results
    
    # Step 3: Generate summary
    try:
        summary = get_pdf_summary(pdf_text, settings)
        results["summary"] = "success"
    except Exception as e:
        log.error(f"Failed to generate summary: {e}")
        results["summary"] = f"error: {str(e)}"
        return results
    
    # Step 4: Generate dialogue script
    try:
        dialogue = generate_dialogue_script(summary, settings)
        results["dialogue"] = "success"
    except Exception as e:
        log.error(f"Failed to generate dialogue: {e}")
        results["dialogue"] = f"error: {str(e)}"
        return results
    
    # Step 5: Enhance dialogue script
    try:
        enhanced_dialogue = enhance_dialogue_script(dialogue, settings)
        results["enhance"] = "success"
    except Exception as e:
        log.error(f"Failed to enhance dialogue: {e}")
        results["enhance"] = f"error: {str(e)}"
        enhanced_dialogue = dialogue  # Fall back to unenhanced dialogue
    
    # Step 6: Generate audio
    if DIA_AVAILABLE:
        try:
            wav_path = generate_audio(enhanced_dialogue, settings)
            if wav_path:
                results["audio"] = "success"
                
                # Step 7: Encode MP3
                mp3_path = encode_mp3(wav_path, settings)
                if mp3_path:
                    results["mp3"] = "success"
                    results["mp3_path"] = mp3_path
                else:
                    results["mp3"] = "error: Failed to encode MP3"
            else:
                results["audio"] = "error: Failed to generate audio"
        except Exception as e:
            log.error(f"Failed to generate audio: {e}")
            results["audio"] = f"error: {str(e)}"
    else:
        results["audio"] = "skipped: Dia TTS not available"
    
    # Save script in final format
    final_script_path = settings.output_root / "scripts" / "final_script.json"
    with open(final_script_path, "w", encoding="utf-8") as f:
        json.dump(enhanced_dialogue, f, indent=2)
    
    # Save metadata
    meta = {
        "timestamp": datetime.now().isoformat(),
        "settings": {
            "pdf": str(settings.pdf_path),
            "model": settings.model_name,
            "temperature": settings.temperature,
        },
        "results": results
    }
    
    meta_path = settings.output_root / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    
    return results