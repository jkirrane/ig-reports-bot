"""
PDF text extraction utility with smart limits to avoid processing huge files
"""

import io
import requests
from pypdf import PdfReader
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Limits to prevent excessive processing and API costs
MAX_FILE_SIZE_MB = 10  # Skip PDFs larger than 10MB
MAX_PAGES = 20         # Only extract first 20 pages
MAX_CHARS = 50000      # Cap at ~50k chars (~12k tokens, ~$0.12 per PDF with GPT-4o-mini)


def extract_pdf_text(pdf_url: str, timeout: int = 30) -> Optional[Dict[str, any]]:
    """
    Extract text from a PDF with smart limits
    
    Args:
        pdf_url: URL to the PDF file
        timeout: Request timeout in seconds
        
    Returns:
        Dict with 'text', 'pages', 'truncated' keys, or None on failure
    """
    try:
        # Check file size before downloading
        logger.info(f"Checking PDF size: {pdf_url}")
        head_response = requests.head(pdf_url, timeout=10, allow_redirects=True)
        
        content_length = head_response.headers.get('Content-Length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                logger.warning(f"PDF too large ({size_mb:.1f}MB), skipping: {pdf_url}")
                return None
        
        # Download PDF
        logger.info(f"Downloading PDF: {pdf_url}")
        response = requests.get(pdf_url, timeout=timeout)
        response.raise_for_status()
        
        # Parse PDF
        pdf_file = io.BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        total_pages = len(reader.pages)
        pages_to_extract = min(total_pages, MAX_PAGES)
        
        logger.info(f"Extracting text from {pages_to_extract}/{total_pages} pages")
        
        # Extract text from pages
        text_parts = []
        total_chars = 0
        truncated = False
        
        for i in range(pages_to_extract):
            try:
                page_text = reader.pages[i].extract_text()
                
                # Check if we're approaching the character limit
                if total_chars + len(page_text) > MAX_CHARS:
                    # Add as much as we can from this page
                    remaining = MAX_CHARS - total_chars
                    text_parts.append(page_text[:remaining])
                    truncated = True
                    logger.info(f"Reached character limit at page {i+1}/{pages_to_extract}")
                    break
                
                text_parts.append(page_text)
                total_chars += len(page_text)
                
            except Exception as e:
                logger.warning(f"Failed to extract page {i+1}: {e}")
                continue
        
        full_text = '\n\n'.join(text_parts)
        
        # Clean up text (remove excessive whitespace)
        full_text = '\n'.join(line.strip() for line in full_text.split('\n') if line.strip())
        
        result = {
            'text': full_text,
            'pages': pages_to_extract,
            'total_pages': total_pages,
            'chars': len(full_text),
            'truncated': truncated or total_pages > MAX_PAGES
        }
        
        logger.info(f"✅ Extracted {len(full_text)} chars from {pages_to_extract} pages")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download PDF {pdf_url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {pdf_url}: {e}")
        return None


def test_extraction():
    """Test PDF extraction with a real IG report"""
    # Test with a recent report
    test_url = "https://www.oversight.gov/sites/default/files/documents/reports/2026-01/G25UT0069-26-06_Utah_HAVA_Audit_Report.pdf"
    
    result = extract_pdf_text(test_url)
    
    if result:
        print(f"✅ Extraction successful!")
        print(f"   Pages: {result['pages']}/{result['total_pages']}")
        print(f"   Characters: {result['chars']:,}")
        print(f"   Truncated: {result['truncated']}")
        print(f"\nFirst 500 chars:")
        print(result['text'][:500])
        print("\n...")
    else:
        print("❌ Extraction failed")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_extraction()
