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
    await file.seek(0)
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
    extracted_text = ""
    errors = []

    # Engine 1: PyMuPDF (pymupdf) - Handles custom font encoding, Canva, and Word exports
    try:
        import pymupdf
        doc = pymupdf.open(stream=content, filetype="pdf")
        pages = []
        for page in doc:
            t = page.get_text("text")
            if t and t.strip():
                pages.append(t.strip())
        extracted_text = "\n".join(pages).strip()
    except Exception as exc:
        logger.debug("PyMuPDF extraction failed: %s", exc)
        errors.append(f"PyMuPDF: {exc}")

    # Engine 2: pdfplumber - Excellent for complex table layout PDFs
    if not extracted_text:
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t and t.strip():
                        pages.append(t.strip())
                extracted_text = "\n".join(pages).strip()
        except Exception as exc:
            logger.debug("pdfplumber extraction failed: %s", exc)
            errors.append(f"pdfplumber: {exc}")

    # Engine 3: pypdf (modern PyPDF successor)
    if not extracted_text:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages = []
            for page in reader.pages:
                t = page.extract_text()
                if t and t.strip():
                    pages.append(t.strip())
            extracted_text = "\n".join(pages).strip()
        except Exception as exc:
            logger.debug("pypdf extraction failed: %s", exc)
            errors.append(f"pypdf: {exc}")

    # Engine 4: PyPDF2 (legacy fallback)
    if not extracted_text:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            if len(reader.pages) == 0:
                raise ValueError("PDF file has 0 pages.")
            pages = []
            for page in reader.pages:
                t = page.extract_text()
                if t and t.strip():
                    pages.append(t.strip())
            extracted_text = "\n".join(pages).strip()
        except Exception as exc:
            logger.debug("PyPDF2 extraction failed: %s", exc)
            errors.append(f"PyPDF2: {exc}")

    if not extracted_text:
        raise ValueError(
            "Failed to extract text from PDF. The file may be a scanned image or photo PDF without selectable text. "
            "Please copy and paste your resume text using the 'Paste Text' tab."
        )

    return extracted_text


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
