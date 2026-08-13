"""
backend/schemas/analysis.py — Pydantic schemas for AI Resume Intelligence System API

These schemas establish a strict, predictable contract between ATS engine output,
LLM qualitative analysis, FastAPI routes, and the React frontend.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from schemas.ats import ATSResult


class SkillGap(BaseModel):
    skill: str = Field(..., description="Name of the missing or incomplete skill")
    severity: Literal["high", "medium", "low"] = Field(
        ..., description="Severity level of the skill gap"
    )
    description: str = Field(
        ..., description="Explanation of why this skill gap matters for the job"
    )


class ProjectSuggestion(BaseModel):
    title: str = Field(..., description="Title of the recommended project")
    description: str = Field(..., description="Short overview of what to build")
    why_it_helps: str = Field(
        ..., description="How this project addresses specific job requirements"
    )
    tech_stack: List[str] = Field(
        default_factory=list, description="Technologies to use"
    )


class AnalysisResponse(BaseModel):
    ats_score: int = Field(..., ge=0, le=100, description="Deterministic ATS match score from 0 to 100")
    match_percentage: str = Field(
        ..., description="ATS match score formatted as percentage e.g. '85%'"
    )
    optimized_resume: str = Field(
        ..., description="Full optimized ATS-ready resume plain text"
    )
    key_improvements: List[str] = Field(
        default_factory=list, description="Key resume improvements made"
    )
    original_bullets: List[str] = Field(
        default_factory=list, description="Original bullet points extracted"
    )
    optimized_bullets: List[str] = Field(
        default_factory=list, description="AI rewritten bullet points"
    )
    skill_gaps: List[SkillGap] = Field(
        default_factory=list, description="Identified skill gaps"
    )
    project_suggestions: List[ProjectSuggestion] = Field(
        default_factory=list, description="Recommended build projects"
    )
    top_strengths: List[str] = Field(
        default_factory=list, description="Candidate top strengths"
    )
    recruiter_insight: str = Field(
        ..., description="Recruiter-level feedback and insight"
    )
    github_integration: List[str] = Field(
        default_factory=list, description="GitHub project resume bullets"
    )
    ats_breakdown: Optional[ATSResult] = Field(
        None, description="Detailed component breakdown from deterministic ATS engine"
    )
