import re
import sqlite3
import uuid
from pathlib import Path

import streamlit as st
from pypdf import PdfReader
from docx import Document

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "resumes"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

STATUSES = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]


def init_hiring_db(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hiring_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                job_role TEXT NOT NULL,
                skills TEXT,
                status TEXT NOT NULL DEFAULT 'Applied',
                notes TEXT,
                resume_path TEXT,
                resume_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def extract_resume_text(path):
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    return ""


def render_hiring_page(db_path):
    init_hiring_db(db_path)
    st.title("Hiring & Resume Management")
    st.caption("Manage applicants, resumes, job roles and recruitment status.")

    with sqlite3.connect(db_path) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM hiring_candidates"
        ).fetchone()[0]
        shortlisted = conn.execute(
            "SELECT COUNT(*) FROM hiring_candidates WHERE status='Shortlisted'"
        ).fetchone()[0]
        interviews = conn.execute(
            "SELECT COUNT(*) FROM hiring_candidates WHERE status='Interview'"
        ).fetchone()[0]
        selected = conn.execute(
            "SELECT COUNT(*) FROM hiring_candidates WHERE status='Selected'"
        ).fetchone()[0]

    a, b, c, d = st.columns(4)
    a.metric("Total Candidates", total)
    b.metric("Shortlisted", shortlisted)
    c.metric("Interviews", interviews)
    d.metric("Selected", selected)

    st.subheader("Add Candidate")
    with st.form("add_hiring_candidate", clear_on_submit=True):
        name = st.text_input("Candidate name *")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        role = st.text_input("Job role *")
        skills = st.text_input("Skills (comma-separated)")
        resume = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"])
        notes = st.text_area("HR notes")
        submitted = st.form_submit_button("Save Candidate")

        if submitted:
            if not name.strip() or not role.strip():
                st.error("Candidate name and job role are required.")
            elif resume is None:
                st.error("Please upload a PDF or DOCX resume.")
            else:
                suffix = Path(resume.name).suffix.lower()
                saved_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
                saved_path.write_bytes(resume.getvalue())
                try:
                    extracted = extract_resume_text(saved_path)
                    email_found = re.search(
                        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                        extracted
                    )
                    phone_found = re.search(r"(?:\+?\d[\d\s()-]{7,}\d)", extracted)
                    final_email = email.strip() or (
                        email_found.group(0) if email_found else ""
                    )
                    final_phone = phone.strip() or (
                        phone_found.group(0).strip() if phone_found else ""
                    )
                    with sqlite3.connect(db_path) as conn:
                        conn.execute("""
                            INSERT INTO hiring_candidates
                            (name, email, phone, job_role, skills, notes,
                             resume_path, resume_name)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            name.strip(), final_email, final_phone,
                            role.strip(), skills.strip(), notes.strip(),
                            str(saved_path), Path(resume.name).name
                        ))
                    st.success("Candidate saved successfully.")
                    st.rerun()
                except Exception as exc:
                    saved_path.unlink(missing_ok=True)
                    st.error(f"Could not process the resume: {exc}")

    st.divider()
    st.subheader("Candidate Records")
    search = st.text_input("Search by name, email, skill or job role")
    status_filter = st.selectbox("Filter by status", ["All"] + STATUSES)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM hiring_candidates ORDER BY id DESC
        """).fetchall()

    candidates = [
        dict(row) for row in rows
        if (status_filter == "All" or row["status"] == status_filter)
        and search.casefold() in " ".join([
            row["name"] or "", row["email"] or "", row["skills"] or "",
            row["job_role"] or ""
        ]).casefold()
    ]

    if not candidates:
        st.info("No candidates match your search.")
    for candidate in candidates:
        with st.expander(
            f'{candidate["name"]} — {candidate["job_role"]} '
            f'({candidate["status"]})'
        ):
            st.write("**Email:**", candidate["email"] or "Not provided")
            st.write("**Phone:**", candidate["phone"] or "Not provided")
            st.write("**Skills:**", candidate["skills"] or "Not provided")
            st.write("**HR notes:**", candidate["notes"] or "None")
            resume_path = Path(candidate["resume_path"] or "")
            if resume_path.is_file() and resume_path.parent == UPLOAD_DIR:
                st.download_button(
                    "Download Resume",
                    data=resume_path.read_bytes(),
                    file_name=candidate["resume_name"] or "resume",
                    key=f'resume_{candidate["id"]}'
                )

            with st.form(f'update_candidate_{candidate["id"]}'):
                new_status = st.selectbox(
                    "Application status",
                    STATUSES,
                    index=STATUSES.index(candidate["status"])
                    if candidate["status"] in STATUSES else 0,
                    key=f'status_{candidate["id"]}'
                )
                new_notes = st.text_area(
                    "Update HR notes",
                    value=candidate["notes"] or "",
                    key=f'notes_{candidate["id"]}'
                )
                update = st.form_submit_button("Update Candidate")
                if update:
                    with sqlite3.connect(db_path) as conn:
                        conn.execute("""
                            UPDATE hiring_candidates
                            SET status=?, notes=? WHERE id=?
                        """, (
                            new_status, new_notes.strip(), candidate["id"]
                        ))
                    st.success("Candidate updated.")
                    st.rerun()
