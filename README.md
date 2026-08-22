# AI-Assisted Resume & Requirements Portfolio Generator

An AI-powered application and interactive Web Studio that automatically builds modern, responsive portfolio websites (`portfolio.html`) from:
1. Plain-text resume files (`resume.txt`)
2. Python dependency files (`requirements.txt`) / tech stacks

---

## 1. Project Overview

- **Interactive Web Studio**: Real-time browser dashboard with multi-theme switcher, live iframe preview, and instant download.
- **CLI Automation**: Run via simple command-line script (`python main.py`).
- **AI Engine**: Google Gemini API (`gemini-2.5-flash` or `gemini-1.5-flash`) with structured schema prompting.
- **Dynamic Theming**:
  - 🌌 **Modern Dark** (Indigo & Slate Glassmorphism)
  - ☀️ **Clean Light** (Minimalist Executive)
  - 🔮 **Cyber Neon** (Cyan & Pink Futuristic)
  - 🌿 **Emerald Pro** (Modern Forest Tech)
- **Tech Stack**: Python, Flask, Jinja2, Google GenAI SDK, HTML5, CSS3.

---

## 2. Project Directory Structure

```
resume-portfolio-generator/
├── app.py               # Interactive Flask Web Studio application (live preview & downloads)
├── main.py              # CLI Python script (reads resume.txt, calls Gemini, generates portfolio.html)
├── resume.txt           # Input plain text resume file
├── requirements.txt     # Python dependencies (and used as input for requirements mode)
├── template.html        # Jinja2 HTML5 template with multi-theme and conditional section rendering
├── style.css            # Responsive CSS stylesheet supporting all 4 visual themes
├── web_templates/       # Web studio UI templates
│   └── index.html       # Studio dashboard (split-screen editor, theme picker, live preview)
├── web_static/          # Web studio static assets
│   └── dashboard.css    # Modern studio dashboard styling
├── test_app.py          # Automated CLI & prompt unit tests
├── test_webapp.py       # Automated Web Application endpoint tests
├── .env.example         # Environment variable template for GEMINI_API_KEY
├── .gitignore           # Git ignore rules for API keys, cache, and virtual environments
├── portfolio.html       # Standalone generated portfolio webpage
└── README.md            # Complete documentation and setup guide
```

---

## 3. Quick Start & Installation

### Step 1: Clone or Navigate to the Folder
```bash
cd resume-portfolio-generator
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: (Optional) Configure Gemini API Key
Create a `.env` file from `.env.example`:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*(Note: If no API key is provided, the application automatically runs in demo mode with sample data so you can test all features offline.)*

---

## 4. How to Use

### Option A: Launch the Interactive Web Studio (Recommended)
Run the Flask web server:
```bash
python app.py
```
Open your browser at **`http://127.0.0.1:5000`**:
- **Switch between Modes**: Select `📄 Resume Text` or `📦 requirements.txt`.
- **Drag & Drop**: Drop your `resume.txt` or `requirements.txt` into the upload zone.
- **Select Themes**: Switch between Dark, Light, Cyber Neon, and Emerald Pro.
- **Real-Time Preview**: Inspect your portfolio in desktop or mobile viewport.
- **Download**: Click **Download portfolio.html** to export a standalone, self-contained portfolio webpage.

---

### Option B: Run via Command Line (CLI)
```bash
python main.py
```
This reads `resume.txt` and outputs `portfolio.html` directly in the project directory.

---

## 5. Automated Testing

Run the full automated test suite:
```bash
# Test CLI application, JSON schema parsing, and anti-hallucination prompts
python test_app.py

# Test Web Studio endpoints, requirements-inference engine, and live routes
python test_webapp.py
```

---

## 6. Responsible AI & Anti-Hallucination Guarantees

- **Strict Grounding**: The Gemini prompt strictly limits extraction to facts directly stated in the input. It forbids fabricating or exaggerating credentials.
- **Deterministic Temperature**: Uses `temperature=0.2` for factual extraction.
- **Data Privacy**: All processing runs locally on your machine. API keys in `.env` are protected by `.gitignore` and never committed.
