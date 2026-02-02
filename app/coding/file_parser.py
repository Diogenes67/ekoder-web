"""
File Parser - Extract text from uploaded files
Supports: .txt, .pdf, .docx
"""
import io
from typing import Tuple, Optional


def parse_file(content: bytes, filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse uploaded file and extract text content.

    Args:
        content: Raw file bytes
        filename: Original filename (used to detect format)

    Returns:
        Tuple of (extracted_text, error_message)
    """
    filename_lower = filename.lower()

    try:
        if filename_lower.endswith('.txt'):
            return parse_txt(content)
        elif filename_lower.endswith('.pdf'):
            return parse_pdf(content)
        elif filename_lower.endswith('.docx'):
            return parse_docx(content)
        else:
            return None, f"Unsupported file format. Please upload .txt, .pdf, or .docx"
    except Exception as e:
        return None, f"Error parsing file: {str(e)}"


def parse_txt(content: bytes) -> Tuple[Optional[str], Optional[str]]:
    """Parse plain text file"""
    try:
        # Try UTF-8 first, then fallback to latin-1
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')
        return text, None
    except Exception as e:
        return None, f"Error reading text file: {str(e)}"


def parse_pdf(content: bytes) -> Tuple[Optional[str], Optional[str]]:
    """Parse PDF file using pypdf"""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, "PDF support requires pypdf. Install with: pip install pypdf"

    try:
        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        if not text_parts:
            return None, "Could not extract text from PDF. It may be scanned/image-based."

        return "\n".join(text_parts), None
    except Exception as e:
        return None, f"Error reading PDF: {str(e)}"


def parse_docx(content: bytes) -> Tuple[Optional[str], Optional[str]]:
    """Parse Word document using python-docx"""
    try:
        from docx import Document
    except ImportError:
        return None, "DOCX support requires python-docx. Install with: pip install python-docx"

    try:
        doc = Document(io.BytesIO(content))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        if not text_parts:
            return None, "Could not extract text from document."

        return "\n".join(text_parts), None
    except Exception as e:
        return None, f"Error reading DOCX: {str(e)}"
