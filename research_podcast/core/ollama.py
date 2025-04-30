"""
Ollama API client for text generation tasks.
"""

from typing import Dict, List

import requests

from research_podcast.utils.logging import configure_logging

log = configure_logging()

def is_ollama_running(host: str = "localhost", port: int = 11434) -> bool:
    """
    Check if Ollama server is running.
    
    Args:
        host: Ollama server hostname
        port: Ollama server port
        
    Returns:
        True if Ollama is running, False otherwise
    """
    try:
        response = requests.get(f"http://{host}:{port}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False

def send_chat_request(
    model_name: str,
    messages: List[Dict],
    temperature: float = 0.7,
    host: str = "localhost",
    port: int = 11434,
) -> str:
    """
    Send a chat request to Ollama API.
    
    Args:
        model_name: Ollama model name
        messages: List of message objects with role and content
        temperature: Generation temperature
        host: Ollama host
        port: Ollama port
        
    Returns:
        Response text
    """
    try:
        response = requests.post(
            f"http://{host}:{port}/api/chat",
            json={
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "stream": False,
            },
            timeout=180  # Longer timeout for complex responses
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("message", {}).get("content", "")
        else:
            log.error(f"Ollama API error: {response.status_code} - {response.text}")
            return f"Error: {response.status_code}"
    except Exception as e:
        log.error(f"Error in chat request: {e}")
        return f"Error: {str(e)}"