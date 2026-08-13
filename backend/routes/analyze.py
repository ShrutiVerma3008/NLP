"""
routes/analyze.py — POST /api/analyze

FastAPI HTTP route executing:
  1. Input validation and file/text parsing -> ResumeDocument (structured + raw text).
  2. Deterministic Job Description feature extraction -> JobRequirements.
  3. Deterministic ATS Scoring Engine -> ATSResult (authoritative ats_score & match_percentage).
  4. GitHub summary retrieval.
  5. LLM qualitative recommendations & insights.
  6. Overwriting LLM ats_score with authoritative deterministic ATSResult.
"""

import io
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from schemas.analysis import AnalysisResponse
from schemas.resume import ResumeDocument
from services.ats_engine import calculate_ats_score
from services.github_service import get_github_summary
from services.jd_analyzer import analyze_job_description
from services.llm_service import analyze_resume
from services.parser_service import parse_file
from services.resume_structurer import create_resume_document

logger = logging.getLogger("ai_ris.routes.analyze")

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_FILE_BYTES = 10 * 1024 * 1024          # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MIN_RESUME_CHARS = 50                       # guard against empty parsed text


def _file_extension(filename: str) -> str:
    """Return the lowercased extension including the dot, e.g. '.pdf'."""
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot != -1 else ""


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str]        = Form(None),
    job_description: str              = Form(...),
    github_username: Optional[str]    = Form(None),
):
    # ── 1. Validate Job Description ───────────────────────────────────────────
    clean_jd = (job_description or "").strip()
    if not clean_jd:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Job description is required and cannot be empty.",
        )

    # ── 2. Validate Resume Source Presence ────────────────────────────────────
    has_file = resume_file is not None and bool(resume_file.filename)
    has_text = resume_text is not None and resume_text.strip() != ""

    if not has_file and not has_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide a resume: upload a PDF/DOCX file, or paste your resume text.",
        )

    # ── 3. Parse File / Raw Text Boundary ──────────────────────────────────────
    raw_extracted_text: str = ""

    if has_file:
        filename = resume_file.filename or ""
        ext = _file_extension(filename)

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=(
                    f"Unsupported file type '{ext or '(none)'}'. "
                    f"Only {', '.join(sorted(ALLOWED_EXTENSIONS))} files are accepted."
                ),
            )

        file_bytes = await resume_file.read()
        if len(file_bytes) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File is too large ({len(file_bytes) // (1024*1024):.1f} MB). "
                    f"Maximum allowed size is {MAX_FILE_BYTES // (1024*1024)} MB."
                ),
            )

        resume_file._file = io.BytesIO(file_bytes)  # type: ignore[attr-defined]

        try:
            raw_extracted_text = await parse_file(resume_file)
        except Exception as exc:
            logger.warning("Resume parse failed for '%s': %s", filename, exc)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from the uploaded file. Ensure it is a valid, non-encrypted PDF or DOCX.",
            )

    else:
        raw_extracted_text = resume_text.strip()  # type: ignore[union-attr]

    # ── 4. Content Length Guard ───────────────────────────────────────────────
    if len(raw_extracted_text) < MIN_RESUME_CHARS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "The resume appears to be empty or too short after parsing. "
                "Try the 'Paste Text' mode if the file extraction produced no output."
            ),
        )

    # ── 5. Structure Resume & Analyze Job Description (Deterministic ATS) ────
    resume_doc: ResumeDocument = create_resume_document(raw_extracted_text)
    job_reqs = analyze_job_description(clean_jd)
    ats_result = calculate_ats_score(resume_doc.structured, job_reqs)

    logger.info(
        "Deterministic ATS engine completed: overall_score=%d (%s)",
        ats_result.overall_score,
        ats_result.match_percentage,
    )

    # ── 6. GitHub Context Service Boundary ────────────────────────────────────
    github_summary = ""
    if github_username and github_username.strip():
        logger.info("Fetching GitHub summary for user: %s", github_username.strip())
        github_summary = await get_github_summary(github_username.strip())

    # ── 7. LLM Qualitative Recommendations ────────────────────────────────────
    logger.info(
        "Starting LLM qualitative analysis (resume_len=%d, jd_len=%d, github=%s)",
        len(raw_extracted_text),
        len(clean_jd),
        bool(github_summary),
    )

    try:
        llm_response: AnalysisResponse = await analyze_resume(
            raw_extracted_text, clean_jd, github_summary
        )

        # ── 8. AUTHORITATIVE OVERWRITE: Use Deterministic ATS Score ───────────
        llm_response.ats_score = ats_result.overall_score
        llm_response.match_percentage = ats_result.match_percentage
        llm_response.ats_breakdown = ats_result

        return llm_response

    except ValueError as exc:
        err_msg = str(exc)
        logger.error("LLM validation/configuration error: %s", err_msg)
        if "OPENROUTER_API_KEY" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=err_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Analysis engine response error: {err_msg}",
            )
    except RuntimeError as exc:
        logger.error("LLM runtime error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during LLM analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during analysis. Please try again.",
        )
