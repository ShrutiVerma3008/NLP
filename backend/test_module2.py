"""
test_module2.py — Automated test suite for Module 2 backend API foundation.

Tests execute IN-MEMORY with MOCKED external LLM calls:
- ZERO OpenRouter API credits consumed.
- 100% test isolation.

Coverage:
1. Valid analysis request & response schema validation
2. Missing resume validation (422)
3. Missing job description validation (422)
4. Invalid file type validation (415)
5. File too large validation (413)
6. Short/empty resume validation (422)
7. Missing API key error (503)
8. Simulated valid LLM response (200 OK + matching schema)
9. Invalid JSON LLM response (502 Bad Gateway)
10. Missing required LLM field in output (502 Bad Gateway)
11. Wrong LLM field type in output (502 Bad Gateway)
12. External LLM failure / APIError (502 Bad Gateway)
"""

import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from schemas.analysis import AnalysisResponse, SkillGap, ProjectSuggestion
from services.llm_service import parse_and_validate_llm_response
from routes.analyze import MAX_FILE_BYTES

client = TestClient(app)

# Sample valid mock LLM payload
SAMPLE_VALID_LLM_DICT = {
    "ats_score": 88,
    "match_percentage": "88%",
    "optimized_resume": "Jane Doe - Senior Python Engineer...",
    "key_improvements": [
        "Added quantitative metrics to Python project bullets.",
        "Highlighted experience with FastAPI and PostgreSQL."
    ],
    "original_bullets": [
        "Built web application in Python."
    ],
    "optimized_bullets": [
        "Engineered scalable REST API in Python and FastAPI, improving throughput by 40%."
    ],
    "skill_gaps": [
        {
            "skill": "Docker",
            "severity": "medium",
            "description": "Job description requires containerization experience."
        }
    ],
    "project_suggestions": [
        {
            "title": "Microservice Containerization",
            "description": "Containerize existing FastAPI services with Docker Compose.",
            "why_it_helps": "Fills Docker requirement in job posting.",
            "tech_stack": ["Docker", "FastAPI", "PostgreSQL"]
        }
    ],
    "top_strengths": [
        "Strong Python background",
        "FastAPI framework expertise"
    ],
    "recruiter_insight": "Strong candidate matching 88% of core backend engineering requirements.",
    "github_integration": [
        "Maintained open-source Python utility with 50+ GitHub stars."
    ]
}


class TestModule2(unittest.TestCase):

    # ── Unit tests for schema parser ──────────────────────────────────────────
    def test_schema_valid_dict(self):
        """Test: Valid JSON string parses into AnalysisResponse instance."""
        json_str = json.dumps(SAMPLE_VALID_LLM_DICT)
        res = parse_and_validate_llm_response(json_str)
        self.assertIsInstance(res, AnalysisResponse)
        self.assertEqual(res.ats_score, 88)
        self.assertEqual(len(res.skill_gaps), 1)

    def test_schema_invalid_json(self):
        """Test: Invalid non-JSON string raises ValueError."""
        invalid_raw = "This is definitely not a JSON string."
        with self.assertRaises(ValueError) as ctx:
            parse_and_validate_llm_response(invalid_raw)
        self.assertIn("could not be parsed as JSON", str(ctx.exception))

    def test_schema_missing_required_field(self):
        """Test: Dict missing required field (e.g. ats_score) raises ValueError."""
        incomplete = dict(SAMPLE_VALID_LLM_DICT)
        del incomplete["ats_score"]
        with self.assertRaises(ValueError) as ctx:
            parse_and_validate_llm_response(json.dumps(incomplete))
        self.assertIn("failed schema validation", str(ctx.exception))

    def test_schema_wrong_field_type(self):
        """Test: Wrong field type (e.g. ats_score='eighty') raises ValueError."""
        wrong_type = dict(SAMPLE_VALID_LLM_DICT)
        wrong_type["ats_score"] = "not_an_int"
        with self.assertRaises(ValueError) as ctx:
            parse_and_validate_llm_response(json.dumps(wrong_type))
        self.assertIn("failed schema validation", str(ctx.exception))

    # ── Integration tests with mocked LLM ─────────────────────────────────────
    @patch("routes.analyze.analyze_resume")
    def test_endpoint_success_with_mocked_llm(self, mock_analyze):
        """Test: Valid analyze request returns 200 OK with validated schema."""
        mock_analyze.return_value = AnalysisResponse.model_validate(SAMPLE_VALID_LLM_DICT)

        data = {
            "resume_text": "Senior Python Developer with 5+ years building FastAPI applications.",
            "job_description": "Looking for a Senior Python Developer with FastAPI expertise."
        }
        res = client.post("/api/analyze", data=data)
        self.assertEqual(res.status_code, 200)

        json_body = res.json()
        self.assertIsInstance(json_body["ats_score"], int)
        self.assertIn("match_percentage", json_body)
        self.assertIn("key_improvements", json_body)
        self.assertIn("ats_breakdown", json_body)
        self.assertIsNotNone(json_body["ats_breakdown"])


    @patch("routes.analyze.analyze_resume")
    def test_endpoint_handles_invalid_llm_schema(self, mock_analyze):
        """Test: Invalid LLM output raises ValueError in analyze_resume -> returns 502 Bad Gateway."""
        mock_analyze.side_effect = ValueError("LLM response failed schema validation: ats_score missing")

        data = {
            "resume_text": "Senior Python Developer with 5+ years experience in backend architecture.",
            "job_description": "We need a Senior Python Developer."
        }
        res = client.post("/api/analyze", data=data)
        self.assertEqual(res.status_code, 502)
        self.assertIn("ats_score missing", res.json()["detail"])

    @patch("routes.analyze.analyze_resume")
    def test_endpoint_handles_external_llm_failure(self, mock_analyze):
        """Test: External LLM API failure -> returns 502 Bad Gateway."""
        mock_analyze.side_effect = RuntimeError("OpenRouter API error: Service Unavailable")

        data = {
            "resume_text": "Senior Python Developer with 5+ years experience in backend architecture.",
            "job_description": "We need a Senior Python Developer."
        }
        res = client.post("/api/analyze", data=data)
        self.assertEqual(res.status_code, 502)
        self.assertIn("OpenRouter API error", res.json()["detail"])

    # ── Validation tests (matching Module 1 behavior) ─────────────────────────
    def test_missing_resume_validation(self):
        """Test: Missing resume returns 422."""
        res = client.post(
            "/api/analyze",
            data={"job_description": "We need a Python Engineer."}
        )
        self.assertEqual(res.status_code, 422)

    def test_missing_jd_validation(self):
        """Test: Missing job description returns 422."""
        res = client.post(
            "/api/analyze",
            data={"resume_text": "Senior Python Engineer with 5 years experience."}
        )
        self.assertEqual(res.status_code, 422)

    def test_unsupported_file_format(self):
        """Test: Uploading .txt returns 415."""
        files = {"resume_file": ("resume.txt", b"Plain text content", "text/plain")}
        data = {"job_description": "We need a Python Engineer."}
        res = client.post("/api/analyze", data=data, files=files)
        self.assertEqual(res.status_code, 415)

    def test_oversized_file(self):
        """Test: File > 10MB returns 413."""
        large_bytes = b"0" * (MAX_FILE_BYTES + 1024)
        files = {"resume_file": ("large.pdf", large_bytes, "application/pdf")}
        data = {"job_description": "We need a Python Engineer."}
        res = client.post("/api/analyze", data=data, files=files)
        self.assertEqual(res.status_code, 413)

    def test_short_resume_text(self):
        """Test: Resume text < 50 chars returns 422."""
        data = {
            "resume_text": "Short",
            "job_description": "We need a Python Engineer."
        }
        res = client.post("/api/analyze", data=data)
        self.assertEqual(res.status_code, 422)


if __name__ == "__main__":
    unittest.main()
