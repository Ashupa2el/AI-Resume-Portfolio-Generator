"""
AI-Assisted Resume Portfolio Generator
======================================
Reads resume content from 'resume.txt', prompts Google Gemini API for structured JSON,
and dynamically generates a modern, responsive 'portfolio.html' using Jinja2 templates.

AIML GLA Bootcamp '26 | Student Project
"""

import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# Try importing the official Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# -----------------------------------------------------------------------------
# 1. FILE & RESUME CLEANING
# -----------------------------------------------------------------------------
def load_and_clean_resume(file_path: str = "resume.txt") -> str:
    """
    Reads resume content from a text file, validates existence and minimum length,
    and removes unnecessary spaces and excess blank lines.
    """
    path = Path(file_path)
    
    if not path.exists():
        print(f"\n[ERROR] Resume file '{file_path}' not found.")
        print("-> Please create 'resume.txt' in the project directory with your resume content.\n")
        sys.exit(1)
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"\n[ERROR] Failed to read '{file_path}': {e}\n")
        sys.exit(1)

    # Basic length validation
    cleaned = content.strip()
    if not cleaned:
        print(f"\n[ERROR] '{file_path}' is completely empty.")
        print("-> Please add your resume text to 'resume.txt'.\n")
        sys.exit(1)

    # Check for minimal content (> 50 characters or > 15 words)
    words = cleaned.split()
    if len(cleaned) < 50 or len(words) < 15:
        print(f"\n[WARNING] '{file_path}' seems too short ({len(words)} words).")
        print("-> A complete resume will produce a much richer portfolio webpage.\n")

    # Clean redundant whitespaces and collapse multiple blank lines
    # Replace 3 or more consecutive newlines with 2 newlines
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    # Remove trailing spaces on lines
    cleaned = '\n'.join(line.strip() for line in cleaned.splitlines())

    return cleaned


# -----------------------------------------------------------------------------
# 2. PROMPT DESIGN & GEMINI SCHEMA
# -----------------------------------------------------------------------------
def build_prompt(resume_text: str) -> str:
    """
    Constructs a controlled, anti-hallucination prompt instructing Gemini
    to extract structured portfolio data adhering strictly to the JSON schema.
    """
    return f"""You are an expert AI Resume and Portfolio Specialist.
Your task is to analyze the provided resume text and extract the information into a strict, well-structured JSON format suitable for a personal portfolio website.

CRITICAL INSTRUCTIONS & RESPONSIBLE AI RULES:
1. ONLY use facts and information present in the resume text. DO NOT fabricate, guess, or exaggerate any details, credentials, companies, or projects.
2. If any section or field is missing from the resume, provide an empty string "" or empty list [] as appropriate.
3. Return VALID JSON ONLY. Do not wrap in explanation text or markdown conversational commentary.

JSON SCHEMA STRUCTURE REQUIRED:
{{
  "name": "Full Name from resume",
  "headline": "Short professional headline / role tagline (e.g. AI & ML Undergraduate | Software Developer)",
  "summary": "Concise 2-4 sentence professional summary / about me",
  "skills": {{
      "Programming Languages": ["Python", "JavaScript"],
      "Frameworks & Tools": ["FastAPI", "Docker"],
      "Specializations & Concepts": ["Machine Learning", "Data Structures"]
  }},
  "education": [
    {{
      "institution": "University / College Name",
      "degree": "Degree / Field of Study",
      "duration": "Year or Duration (e.g. 2022 - 2026)",
      "details": "GPA / Percentage or notable honors (if mentioned, otherwise empty)"
    }}
  ],
  "experience": [
    {{
      "role": "Job / Internship Title",
      "company": "Company / Organization Name",
      "duration": "Dates (e.g. June 2025 - August 2025)",
      "responsibilities": [
        "Key achievement or responsibility bullet point 1",
        "Key achievement or responsibility bullet point 2"
      ]
    }}
  ],
  "projects": [
    {{
      "title": "Project Title",
      "description": "Clear 1-2 sentence description of the project and impact",
      "technologies": ["Python", "Gemini API", "Jinja2"],
      "link": "URL to GitHub repository or live demo (or empty string if not available)"
    }}
  ],
  "achievements": [
    "Award, certification, or notable achievement 1",
    "Certification or achievement 2"
  ],
  "contact": {{
    "email": "email@example.com",
    "phone": "Phone number or empty",
    "location": "City, State / Country",
    "linkedin": "Full URL or profile handle",
    "github": "Full URL or profile handle",
    "website": "Personal portfolio or blog URL (or empty)"
  }}
}}

RESUME TEXT:
----------------------------------------
{resume_text}
----------------------------------------
"""


# -----------------------------------------------------------------------------
# 3. GEMINI API CALL WITH ERROR HANDLING
# -----------------------------------------------------------------------------
def call_gemini_api(prompt: str, api_key: str, model_name: str = "gemini-3.6-flash") -> str:
    """
    Sends the prompt to Google Gemini API using the official google-genai SDK.
    Handles API errors, invalid keys, and network issues gracefully.
    """
    if not GENAI_AVAILABLE:
        raise RuntimeError("The 'google-genai' package is not installed. Run 'pip install google-genai'.")

    try:
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,  # Low temperature for factual precision
            )
        )
        
        if not response.text:
            raise ValueError("Gemini returned an empty response.")
            
        return response.text
        
    except Exception as e:
        print(f"\n[API ERROR] Gemini API call failed: {e}")
        raise


# -----------------------------------------------------------------------------
# 4. JSON PARSING & DATA NORMALIZATION
# -----------------------------------------------------------------------------
def parse_and_validate_json(raw_response: str) -> dict:
    """
    Parses the JSON response from Gemini, handles markdown code fences if present,
    and normalizes all expected keys to prevent template rendering errors.
    """
    # Clean potential markdown wrapping (e.g. ```json ... ```)
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as err:
        print(f"[ERROR] Failed to decode JSON from Gemini output: {err}")
        print("Raw response snippet:")
        print(cleaned[:300])
        raise

    # Safe defaults to prevent template KeyErrors
    default_schema = {
        "name": "Portfolio Owner",
        "headline": "",
        "summary": "",
        "skills": {},
        "education": [],
        "experience": [],
        "projects": [],
        "achievements": [],
        "contact": {
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "github": "",
            "website": ""
        }
    }

    for key, default_val in default_schema.items():
        if key not in data or data[key] is None:
            data[key] = default_val

    # Ensure contact sub-keys are clean
    if not isinstance(data.get("contact"), dict):
        data["contact"] = default_schema["contact"]

    return data


# -----------------------------------------------------------------------------
# 5. HTML GENERATION (JINJA2)
# -----------------------------------------------------------------------------
def generate_portfolio_html(data: dict, template_file: str = "template.html", output_file: str = "portfolio.html") -> str:
    """
    Renders data into template.html using Jinja2 and writes to portfolio.html
    with inline CSS and timestamp for standalone portability.
    """
    from datetime import datetime
    env = Environment(loader=FileSystemLoader(searchpath="."))
    
    try:
        template = env.get_template(template_file)
    except Exception as e:
        print(f"[ERROR] Could not load template '{template_file}': {e}")
        sys.exit(1)

    css_content = ""
    style_path = Path("style.css")
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            css_content = f.read()

    generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    theme = data.get("theme", "dark")

    html_content = template.render(**data, inline_css=css_content, theme=theme, generated_at=generated_at)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return os.path.abspath(output_file)


# -----------------------------------------------------------------------------
# 6. MOCK DATA FALLBACK (FOR OFFLINE TESTING WITHOUT API KEY)
# -----------------------------------------------------------------------------
def get_mock_portfolio_data() -> dict:
    """
    Provides mock structured data for offline verification when an API key is not yet set.
    """
    return {
        "name": "Ashutosh Patel",
        "headline": "AI & Software Engineering Undergraduate",
        "summary": "Motivated Computer Science undergraduate specializing in Artificial Intelligence and Full Stack Software Engineering. Proficient in Python, Machine Learning workflows, and Generative AI prompt design.",
        "skills": {
            "Programming Languages": ["Python", "JavaScript", "TypeScript", "SQL", "HTML5", "CSS3"],
            "Frameworks & Libraries": ["FastAPI", "Flask", "Jinja2", "Pandas", "NumPy", "Scikit-Learn"],
            "AI & GenAI": ["Google Gemini API", "Prompt Engineering", "RAG", "LLM Integration"],
            "Developer Tools": ["Git", "GitHub", "Docker", "VS Code", "Postman"]
        },
        "education": [
            {
                "institution": "University of Technology",
                "degree": "B.S. in Computer Science & Artificial Intelligence",
                "duration": "2022 - 2026",
                "details": "GPA: 3.85 / 4.0"
            }
        ],
        "experience": [
            {
                "role": "AI Engineering Intern",
                "company": "NexaTech Innovations",
                "duration": "June 2025 - August 2025",
                "responsibilities": [
                    "Developed and deployed an automated document extraction pipeline using Python and Gemini API.",
                    "Designed and evaluated structured JSON prompting strategies to maintain 99% schema accuracy."
                ]
            }
        ],
        "projects": [
            {
                "title": "SmartResume - AI Portfolio Generator",
                "description": "Automated pipeline that parses unstructured resume text, prompts Gemini for structured JSON generation, and renders an interactive portfolio.",
                "technologies": ["Python", "Gemini API", "Jinja2", "HTML5", "CSS3"],
                "link": "https://ashupa2el.github.io/Portfolio/"
            },
            {
                "title": "MediPredict - Health Analytics Platform",
                "description": "Explainable machine learning application for clinical risk estimation with interactive visual dashboards.",
                "technologies": ["Python", "Scikit-Learn", "Streamlit", "Pandas"],
                "link": "https://e-sim-dashboard.vercel.app/"
            }
        ],
        "achievements": [
            "1st Place Winner - University Annual Hackathon 2025",
            "Google Cloud Certified: Generative AI Fundamentals",
            "300+ algorithm challenges solved on LeetCode"
        ],
        "contact": {
            "email": "patelashutosh661@gmail.com",
            "phone": "+1 (555) 019-2834",
            "location": "San Francisco, CA",
            "linkedin": "https://ashupa2el.github.io/Portfolio/",
            "github": "https://github.com/Ashupa2el",
            "website": "https://ashutosh.dev"
        }
    }


# -----------------------------------------------------------------------------
# MAIN APPLICATION CONTROLLER
# -----------------------------------------------------------------------------
def main():
    print("=" * 65)
    print("   AI-ASSISTED RESUME PORTFOLIO GENERATOR (GLA BOOTCAMP '26)")
    print("=" * 65)

    # 1. Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    # 2. Read and clean resume
    print("\n[1/4] Reading and cleaning resume text from 'resume.txt'...")
    resume_text = load_and_clean_resume("resume.txt")
    print(f"      -> Successfully loaded {len(resume_text.split())} words.")

    # 3. Check for API key & call Gemini or offer mock mode
    portfolio_data = None
    if not api_key or api_key.strip() == "" or api_key == "your_gemini_api_key_here":
        print("\n[NOTE] No GEMINI_API_KEY found in '.env'.")
        print("       To use live AI generation:")
        print("       1. Get your free key at https://aistudio.google.com/")
        print("       2. Add it to a '.env' file: GEMINI_API_KEY=your_actual_key\n")
        print("       Running with sample structured portfolio data for local testing...")
        portfolio_data = get_mock_portfolio_data()
    else:
        print(f"\n[2/4] Sending structured prompt to Gemini ({model_name})...")
        prompt = build_prompt(resume_text)
        try:
            raw_response = call_gemini_api(prompt, api_key=api_key, model_name=model_name)
            print("      -> Gemini response received successfully.")
            
            print("\n[3/4] Parsing and validating JSON response...")
            portfolio_data = parse_and_validate_json(raw_response)
            print(f"      -> JSON validated. Name extracted: {portfolio_data.get('name')}")
            
        except Exception as e:
            print(f"\n[ERROR] AI extraction encountered an issue: {e}")
            print("       Falling back to offline preview data so you can inspect the template...")
            portfolio_data = get_mock_portfolio_data()

    # 4. Generate HTML
    print("\n[4/4] Generating 'portfolio.html' using template.html & style.css...")
    output_path = generate_portfolio_html(portfolio_data, "template.html", "portfolio.html")
    
    print("\n" + "=" * 65)
    print("   PORTFOLIO WEBPAGE GENERATED SUCCESSFULLY!")
    print("=" * 65)
    print(f"\nOutput File : {output_path}")
    print("To view     : Open 'portfolio.html' in any web browser.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
