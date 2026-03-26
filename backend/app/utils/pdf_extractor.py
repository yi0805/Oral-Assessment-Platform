"""
PDF text extraction utility using pdfplumber.
Extracts full text from uploaded PDF files for the processing pipeline.
"""
import logging
from dataclasses import dataclass

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class ExtractResult:
    text: str
    page_count: int
    extraction_method: str = "pdfplumber"


def extract_text_from_bytes(pdf_bytes: bytes) -> ExtractResult:
    """
    Extract full text from a PDF given as bytes.
    Returns ExtractResult with the combined text, page count, and method used.
    """
    import io

    pages_text = []
    page_count = 0

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    full_text = "\n\n".join(pages_text)

    if not full_text.strip():
        logger.warning("PDF extraction returned empty text (possibly scanned/image PDF)")

    return ExtractResult(
        text=full_text,
        page_count=page_count,
        extraction_method="pdfplumber",
    )
