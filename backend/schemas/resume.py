"""
backend/schemas/resume.py — Structured Resume Pydantic Schemas

Represents extracted resume data in a clean, typed, deterministic format.
All fields that may be absent in source resumes are optional or default to empty lists.
No fields are hallucinated or guessed.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: Optional[str] = Field(None, description="Candidate full name")
    email: Optional[str] = Field(None, description="Primary contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    location: Optional[str] = Field(None, description="City, State, or Country")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio: Optional[str] = Field(None, description="Personal website or portfolio URL")


class ExperienceEntry(BaseModel):
    company: Optional[str] = Field(None, description="Company or organization name")
    role: Optional[str] = Field(None, description="Job title or role")
    location: Optional[str] = Field(None, description="Work location")
    start_date: Optional[str] = Field(None, description="Start date (e.g. 'Jan 2021')")
    end_date: Optional[str] = Field(None, description="End date (e.g. 'Present' or 'Dec 2022')")
    bullets: List[str] = Field(default_factory=list, description="Bullet points / achievement descriptions")


class ProjectEntry(BaseModel):
    name: Optional[str] = Field(None, description="Project title")
    description: Optional[str] = Field(None, description="Short description of the project")
    technologies: List[str] = Field(default_factory=list, description="Technologies / tools explicitly mentioned")
    bullets: List[str] = Field(default_factory=list, description="Project details or key accomplishments")
    url: Optional[str] = Field(None, description="Project repository or live URL")


class EducationEntry(BaseModel):
    institution: Optional[str] = Field(None, description="University, college, or school name")
    degree: Optional[str] = Field(None, description="Degree earned (e.g. 'B.S.', 'M.S.')")
    field: Optional[str] = Field(None, description="Field of study / major")
    start_date: Optional[str] = Field(None, description="Start date or year")
    end_date: Optional[str] = Field(None, description="Graduation date or year")
    grade: Optional[str] = Field(None, description="GPA, CGPA, or honors if explicitly present")


class CertificationEntry(BaseModel):
    name: str = Field(..., description="Certification title")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    date: Optional[str] = Field(None, description="Issue date or year")


class ParsedResume(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo, description="Extracted contact details")
    summary: Optional[str] = Field(None, description="Professional summary or objective text")
    skills: List[str] = Field(default_factory=list, description="Extracted technical and professional skills")
    experience: List[ExperienceEntry] = Field(default_factory=list, description="Work experience entries")
    projects: List[ProjectEntry] = Field(default_factory=list, description="Project entries")
    education: List[EducationEntry] = Field(default_factory=list, description="Education entries")
    certifications: List[CertificationEntry] = Field(default_factory=list, description="Certifications")


class ResumeDocument(BaseModel):
    raw_text: str = Field(..., description="Original raw extracted plain text")
    structured: ParsedResume = Field(..., description="Structured representation of the resume")
