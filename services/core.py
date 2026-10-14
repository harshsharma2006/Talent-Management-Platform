
from pathlib import Path
import sqlite3
import hashlib
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "talentsphere_healthy.db"

LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]
ROLE_CATALOG = {
    "Data Analyst": {"skills": {"Python": 2, "SQL": 2, "Pandas": 2, "Excel": 1},
                     "criteria": "Strong data analysis, SQL and reporting skills."},
    "Data Scientist": {"skills": {"Python": 3, "SQL": 2, "Pandas": 3, "Machine Learning": 2},
                       "criteria": "Strong Python, statistics and machine learning skills."},
    "Software Engineer": {"skills": {"Python": 2, "Git": 2, "SQL": 1},
                          "criteria": "Programming, version control and software development skills."},
}

def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            phone TEXT DEFAULT '', location TEXT DEFAULT '', job_title TEXT DEFAULT '',
            company TEXT DEFAULT '', department TEXT DEFAULT '', industry TEXT DEFAULT '',
            employment_type TEXT DEFAULT '', years_experience REAL DEFAULT 0,
            linkedin TEXT DEFAULT '', github TEXT DEFAULT '', portfolio TEXT DEFAULT '',
            education TEXT DEFAULT '', certifications TEXT DEFAULT '', summary TEXT DEFAULT '',
            experience TEXT DEFAULT '', projects TEXT DEFAULT '', target_role TEXT DEFAULT '',
            target_level TEXT DEFAULT 'Senior', timeline TEXT DEFAULT '',
            target_industry TEXT DEFAULT '', career_goal TEXT DEFAULT '', resume_text TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            name TEXT NOT NULL, category TEXT NOT NULL, proficiency TEXT NOT NULL, years REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            category TEXT NOT NULL, score INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            item TEXT NOT NULL, percent INTEGER NOT NULL, status TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            years_experience REAL NOT NULL,
            primary_skills TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        c.commit()

def _hash(p): return hashlib.sha256(p.encode("utf-8")).hexdigest()

def register(name,email,password):
    if not name.strip() or not email.strip() or not password:
        return False, "All fields are required."
    if len(password) < 8: return False, "Password must be at least 8 characters."
    try:
        with _conn() as c:
            cur=c.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",(name.strip(),email.strip().lower(),_hash(password)))
            uid=cur.lastrowid
            c.execute("INSERT INTO profiles(user_id) VALUES(?)",(uid,))
            c.commit()
        return True,"Account created successfully."
    except sqlite3.IntegrityError:
        return False,"An account with this email already exists."

def login(email,password):
    with _conn() as c:
        r=c.execute("SELECT id,name,email FROM users WHERE email=? AND password_hash=?",(email.strip().lower(),_hash(password))).fetchone()
    return dict(r) if r else None

def get_profile(uid):
    with _conn() as c:
        r=c.execute("SELECT * FROM profiles WHERE user_id=?",(uid,)).fetchone()
    return dict(r) if r else {"user_id":uid}

def save_profile(uid,data):
    fields=[k for k in data if k in {
        "phone","location","job_title","company","department","industry","employment_type",
        "years_experience","linkedin","github","portfolio","education","certifications",
        "summary","experience","projects","target_role","target_level","timeline",
        "target_industry","career_goal","resume_text"}]
    if not fields: return
    with _conn() as c:
        sets=", ".join(f"{k}=?" for k in fields)
        c.execute(f"UPDATE profiles SET {sets} WHERE user_id=?", [data[k] for k in fields]+[uid])
        c.commit()

def list_skills(uid):
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM skills WHERE user_id=? ORDER BY id DESC",(uid,)).fetchall()]

def add_skill(uid,name,category,proficiency,years):
    if not name.strip(): return False,"Skill name is required."
    with _conn() as c:
        c.execute("INSERT INTO skills(user_id,name,category,proficiency,years) VALUES(?,?,?,?,?)",(uid,name.strip(),category,proficiency,years))
        c.commit()
    return True,"Skill added."

def delete_skill(uid,sid):
    with _conn() as c: c.execute("DELETE FROM skills WHERE user_id=? AND id=?",(uid,sid)); c.commit()

def add_assessment(uid,cat,score):
    with _conn() as c: c.execute("INSERT INTO assessments(user_id,category,score) VALUES(?,?,?)",(uid,cat,score)); c.commit()

def get_assessments(uid):
    with _conn() as c: return [dict(r) for r in c.execute("SELECT * FROM assessments WHERE user_id=? ORDER BY id DESC",(uid,)).fetchall()]

def save_progress(uid,item,percent):
    status="Completed" if percent==100 else ("In progress" if percent>0 else "Not started")
    with _conn() as c:
        c.execute("INSERT INTO progress(user_id,item,percent,status) VALUES(?,?,?,?)",(uid,item,percent,status)); c.commit()

def get_progress(uid):
    with _conn() as c: return [dict(r) for r in c.execute("SELECT * FROM progress WHERE user_id=? ORDER BY id DESC",(uid,)).fetchall()]

def profile_completion(profile,skills):
    checks=["phone","location","job_title","department","education","summary","experience","projects","target_role"]
    done=sum(bool(profile.get(k)) for k in checks)+bool(skills)
    return round(done/(len(checks)+1)*100), [k for k in checks if not profile.get(k)]

def gap_analysis(target,skills):
    required=ROLE_CATALOG.get(target,{}).get("skills",{})
    levels={x:i+1 for i,x in enumerate(LEVELS)}
    have={s["name"].lower():levels.get(s["proficiency"],1) for s in skills}
    out=[]
    for skill,req in required.items():
        cur=have.get(skill.lower(),0); gap=max(0,req-cur)
        out.append({"skill":skill,"current":cur,"required":req,"gap":gap,"priority":"High" if gap>=2 else ("Medium" if gap else "Low")})
    return out

def role_match(target,skills,years):
    req=ROLE_CATALOG.get(target,{}).get("skills",{})
    if not req:return 0
    levels={x:i+1 for i,x in enumerate(LEVELS)}
    have={s["name"].lower():levels.get(s["proficiency"],1) for s in skills}
    score=sum(min(have.get(k.lower(),0)/v,1) for k,v in req.items())/len(req)*100
    return round(score)

def profile_analysis(profile,skills):
    completion,_=profile_completion(profile,skills)
    score=min(100,round(completion*.7+min(len(skills),10)*3))
    return {"completion":completion,"score":score,
            "strengths":["Saved professional profile"] if completion>=50 else [],
            "weaknesses":["Complete your profile"] if completion<80 else []}

def recommendations(profile,skills):
    return [{"priority":"High","title":"Build your skill evidence","description":"Add relevant skills and measurable project outcomes to strengthen your profile."}]

def export_user_data(uid):
    return {"profile":get_profile(uid),"skills":list_skills(uid),"assessments":get_assessments(uid),"progress":get_progress(uid)}

def save_employee(employee_id,employee_name,department,designation,years_experience,primary_skills):
    vals=[str(employee_id).strip(),str(employee_name).strip(),str(department).strip(),str(designation).strip(),str(primary_skills).strip()]
    if not all(vals): return False,"Please fill all required fields."
    try: years=float(years_experience)
    except: return False,"Years of experience must be a valid number."
    if years<0 or years>60: return False,"Years of experience must be between 0 and 60."
    try:
        with _conn() as c:
            c.execute("""INSERT INTO employees(employee_id,employee_name,department,designation,years_experience,primary_skills)
                         VALUES(?,?,?,?,?,?)""",(*vals[:4],years,vals[4]))
            c.commit()
        return True,"Employee saved successfully."
    except sqlite3.IntegrityError:
        return False,f"Employee ID '{vals[0]}' already exists."

def list_employees():
    with _conn() as c:
        return [dict(r) for r in c.execute("""SELECT employee_id,employee_name,department,designation,
            years_experience,primary_skills,created_at FROM employees ORDER BY id DESC""").fetchall()]

def delete_employee(employee_id):
    with _conn() as c: c.execute("DELETE FROM employees WHERE employee_id=?",(employee_id,)); c.commit()
