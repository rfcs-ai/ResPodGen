"""
Configuration settings for the podcast generation pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

@dataclass
class Settings:
    """Configuration settings for the podcast generation pipeline."""
    
    # Input settings
    pdf_path: Path
    model_name: str = "mistral:latest"
    temperature: float = 0.7
    
    # Ollama settings
    host: str = "localhost"
    port: int = 11434
    
    # Output settings
    output_root: Path = field(default_factory=lambda: Path("outputs"))
    
    # Voice settings
    voice_prompts: Optional[Dict[str, Path]] = None

    # Podcast Title settings
    podcast_title: Optional[str] = None # Add default None or a default title string
    
    def __post_init__(self):
        """Initialize paths and create output directories."""
        # Resolve input path
        self.pdf_path = self.pdf_path.resolve()
        
        # Create timestamped output directory
        self.output_root = (self.output_root / datetime.now().strftime("%Y%m%d_%H%M%S")).resolve()
        self.output_root.mkdir(parents=True, exist_ok=True)
        
        # Create podcast directory
        podcast_dir = self.output_root / "podcast"
        podcast_dir.mkdir(parents=True, exist_ok=True)
        
        # Create script directory
        script_dir = self.output_root / "scripts"
        script_dir.mkdir(parents=True, exist_ok=True)