"""
Dialogue script generation and enhancement.
"""

import json
from pathlib import Path
from typing import Dict, List

from research_podcast.core.ollama import send_chat_request
from research_podcast.models.settings import Settings
from research_podcast.utils.logging import configure_logging

log = configure_logging()

def get_pdf_summary(text: str, settings: Settings) -> str:
    """
    Generate a summary of the PDF content using Ollama.
    
    Args:
        text: PDF text content
        settings: Configuration settings
        
    Returns:
        Generated summary
    """
    log.info("Generating PDF summary...")
    
    # Truncate text if too long
    max_length = 32000  # Safe limit for most models
    if len(text) > max_length:
        log.info(f"PDF text too long ({len(text)} chars), truncating to {max_length} chars")
        text = text[:max_length]
    
    prompt = f"""
    Please provide a comprehensive summary of this research paper in 300 words or less.
    Focus on:
    1. The main problem addressed
    2. Key methodology
    3. Most significant findings
    4. Real-world implications

    Here is the paper content:
    {text}
    """
    
    messages = [{"role": "user", "content": prompt}]
    summary = send_chat_request(
        model_name=settings.model_name,
        messages=messages,
        temperature=settings.temperature,
        host=settings.host,
        port=settings.port
    )
    
    # Save summary to file
    summary_path = settings.output_root / "scripts" / "summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)
    
    log.info(f"Summary saved to {summary_path}")
    return summary

def generate_dialogue_script(summary: str, settings: Settings) -> List[Dict[str, str]]:
    """
    Generate a dialogue script based on the summary.
    
    Args:
        summary: Research paper summary
        settings: Configuration settings
        
    Returns:
        List of dialogue exchanges with 'speaker' and 'text' keys
    """
    log.info("Generating dialogue script...")
    
    prompt = f"""
    Transform this research paper summary into an engaging dialogue script between hosts Julia and Guido.
    
    Requirements:
    1. Create 12-15 conversational exchanges
    2. Include non-verbal cues where natural (e.g., (laughs), (pauses thoughtfully))
    3. Make the content accessible to an educated but non-specialist audience
    4. Structure as a JSON array of objects with 'speaker' and 'text' keys
    
    Format your response as a valid JSON array:
    [
      {{"speaker": "Julia", "text": "Welcome to Research Spotlight!"}},
      {{"speaker": "Guido", "text": "Today we're discussing..."}}
    ]
    
    Paper summary:
    {summary}
    
    Return ONLY the JSON script with no additional text before or after.
    """
    
    messages = [{"role": "user", "content": prompt}]
    script_text = send_chat_request(
        model_name=settings.model_name,
        messages=messages,
        temperature=settings.temperature,
        host=settings.host,
        port=settings.port
    )
    
    # Extract JSON from the response
    script_text = script_text.strip()
    
    # If the response begins with a code block, clean it up
    if script_text.startswith("```json"):
        script_text = script_text.split("```json", 1)[1]
    if script_text.startswith("```"):
        script_text = script_text.split("```", 1)[1]
    if script_text.endswith("```"):
        script_text = script_text.rsplit("```", 1)[0]
    
    # Save raw script to file
    raw_script_path = settings.output_root / "scripts" / "raw_script.json"
    with open(raw_script_path, "w", encoding="utf-8") as f:
        f.write(script_text)
    
    # Parse JSON
    try:
        dialogue = json.loads(script_text)
        log.info(f"Generated script with {len(dialogue)} exchanges")
        return dialogue
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse script as JSON: {e}")
        log.error(f"Raw script: {script_text}")
        # Create a simple fallback script
        return [
            {"speaker": "Julia", "text": "Welcome to Research Spotlight!"},
            {"speaker": "Guido", "text": "Today we're discussing a research paper, but unfortunately we had some technical difficulties with our script."},
            {"speaker": "Julia", "text": "We apologize for the inconvenience and will be back with properly formatted content next time."}
        ]

def enhance_dialogue_script(dialogue: List[Dict[str, str]], settings: Settings) -> List[Dict[str, str]]:
    """
    Enhance the dialogue script for better engagement and flow.
    
    Args:
        dialogue: Original dialogue script
        settings: Configuration settings
        
    Returns:
        Enhanced dialogue script
    """
    log.info("Enhancing dialogue script...")
    
    # Convert dialogue to string for the prompt
    dialogue_str = json.dumps(dialogue, indent=2)
    
    prompt = f"""
    Refine this dialogue script to improve:
    1. Natural conversational flow
    2. Clarity of complex concepts
    3. Engagement through storytelling techniques
    4. Accuracy of scientific content
    
    Maintain the JSON format while improving the content.
    
    Current script:
    {dialogue_str}
    
    Return ONLY the enhanced JSON script with no additional text before or after.
    """
    
    messages = [{"role": "user", "content": prompt}]
    enhanced_text = send_chat_request(
        model_name=settings.model_name,
        messages=messages,
        temperature=settings.temperature,
        host=settings.host,
        port=settings.port
    )
    
    # Extract JSON from the response
    enhanced_text = enhanced_text.strip()
    
    # If the response begins with a code block, clean it up
    if enhanced_text.startswith("```json"):
        enhanced_text = enhanced_text.split("```json", 1)[1]
    if enhanced_text.startswith("```"):
        enhanced_text = enhanced_text.split("```", 1)[1]
    if enhanced_text.endswith("```"):
        enhanced_text = enhanced_text.rsplit("```", 1)[0]
    
    # Save enhanced script to file
    enhanced_script_path = settings.output_root / "scripts" / "enhanced_script.json"
    with open(enhanced_script_path, "w", encoding="utf-8") as f:
        f.write(enhanced_text)
    
    # Parse JSON
    try:
        enhanced_dialogue = json.loads(enhanced_text)
        log.info(f"Enhanced script with {len(enhanced_dialogue)} exchanges")
        return enhanced_dialogue
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse enhanced script as JSON: {e}")
        log.error(f"Raw enhanced script: {enhanced_text}")
        # Fall back to the original script
        return dialogue