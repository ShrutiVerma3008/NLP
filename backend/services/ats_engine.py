"""
backend/services/ats_engine.py — Deterministic ATS Scoring Engine

Calculates explainable, reproducible, deterministic ATS scores (0-100) and component breakdowns.
Does NOT rely on LLM outputs or non-deterministic APIs.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from schemas.ats import ATSResult, ATSScoreComponents, SkillMatchEvidence
from schemas.resume import ParsedResume
from services.jd_analyzer import JobRequirements, analyze_job_description
from services.skill_normalizer import normalize_skill_name

logger = logging.getLogger("ai_ris.ats_engine")

# ── Component Scoring Weights ──────────────────────────────────────────────────
WEIGHT_SKILL_MATCH = 0.45
WEIGHT_EXPERIENCE = 0.20
WEIGHT_KEYWORD = 0.15
WEIGHT_EDUCATION = 0.10
WEIGHT_CERTIFICATION = 0.05
WEIGHT_STRUCTURE = 0.05


def _parse_year_number(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    m = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
    return int(m.group(1)) if m else None


def calculate_total_experience_years(resume: ParsedResume) -> float:
    """Calculate total years of professional experience from structured experience entries."""
    if not resume.experience:
        return 0.0

    total_months = 0.0
    for exp in resume.experience:
        s_year = _parse_year_number(exp.start_date)
        if not s_year:
            continue

        if exp.end_date and exp.end_date.lower() in ["present", "current"]:
            e_year = 2026  # Current environment year reference
        else:
            e_year = _parse_year_number(exp.end_date) or s_year

        diff = max(0, e_year - s_year)
        # Assume average 1 year if same start/end year
        total_months += max(1.0, float(diff))

    return total_months


def evaluate_skill_matches(
    resume: ParsedResume, required_skills: List[str]
) -> Tuple[List[SkillMatchEvidence], List[str], List[str]]:
    """
    Evaluate each required skill against the structured resume.
    Returns (skill_evidences, matched_skills, missing_skills).
    Deduplicates evidence so no skill is double counted.
    """
    evidences: List[SkillMatchEvidence] = []
    matched: List[str] = []
    missing: List[str] = []

    # Map normalized resume content for evidence tracing
    declared_skills = {normalize_skill_name(s).lower(): s for s in resume.skills}

    # Projects text & tech
    project_text_map: Dict[str, str] = {}
    for p in resume.projects:
        p_name = p.name or "Project"
        combo = f"{p.name or ''} {p.description or ''} {' '.join(p.bullets)} {' '.join(p.technologies)}"
        project_text_map[p_name] = combo.lower()

    # Experience text
    exp_text_map: Dict[str, str] = {}
    for e in resume.experience:
        e_title = f"{e.role or ''} at {e.company or ''}".strip(" at") or "Experience"
        combo = f"{e.role or ''} {e.company or ''} {' '.join(e.bullets)}"
        exp_text_map[e_title] = combo.lower()

    summary_lower = (resume.summary or "").lower()

    for req_skill in required_skills:
        canon_req = normalize_skill_name(req_skill)
        canon_lower = canon_req.lower()

        found_evidence: Optional[str] = None
        status = "missing"

        # Priority 1: Declared in skills section
        if canon_lower in declared_skills:
            status = "matched"
            found_evidence = "Skills section"
        else:
            # Priority 2: Found in experience
            for title, exp_text in exp_text_map.items():
                if re.search(r"(?i)\b" + re.escape(canon_lower) + r"\b", exp_text):
                    status = "matched"
                    found_evidence = f"Experience: {title}"
                    break

            # Priority 3: Found in projects
            if status == "missing":
                for p_name, p_text in project_text_map.items():
                    if re.search(r"(?i)\b" + re.escape(canon_lower) + r"\b", p_text):
                        status = "matched"
                        found_evidence = f"Project: {p_name}"
                        break

            # Priority 4: Found in summary
            if status == "missing" and re.search(r"(?i)\b" + re.escape(canon_lower) + r"\b", summary_lower):
                status = "matched"
                found_evidence = "Professional Summary"

        evidences.append(
            SkillMatchEvidence(
                skill=canon_req,
                status=status,  # type: ignore[arg-type]
                evidence=found_evidence,
            )
        )

        if status == "matched":
            matched.append(canon_req)
        else:
            missing.append(canon_req)

    return evidences, matched, missing


def calculate_ats_score(
    resume: ParsedResume, job_requirements: JobRequirements
) -> ATSResult:
    """
    Main deterministic ATS calculation algorithm.
    Produces repeatable, explainable 0-100 score and breakdown.
    """
    req_skills = job_requirements.required_skills
    evidences, matched_skills, missing_skills = evaluate_skill_matches(resume, req_skills)

    # 1. Skill Match Score
    if req_skills:
        skill_score = int(round((len(matched_skills) / len(req_skills)) * 100))
    else:
        skill_score = 100

    # 2. Experience Alignment Score
    total_exp_years = calculate_total_experience_years(resume)
    req_years = job_requirements.required_experience_years
    if req_years and req_years > 0:
        ratio = min(total_exp_years / float(req_years), 1.0)
        exp_score = int(round(ratio * 100))
    else:
        exp_score = 100

    # 3. Keyword Match Score
    keywords = job_requirements.keywords
    if keywords:
        kw_match_count = sum(1 for k in keywords if normalize_skill_name(k) in matched_skills)
        kw_score = int(round((kw_match_count / len(keywords)) * 100))
    else:
        kw_score = 100

    # 4. Education Alignment Score
    req_edu = job_requirements.required_education
    if req_edu:
        edu_score = 0
        req_edu_lower = req_edu.lower()
        for edu in resume.education:
            deg_str = (edu.degree or "").lower()
            inst_str = (edu.institution or "").lower()
            if req_edu_lower in deg_str or req_edu_lower in inst_str or ("bachelor" in req_edu_lower and ("b.s" in deg_str or "b.tech" in deg_str or "bachelor" in deg_str)):
                edu_score = 100
                break
    else:
        edu_score = 100

    # 5. Certification Alignment Score
    req_certs = job_requirements.required_certifications
    if req_certs:
        cert_names = [c.name.lower() for c in resume.certifications]
        matched_c = 0
        for rc in req_certs:
            rc_lower = rc.lower()
            if any(rc_lower in cn for cn in cert_names):
                matched_c += 1
        cert_score = int(round((matched_c / len(req_certs)) * 100))
    else:
        cert_score = 100

    # 6. Resume Structure Score
    struct_pts = 0
    if resume.contact.email or resume.contact.phone:
        struct_pts += 25
    if resume.skills:
        struct_pts += 25
    if resume.experience or resume.projects:
        struct_pts += 30
    if resume.education:
        struct_pts += 20
    struct_score = min(struct_pts, 100)

    # Calculate weighted overall score
    raw_overall = (
        WEIGHT_SKILL_MATCH * skill_score
        + WEIGHT_EXPERIENCE * exp_score
        + WEIGHT_KEYWORD * kw_score
        + WEIGHT_EDUCATION * edu_score
        + WEIGHT_CERTIFICATION * cert_score
        + WEIGHT_STRUCTURE * struct_score
    )

    overall_score = max(0, min(100, int(round(raw_overall))))
    match_percentage = f"{overall_score}%"

    components = ATSScoreComponents(
        skill_match=skill_score,
        experience_alignment=exp_score,
        keyword_match=kw_score,
        education_alignment=edu_score,
        certification_alignment=cert_score,
        resume_structure=struct_score,
    )

    return ATSResult(
        overall_score=overall_score,
        match_percentage=match_percentage,
        components=components,
        skill_evidences=evidences,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )
