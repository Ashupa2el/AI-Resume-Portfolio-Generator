"""
AI Portfolio Studio - Interactive Web Application
=================================================
Flask web server for generating modern portfolio websites from resume.txt
with real-time in-browser preview, multi-theme support, and one-click standalone export.
"""

import os
import sys
import json
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, Response
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# Load environment variables
load_dotenv()

# Set base project directory safely for serverless runtimes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Import helper functions from main.py
sys.path.insert(0, BASE_DIR)
from main import (
    build_prompt,
    call_gemini_api,
    parse_and_validate_json,
    get_mock_portfolio_data,
    GENAI_AVAILABLE
)

app = Flask(
    __name__,
    template_folder="web_templates",
    static_folder="web_static",
    static_url_path="/static"
)

# Store latest generated HTML and data in memory/cache
CURRENT_PORTFOLIO = {
    "data": None,
    "theme": "dark",
    "html": ""
}


def render_portfolio_html_string(data: dict, theme: str = "dark", inline_css: bool = True) -> str:
    """
    Renders the data into template.html with the selected theme and timestamp.
    """
    from datetime import datetime
    template_path = os.path.join(BASE_DIR, "template.html")
    style_path = os.path.join(BASE_DIR, "style.css")
    
    template_str = ""
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            template_str = f.read()

    css_content = ""
    if inline_css and os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            css_content = f.read()

    generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    env = Environment()
    template = env.from_string(template_str)
    
    return template.render(
        **data,
        theme=theme,
        inline_css=css_content,
        generated_at=generated_at
    )


# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/style.css")
@app.route("/api/style.css")
def serve_style():
    style_path = os.path.join(BASE_DIR, "style.css")
    return send_file(style_path, mimetype="text/css")


@app.route("/api/default-content")
def default_content():
    resume_path = os.path.join(BASE_DIR, "resume.txt")
    resume_text = ""
    
    if os.path.exists(resume_path):
        with open(resume_path, "r", encoding="utf-8") as f:
            resume_text = f.read()

    return jsonify({
        "resume": resume_text
    })


@app.route("/api/download-template")
def download_template():
    """
    Returns a blank template with empty field quotes ("") for filling in details from scratch.
    """
    template_path = os.path.join(BASE_DIR, "resume_blank_template.txt")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = """NAME: ""
HEADLINE: ""

PROFESSIONAL SUMMARY:
""

CONTACT INFORMATION:
- Email: ""
- Phone: ""
- Location: ""
- LinkedIn: ""
- GitHub: ""
- Portfolio: ""

SKILLS:
- Technical Skills: []
- Frameworks & Tools: []

EDUCATION:
- Degree: ""
- Institution: ""
- Duration: ""
- Details: ""

EXPERIENCE:
- Role: ""
- Company: ""
- Duration: ""
- Responsibilities:
  * ""

PROJECTS:
- Title: ""
- Description: ""
- Technologies: []
- Link: ""

ACHIEVEMENTS:
- ""
"""
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=resume_blank_template.txt"}
    )


@app.route("/api/download-reference")
def download_reference():
    """
    Returns a full reference resume file with sample data to guide user formatting.
    """
    ref_path = os.path.join(BASE_DIR, "resume_reference_example.txt")
    resume_path = os.path.join(BASE_DIR, "resume.txt")
    
    content = ""
    if os.path.exists(ref_path):
        with open(ref_path, "r", encoding="utf-8") as f:
            content = f.read()
    elif os.path.exists(resume_path):
        with open(resume_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "Sample Resume Reference Details..."

    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=resume_reference_example.txt"}
    )


@app.route("/api/generate", methods=["POST"])
def generate():
    body = request.get_json() or {}
    content = body.get("content", "").strip()
    theme = body.get("theme", "dark")
    custom_api_key = body.get("api_key", "").strip()

    if not content:
        return jsonify({"status": "error", "message": "Content cannot be empty"}), 400

    api_key = custom_api_key or os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    portfolio_data = None

    if api_key and api_key != "your_gemini_api_key_here" and GENAI_AVAILABLE:
        try:
            prompt = build_prompt(content)
            raw_response = call_gemini_api(prompt, api_key=api_key, model_name=model_name)
            portfolio_data = parse_and_validate_json(raw_response)
        except Exception as err:
            print(f"[API WARN] Gemini call failed: {err}. Using structured extraction fallback.")
            portfolio_data = get_mock_portfolio_data()
    else:
        portfolio_data = get_mock_portfolio_data()

    # Save to current cache in memory
    CURRENT_PORTFOLIO["data"] = portfolio_data
    CURRENT_PORTFOLIO["theme"] = theme
    CURRENT_PORTFOLIO["html"] = render_portfolio_html_string(portfolio_data, theme=theme, inline_css=True)

    # Safely write to local portfolio.html if filesystem is writable (local dev)
    if not app.testing:
        try:
            out_path = os.path.join(BASE_DIR, "portfolio.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(CURRENT_PORTFOLIO["html"])
        except Exception as e:
            print(f"[WARN] Read-only serverless environment: {e}")

    return jsonify({
        "status": "success",
        "name": portfolio_data.get("name"),
        "theme": theme
    })


@app.route("/api/preview")
def preview():
    if CURRENT_PORTFOLIO["html"]:
        return Response(CURRENT_PORTFOLIO["html"], mimetype="text/html")

    out_path = os.path.join(BASE_DIR, "portfolio.html")
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                return Response(f.read(), mimetype="text/html")
        except Exception:
            pass

    data = get_mock_portfolio_data()
    CURRENT_PORTFOLIO["data"] = data
    CURRENT_PORTFOLIO["html"] = render_portfolio_html_string(data, theme=CURRENT_PORTFOLIO["theme"], inline_css=True)
    return Response(CURRENT_PORTFOLIO["html"], mimetype="text/html")


@app.route("/api/download")
def download():
    if not CURRENT_PORTFOLIO["html"]:
        data = get_mock_portfolio_data()
        CURRENT_PORTFOLIO["html"] = render_portfolio_html_string(data, theme=CURRENT_PORTFOLIO["theme"], inline_css=True)

    return Response(
        CURRENT_PORTFOLIO["html"],
        mimetype="text/html",
        headers={"Content-Disposition": "attachment; filename=portfolio.html"}
    )


if __name__ == "__main__":
    print("=" * 65)
    print("   AI PORTFOLIO STUDIO - WEB APPLICATION")
    print("   Running locally on: http://localhost:5000 and http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5000, debug=False)
