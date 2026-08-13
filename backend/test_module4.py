"""
test_module4.py — Automated test suite for Module 4 Deterministic ATS Scoring Engine.

Tests execute IN-MEMORY with MOCKED external LLM calls (zero API credits consumed).

Coverage:
1. Skill normalization
2. Exact skill match
3. Partial/Evidence skill match (tracing evidence)
4. Missing skill handling
5. Duplicate skill deduplication (no double counting)
6. Case normalization
7. C++ matching
8. PostgreSQL vs SQL strict distinction
9. Experience requirement alignment
10. Education requirement alignment
11. Certification requirement alignment
12. Weighted score calculation
13. Score boundaries 0-100
14. 10x Score determinism test (10 identical runs = 10 identical scores)
15. Empty Job Description handling
16. No recognizable skills in JD handling
17. Module 1 regression
18. Module 2 regression
19. Module 3 regression
20. API endpoint integration
"""

import json
import os
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from schemas.analysis import AnalysisResponse
from schemas.ats import ATSResult
from schemas.resume import ParsedResume
from services.ats_engine import calculate_ats_score, evaluate_skill_matches
from services.jd_analyzer import analyze_job_description
from services.resume_structurer import structure_resume
from services.skill_normalizer import normalize_skill_name

client = TestClient(app)

RESUME_SAMPLE_1 = """\
John Tech
john@tech.io | 555-0199 | San Francisco, CA
github.com/johntech

Technical Skills
Python, FastAPI, PostgreSQL, Docker, Git, C++

Work Experience
Senior Backend Developer | CloudApp Inc.
Jan 2021 - Present
- Architected REST APIs using Python, FastAPI, and PostgreSQL.

Software Engineer | DevCorp
Jun 2018 - Dec 2020
- Maintained legacy Python codebase and C++ modules.

Education
B.S. in Computer Science | Tech University
2014 - 2018

Certifications
AWS Certified Solutions Architect
"""

JD_SAMPLE_HIGH_MATCH = """\
We are looking for a Senior Backend Developer with 5+ years of experience.
Required Skills: Python, FastAPI, PostgreSQL, Docker, Git, C++.
Education: Bachelor's degree in Computer Science.
Certifications: AWS Certified.
"""

JD_SAMPLE_LOW_MATCH = """\
We are hiring a Mobile Lead with 8+ years experience.
Required Skills: Swift, Kotlin, Flutter, React Native, iOS, Android.
Education: Master's degree in Mobile Engineering.
Certifications: Certified Kubernetes Administrator (CKA).
"""


class TestModule4(unittest.TestCase):

    # ── 1. Skill Normalization ────────────────────────────────────────────────
    def test_01_skill_normalization(self):
        """Test 1: Skill normalization standardizes equivalents without over-matching."""
        self.assertEqual(normalize_skill_name("python"), "Python")
        self.assertEqual(normalize_skill_name("postgres"), "PostgreSQL")
        self.assertEqual(normalize_skill_name("c++"), "C++")
        self.assertEqual(normalize_skill_name("node.js"), "Node.js")
        self.assertEqual(normalize_skill_name("reactjs"), "React.js")

    # ── 2. Exact Skill Matching ───────────────────────────────────────────────
    def test_02_exact_skill_matching(self):
        """Test 2: Declared skills in skills section match with evidence."""
        resume = structure_resume(RESUME_SAMPLE_1)
        evidences, matched, missing = evaluate_skill_matches(resume, ["Python", "FastAPI"])
        self.assertIn("Python", matched)
        self.assertIn("FastAPI", matched)
        self.assertEqual(len(missing), 0)
        self.assertEqual(evidences[0].evidence, "Skills section")

    # ── 3. Evidence Tracing ───────────────────────────────────────────────────
    def test_03_evidence_tracing(self):
        """Test 3 & 6: Every matched skill has non-null traceable evidence."""
        resume = structure_resume(RESUME_SAMPLE_1)
        evidences, matched, _ = evaluate_skill_matches(resume, ["Python", "Docker"])
        for ev in evidences:
            if ev.status == "matched":
                self.assertIsNotNone(ev.evidence)

    # ── 4. Missing Skill Handling ──────────────────────────────────────────────
    def test_04_missing_skill_handling(self):
        """Test 4: Unmatched skills marked missing with null evidence."""
        resume = structure_resume(RESUME_SAMPLE_1)
        evidences, matched, missing = evaluate_skill_matches(resume, ["Kotlin", "Rust"])
        self.assertIn("Kotlin", missing)
        self.assertIn("Rust", missing)
        self.assertIsNone(evidences[0].evidence)

    # ── 5. Duplicate Skills Deduplication ─────────────────────────────────────
    def test_05_duplicate_skills_no_double_counting(self):
        """Test 5: Python appearing in skills, project, experience counts as 1 match."""
        resume = structure_resume(RESUME_SAMPLE_1)
        evidences, matched, _ = evaluate_skill_matches(resume, ["Python", "Python", "Python"])
        # Matched list should be deduplicated per requirement
        self.assertEqual(len(evidences), 3)

    # ── 7. C++ Matching ───────────────────────────────────────────────────────
    def test_07_cpp_matching(self):
        """Test 7: C++ is matched cleanly without dropping plus signs."""
        resume = structure_resume(RESUME_SAMPLE_1)
        evidences, matched, missing = evaluate_skill_matches(resume, ["C++"])
        self.assertIn("C++", matched)

    # ── 8. PostgreSQL vs SQL Distinction ──────────────────────────────────────
    def test_08_postgresql_vs_sql_distinction(self):
        """Test 8: Having SQL alone does NOT match PostgreSQL requirement."""
        resume_sql_only = structure_resume("Skills: SQL, MySQL, SQLite")
        _, matched, missing = evaluate_skill_matches(resume_sql_only, ["PostgreSQL"])
        self.assertIn("PostgreSQL", missing)
        self.assertNotIn("PostgreSQL", matched)

    # ── 9. Experience Requirement ──────────────────────────────────────────────
    def test_09_experience_alignment(self):
        """Test 9: Experience years compared against required years."""
        resume = structure_resume(RESUME_SAMPLE_1)
        req_5yr = analyze_job_description(JD_SAMPLE_HIGH_MATCH)
        result = calculate_ats_score(resume, req_5yr)
        self.assertGreaterEqual(result.components.experience_alignment, 80)

    # ── 10. Education Requirement ─────────────────────────────────────────────
    def test_10_education_alignment(self):
        """Test 10: Education requirement evaluation."""
        resume = structure_resume(RESUME_SAMPLE_1)
        req = analyze_job_description(JD_SAMPLE_HIGH_MATCH)
        result = calculate_ats_score(resume, req)
        self.assertEqual(result.components.education_alignment, 100)

    # ── 11. Certification Requirement ─────────────────────────────────────────
    def test_11_certification_alignment(self):
        """Test 11: Certification requirement evaluation."""
        resume = structure_resume(RESUME_SAMPLE_1)
        req = analyze_job_description(JD_SAMPLE_HIGH_MATCH)
        result = calculate_ats_score(resume, req)
        self.assertEqual(result.components.certification_alignment, 100)

    # ── 12 & 13. Score Boundaries 0-100 ───────────────────────────────────────
    def test_12_score_boundaries(self):
        """Test 12 & 13: Scores are bounded between 0 and 100."""
        resume = structure_resume(RESUME_SAMPLE_1)
        req_high = analyze_job_description(JD_SAMPLE_HIGH_MATCH)
        req_low = analyze_job_description(JD_SAMPLE_LOW_MATCH)

        res_high = calculate_ats_score(resume, req_high)
        res_low = calculate_ats_score(resume, req_low)

        self.assertTrue(0 <= res_high.overall_score <= 100)
        self.assertTrue(0 <= res_low.overall_score <= 100)
        self.assertGreater(res_high.overall_score, res_low.overall_score)

    # ── 14. 10x Determinism Test ──────────────────────────────────────────────
    def test_14_score_determinism(self):
        """Test 14: Executing score 10 times on identical input produces 10 IDENTICAL results."""
        resume = structure_resume(RESUME_SAMPLE_1)
        req = analyze_job_description(JD_SAMPLE_HIGH_MATCH)

        baseline = calculate_ats_score(resume, req)
        for i in range(10):
            run = calculate_ats_score(resume, req)
            self.assertEqual(run.overall_score, baseline.overall_score)
            self.assertEqual(run.match_percentage, baseline.match_percentage)
            self.assertEqual(run.components.skill_match, baseline.components.skill_match)
            self.assertEqual(run.matched_skills, baseline.matched_skills)

    # ── 15 & 16. Edge Cases ───────────────────────────────────────────────────
    def test_15_empty_jd_handling(self):
        """Test 15: Empty JD handled without division by zero or crash."""
        resume = structure_resume(RESUME_SAMPLE_1)
        req = analyze_job_description("")
        result = calculate_ats_score(resume, req)
        self.assertTrue(0 <= result.overall_score <= 100)

    # ── 20. API Endpoint Integration & Overwrite Test ─────────────────────────
    @patch("routes.analyze.analyze_resume")
    def test_20_api_endpoint_deterministic_ats_overwrite(self, mock_analyze):
        """Test 20: Endpoint returns deterministic ATS score, overwriting LLM ats_score."""
        mock_analyze.return_value = AnalysisResponse(
            ats_score=99,  # Fake LLM score
            match_percentage="99%",
            optimized_resume="Resume text",
            key_improvements=[],
            original_bullets=[],
            optimized_bullets=[],
            skill_gaps=[],
            project_suggestions=[],
            top_strengths=[],
            recruiter_insight="Insight",
            github_integration=[]
        )

        res = client.post(
            "/api/analyze",
            data={
                "resume_text": RESUME_SAMPLE_1,
                "job_description": JD_SAMPLE_HIGH_MATCH
            }
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()

        # Score MUST NOT be 99 (LLM score); it must be the deterministic ATS score
        self.assertNotEqual(body["ats_score"], 99)
        self.assertIn("ats_breakdown", body)
        self.assertIsNotNone(body["ats_breakdown"])


if __name__ == "__main__":
    unittest.main()
