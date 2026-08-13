"""
services/parser_service.py — Document parsing and structuring service

Extracts raw plain text and structures PDF or DOCX binary buffers into ResumeDocument instances.
Strictly decoupled from LLM, ATS scoring algorithms, and HTTP router logic.
"""

import io
import logging
from typing import Union
from fastapi import UploadFile
import PyPDF2
from docx import Document

from schemas.resume import ResumeDocument
from services.resume_structurer import create_resume_document

logger = logging.getLogger("ai_ris.parser")


async def parse_file(file: UploadFile) -> str:
    """Extract plain text from an uploaded PDF or DOCX file."""
    content = await file.read()
    filename = (file.filename or "").lower()
    return parse_resume_bytes(content, filename)


async def parse_file_to_document(file: UploadFile) -> ResumeDocument:
    """Extract text and return a structured ResumeDocument containing raw_text and structured data."""
    raw_text = await parse_file(file)
    return create_resume_document(raw_text)


def parse_resume_bytes(content: bytes, filename: str) -> str:
    """Parse resume binary bytes according to file extension."""
    if not content:
        raise ValueError("Uploaded file content is empty.")

    fname = (filename or "").lower()
    if fname.endswith(".pdf"):
        return _parse_pdf(content)
    elif fname.endswith(".docx"):
        return _parse_docx(content)
    else:
        # Fallback: try utf-8 decode
        try:
            return content.decode("utf-8", errors="replace")
        except Exception as exc:
            raise ValueError(f"Failed to decode text file: {exc}")


def _parse_pdf(content: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        if len(reader.pages) == 0:
            raise ValueError("PDF file has 0 pages.")
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        extracted = "\n".join(pages).strip()
        if not extracted:
            raise ValueError("PDF contains no extractable text.")
        return extracted
    except Exception as exc:
        logger.warning("PDF extraction error: %s", exc)
        raise ValueError(f"Failed to extract text from PDF: {exc}")


def _parse_docx(content: bytes) -> str:
    try:
        doc = Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        extracted = "\n".join(paragraphs).strip()
        if not extracted:
            raise ValueError("DOCX contains no extractable text.")
        return extracted
    except Exception as exc:
        logger.warning("DOCX extraction error: %s", exc)
        raise ValueError(f"Failed to extract text from DOCX: {exc}")
