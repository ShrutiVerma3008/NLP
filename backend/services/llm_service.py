import os
import json
import re
import asyncio

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GOOGLE_API_KEY", "")
if _api_key:
    genai.configure(api_key=_api_key)

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an expert AI system combining:
1. Senior Technical Recruiter (10+ years experience)
2. ATS (Applicant Tracking System) optimizer
3. Career Coach specializing in tech roles

Your task is to analyze and optimize a candidate's profile against a given job description.

=== INPUTS ===

RESUME_TEXT:
{resume_text}

JOB_DESCRIPTION:
{job_description}

GITHUB_DATA:
{github_summary}

=== OBJECTIVES ===

Step 1: Extract key requirements from the job description (skills, tools, experience level, keywords)
Step 2: Analyze the resume — extract skills, projects, experience; identify gaps
Step 3: Calculate ATS match score 0-100 based on keyword and skill alignment
Step 4: Rewrite 3-5 resume bullets: strong action verbs, quantifiable impact, JD-aligned keywords
Step 5: Integrate top GitHub projects as professional resume bullet points
Step 6: Provide recruiter-level insight

=== OUTPUT FORMAT (STRICT JSON — NO MARKDOWN WRAPPING) ===

{{
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
    "<AI-rewritten bullet 1 with action verb + metric>",
    "<AI-rewritten bullet 2 with action verb + metric>",
    "<AI-rewritten bullet 3 with action verb + metric>"
  ],
  "skill_gaps": [
    {{"skill": "<skill name>", "severity": "high", "description": "<why this matters for the JD>"}},
    {{"skill": "<skill name>", "severity": "medium", "description": "<why this matters>"}},
    {{"skill": "<skill name>", "severity": "low", "description": "<why this matters>"}}
  ],
  "project_suggestions": [
    {{
      "title": "<project title>",
      "description": "<what to build in 1-2 sentences>",
      "why_it_helps": "<direct reference to JD requirement it addresses>",
      "tech_stack": ["<tech1>", "<tech2>", "<tech3>"]
    }},
    {{
      "title": "<project title>",
      "description": "<what to build>",
      "why_it_helps": "<reason>",
      "tech_stack": ["<tech1>", "<tech2>"]
    }},
    {{
      "title": "<project title>",
      "description": "<what to build>",
      "why_it_helps": "<reason>",
      "tech_stack": ["<tech1>", "<tech2>"]
    }}
  ],
  "top_strengths": [
    "<strength 1>",
    "<strength 2>",
    "<strength 3>"
  ],
  "recruiter_insight": "<2-3 sentences of professional recruiter-level insight. Be specific and data-driven.>",
  "github_integration": [
    "<GitHub project converted to resume bullet 1>",
    "<GitHub project converted to resume bullet 2>"
  ]
}}

=== RULES ===
- Return ONLY the JSON object above. No markdown, no explanation, no ```json fencing.
- Be specific and data-driven. No generic advice.
- Use strong action verbs: Engineered, Architected, Optimized, Delivered, Deployed, Automated, Orchestrated.
- Add quantifiable impact wherever possible (%, users, ms, lines of code, etc.)
- skill_gaps severity must be exactly "high", "medium", or "low"
- If github_summary is "Not provided", set github_integration to an empty array.
"""


async def analyze_resume(resume_text: str, job_description: str, github_summary: str) -> dict:
    """Call Gemini 1.5 Flash with the structured system prompt and return parsed JSON."""
    if not _api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Copy .env.example → .env and add your key "
            "from https://aistudio.google.com/app/apikey"
        )

    prompt = SYSTEM_PROMPT.format(
        resume_text=resume_text or "Not provided",
        job_description=job_description,
        github_summary=github_summary or "Not provided",
    )

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=genai.GenerationConfig(
            temperature=0.4,
            max_output_tokens=4096,
        ),
    )

    # Gemini SDK is synchronous — run in thread pool
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: model.generate_content(prompt)
    )

    raw = response.text.strip()

    # Strip any accidental markdown fencing
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract a JSON object from the response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        # Return structured error so the frontend can display it
        return {
            "error": "LLM returned non-JSON output",
            "raw": raw[:1000],
            "ats_score": 0,
            "match_percentage": "0%",
            "optimized_resume": "",
            "key_improvements": [],
            "original_bullets": [],
            "optimized_bullets": [],
            "skill_gaps": [],
            "project_suggestions": [],
            "top_strengths": [],
            "recruiter_insight": "Analysis failed — please try again.",
            "github_integration": [],
        }
