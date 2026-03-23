"""
Text extraction from different file types (PDF, TXT, MD, DOCX).
"""

from pathlib import Path

import docx
import pdfplumber


def extract_text(file_path: str) -> str:
    """Extract text content from a file based on its extension."""
    path = Path(file_path)
    ext = path.suffix.lower()

    extractors = {
        ".pdf": _extract_pdf,
        ".txt": _extract_plain,
        ".md": _extract_plain,
        ".docx": _extract_docx,
    }

    extractor = extractors.get(ext)
    if not extractor:
        raise ValueError(f"Unsupported file type: {ext}")

    text = extractor(file_path)
    if not text or not text.strip():
        raise ValueError("No text content could be extracted from the file")

    return text.strip()


def _extract_pdf(file_path: str) -> str:
    pages: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def _extract_plain(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")


def _extract_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
