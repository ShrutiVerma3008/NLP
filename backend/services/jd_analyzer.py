"""
backend/services/jd_analyzer.py — Deterministic Job Description Analyzer

Extracts required skills, experience years, education requirements, and keywords
from raw Job Description text without using an LLM.
"""

import re
from typing import List, Optional, Set
from pydantic import BaseModel, Field

from services.skill_normalizer import SKILL_CANONICAL_MAP, normalize_skill_name


class JobRequirements(BaseModel):
    required_skills: List[str] = Field(default_factory=list, description="Extracted canonical required skills")
    required_experience_years: Optional[int] = Field(None, description="Required years of professional experience")
    required_education: Optional[str] = Field(None, description="Required degree (e.g. Bachelor, Master)")
    required_certifications: List[str] = Field(default_factory=list, description="Explicitly required certifications")
    keywords: List[str] = Field(default_factory=list, description="Extracted technical keywords")


EXP_YEARS_REGEX = re.compile(
    r"(?i)\b(\d{1,2})\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|work|background)\b"
)

DEGREE_REGEX = re.compile(
    r"(?i)\b(Bachelor(?:'s)?|B\.?S\.?|B\.?E\.?|B\.?Tech|Master(?:'s)?|M\.?S\.?|M\.?Tech|Ph\.?D\.?)\b"
)

CERT_REGEX = re.compile(
    r"(?i)\b(AWS Certified|Certified Kubernetes|CKA|PMP|CISSP|CompTIA|CCNA)\b"
)


def analyze_job_description(jd_text: str) -> JobRequirements:
    """
    Deterministically analyze Job Description text to extract structured requirements.
    """
    if not jd_text or not jd_text.strip():
        return JobRequirements()

    text = jd_text.strip()
    text_lower = text.lower()

    # 1. Skill Extraction via vocabulary phrase matching
    found_skills: List[str] = []
    seen_canonical: Set[str] = set()

    # Match canonical keys in vocabulary
    for key, canonical in SKILL_CANONICAL_MAP.items():
        # Match as whole word or boundaries
        pattern = r"(?i)\b" + re.escape(key) + r"\b"
        if key in ["c++", "c#", ".net"]:
            pattern = r"(?i)" + re.escape(key)

        if re.search(pattern, text):
            if canonical not in seen_canonical:
                seen_canonical.add(canonical)
                found_skills.append(canonical)

    # 2. Experience years extraction
    exp_years: Optional[int] = None
    exp_match = EXP_YEARS_REGEX.search(text)
    if exp_match:
        try:
            exp_years = int(exp_match.group(1))
        except ValueError:
            exp_years = None

    # 3. Education extraction
    edu_req: Optional[str] = None
    edu_match = DEGREE_REGEX.search(text)
    if edu_match:
        edu_req = edu_match.group(0)

    # 4. Certifications extraction
    certs: List[str] = []
    cert_matches = CERT_REGEX.findall(text)
    for c in cert_matches:
        if c not in certs:
            certs.append(c)

    return JobRequirements(
        required_skills=found_skills,
        required_experience_years=exp_years,
        required_education=edu_req,
        required_certifications=certs,
        keywords=found_skills,
    )
