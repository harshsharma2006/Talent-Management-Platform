
from __future__ import annotations

import csv
import io
import sqlite3
from pathlib import Path
from typing import Any

import streamlit as st


def init_learning_db(db_path: str | Path) -> None:
    """Create L&D tables without changing existing application tables."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                skills TEXT DEFAULT '',
                duration_hours INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS employee_course_enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                employee_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Not Started'
                    CHECK(status IN ('Not Started', 'In Progress', 'Completed')),
                progress INTEGER NOT NULL DEFAULT 0
                    CHECK(progress BETWEEN 0 AND 100),
                certificate_name TEXT DEFAULT '',
                certificate_path TEXT DEFAULT '',
                enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(course_id, employee_id),
                FOREIGN KEY(course_id) REFERENCES learning_courses(course_id)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_learning_enroll_employee
            ON employee_course_enrollments(employee_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_learning_enroll_course
            ON employee_course_enrollments(course_id)
        """)


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _get_courses(db_path: str | Path):
    with _connect(db_path) as conn:
        return conn.execute(
            "SELECT * FROM learning_courses ORDER BY created_at DESC, title"
        ).fetchall()


def _get_enrollments(
    db_path: str | Path,
    employee_id: str | None = None
):
    query = """
        SELECT e.*, c.title AS course_title, c.skills, c.duration_hours
        FROM employee_course_enrollments e
        JOIN learning_courses c ON c.course_id = e.course_id
    """

    params = ()

    if employee_id is not None:
        query += " WHERE e.employee_id = ?"
        params = (str(employee_id),)

    query += " ORDER BY e.updated_at DESC"

    with _connect(db_path) as conn:
        return conn.execute(query, params).fetchall()


def _employee_identifier(employee: Any) -> str:
    if isinstance(employee, dict):
        for key in ("employee_id", "id", "emp_id"):
            if employee.get(key) is not None:
                return str(employee[key])

    for key in ("employee_id", "id", "emp_id"):
        value = getattr(employee, key, None)
        if value is not None:
            return str(value)

    return str(employee)


def render_learning_page(
    db_path: str | Path,
    role: str = "admin",
    employee_id: str | None = None,
    employees: list[Any] | None = None,
) -> None:

    init_learning_db(db_path)

    st.title("Learning & Development")
    st.caption(
        "Manage training courses, employee enrollments and learning progress."
    )

    if str(role).lower() == "admin":
        _render_admin(db_path, employees or [])
    else:
        if employee_id is None:
            st.error("Employee ID is required to open your learning dashboard.")
            return

        _render_employee(db_path, str(employee_id))


def _render_admin(db_path: str | Path, employees: list[Any]) -> None:

    with st.expander("Add a new course", expanded=False):

        with st.form("add_learning_course_form", clear_on_submit=True):

            title = st.text_input("Course title")
            description = st.text_area("Course description")
            skills = st.text_input("Skills covered (comma-separated)")
            duration = st.number_input(
                "Duration (hours)",
                min_value=0,
                step=1
            )

            submitted = st.form_submit_button("Add course")

            if submitted:

                if not title.strip():
                    st.error("Please enter a course title.")

                else:
                    with _connect(db_path) as conn:
                        conn.execute(
                            """
                            INSERT INTO learning_courses
                            (title, description, skills, duration_hours)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                title.strip(),
                                description.strip(),
                                skills.strip(),
                                int(duration),
                            ),
                        )

                    st.success("Course added successfully.")
                    st.rerun()

    courses = _get_courses(db_path)
    enrollments = _get_enrollments(db_path)

    total = len(enrollments)

    completed = sum(
        1 for row in enrollments
        if row["status"] == "Completed"
    )

    completion_rate = (
        completed / total * 100
        if total else 0.0
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Total courses", len(courses))
    c2.metric("Total enrollments", total)
    c3.metric("Completion rate", f"{completion_rate:.1f}%")

    st.subheader("Course catalog")

    if not courses:
        st.info("No courses added yet.")

    else:
        for course in courses:

            with st.container(border=True):

                st.markdown(f"**{course['title']}**")

                if course["description"]:
                    st.write(course["description"])

                st.caption(
                    f"Skills: {course['skills'] or 'Not specified'} · "
                    f"Duration: {course['duration_hours']} hours"
                )

                course_enrollments = [
                    row for row in enrollments
                    if row["course_id"] == course["course_id"]
                ]

                st.caption(
                    f"Enrollments: {len(course_enrollments)}"
                )

                if not course_enrollments:

                    if st.button(
                        "Delete course",
                        key=f"delete_course_{course['course_id']}"
                    ):

                        with _connect(db_path) as conn:
                            conn.execute(
                                "DELETE FROM learning_courses WHERE course_id = ?",
                                (course["course_id"],),
                            )

                        st.rerun()

    st.subheader("Employee enrollments")

    if employees:

        employee_options = {"All employees": None}

        for emp in employees:

            emp_id = _employee_identifier(emp)

            if isinstance(emp, dict):
                label = str(
                    emp.get("name")
                    or emp.get("employee_name")
                    or emp_id
                )
            else:
                label = str(getattr(emp, "name", emp_id))

            employee_options[f"{label} ({emp_id})"] = emp_id

        selected_label = st.selectbox(
            "Filter by employee",
            list(employee_options.keys())
        )

        selected_employee = employee_options[selected_label]

        visible = (
            _get_enrollments(db_path, selected_employee)
            if selected_employee is not None
            else enrollments
        )

    else:
        visible = enrollments

    if visible:

        table_rows = [
            {
                "Employee ID": row["employee_id"],
                "Course": row["course_title"],
                "Status": row["status"],
                "Progress": f"{row['progress']}%",
                "Enrolled": row["enrolled_at"],
                "Updated": row["updated_at"],
            }
            for row in visible
        ]

        st.dataframe(
            table_rows,
            use_container_width=True,
            hide_index=True
        )

        csv_buffer = io.StringIO()

        writer = csv.DictWriter(
            csv_buffer,
            fieldnames=list(table_rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(table_rows)

        st.download_button(
            "Download enrollment report (CSV)",
            data=csv_buffer.getvalue().encode("utf-8"),
            file_name="learning_enrollments.csv",
            mime="text/csv",
        )

    else:
        st.info("No employee enrollments yet.")


def _render_employee(db_path: str | Path, employee_id: str) -> None:

    courses = _get_courses(db_path)
    enrollments = _get_enrollments(db_path, employee_id)

    enrolled_course_ids = {
        row["course_id"] for row in enrollments
    }

    st.subheader("Available courses")

    available = [
        course for course in courses
        if course["course_id"] not in enrolled_course_ids
    ]

    if not available:
        st.info("No new courses are currently available.")

    else:
        for course in available:

            with st.container(border=True):

                st.markdown(f"**{course['title']}**")

                st.write(
                    course["description"]
                    or "No description provided."
                )

                st.caption(
                    f"Skills: {course['skills'] or 'Not specified'} · "
                    f"Duration: {course['duration_hours']} hours"
                )

                if st.button(
                    "Enroll",
                    key=f"enroll_{course['course_id']}"
                ):

                    with _connect(db_path) as conn:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO employee_course_enrollments
                            (course_id, employee_id)
                            VALUES (?, ?)
                            """,
                            (course["course_id"], employee_id),
                        )

                    st.success("Enrollment successful.")
                    st.rerun()

    st.subheader("My learning progress")

    enrollments = _get_enrollments(db_path, employee_id)

    if not enrollments:
        st.info("You have not enrolled in any course yet.")
        return

    for enrollment in enrollments:

        with st.container(border=True):

            st.markdown(f"**{enrollment['course_title']}**")

            st.progress(
                int(enrollment["progress"]) / 100
            )

            st.caption(
                f"Current status: {enrollment['status']} · "
                f"{enrollment['progress']}%"
            )

            with st.form(
                f"progress_form_{enrollment['enrollment_id']}"
            ):

                new_progress = st.slider(
                    "Update progress",
                    min_value=0,
                    max_value=100,
                    value=int(enrollment["progress"]),
                    step=5,
                    key=f"progress_slider_{enrollment['enrollment_id']}",
                )

                save_progress = st.form_submit_button(
                    "Save progress"
                )

                if save_progress:

                    status = (
                        "Completed" if new_progress == 100
                        else "In Progress" if new_progress > 0
                        else "Not Started"
                    )

                    with _connect(db_path) as conn:
                        conn.execute(
                            """
                            UPDATE employee_course_enrollments
                            SET progress = ?, status = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE enrollment_id = ?
                            AND employee_id = ?
                            """,
                            (
                                int(new_progress),
                                status,
                                enrollment["enrollment_id"],
                                employee_id,
                            ),
                        )

                    st.success("Progress updated.")
                    st.rerun()

            if enrollment["status"] == "Completed":

                st.caption(
                    "Upload your course completion certificate (PDF, PNG or JPG)."
                )

                uploaded = st.file_uploader(
                    "Certificate",
                    type=["pdf", "png", "jpg", "jpeg"],
                    key=f"certificate_{enrollment['enrollment_id']}",
                )

                if uploaded is not None:

                    cert_dir = (
                        Path(db_path).resolve().parent.parent
                        / "uploads"
                        / "certificates"
                    )

                    cert_dir.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    safe_name = (
                        Path(uploaded.name).name.replace(" ", "_")
                    )

                    cert_name = (
                        f"{employee_id}_"
                        f"{enrollment['enrollment_id']}_"
                        f"{safe_name}"
                    )

                    cert_path = cert_dir / cert_name

                    cert_path.write_bytes(
                        uploaded.getvalue()
                    )

                    with _connect(db_path) as conn:
                        conn.execute(
                            """
                            UPDATE employee_course_enrollments
                            SET certificate_name = ?,
                                certificate_path = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE enrollment_id = ?
                            AND employee_id = ?
                            """,
                            (
                                uploaded.name,
                                str(cert_path),
                                enrollment["enrollment_id"],
                                employee_id,
                            ),
                        )

                    st.success("Certificate uploaded.")
                    st.rerun()

                if enrollment["certificate_path"]:

                    cert_path = Path(
                        enrollment["certificate_path"]
                    )

                    if cert_path.is_file():

                        st.download_button(
                            "Download certificate",
                            data=cert_path.read_bytes(),
                            file_name=(
                                enrollment["certificate_name"]
                                or cert_path.name
                            ),
                            key=(
                                f"download_certificate_"
                                f"{enrollment['enrollment_id']}"
                            ),
                        )
