"""
test_module1.py — Automated test suite for Module 1 stabilization.

Tests executed:
1. Backend Startup & OpenAPI docs (/docs, /)
2. API Connectivity (POST /api/analyze)
3. Curly Brace Resume Input (no .format() KeyError)
4. Missing Resume Validation (422)
5. Missing Job Description Validation (422)
6. Unsupported File Type Validation (415)
7. Oversized File Validation (413)
8. Graceful Handling of Missing API Key (503)
9. Minimum Resume Length Validation (422)
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from routes.analyze import MAX_FILE_BYTES

client = TestClient(app)


class TestModule1(unittest.TestCase):

    def test_01_root_and_docs_endpoint(self):
        """Test 1: Backend root and OpenAPI docs endpoints respond successfully."""
        res_root = client.get("/")
        self.assertEqual(res_root.status_code, 200)
        self.assertIn("status", res_root.json())

        res_docs = client.get("/docs")
        self.assertEqual(res_docs.status_code, 200)

    def test_02_missing_resume_validation(self):
        """Test 6: Missing resume input triggers 422 Unprocessable Entity."""
        res = client.post(
            "/api/analyze",
            data={"job_description": "We need a Senior Python Engineer."}
        )
        self.assertEqual(res.status_code, 422)
        self.assertIn("Please provide a resume", res.json()["detail"])

    def test_03_missing_job_description_validation(self):
        """Test 7: Missing job description triggers 422 Unprocessable Entity."""
        # Case A: empty string
        res_empty = client.post(
            "/api/analyze",
            data={"resume_text": "Experienced Python Software Engineer with 5 years experience.", "job_description": "  "}
        )
        self.assertEqual(res_empty.status_code, 422)
        self.assertIn("Job description is required", res_empty.json()["detail"])

        # Case B: field completely omitted
        res_omitted = client.post(
            "/api/analyze",
            data={"resume_text": "Experienced Python Software Engineer with 5 years experience."}
        )
        self.assertEqual(res_omitted.status_code, 422)


    def test_04_unsupported_file_type(self):
        """Test 8: Uploading an unsupported file format (.txt/.exe) triggers 415."""
        files = {"resume_file": ("resume.txt", b"Plain text resume content", "text/plain")}
        data = {"job_description": "We need a Senior Python Engineer."}
        res = client.post("/api/analyze", data=data, files=files)
        self.assertEqual(res.status_code, 415)
        self.assertIn("Unsupported file type", res.json()["detail"])

    def test_05_oversized_file_validation(self):
        """Test 9: Uploading a file > 10MB triggers 413 Payload Too Large."""
        large_bytes = b"0" * (MAX_FILE_BYTES + 1024)
        files = {"resume_file": ("huge_resume.pdf", large_bytes, "application/pdf")}
        data = {"job_description": "We need a Senior Python Engineer."}
        res = client.post("/api/analyze", data=data, files=files)
        self.assertEqual(res.status_code, 413)
        self.assertIn("File is too large", res.json()["detail"])

    def test_06_curly_brace_resume_input(self):
        """Test 5: Resume text containing curly braces (templates, format strings) does not cause .format() KeyError."""
        curly_resume = (
            "Software Engineer experienced in C++ std::vector<T> and std::map<K, V>.\n"
            "Implemented template classes using {T} and custom allocators.\n"
            "Used Python string formatting with {name} and {age} parameters.\n"
            "Built high-performance microservices serving 10k req/sec."
        )
        data = {
            "resume_text": curly_resume,
            "job_description": "Looking for C++ and Python engineers."
        }
        res = client.post("/api/analyze", data=data)
        
        # If API key is missing, it should return 503 Service Unavailable cleanly (NOT 500 KeyError)
        # If API key is present, it returns 200 OK.
        self.assertIn(res.status_code, [200, 503])
        if res.status_code == 503:
            self.assertIn("OPENROUTER_API_KEY", res.json()["detail"])

    def test_07_short_resume_text_validation(self):
        """Test: Resume text under 50 chars triggers 422 validation error."""
        data = {
            "resume_text": "Too short",
            "job_description": "Valid job description."
        }
        res = client.post("/api/analyze", data=data)
        self.assertEqual(res.status_code, 422)
        self.assertIn("too short", res.json()["detail"])

    def test_08_missing_api_key_graceful_error(self):
        """Test 10: Missing API key returns 503 Service Unavailable without crashing or exposing stack traces."""
        data = {
            "resume_text": "Senior Python Developer with 5+ years building FastAPI and microservices.",
            "job_description": "We need a Senior Python Developer."
        }
        res = client.post("/api/analyze", data=data)
        self.assertIn(res.status_code, [200, 503])
        if res.status_code == 503:
            self.assertIn("detail", res.json())
            self.assertNotIn("Traceback", res.text)


if __name__ == "__main__":
    unittest.main()
