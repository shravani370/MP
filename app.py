from flask import Flask, redirect, request, render_template, session, url_for, flash
import requests
import sqlite3
import os
import tempfile
from dotenv import load_dotenv
from utils.ai_engine import generate_question, evaluate_answer
from PyPDF2 import PdfReader
from docx import Document
from functools import wraps
import json

# ================= ENV =================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_key")

# ── Enumerate filter for Jinja2 (used by screening templates) ──
app.jinja_env.filters['enumerate'] = enumerate

# ================= DB =================
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)
    
    # Create screening_results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screening_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        role TEXT,
        mcq_score INTEGER,
        code_score INTEGER,
        passed INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create saved_jobs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        job_id TEXT,
        title TEXT,
        company TEXT,
        location TEXT,
        url TEXT,
        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(email, job_id)
    )
    """)
    
    # Ensure saved_jobs table has email column (migration for existing databases)
    try:
        cursor.execute("SELECT email FROM saved_jobs LIMIT 1")
    except sqlite3.OperationalError:
        print("Migration: Adding email column to saved_jobs if missing...")
        try:
            cursor.execute("ALTER TABLE saved_jobs ADD COLUMN email TEXT")
        except:
            pass  # Column might already exist
    
    # Create cover_letters table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cover_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        name TEXT,
        role TEXT,
        company TEXT,
        job_desc TEXT,
        resume_text TEXT,
        letter TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

init_db()

# ================= SCREENING BLUEPRINT =================
from screening.screening_routes import screening_bp
app.register_blueprint(screening_bp)

# ================= LOGIN REQUIRED =================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect("/google-login")
        return f(*args, **kwargs)
    return wrapper

# ================= GOOGLE AUTH =================
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:5000/callback")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

@app.route("/google-login")
def google_login():
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid email profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Login failed ❌"
    try:
        token = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        ).json()

        access_token = token.get("access_token")
        user_info = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        name = user_info.get("name")
        email = user_info.get("email")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (name,email,password) VALUES (?,?,?)",
                (name, email, "google_auth")
            )
            conn.commit()
        conn.close()

        session["user"] = name
        session["email"] = email
        return redirect("/")

    except Exception as e:
        return f"Google Login Error: {e}"

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html", user=session.get("user"))

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("google_login"))
    return render_template("dashboard.html", user=session.get("user"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= LOGIN / SIGNUP / PROFILE =================
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("google_login"))
    return render_template("profile.html")

# ================= INTERVIEW =================
@app.route("/start")
def start():
    if "user" not in session:
        return redirect(url_for("google_login"))

    raw_mode = request.args.get("mode", "")
    mode = raw_mode.strip().lower()
    if mode != "video":
        mode = "chat"

    topic = request.args.get("topic", "Machine Learning")
    role = request.args.get("role", topic)
    first_q = generate_question(role)

    # Preserve auth session, clear interview state
    current_user = session.get("user")
    current_email = session.get("email")
    session.clear()
    session["user"] = current_user
    session["email"] = current_email

    session["topic"] = role
    session["mode"] = mode
    session["question"] = first_q
    session["count"] = 0
    session["messages"] = [{"role": "ai", "text": first_q, "type": "question"}]
    session["asked_questions"] = [first_q]
    session["answers"] = []
    session["results"] = []

    if mode == "video":
        return render_template("video.html", question=first_q)
    return render_template("interview.html", messages=session["messages"])


@app.route("/interview", methods=["GET", "POST"])
def interview():
    """Handle interview page and form submission"""
    if request.method == "POST":
        return submit()
    if "user" not in session:
        return redirect(url_for("google_login"))
    messages = session.get("messages", [])
    if not messages:
        return redirect(url_for("start"))
    return render_template("interview.html", messages=messages)

@app.route("/submit", methods=["POST"])
def submit():
    answer = request.form.get("answer", "").strip()
    topic = session.get("topic")
    current_q = session.get("question")
    count = session.get("count", 0)
    mode = (session.get("mode") or "").strip().lower()
    if mode != "video":
        mode = "chat"

    messages = session.get("messages", [])
    asked = session.get("asked_questions", [])

    if not answer:
        if mode == "video":
            return render_template("video.html", question=current_q)
        return render_template("interview.html", messages=messages)

    # ── 1. Append candidate's answer ──
    messages.append({"role": "user", "text": answer})

    # ── 2. Initialise storage if missing ──
    if "answers" not in session:
        session["answers"] = []
    if "results" not in session:
        session["results"] = []

    session["answers"].append({"question": current_q, "answer": answer})

    # ── 3. Evaluate answer → get natural feedback ──
    result = evaluate_answer(current_q, answer)

    if isinstance(result, dict):
        session["results"].append(result)
        feedback_text = result.get("feedback", "").strip()
        score = result.get("score", 5)
    else:
        fallback_result = {
            "score": 5,
            "feedback": "Got it, thanks for that.",
            "strength": "Answer provided",
            "area_to_improve": "Add more specific examples"
        }
        session["results"].append(fallback_result)
        feedback_text = fallback_result["feedback"]
        score = 5

    # ── 4. Interviewer reacts to the answer (feedback bubble) ──
    if feedback_text:
        messages.append({
            "role": "ai",
            "text": feedback_text,
            "type": "feedback"
        })

    count += 1
    session["count"] = count

    # ── 5. If interview is done, go to results ──
    if count >= 5:
        session["messages"] = messages
        session.modified = True
        return render_template(
            "result.html",
            answers=session["answers"],
            results=session["results"]
        )

    # ── 6. Generate the next question ──
    next_q = generate_question(
        topic,
        previous_answer=answer,
        history=messages,
        asked_questions=asked
    )

    # Deduplicate
    retry = 0
    while next_q in asked and retry < 3:
        next_q = generate_question(topic, previous_answer=answer, history=messages, asked_questions=asked)
        retry += 1

    if next_q in asked:
        next_q = f"What's been the most challenging aspect of working with {topic} for you?"

    # ── 7. Append the next question ──
    messages.append({
        "role": "ai",
        "text": next_q,
        "type": "question"
    })
    asked.append(next_q)

    session["messages"] = messages
    session["asked_questions"] = asked
    session["question"] = next_q
    session.modified = True

    if mode == "video":
        return render_template("video.html", question=next_q)
    return render_template("interview.html", messages=messages)

# ================= RESUME SUITE PAGE =================
@app.route("/resume_suite")
def resume_suite():
    if "user" not in session:
        return redirect(url_for("google_login"))
    # Redirect to template selection first
    return redirect(url_for("resume_templates"))

# ================= RESUME TEMPLATES =================
RESUME_TEMPLATES = {
    "classic": {
        "name": "Classic",
        "description": "Traditional, clean design. Perfect for formal industries.",
        "icon": "📄"
    },
    "modern": {
        "name": "Modern",
        "description": "Sleek and contemporary. Great for tech and creative roles.",
        "icon": "✨"
    },
    "professional": {
        "name": "Professional",
        "description": "Corporate style. Ideal for executive and business roles.",
        "icon": "💼"
    },
    "compact": {
        "name": "Compact",
        "description": "Space-efficient design. Fit more content on one page.",
        "icon": "📋"
    },
    "creative": {
        "name": "Creative",
        "description": "Colorful and bold. Perfect for designers and creatives.",
        "icon": "🎨"
    }
}

@app.route("/resume_templates")
def resume_templates():
    """Show available resume templates"""
    if "user" not in session:
        return redirect(url_for("google_login"))
    return render_template("resume_templates.html", templates=RESUME_TEMPLATES)

# ================= RESUME BUILDER =================
@app.route("/resume", methods=["GET", "POST"])
def resume():
    template = request.args.get("template", "classic")
    
    if template not in RESUME_TEMPLATES:
        template = "classic"
    
    if request.method == "POST":
        skills = [s.strip() for s in request.form.getlist("skills[]") if s.strip()]
        experience = [e.strip() for e in request.form.getlist("experience[]") if e.strip()]

        data = {
            "name": request.form.get("name", "").strip(),
            "role": request.form.get("role", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "email": request.form.get("email", "").strip(),
            "address": request.form.get("address", "").strip(),
            "about": request.form.get("about", "").strip(),
            "education": request.form.get("education", "").strip(),
            "experience": experience,
            "skills": skills,
            "template": template
        }

        if not data["name"] or not data["email"]:
            return render_template("resume.html", data=data, error="Name & Email required ❌", template=template, template_name=RESUME_TEMPLATES[template]["name"])

        return render_template("resume.html", data=data, success="Resume Generated ✅", template=template, template_name=RESUME_TEMPLATES[template]["name"])

    return render_template("resume.html", data={"skills": [], "experience": [], "template": template}, template=template, template_name=RESUME_TEMPLATES[template]["name"])

# ================= ANALYZER =================
@app.route("/analyze", methods=["POST"])
def analyze():
    resume_text = request.form.get("resume", "").strip()

    if not resume_text:
        return render_template("resume.html", result="❌ No resume content")

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3:latest",
                "prompt": f"""
Analyze this resume and provide:
1. ATS Score
2. Strengths
3. Weaknesses
4. Improvements

Resume:
{resume_text}
""",
                "stream": False
            },
            timeout=60
        )
        result = response.json().get("response", "No response")
    except Exception as e:
        result = f"⚠️ AI not running: {e}"

    return render_template("resume.html", result=result)

# ================= ANALYZE PAGE =================
@app.route("/analyze_page")
def analyze_page():
    if "user" not in session:
        return redirect(url_for("google_login"))
    return render_template("analyzer.html")

# ================= BUILDER PAGE =================
@app.route("/builder", methods=["GET", "POST"])
def builder():
    if "user" not in session:
        return redirect(url_for("google_login"))
    if request.method == "POST":
        return render_template("builder.html")
    return render_template("builder.html")

# ================= ATS =================
@app.route("/ats", methods=["GET", "POST"])
def ats():
    if request.method == "POST":
        file = request.files.get("resume_file")
        job_desc = request.form.get("job_desc", "").strip()

        if not file or file.filename == "":
            return render_template("ats.html", error="❌ No file uploaded")
        if not job_desc:
            return render_template("ats.html", error="❌ Job description required")
        if len(job_desc) < 50:
            return render_template("ats.html", error="❌ Job description too short (minimum 50 characters). Provide full details for accurate ATS analysis.")

        resume_text = ""
        filename = file.filename.lower()

        try:
            if filename.endswith(".pdf"):
                reader = PdfReader(file)
                for page in reader.pages:
                    resume_text += page.extract_text() or ""
            elif filename.endswith(".docx"):
                doc = Document(file)
                for para in doc.paragraphs:
                    resume_text += para.text + "\n"
            else:
                return render_template("ats.html", error="❌ Unsupported file type")
        except Exception as e:
            return render_template("ats.html", error=f"❌ File read error: {e}")

        if not resume_text.strip():
            return render_template("ats.html", error="❌ Could not extract text from file")

        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w")
            json.dump({"resume_text": resume_text, "job_desc": job_desc}, tmp)
            tmp.close()
            session["ats_tmp"] = tmp.name
        except Exception as e:
            return render_template("ats.html", error=f"❌ Session error: {e}")

        return redirect(url_for("ats_result"))

    return render_template("ats.html")

# ================= ATS RESULT =================
@app.route("/ats_result")
def ats_result():
    tmp_path = session.get("ats_tmp")

    if not tmp_path or not os.path.exists(tmp_path):
        return redirect(url_for("ats"))

    try:
        with open(tmp_path, "r") as f:
            payload = json.load(f)
        resume_text = payload["resume_text"]
        job_desc = payload["job_desc"]
    except Exception:
        return redirect(url_for("ats"))
    finally:
        try:
            os.remove(tmp_path)
        except:
            pass
        session.pop("ats_tmp", None)

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3:latest",
                "prompt": f"""Return ONLY a JSON object. No explanation. No markdown. No extra text. Just raw JSON.

You MUST fill ALL four fields. Do NOT leave any field empty.
- score: integer from 0 to 100 based on how well the resume matches the job description
- matched_skills: list of skills found in BOTH the resume and job description
- missing_skills: list of skills in the job description that are NOT in the resume
- suggestions: list of exactly 3 specific actionable tips to improve the resume for this job

Format:
{{
  "score": <integer 0-100>,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "suggestions": ["suggestion1", "suggestion2", "suggestion3"]
}}

JOB DESCRIPTION:
{job_desc}

RESUME:
{resume_text}

JSON:""",
                "stream": False,
                "num_predict": 2048,
                "options": {
                    "temperature": 0,
                    "num_predict": 2048
                }
            },
            timeout=120
        )

        raw = response.json().get("response", "").strip()
        print("RAW AI RESPONSE:", raw)

        data = None
        try:
            data = json.loads(raw)
        except Exception:
            pass

        if not data:
            try:
                start = raw.index("{")
                end = raw.rindex("}") + 1
                data = json.loads(raw[start:end])
            except Exception:
                pass

        if not data:
            try:
                fixed = raw.strip()
                open_brackets = fixed.count("[") - fixed.count("]")
                open_braces = fixed.count("{") - fixed.count("}")
                for _ in range(open_brackets):
                    fixed += "]"
                for _ in range(open_braces):
                    fixed += "}"
                data = json.loads(fixed)
                print("FIXED TRUNCATED JSON ✅")
            except Exception:
                pass

        if not data:
            print("JSON PARSE FAILED. Raw was:", raw)
            data = {
                "score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "suggestions": ["Could not parse AI response. Check terminal for raw output."]
            }

    except Exception as e:
        print("AI Error:", e)
        data = {
            "score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "suggestions": [f"AI not responding: {e}"]
        }

    return render_template("ats_result.html", data=data)

# ================= JOB =================
@app.route("/job")
@login_required
def job():
    return render_template("job_role.html")

# ================= JOB SETUP =================
@app.route("/job_setup", methods=["GET", "POST"])
def job_setup():
    if "user" not in session:
        return redirect(url_for("google_login"))
    if request.method == "POST":
        session["job_role"] = request.form.get("role", "").strip()
        session["job_location"] = request.form.get("location", "").strip()
        job_types = request.form.getlist("job_type")
        session["job_types"] = job_types if job_types else ["Full-time", "Contract", "Part-time", "Internship"]
        return redirect(url_for("job_resume_page"))
    return render_template("job_role.html")

# ================= JOB RESUME UPLOAD PAGE =================
@app.route("/job_resume_page")
@app.route("/job_resume")
def job_resume_page():
    if "user" not in session:
        return redirect(url_for("google_login"))
    if not session.get("job_role"):
        return redirect(url_for("job"))
    return render_template("job_resume.html")

# ================= COUNTRY MAP =================
COUNTRY_MAP = {
    "india": "in", "us": "us", "usa": "us", "united states": "us",
    "uk": "gb", "united kingdom": "gb", "australia": "au", "canada": "ca",
    "germany": "de", "france": "fr", "netherlands": "nl", "singapore": "sg",
    "new zealand": "nz", "south africa": "za", "brazil": "br", "russia": "ru",
    "poland": "pl", "austria": "at", "belgium": "be", "switzerland": "ch",
    "italy": "it", "mexico": "mx", "spain": "es", "argentina": "ar",
}


def detect_country_code(location: str) -> tuple[str, str]:
    loc_lower = location.lower()
    country_code = "in"
    for country_name, code in COUNTRY_MAP.items():
        if country_name in loc_lower:
            country_code = code
            break
    city_location = location
    for country_name in COUNTRY_MAP:
        city_location = city_location.lower().replace(country_name, "").strip(" ,")
    return country_code, city_location


def extract_skills_from_resume(file) -> str:
    resume_text = ""
    if not file or not file.filename:
        return ""
    filename = file.filename.lower()
    try:
        if filename.endswith(".pdf"):
            reader = PdfReader(file)
            for page in reader.pages:
                resume_text += page.extract_text() or ""
        elif filename.endswith(".docx"):
            doc = Document(file)
            for para in doc.paragraphs:
                resume_text += para.text + "\n"
        else:
            resume_text = file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print("Resume read error:", e)
        return ""
    if not resume_text.strip():
        return ""
    try:
        ai_response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3:latest",
                "prompt": (
                    "Extract a comma-separated list of technical skills from this resume. "
                    "Return ONLY the skills, nothing else:\n\n" + resume_text
                ),
                "stream": False
            },
            timeout=60
        )
        return ai_response.json().get("response", "").strip()
    except Exception as e:
        print("AI skill extraction error:", e)
        return ""


def search_adzuna_jobs(country_code: str, query: str, location: str = "", page: int = 1, job_types: list = None) -> list:
    APP_ID = os.getenv("APP_ID")
    APP_KEY = os.getenv("APP_KEY")

    search_query = query
    if job_types and len(job_types) == 1 and "Internship" in job_types:
        search_query = f"{query} internship"
    elif job_types and "Internship" in job_types and len(job_types) > 1:
        search_query = f"{query} internship"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": search_query,
        "results_per_page": 10,
        "sort_by": "relevance",
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/{page}"
    print(f"Adzuna → {url} | params: {params}")

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    results = response.json().get("results", [])
    
    # Map ADZUNA response fields to template expectations
    for job in results:
        # Rename redirect_url to url for template compatibility
        if "redirect_url" in job and "url" not in job:
            job["url"] = job["redirect_url"]
        
        # Extract company display_name
        if isinstance(job.get("company"), dict) and "display_name" in job["company"]:
            job["company"] = job["company"]["display_name"]
        
        # Extract location display_name
        if isinstance(job.get("location"), dict) and "display_name" in job["location"]:
            job["location"] = job["location"]["display_name"]
        
        # Extract salary if available
        if "salary_max" in job and job["salary_max"]:
            job["salary"] = job["salary_max"]
        elif "salary_min" in job and job["salary_min"]:
            job["salary"] = job["salary_min"]
    
    return results


# ================= SAVED JOBS =================
@app.route("/saved_jobs")
@login_required
def saved_jobs():
    email = session.get("email")
    if not email:
        return redirect(url_for("google_login"))
    
    try:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM saved_jobs WHERE email=? ORDER BY saved_at DESC", (email,))
        jobs = [dict(job) for job in cursor.fetchall()]
        # Ensure job_id is treated as string for consistency
        for job in jobs:
            job['job_id'] = str(job['job_id'])
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"Database error in saved_jobs: {e}")
        jobs = []
    
    return render_template("saved_jobs.html", jobs=jobs)

@app.route("/api/save_job", methods=["POST"])
def api_save_job():
    """API endpoint to save or remove a job"""
    if "email" not in session:
        return {"status": "error", "message": "Not logged in"}, 401
    
    try:
        data = request.get_json()
        job_id = data.get("job_id")
        action = data.get("action")  # 'save' or 'unsave'
        email = session.get("email")
        
        if not job_id:
            return {"status": "error", "message": "Missing job_id"}, 400
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        try:
            if action == "save":
                # Insert or ignore if already saved
                cursor.execute(
                    """INSERT OR IGNORE INTO saved_jobs 
                       (email, job_id, title, company, location, url) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (email, job_id, data.get("title", ""), data.get("company", ""),
                     data.get("location", ""), data.get("url", ""))
                )
            elif action == "unsave":
                cursor.execute(
                    "DELETE FROM saved_jobs WHERE email=? AND job_id=?",
                    (email, job_id)
                )
            conn.commit()
            return {"status": "ok", "message": f"Job {action}d successfully"}
        except sqlite3.OperationalError as e:
            print(f"Database error in api_save_job: {e}")
            # Table might not exist, try to create it
            try:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    job_id TEXT,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    url TEXT,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(email, job_id)
                )
                """)
                conn.commit()
                return {"status": "error", "message": "Database table created. Please try again."}, 500
            except Exception as create_err:
                return {"status": "error", "message": str(create_err)}, 500
        finally:
            conn.close()
    except Exception as e:
        print(f"Error in api_save_job: {e}")
        return {"status": "error", "message": str(e)}, 500

# ================= SKILLS GAP ANALYSIS =================
@app.route("/skills", methods=["GET", "POST"])
@login_required
def skills():
    """Skill gap analysis page"""
    if request.method == "POST":
        role = request.form.get("role", "").strip()
        user_skills = request.form.get("user_skills", "").strip()
        
        if not role or not user_skills:
            return render_template("skills.html", roles=["Python Developer", "Data Scientist", "DevOps Engineer", "Full Stack Developer", "Frontend Developer", "Backend Developer", "Mobile Developer", "QA Engineer", "Cloud Architect", "Machine Learning Engineer"], gap_result=None)
        
        # Skills required for different roles (predefined mapping)
        role_skills_map = {
            "Python Developer": ["Python", "Django", "FastAPI", "SQL", "Git", "Docker", "REST APIs", "Unit Testing"],
            "Data Scientist": ["Python", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "SQL", "Statistics", "Matplotlib"],
            "DevOps Engineer": ["Docker", "Kubernetes", "Jenkins", "Git", "Linux", "AWS", "Terraform", "CI/CD"],
            "Full Stack Developer": ["JavaScript", "React", "Node.js", "MongoDB", "SQL", "HTML", "CSS", "Git"],
            "Frontend Developer": ["JavaScript", "React", "Vue.js", "CSS", "HTML", "Webpack", "Git", "UI/UX"],
            "Backend Developer": ["Node.js", "Python", "Java", "SQL", "APIs", "Docker", "Git", "Database Design"],
            "Mobile Developer": ["React Native", "Flutter", "Swift", "Kotlin", "Firebase", "Git", "REST APIs", "Mobile UI"],
            "QA Engineer": ["Selenium", "Jest", "Cypress", "Manual Testing", "SQL", "Git", "JIRA", "Test Planning"],
            "Cloud Architect": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Networking", "Security"],
            "Machine Learning Engineer": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "SQL", "Statistics", "Git", "Data Analysis"],
        }
        
        required = role_skills_map.get(role, [])
        user_skills_list = [s.strip() for s in user_skills.split(",")]
        matched = [s for s in required if any(req.lower() in s.lower() or s.lower() in req.lower() for req in user_skills_list)]
        missing = [s for s in required if s not in matched]
        match_pct = int(len(matched) / len(required) * 100) if required else 0
        
        gap_result = {
            "role": role,
            "required": required,
            "matched": matched,
            "missing": missing,
            "match_pct": match_pct
        }
        return render_template("skills.html", roles=["Python Developer", "Data Scientist", "DevOps Engineer", "Full Stack Developer", "Frontend Developer", "Backend Developer", "Mobile Developer", "QA Engineer", "Cloud Architect", "Machine Learning Engineer"], gap_result=gap_result, prefill_skills=user_skills)
    
    return render_template("skills.html", roles=["Python Developer", "Data Scientist", "DevOps Engineer", "Full Stack Developer", "Frontend Developer", "Backend Developer", "Mobile Developer", "QA Engineer", "Cloud Architect", "Machine Learning Engineer"], gap_result=None, prefill_skills="")

# ================= JOB RESULT =================
@app.route("/job_result", methods=["GET", "POST"])
def job_result():
    role = session.get("job_role", "")
    location = session.get("job_location", "")
    job_types = session.get("job_types", ["Full-time", "Contract", "Part-time", "Internship"])

    skills = ""
    if request.method == "POST":
        skills = extract_skills_from_resume(request.files.get("resume"))

    country_code, city_location = detect_country_code(location)
    search_query = role.strip() if role.strip() else "software engineer"

    jobs = []
    error_msg = None

    try:
        jobs = search_adzuna_jobs(country_code, search_query, city_location, job_types=job_types)

        if not jobs and city_location:
            print("No results with location — retrying without location filter")
            jobs = search_adzuna_jobs(country_code, search_query, job_types=job_types)
            if jobs:
                error_msg = f"No jobs found in '{location}' — showing remote / nationwide results instead."

        if not jobs:
            broad_query = role.split()[0] if role.strip() else "developer"
            print(f"Still no results — retrying with broad query: '{broad_query}'")
            jobs = search_adzuna_jobs(country_code, broad_query, job_types=job_types)
            if jobs:
                error_msg = f"No exact matches for '{role}' — showing broader results for '{broad_query}'."

        if not jobs and country_code != "gb":
            print("Falling back to GB endpoint")
            jobs = search_adzuna_jobs("gb", search_query, job_types=job_types)
            if jobs:
                error_msg = "No results found in your region — showing international listings instead."

        if not jobs:
            error_msg = "No jobs found. Try a broader role title or a different location."

    except requests.exceptions.HTTPError as e:
        print(f"Adzuna HTTP error: {e}")
        error_msg = f"Job search API returned an error: {e}"
    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to job search service. Check your internet connection."
    except requests.exceptions.Timeout:
        error_msg = "Job search request timed out. Please try again."
    except Exception as e:
        print("Job API unexpected error:", e)
        error_msg = f"Unexpected error during job search: {e}"

    session.pop("job_role", None)
    session.pop("job_location", None)
    session.pop("job_types", None)

    # Add saved status to each job
    email = session.get("email")
    if email:
        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT job_id FROM saved_jobs WHERE email=?", (email,))
            saved_job_ids = {str(row[0]) for row in cursor.fetchall()}
            conn.close()
            for job in jobs:
                job["saved"] = str(job.get("id", "")) in saved_job_ids
        except sqlite3.OperationalError as db_error:
            print(f"Database error in job_result: {db_error}")
            # Mark all jobs as not saved if table doesn't exist
            for job in jobs:
                job["saved"] = False
    else:
        for job in jobs:
            job["saved"] = False
    
    # Create job saves dict for template
    job_saves = {job.get("id", ""): job.get("saved", False) for job in jobs}
    
    return render_template(
        "job_result.html",
        jobs=jobs,
        jobs_saves=job_saves,
        skills=skills,
        role=role,
        location=location,
        job_types=job_types,
        error_msg=error_msg,
    )

# ================= COVER LETTER =================
@app.route("/cover_letter", methods=["GET", "POST"])
@login_required
def cover_letter():
    email = session.get("email")
    if not email:
        return redirect(url_for("google_login"))
    
    letter = None
    saved = []
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        company = request.form.get("company", "").strip()
        job_desc = request.form.get("job_desc", "").strip()
        resume_text = request.form.get("resume_text", "").strip()
        
        if not name or not role or not company:
            flash("❌ Name, role, and company are required", "error")
            return render_template("cover_letter.html", letter=None, saved=[])
        
        if not job_desc:
            flash("❌ Job description is required", "error")
            return render_template("cover_letter.html", letter=None, saved=[])
        
        try:
            # Generate cover letter using AI
            prompt = f"""Write a professional cover letter for:
- Name: {name}
- Role: {role}
- Company: {company}
- Key job requirements: {job_desc}
{f'- My experience: {resume_text}' if resume_text else ''}

Write a compelling, personalized 3-4 paragraph cover letter. No salutation/date needed, just the body."""
            
            # Call Ollama AI
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": "llama3:latest", "prompt": prompt, "stream": False},
                timeout=60,
            )
            response.raise_for_status()
            letter = response.json().get("response", "").strip()
            
            if not letter:
                flash("❌ AI failed to generate letter. Try again.", "error")
                return render_template("cover_letter.html", letter=None, saved=[])
            
            # Save to database
            try:
                conn = sqlite3.connect("users.db")
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO cover_letters (email, name, role, company, job_desc, resume_text, letter)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (email, name, role, company, job_desc, resume_text, letter)
                )
                conn.commit()
                conn.close()
                flash("✅ Cover letter saved!", "success")
            except sqlite3.OperationalError as e:
                print(f"Database error in cover_letter: {e}")
                # Table might not exist, but letter is still generated
                flash("⚠️ Letter generated but not saved", "warning")
        
        except requests.exceptions.Timeout:
            flash("❌ AI request timed out. Check if Ollama is running.", "error")
        except requests.exceptions.ConnectionError:
            flash("❌ Cannot connect to AI service. Check Ollama is running.", "error")
        except Exception as e:
            print(f"Error in cover_letter generation: {e}")
            flash(f"❌ Error: {str(e)}", "error")
    
    # Load saved letters
    try:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, name, role, company, created_at FROM cover_letters 
               WHERE email=? ORDER BY created_at DESC LIMIT 10""",
            (email,)
        )
        saved = [dict(row) for row in cursor.fetchall()]
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"Database error loading saved letters: {e}")
        saved = []
    
    return render_template("cover_letter.html", letter=letter, saved=saved)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)