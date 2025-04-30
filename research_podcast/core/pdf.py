"""
PDF processing utilities for extracting text from research papers.
"""

from pathlib import Path

import fitz  # PyMuPDF

from research_podcast.utils.logging import configure_logging

log = configure_logging()

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
        
    Raises:
        Exception: If PDF extraction fails
    """
    try:
        log.info(f"Extracting text from PDF: {pdf_path}")
        pdf_document = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text += page.get_text()
        
        log.info(f"Extracted {len(text)} characters from {len(pdf_document)} pages")
        return text
    except Exception as e:
        log.error(f"Error extracting PDF text: {e}")
        raise