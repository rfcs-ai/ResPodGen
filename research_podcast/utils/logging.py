"""
Logging utilities for the Research Paper Podcast Generator.
"""

import logging
import sys
from typing import Optional

def configure_logging(name: str = "research-podcast", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger with the specified name and level.
    
    Args:
        name: The name for the logger
        level: The logging level (e.g., logging.INFO, logging.DEBUG)
        
    Returns:
        A configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s • %(levelname)-8s • %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger if it doesn't already have one
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger