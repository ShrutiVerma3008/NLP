"""
services/llm_service.py — OpenRouter / Gemini 2.5 Flash integration

Key responsibilities:
- Assembles LLM system prompt via safe string concatenation.
- Calls OpenRouter via singleton AsyncOpenAI client.
- Parses LLM output and validates it strictly against AnalysisResponse schema.
- Raises typed exceptions (ValueError, RuntimeError) if configuration, network, or schema validation fails.
"""

import json
import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI, APIError, APITimeoutError, AuthenticationError
from pydantic import ValidationError

from schemas.analysis import AnalysisResponse

load_dotenv()

logger = logging.getLogger("ai_ris.llm")

# ── Configuration ─────────────────────────────────────────────────────────────
OPENROUTER_MODEL = "google/gemini-2.5-flash"
LLM_TEMPERATURE  = 0.4
LLM_MAX_TOKENS   = 4096
LLM_TIMEOUT_SECS = 90.0

_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

if not _api_key:
    logger.warning(
        "OPENROUTER_API_KEY is not set — analysis requests will fail. "
        "Add your key to backend/.env (see .env.example)."
    )

# ── Singleton client ──────────────────────────────────────────────────────────
_client: Optional[AsyncOpenAI] = (
    AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=_api_key,
        timeout=LLM_TIMEOUT_SECS,
    )
    if _api_key
    else None
)

# ── Prompt template ───────────────────────────────────────────────────────────
_PROMPT_HEADER = """\
You are an expert AI system combining:
1. Senior Technical Recruiter (10+ years experience)
2. ATS (Applicant Tracking System) optimizer
3. Career Coach specializing in tech roles

Your task is to analyze and optimize a candidate's profile against a given job description.

=== INPUTS ===

RESUME_TEXT:
"""

_PROMPT_MIDDLE_1 = """

JOB_DESCRIPTION:
"""

_PROMPT_MIDDLE_2 = """

GITHUB_DATA:
"""

_PROMPT_FOOTER = """

=== OBJECTIVES ===

Step 1: Extract key requirements from the job description (skills, tools, experience level, keywords)
Step 2: Analyze the resume — extract skills, projects, experience; identify gaps
Step 3: Calculate ATS match score 0-100 based on keyword and skill alignment
Step 4: Rewrite 3-5 resume bullets: strong action verbs, JD-aligned keywords.
        IMPORTANT — only use facts present in the resume. Do NOT invent metrics,
        percentages, team sizes, or technologies that are not in the original text.
Step 5: Integrate top GitHub projects as professional resume bullet points
Step 6: Provide recruiter-level insight

=== OUTPUT FORMAT (STRICT JSON — NO MARKDOWN WRAPPING) ===

{
  "ats_score": <integer 0-100>,
  "match_percentage": "<XX%>",
  "optimized_resume": "<full optimized resume in plain text, clean ATS-ready format>",
  "key_improvements": [
    "<specific improvement 1>",
    "<specific improvement 2>",
    "<specific improvement 3>"
  ],
  "original_bullets": [
    "<original bullet from resume 1>",
    "<original bullet from resume 2>",
    "<original bullet from resume 3>"
  ],
  "optimized_bullets": [
    "<AI-rewritten bullet 1 with action verb>",
    "<AI-rewritten bullet 2 with action verb>",
    "<AI-rewritten bullet 3 with action verb>"
  ],
  "skill_gaps": [
    {"skill": "<skill name>", "severity": "high",   "description": "<why this matters for the JD>"},
    {"skill": "<skill name>", "severity": "medium", "description": "<why this matters>"},
    {"skill": "<skill name>", "severity": "low",    "description": "<why this matters>"}
  ],
  "project_suggestions": [
    {
      "title": "<project title>",
      "description": "<what to build in 1-2 sentences>",
      "why_it_helps": "<direct reference to JD requirement it addresses>",
      "tech_stack": ["<tech1>", "<tech2>", "<tech3>"]
    },
    {
      "title": "<project title>",
      "description": "<what to build>",
      "why_it_helps": "<reason>",
      "tech_stack": ["<tech1>", "<tech2>"]
    },
    {
      "title": "<project title>",
      "description": "<what to build>",
      "why_it_helps": "<reason>",
      "tech_stack": ["<tech1>", "<tech2>"]
    }
  ],
  "top_strengths": [
    "<strength 1>",
    "<strength 2>",
    "<strength 3>"
  ],
  "recruiter_insight": "<2-3 sentences of professional recruiter-level insight. Be specific.>",
  "github_integration": [
    "<GitHub project converted to resume bullet 1>",
    "<GitHub project converted to resume bullet 2>"
  ]
}

=== RULES ===
- Return ONLY the JSON object above. No markdown, no explanation, no ```json fencing.
- Be specific. No generic advice.
- Use strong action verbs: Engineered, Architected, Optimized, Delivered, Deployed, Automated.
- skill_gaps severity must be exactly "high", "medium", or "low"
- If github_summary is "Not provided", set github_integration to an empty array.
- Do NOT invent any fact not present in the provided resume or GitHub data.
"""


def parse_and_validate_llm_response(raw_text: str) -> AnalysisResponse:
    """
    Parse raw string output from LLM and validate strictly against AnalysisResponse Pydantic schema.
    Raises ValueError if JSON is invalid or schema validation fails.
    """
    raw = (raw_text or "").strip()
    # Strip any accidental markdown fencing
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    if not raw:
        raise ValueError("LLM returned an empty response.")

    try:
        data_dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Fallback search for JSON object inside response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                data_dict = json.loads(match.group())
            except json.JSONDecodeError:
                raise ValueError(f"LLM output could not be parsed as JSON: {exc}")
        else:
            raise ValueError(f"LLM output could not be parsed as JSON: {exc}")

    try:
        return AnalysisResponse.model_validate(data_dict)
    except ValidationError as exc:
        logger.warning("LLM response failed Pydantic schema validation: %s", exc)
        raise ValueError(f"LLM response failed schema validation: {exc}")


async def analyze_resume(
    resume_text: str, job_description: str, github_summary: str
) -> AnalysisResponse:
    """
    Call OpenRouter API with prompt and validate response against AnalysisResponse.
    Raises ValueError for configuration or validation errors.
    Raises RuntimeError for network or API errors.
    """
    if not _api_key or _client is None:
        raise ValueError(
            "OPENROUTER_API_KEY is not configured. "
            "Set it in backend/.env — see backend/.env.example for instructions."
        )

    prompt = (
        _PROMPT_HEADER
        + (resume_text or "Not provided")
        + _PROMPT_MIDDLE_1
        + (job_description or "Not provided")
        + _PROMPT_MIDDLE_2
        + (github_summary or "Not provided")
        + _PROMPT_FOOTER
    )

    logger.info(
        "Sending analysis request to OpenRouter (model=%s, prompt_len=%d chars)",
        OPENROUTER_MODEL,
        len(prompt),
    )

    try:
        response = await _client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
    except AuthenticationError:
        logger.error("OpenRouter authentication failed — check OPENROUTER_API_KEY")
        raise ValueError("OpenRouter authentication failed. Verify your API key.")
    except APITimeoutError:
        logger.error("OpenRouter request timed out after %.0f seconds", LLM_TIMEOUT_SECS)
        raise RuntimeError(
            f"The AI model did not respond within {int(LLM_TIMEOUT_SECS)} seconds. Please try again."
        )
    except APIError as exc:
        logger.error("OpenRouter API error: %s", exc)
        raise RuntimeError(f"OpenRouter API error: {exc.message}")

    raw_content = response.choices[0].message.content or ""
    logger.info("Received LLM response (%d chars)", len(raw_content))

    return parse_and_validate_llm_response(raw_content)
