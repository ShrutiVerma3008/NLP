"""
backend/schemas/ats.py — Pydantic Schemas for Deterministic ATS Scoring Results

Defines structured ATS score components, skill matching evidence, and overall score results.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class SkillMatchEvidence(BaseModel):
    skill: str = Field(..., description="Canonical skill name being evaluated")
    status: Literal["matched", "partial", "missing"] = Field(
        ..., description="Match status for the skill"
    )
    evidence: Optional[str] = Field(
        None, description="Traceable location/source in resume where skill was found"
    )


class ATSScoreComponents(BaseModel):
    skill_match: int = Field(..., ge=0, le=100, description="Skill match component score (0-100)")
    experience_alignment: int = Field(..., ge=0, le=100, description="Experience alignment score (0-100)")
    keyword_match: int = Field(..., ge=0, le=100, description="Keyword match component score (0-100)")
    education_alignment: int = Field(..., ge=0, le=100, description="Education alignment score (0-100)")
    certification_alignment: int = Field(..., ge=0, le=100, description="Certification alignment score (0-100)")
    resume_structure: int = Field(..., ge=0, le=100, description="Resume structure completeness score (0-100)")


class ATSResult(BaseModel):
    overall_score: int = Field(..., ge=0, le=100, description="Deterministic overall ATS score (0-100)")
    match_percentage: str = Field(..., description="Overall score formatted as percentage string")
    components: ATSScoreComponents = Field(..., description="Breakdown of component scores")
    skill_evidences: List[SkillMatchEvidence] = Field(
        default_factory=list, description="Traceable evidence for each required skill"
    )
    matched_skills: List[str] = Field(
        default_factory=list, description="List of matched canonical skills"
    )
    missing_skills: List[str] = Field(
        default_factory=list, description="List of missing required skills"
    )
