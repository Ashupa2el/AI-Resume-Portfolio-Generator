import os
import unittest
import json
from pathlib import Path
import sys

# Add project directory to path
PROJECT_DIR = r"C:\Users\dhire\.gemini\antigravity\scratch\resume-portfolio-generator"
sys.path.insert(0, PROJECT_DIR)

from main import (
    load_and_clean_resume,
    build_prompt,
    parse_and_validate_json,
    generate_portfolio_html,
    get_mock_portfolio_data
)

class TestResumePortfolioGenerator(unittest.TestCase):

    def setUp(self):
        self.test_dir = PROJECT_DIR

    def test_load_and_clean_resume(self):
        resume_path = os.path.join(self.test_dir, "resume.txt")
        cleaned = load_and_clean_resume(resume_path)
        self.assertTrue(len(cleaned) > 50)
        self.assertNotIn("\n\n\n", cleaned)

    def test_build_prompt(self):
        sample_text = "Jane Doe\nSoftware Engineer\nPython, Docker"
        prompt = build_prompt(sample_text)
        self.assertIn("CRITICAL INSTRUCTIONS", prompt)
        self.assertIn("JSON SCHEMA STRUCTURE REQUIRED", prompt)
        self.assertIn(sample_text, prompt)

    def test_parse_and_validate_json_clean(self):
        sample_json = json.dumps({
            "name": "Jane Doe",
            "headline": "Full Stack Dev",
            "summary": "Building great web apps.",
            "skills": {"Languages": ["Python", "Go"]},
            "education": [{"degree": "B.Tech", "institution": "Tech Univ", "duration": "2021-2025"}],
            "experience": [],
            "projects": [{"title": "API Hub", "description": "Microservices backend", "technologies": ["Python"], "link": ""}],
            "achievements": ["Dean's List 2024"],
            "contact": {"email": "jane@example.com"}
        })
        parsed = parse_and_validate_json(sample_json)
        self.assertEqual(parsed["name"], "Jane Doe")
        self.assertEqual(parsed["skills"]["Languages"], ["Python", "Go"])
        self.assertIsInstance(parsed["contact"], dict)

    def test_parse_and_validate_json_with_code_fences(self):
        fenced_json = "```json\n" + json.dumps({"name": "Code Fence User"}) + "\n```"
        parsed = parse_and_validate_json(fenced_json)
        self.assertEqual(parsed["name"], "Code Fence User")
        self.assertEqual(parsed["projects"], [])

    def test_html_rendering_omits_empty_sections(self):
        minimal_data = {
            "name": "Minimalist Dev",
            "headline": "Specialist",
            "summary": "Minimal bio",
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "achievements": [],
            "contact": {"email": "min@example.com", "phone": "", "location": "", "linkedin": "", "github": "", "website": ""}
        }
        
        # Change working directory temporarily for template loader
        prev_cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            output_file = "test_output.html"
            generate_portfolio_html(minimal_data, "template.html", output_file)
            self.assertTrue(os.path.exists(output_file))
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Minimalist Dev", content)
            self.assertIn("min@example.com", content)
            # Empty sections must NOT render section headers
            self.assertNotIn("Skills & Expertise", content)
            self.assertNotIn("Experience & Internships", content)
            self.assertNotIn("Featured Projects", content)
            self.assertNotIn("Achievements & Certifications", content)
            if os.path.exists(output_file):
                os.remove(output_file)
        finally:
            os.chdir(prev_cwd)


if __name__ == "__main__":
    unittest.main()
