import re
import sqlite3
import uuid
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd
import streamlit as st
from docx import Document
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "resumes"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

STATUSES = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]
INTERVIEW_STATUSES = ["Scheduled", "Completed", "Cancelled", "No-show"]
INTERVIEW_MODES = ["Online", "In-person", "Phone"]


def init_hiring_db(db_path):
    """Create hiring tables and safely add interview management support."""
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
        # Additive migration: this creates a new table and does not alter or
        # delete existing candidate records.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                interviewer TEXT NOT NULL,
                scheduled_at TEXT NOT NULL,
                interview_mode TEXT NOT NULL,
                meeting_details TEXT,
                interview_status TEXT NOT NULL DEFAULT 'Scheduled',
                rating INTEGER,
                feedback TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(candidate_id) REFERENCES hiring_candidates(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidate_interviews_scheduled_at
            ON candidate_interviews(scheduled_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidate_interviews_candidate_id
            ON candidate_interviews(candidate_id)
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


def _get_candidates(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(
            "SELECT * FROM hiring_candidates ORDER BY name COLLATE NOCASE"
        ).fetchall()]


def _render_candidate_form(db_path):
    st.subheader("Add Candidate")
    with st.form("add_hiring_candidate", clear_on_submit=True):
        name = st.text_input("Candidate name *")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        role = st.text_input("Job role *")
        skills = st.text_input("Skills (comma-separated)")
        resume = st.file_uploader(
            "Upload resume (PDF or DOCX)", type=["pdf", "docx"]
        )
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
                    phone_found = re.search(
                        r"(?:\+?\d[\d\s()-]{7,}\d)", extracted
                    )
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


def _render_candidate_records(db_path):
    st.subheader("Candidate Records")
    search = st.text_input("Search by name, email, skill or job role")
    status_filter = st.selectbox(
        "Filter by status", ["All"] + STATUSES, key="candidate_status_filter"
    )

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM hiring_candidates ORDER BY id DESC"
        ).fetchall()

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


def _render_schedule_interview(db_path, candidates):
    st.subheader("Schedule Interview")
    if not candidates:
        st.info("Add a candidate before scheduling an interview.")
        return

    candidate_options = {
        f'{c["name"]} — {c["job_role"]} (ID: {c["id"]})': c["id"]
        for c in candidates
    }
    with st.form("schedule_candidate_interview", clear_on_submit=True):
        selected_label = st.selectbox(
            "Candidate", list(candidate_options.keys())
        )
        interviewer = st.text_input("Interviewer name *")
        interview_date = st.date_input("Interview date", min_value=date.today())
        interview_time = st.time_input("Interview time", value=time(10, 0))
        mode = st.selectbox("Interview mode", INTERVIEW_MODES)
        details = st.text_area(
            "Meeting details / location / meeting link",
            help="For online interviews, paste the meeting link here."
        )
        schedule = st.form_submit_button("Schedule Interview")

        if schedule:
            if not interviewer.strip():
                st.error("Interviewer name is required.")
            else:
                candidate_id = candidate_options[selected_label]
                scheduled_at = datetime.combine(
                    interview_date, interview_time
                ).isoformat(timespec="minutes")
                with sqlite3.connect(db_path) as conn:
                    conn.execute("""
                        INSERT INTO candidate_interviews
                        (candidate_id, interviewer, scheduled_at,
                         interview_mode, meeting_details)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        candidate_id, interviewer.strip(), scheduled_at,
                        mode, details.strip()
                    ))
                    conn.execute("""
                        UPDATE hiring_candidates
                        SET status='Interview'
                        WHERE id=? AND status NOT IN ('Selected', 'Rejected')
                    """, (candidate_id,))
                st.success("Interview scheduled successfully.")
                st.rerun()


def _load_interviews(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT i.*, c.name AS candidate_name, c.email AS candidate_email,
                   c.phone AS candidate_phone, c.job_role AS job_role
            FROM candidate_interviews i
            JOIN hiring_candidates c ON c.id = i.candidate_id
            ORDER BY i.scheduled_at ASC
        """).fetchall()
    return [dict(row) for row in rows]


def _render_interview_management(db_path):
    st.subheader("Interview Calendar & Management")
    interviews = _load_interviews(db_path)
    filter_options = ["All", "Upcoming", "Completed", "Cancelled", "No-show"]
    interview_filter = st.selectbox(
        "Show interviews", filter_options, key="interview_filter"
    )

    now_text = datetime.now().isoformat(timespec="minutes")
    visible = interviews
    if interview_filter == "Upcoming":
        visible = [
            x for x in interviews
            if x["interview_status"] == "Scheduled"
            and x["scheduled_at"] >= now_text
        ]
    elif interview_filter != "All":
        visible = [
            x for x in interviews
            if x["interview_status"] == interview_filter
        ]

    if not visible:
        st.info("No interviews found for this filter.")
    for interview in visible:
        scheduled = datetime.fromisoformat(interview["scheduled_at"])
        heading = (
            f'{interview["candidate_name"]} — {interview["job_role"]} | '
            f'{scheduled.strftime("%d %b %Y, %I:%M %p")} '
            f'({interview["interview_status"]})'
        )
        with st.expander(heading):
            st.write("**Interviewer:**", interview["interviewer"])
            st.write("**Mode:**", interview["interview_mode"])
            st.write("**Candidate email:**", interview["candidate_email"] or "Not provided")
            st.write("**Candidate phone:**", interview["candidate_phone"] or "Not provided")
            st.write(
                "**Meeting details:**",
                interview["meeting_details"] or "Not provided"
            )

            with st.form(f'update_interview_{interview["id"]}'):
                status_index = (
                    INTERVIEW_STATUSES.index(interview["interview_status"])
                    if interview["interview_status"] in INTERVIEW_STATUSES else 0
                )
                new_interview_status = st.selectbox(
                    "Interview status", INTERVIEW_STATUSES,
                    index=status_index, key=f'interview_status_{interview["id"]}'
                )
                rating_options = ["Not rated", "1", "2", "3", "4", "5"]
                current_rating = (
                    str(interview["rating"])
                    if interview["rating"] in range(1, 6) else "Not rated"
                )
                new_rating = st.selectbox(
                    "Rating (1–5)", rating_options,
                    index=rating_options.index(current_rating),
                    key=f'interview_rating_{interview["id"]}'
                )
                feedback = st.text_area(
                    "Interview feedback",
                    value=interview["feedback"] or "",
                    key=f'interview_feedback_{interview["id"]}'
                )
                current_candidate_status = next(
                    (
                        c["status"] for c in _get_candidates(db_path)
                        if c["id"] == interview["candidate_id"]
                    ),
                    "Interview"
                )
                pipeline_index = (
                    STATUSES.index(current_candidate_status)
                    if current_candidate_status in STATUSES else 0
                )
                pipeline_status = st.selectbox(
                    "Candidate application status", STATUSES,
                    index=pipeline_index,
                    key=f'pipeline_status_{interview["id"]}'
                )
                save = st.form_submit_button("Save Interview Feedback")
                if save:
                    rating_value = int(new_rating) if new_rating != "Not rated" else None
                    with sqlite3.connect(db_path) as conn:
                        conn.execute("""
                            UPDATE candidate_interviews
                            SET interview_status=?, rating=?, feedback=?,
                                updated_at=CURRENT_TIMESTAMP
                            WHERE id=?
                        """, (
                            new_interview_status, rating_value,
                            feedback.strip(), interview["id"]
                        ))
                        conn.execute("""
                            UPDATE hiring_candidates SET status=? WHERE id=?
                        """, (pipeline_status, interview["candidate_id"]))
                    st.success("Interview details and candidate status updated.")
                    st.rerun()

    st.divider()
    st.subheader("Interview Report")
    if interviews:
        report_rows = [{
            "Interview ID": x["id"],
            "Candidate": x["candidate_name"],
            "Email": x["candidate_email"],
            "Job Role": x["job_role"],
            "Interviewer": x["interviewer"],
            "Scheduled At": x["scheduled_at"],
            "Mode": x["interview_mode"],
            "Interview Status": x["interview_status"],
            "Rating": x["rating"],
            "Feedback": x["feedback"],
        } for x in interviews]
        report_df = pd.DataFrame(report_rows)
        st.dataframe(report_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Interview Report (CSV)",
            data=report_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="interview_report.csv",
            mime="text/csv",
            key="download_interview_report"
        )
    else:
        st.caption("Interview report will appear after the first interview is scheduled.")


def render_hiring_page(db_path):
    init_hiring_db(db_path)
    st.title("Hiring & Resume Management")
    st.caption(
        "Manage applicants, resumes, job roles, recruitment status "
        "and interview scheduling."
    )

    with sqlite3.connect(db_path) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM hiring_candidates"
        ).fetchone()[0]
        shortlisted = conn.execute(
            "SELECT COUNT(*) FROM hiring_candidates WHERE status='Shortlisted'"
        ).fetchone()[0]
        interviews_count = conn.execute(
            "SELECT COUNT(*) FROM hiring_candidates WHERE status='Interview'"
        ).fetchone()[0]
        selected = conn.execute(
            "SELECT COUNT(*) FROM hiring_candidates WHERE status='Selected'"
        ).fetchone()[0]

    a, b, c, d = st.columns(4)
    a.metric("Total Candidates", total)
    b.metric("Shortlisted", shortlisted)
    c.metric("Interviews", interviews_count)
    d.metric("Selected", selected)

    candidates = _get_candidates(db_path)
    tabs = st.tabs([
        "Add Candidate", "Candidate Records",
        "Schedule Interview", "Interview Management"
    ])
    with tabs[0]:
        _render_candidate_form(db_path)
    with tabs[1]:
        _render_candidate_records(db_path)
    with tabs[2]:
        _render_schedule_interview(db_path, candidates)
    with tabs[3]:
        _render_interview_management(db_path)
