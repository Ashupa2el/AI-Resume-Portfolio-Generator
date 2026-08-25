import os
import sys
import unittest

PROJECT_DIR = r"C:\Users\dhire\.gemini\antigravity\scratch\resume-portfolio-generator"
sys.path.insert(0, PROJECT_DIR)

from app import app

class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Portfolio Studio", response.data)

    def test_default_content_route(self):
        response = self.app.get("/api/default-content")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("resume", data)

    def test_generate_from_resume(self):
        payload = {
            "content": "Ashutosh Patel\nSoftware Developer\nPython, Docker\nGPA: 3.9",
            "theme": "cyber",
            "api_key": ""
        }
        response = self.app.post("/api/generate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["theme"], "cyber")

    def test_preview_and_download(self):
        preview_res = self.app.get("/api/preview")
        self.assertEqual(preview_res.status_code, 200)
        self.assertIn(b"<!DOCTYPE html>", preview_res.data)

        download_res = self.app.get("/api/download")
        self.assertEqual(download_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
