"""
services/resume_structurer.py — Deterministic Resume Structuring Service

Extracts structured resume data (contact, summary, skills, experience, projects, education,
certifications) from raw text without inventing facts or hallucinating unmentioned attributes.
Strictly preserves technical terms, special characters (C++, C#, std::vector<T>, {templates}),
and missing value semantics (null / empty lists).
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

from schemas.resume import (
    CertificationEntry,
    ContactInfo,
    EducationEntry,
    ExperienceEntry,
    ParsedResume,
    ProjectEntry,
    ResumeDocument,
)

logger = logging.getLogger("ai_ris.structurer")

# ── Canonical Section Map ──────────────────────────────────────────────────────
SECTION_CANONICAL_MAP = {
    # Summary
    "summary": "SUMMARY",
    "professional summary": "SUMMARY",
    "summary of qualifications": "SUMMARY",
    "profile": "SUMMARY",
    "about me": "SUMMARY",
    "objective": "SUMMARY",
    "career objective": "SUMMARY",
    # Skills
    "skills": "SKILLS",
    "technical skills": "SKILLS",
    "core skills": "SKILLS",
    "core competencies": "SKILLS",
    "technologies": "SKILLS",
    "skills & tools": "SKILLS",
    "skills and tools": "SKILLS",
    "technical stack": "SKILLS",
    "technical competencies": "SKILLS",
    "technical competencies:": "SKILLS",
    # Experience
    "experience": "EXPERIENCE",
    "work experience": "EXPERIENCE",
    "professional experience": "EXPERIENCE",
    "professional background": "EXPERIENCE",
    "employment history": "EXPERIENCE",
    "work history": "EXPERIENCE",
    "career history": "EXPERIENCE",
    "relevant experience": "EXPERIENCE",
    # Projects
    "projects": "PROJECTS",
    "technical projects": "PROJECTS",
    "personal projects": "PROJECTS",
    "key projects": "PROJECTS",
    "academic projects": "PROJECTS",
    # Education
    "education": "EDUCATION",
    "academic background": "EDUCATION",
    "education & qualifications": "EDUCATION",
    "education and qualifications": "EDUCATION",
    "qualifications": "EDUCATION",
    # Certifications
    "certifications": "CERTIFICATIONS",
    "licenses & certifications": "CERTIFICATIONS",
    "certificates": "CERTIFICATIONS",
}

# Regex Patterns for Contact & Data Extraction
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
)
LINKEDIN_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?", re.IGNORECASE
)
GITHUB_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)/?", re.IGNORECASE
)
URL_REGEX = re.compile(
    r"https?://[^\s/$.?#].[^\s]*", re.IGNORECASE
)
DATE_RANGE_REGEX = re.compile(
    r"(?i)\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*\d{2,4}|\d{4})\s*[-–—to\s]+\s*(Present|Current|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*\d{2,4}|\d{4})\b"
)
DEGREE_PATTERNS = [
    r"(?i)\bB\.?S\.?\b", r"(?i)\bM\.?S\.?\b", r"(?i)\bPh\.?D\.?\b",
    r"(?i)\bB\.?E\.?\b", r"(?i)\bB\.?Tech\b", r"(?i)\bM\.?Tech\b",
    r"(?i)\bBachelor(?:'s)?\b", r"(?i)\bMaster(?:'s)?\b", r"(?i)\bAssociate\b"
]


def normalize_resume_text(text: str) -> str:
    """
    Clean up line endings, unicode bullet characters, and excessive whitespace.
    Preserves all syntax, code snippets, and special characters.
    """
    if not text:
        return ""

    # Standardize line endings
    norm = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace common Unicode bullet symbols with uniform '- '
    bullet_symbols = ["\u2022", "\u2023", "\u25e6", "\u2043", "\u2219", "\u25aa", "\u25ab", "\uf0b7", "", "•"]
    for sym in bullet_symbols:
        norm = norm.replace(sym, "\n- ")

    # Clean double spaces after bullet replacements
    norm = re.sub(r"\n\-\s+", "\n- ", norm)
    # Collapse >3 consecutive newlines into 2
    norm = re.sub(r"\n{3,}", "\n\n", norm)
    return norm.strip()


def extract_contact_info(lines: List[str], full_text: str) -> ContactInfo:
    """Extract contact information deterministically using regex and heuristics."""
    email = None
    phone = None
    linkedin = None
    github = None
    portfolio = None
    name = None

    # Emails
    email_match = EMAIL_REGEX.search(full_text)
    if email_match:
        email = email_match.group(0)

    # Phones
    phone_match = PHONE_REGEX.search(full_text)
    if phone_match:
        phone = phone_match.group(0).strip()

    # LinkedIn
    linkedin_match = LINKEDIN_REGEX.search(full_text)
    if linkedin_match:
        linkedin = linkedin_match.group(0)

    # GitHub
    github_match = GITHUB_REGEX.search(full_text)
    if github_match:
        github = github_match.group(0)

    # Portfolio / Website (URLs not linkedin or github)
    all_urls = URL_REGEX.findall(full_text)
    for url in all_urls:
        url_lower = url.lower()
        if "linkedin.com" not in url_lower and "github.com" not in url_lower:
            portfolio = url
            break

    # Name heuristic: First non-empty line that doesn't contain email/phone/url or heading
    for line in lines[:5]:
        clean_l = line.strip()
        if not clean_l:
            continue
        if EMAIL_REGEX.search(clean_l) or PHONE_REGEX.search(clean_l) or URL_REGEX.search(clean_l):
            continue
        clean_h = re.sub(r"^[#\*\-:\s]+", "", clean_l).rstrip(":").strip().lower()
        clean_h = re.sub(r"[\*\_#]+", "", clean_h).strip()
        if clean_h in SECTION_CANONICAL_MAP:
            continue
        if len(clean_l) < 50 and not any(char in clean_l for char in [":", "@", "/", "\\"]):
            name = clean_l
            break

    return ContactInfo(
        name=name,
        email=email,
        phone=phone,
        location=None,
        linkedin=linkedin,
        github=github,
        portfolio=portfolio,
    )


def split_into_sections(raw_text: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Split normalized resume text into recognized canonical sections.
    Returns (lines, dict_of_section_lines).
    """
    normalized = normalize_resume_text(raw_text)
    lines = normalized.split("\n")

    sections: Dict[str, List[str]] = {}
    current_section = "HEADER"
    sections[current_section] = []

    for line in lines:
        stripped = line.strip()
        clean_header = re.sub(r"^[#\*\-:\s]+", "", stripped).rstrip(":").strip().lower()
        clean_header = re.sub(r"[\*\_#]+", "", clean_header).strip()

        if clean_header in SECTION_CANONICAL_MAP and len(stripped) < 45:
            current_section = SECTION_CANONICAL_MAP[clean_header]
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(line)

    return lines, sections


def parse_skills_section(skill_lines: List[str]) -> List[str]:
    """
    Extract skills preserving exact technical names (C++, C#, std::vector<T>, {templates}, etc.).
    Splits by commas, pipes, bullets, or newlines. Strips category label prefixes before colons.
    """
    skills: List[str] = []
    seen = set()

    for line in skill_lines:
        clean = line.strip()
        if not clean:
            continue
        clean = re.sub(r"^[\-\*\u2022]\s*", "", clean)

        # Strip category prefixes like "Languages & Frameworks: "
        if ":" in clean and "::" not in clean and not clean.startswith("http"):
            parts = clean.split(":", 1)
            if len(parts[0].strip().split()) <= 4:
                clean = parts[1].strip()

        # Split on commas or pipes or slashes (do NOT split on C++ '::')
        tokens = re.split(r"[,|/•\t]", clean)
        for tok in tokens:
            item = tok.strip()
            item = re.sub(r"^[\"\']|[\"\']$", "", item).strip()
            if item and item.lower() not in seen:
                if item.lower() in ["skills", "technical skills", "languages", "tools", "frameworks"]:
                    continue
                seen.add(item.lower())
                skills.append(item)

    return skills


def parse_experience_section(exp_lines: List[str]) -> List[ExperienceEntry]:
    """Extract experience entries preserving roles, companies, dates, and bullets."""
    entries: List[ExperienceEntry] = []
    if not exp_lines:
        return entries

    current_company: Optional[str] = None
    current_role: Optional[str] = None
    current_start: Optional[str] = None
    current_end: Optional[str] = None
    current_bullets: List[str] = []

    def flush_entry():
        nonlocal current_company, current_role, current_start, current_end, current_bullets
        if current_role or current_company or current_bullets:
            entries.append(
                ExperienceEntry(
                    company=current_company,
                    role=current_role,
                    location=None,
                    start_date=current_start,
                    end_date=current_end,
                    bullets=list(current_bullets),
                )
            )
            current_company = None
            current_role = None
            current_start = None
            current_end = None
            current_bullets = []

    for line in exp_lines:
        stripped = line.strip()
        if not stripped:
            continue

        date_match = DATE_RANGE_REGEX.search(stripped)
        is_bullet = stripped.startswith("-") or stripped.startswith("*") or stripped.startswith("•")

        if is_bullet:
            bullet_content = re.sub(r"^[\-\*\u2022]\s*", "", stripped).strip()
            if bullet_content:
                current_bullets.append(bullet_content)
        elif date_match:
            remainder = DATE_RANGE_REGEX.sub("", stripped).strip(" -–|,")
            if not remainder and (current_role or current_company) and not current_start:
                current_start = date_match.group(1)
                current_end = date_match.group(2)
            else:
                if current_bullets:
                    flush_entry()
                current_start = date_match.group(1)
                current_end = date_match.group(2)
                if remainder:
                    parts = [p.strip() for p in re.split(r"[-–|@,]", remainder) if p.strip()]
                    if len(parts) >= 2:
                        current_role = parts[0]
                        current_company = parts[1]
                    elif len(parts) == 1:
                        if not current_role:
                            current_role = parts[0]
                        else:
                            current_company = parts[0]
        else:
            if current_bullets:
                flush_entry()

            if not current_role:
                parts = [p.strip() for p in re.split(r"[-–|@,]", stripped) if p.strip()]
                if len(parts) >= 2:
                    current_role = parts[0]
                    current_company = parts[1]
                elif len(parts) == 1:
                    current_role = parts[0]
            elif not current_company:
                current_company = stripped

    flush_entry()
    return entries


def parse_projects_section(proj_lines: List[str]) -> List[ProjectEntry]:
    """Extract project entries preserving names, descriptions, bullets, and URLs."""
    projects: List[ProjectEntry] = []
    if not proj_lines:
        return projects

    current_name: Optional[str] = None
    current_desc: Optional[str] = None
    current_bullets: List[str] = []
    current_url: Optional[str] = None

    def flush_project():
        nonlocal current_name, current_desc, current_bullets, current_url
        if current_name or current_bullets:
            projects.append(
                ProjectEntry(
                    name=current_name,
                    description=current_desc,
                    technologies=[],  # Do NOT infer unmentioned technologies
                    bullets=list(current_bullets),
                    url=current_url,
                )
            )
            current_name = None
            current_desc = None
            current_bullets = []
            current_url = None

    for line in proj_lines:
        stripped = line.strip()
        if not stripped:
            continue

        url_match = URL_REGEX.search(stripped)
        if url_match and not current_url:
            current_url = url_match.group(0)

        is_bullet = stripped.startswith("-") or stripped.startswith("*") or stripped.startswith("•")

        if is_bullet:
            bullet_content = re.sub(r"^[\-\*\u2022]\s*", "", stripped).strip()
            if bullet_content:
                current_bullets.append(bullet_content)
        else:
            if not current_name:
                current_name = re.sub(r"^[\#\*\-:\s]+", "", stripped).strip()
            elif not current_desc and not current_bullets:
                current_desc = stripped
            elif current_bullets:
                flush_project()
                current_name = re.sub(r"^[\#\*\-:\s]+", "", stripped).strip()

    flush_project()
    return projects


def parse_education_section(edu_lines: List[str]) -> List[EducationEntry]:
    """Extract education entries including institutions, degrees, fields, and grades."""
    entries: List[EducationEntry] = []
    if not edu_lines:
        return entries

    current_inst: Optional[str] = None
    current_degree: Optional[str] = None
    current_field: Optional[str] = None
    current_start: Optional[str] = None
    current_end: Optional[str] = None
    current_grade: Optional[str] = None

    def flush_edu():
        nonlocal current_inst, current_degree, current_field, current_start, current_end, current_grade
        if current_inst or current_degree or current_grade or current_start:
            entries.append(
                EducationEntry(
                    institution=current_inst,
                    degree=current_degree,
                    field=current_field,
                    start_date=current_start,
                    end_date=current_end,
                    grade=current_grade,
                )
            )
            current_inst = None
            current_degree = None
            current_field = None
            current_start = None
            current_end = None
            current_grade = None

    for line in edu_lines:
        stripped = line.strip()
        if not stripped:
            continue
        clean = re.sub(r"^[\-\*\u2022]\s*", "", stripped).strip()

        date_match = DATE_RANGE_REGEX.search(clean)
        gpa_match = re.search(r"(?i)(?:gpa|cgpa|grade)[:\s]*([0-9\.]+\s*(?:/\s*[0-9\.]+)?|[\w\+]+)", clean)

        degree = None
        for deg_pat in DEGREE_PATTERNS:
            m = re.search(deg_pat, clean)
            if m:
                degree = m.group(0)
                break

        if date_match and not (degree or "university" in clean.lower() or "college" in clean.lower() or "school" in clean.lower()):
            if not current_start:
                current_start = date_match.group(1)
                current_end = date_match.group(2)
        elif gpa_match and not degree:
            current_grade = gpa_match.group(1)
        else:
            if current_inst or current_degree:
                flush_edu()
            if degree:
                current_degree = degree
                remainder = re.sub(r"(?i)\b(in|of)\b", "", clean).replace(degree, "").strip(" -–|,")
                parts = [p.strip() for p in re.split(r"[-–|@,]", remainder) if p.strip()]
                if len(parts) >= 1:
                    current_inst = parts[-1]
                    if len(parts) >= 2:
                        current_field = parts[0]
            else:
                current_inst = clean
            if date_match:
                current_start = date_match.group(1)
                current_end = date_match.group(2)
            if gpa_match:
                current_grade = gpa_match.group(1)

    flush_edu()
    return entries


def parse_certifications_section(cert_lines: List[str]) -> List[CertificationEntry]:
    """Extract certification entries."""
    certs: List[CertificationEntry] = []
    for line in cert_lines:
        stripped = line.strip()
        if not stripped:
            continue
        clean = re.sub(r"^[\-\*\u2022]\s*", "", stripped).strip()
        if clean:
            certs.append(CertificationEntry(name=clean, issuer=None, date=None))
    return certs


def structure_resume(raw_text: str) -> ParsedResume:
    """
    Main entry point: Parse raw resume text into a structured ParsedResume object.
    Guaranteed never to crash or invent unmentioned information.
    """
    if not raw_text or not raw_text.strip():
        return ParsedResume()

    lines, sections = split_into_sections(raw_text)

    contact = extract_contact_info(lines, raw_text)
    summary_text = "\n".join(sections.get("SUMMARY", [])).strip() or None
    skills = parse_skills_section(sections.get("SKILLS", []))
    experience = parse_experience_section(sections.get("EXPERIENCE", []))
    projects = parse_projects_section(sections.get("PROJECTS", []))
    education = parse_education_section(sections.get("EDUCATION", []))
    certifications = parse_certifications_section(sections.get("CERTIFICATIONS", []))

    return ParsedResume(
        contact=contact,
        summary=summary_text,
        skills=skills,
        experience=experience,
        projects=projects,
        education=education,
        certifications=certifications,
    )


def create_resume_document(raw_text: str) -> ResumeDocument:
    """Wrap raw text and structured resume into a ResumeDocument."""
    norm_text = normalize_resume_text(raw_text)
    structured = structure_resume(norm_text)
    return ResumeDocument(raw_text=norm_text, structured=structured)
