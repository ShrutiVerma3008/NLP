from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.parser_service import parse_file
from services.github_service import get_github_summary
from services.llm_service import analyze_resume

router = APIRouter()


@router.post("/analyze")
async def analyze(
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str]       = Form(None),
    job_description: str             = Form(...),
    github_username: Optional[str]   = Form(None),
):
    # ── 1. Parse Resume ──────────────────────────────────────────────
    if resume_file and resume_file.filename:
        try:
            extracted_text = await parse_file(resume_file)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not parse resume file: {e}")
    elif resume_text and resume_text.strip():
        extracted_text = resume_text.strip()
    else:
        raise HTTPException(status_code=400, detail="Please provide a resume file or resume text.")

    # ── 2. GitHub Summary ─────────────────────────────────────────────
    github_summary = ""
    if github_username and github_username.strip():
        github_summary = await get_github_summary(github_username.strip())

    # ── 3. LLM Analysis ──────────────────────────────────────────────
    try:
        result = await analyze_resume(extracted_text, job_description, github_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {e}")

    return result
