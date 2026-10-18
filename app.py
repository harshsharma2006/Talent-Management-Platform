
import streamlit as st
import pandas as pd
from services.core import init_db, save_employee, list_employees, delete_employee

st.set_page_config(
    page_title="Talent Management Platform",
    page_icon="ðŸ‘¥",
    layout="wide"
)

init_db()

st.title("Talent Management Platform")
st.caption("Employee Management")
st.divider()

st.header("Create Employee Profile")

with st.form("employee_form"):
    left, right = st.columns(2)

    with left:
        name = st.text_input("Employee Name *")
        emp_id = st.text_input("Employee ID *")
        dept = st.selectbox(
            "Department *",
            [
                "Select Department", "Data Science", "Engineering",
                "Human Resources", "Finance", "Marketing", "Sales",
                "Operations", "IT", "Other"
            ]
        )

    with right:
        designation = st.text_input("Designation *")
        experience = st.number_input(
            "Years of Experience *",
            min_value=0.0,
            max_value=60.0,
            value=0.0,
            step=0.5
        )
        skills = st.text_input("Primary Skills *")

    a, b = st.columns(2)
    save = a.form_submit_button(
        "Save Employee", type="primary", use_container_width=True
    )
    clear = b.form_submit_button(
        "Clear Form", use_container_width=True
    )

if clear:
    st.rerun()

if save:
    if not name.strip() or not emp_id.strip() or not designation.strip() or not skills.strip():
        st.error("Please complete all required fields.")
    elif dept == "Select Department":
        st.error("Please select a department.")
    else:
        ok, msg = save_employee(
            emp_id.strip(), name.strip(), dept,
            designation.strip(), experience, skills.strip()
        )
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

st.divider()
st.header("Saved Employees")

rows = list_employees()

if rows:
    df = pd.DataFrame(rows)
    df.columns = [
        "Employee ID", "Employee Name", "Department",
        "Designation", "Years of Experience",
        "Primary Skills", "Created At"
    ]

    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"Total employees: {len(df)}")

    st.download_button(
        "Download Employee Data CSV",
        df.to_csv(index=False).encode("utf-8"),
        "employees.csv",
        "text/csv"
    )

    selected = st.selectbox(
        "Delete Employee",
        ["Select Employee"] + [
            f"{r['employee_id']} - {r['employee_name']}"
            for r in rows
        ]
    )

    if selected != "Select Employee":
        if st.button("Delete Selected Employee"):
            delete_employee(selected.split(" - ", 1)[0])
            st.success("Employee deleted.")
            st.rerun()
else:
    st.info("No employees saved yet. Add an employee using the form above.")


# PERFORMANCE_REVIEWS_MODULE
from services.performance_service import (
    initialize_reviews,
    add_review,
    list_reviews,
    employee_average_rating,
)

initialize_reviews()

st.divider()
st.header("Performance Reviews")

employees = list_employees()

if not employees:
    st.info("Add an employee before creating a performance review.")
else:
    employee_options = {
        f"{employee['employee_id']} - {employee['employee_name']}": employee["employee_id"]
        for employee in employees
    }

    selected_employee = st.selectbox(
        "Select Employee for Review",
        list(employee_options.keys()),
        key="review_employee",
    )
    employee_id = employee_options[selected_employee]

    summary = employee_average_rating(employee_id)
    metric_col1, metric_col2 = st.columns(2)

    with metric_col1:
        average = summary.get("average_rating")
        st.metric("Average Rating", f"{average:.1f}/5" if average is not None else "Not rated")

    with metric_col2:
        st.metric("Total Reviews", summary.get("review_count", 0))

    with st.form("performance_review_form"):
        rating = st.slider("Performance Rating", 1, 5, 3)
        achievements = st.text_area("Achievements *")
        improvement_areas = st.text_area("Areas for Improvement")
        reviewer = st.text_input("Reviewer Name *")
        submit_review = st.form_submit_button("Save Performance Review", type="primary")

    if submit_review:
        ok, message = add_review(
            employee_id,
            rating,
            achievements,
            improvement_areas,
            reviewer,
        )
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    st.subheader("Review History")
    reviews = list_reviews(employee_id)

    if reviews:
        review_df = pd.DataFrame(reviews)
        review_df = review_df.rename(columns={
            "review_id": "Review ID",
            "employee_id": "Employee ID",
            "rating": "Rating",
            "achievements": "Achievements",
            "improvement_areas": "Areas for Improvement",
            "reviewer": "Reviewer",
            "review_date": "Review Date",
        })
        st.dataframe(review_df, use_container_width=True, hide_index=True)
    else:
        st.info("No performance reviews recorded for this employee yet.")


# PERFORMANCE_DASHBOARD_MODULE
st.divider()
st.header("Employee Performance Dashboard")

dashboard_employees = list_employees()
dashboard_reviews = list_reviews()

if dashboard_employees:
    employee_df = pd.DataFrame(dashboard_employees)

    ratings = [
        review for review in dashboard_reviews
        if review.get("rating") is not None
    ]

    average_rating = (
        sum(float(review["rating"]) for review in ratings) / len(ratings)
        if ratings else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Employees", len(dashboard_employees))
    col2.metric("Average Performance Rating", f"{average_rating:.1f}/5" if ratings else "Not rated")
    col3.metric("Total Performance Reviews", len(ratings))

    st.subheader("Department-wise Employee Distribution")
    department_counts = (
        employee_df.groupby("department")
        .size()
        .sort_values(ascending=False)
    )
    st.bar_chart(department_counts, x_label="Department", y_label="Employee Count")

    if ratings:
        review_df = pd.DataFrame(ratings)
        review_df["rating"] = pd.to_numeric(review_df["rating"], errors="coerce")
        review_df = review_df.dropna(subset=["rating"])

        employee_names = {
            employee["employee_id"]: employee["employee_name"]
            for employee in dashboard_employees
        }

        performance = (
            review_df.groupby("employee_id")["rating"]
            .agg(["mean", "count"])
            .reset_index()
        )
        performance["Employee Name"] = performance["employee_id"].map(employee_names)
        performance = performance.rename(columns={
            "mean": "Average Rating",
            "count": "Review Count",
        })
        performance = performance[
            ["Employee Name", "Average Rating", "Review Count"]
        ].sort_values("Average Rating", ascending=False)

        st.subheader("Employee Performance Comparison")
        chart_data = performance.set_index("Employee Name")[["Average Rating"]]
        st.bar_chart(chart_data, y_label="Rating (out of 5)")
        st.dataframe(performance, use_container_width=True, hide_index=True)

        st.subheader("Top-Performing Employees")
        st.dataframe(
            performance.head(5),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Save performance reviews to view employee ratings and rankings.")
else:
    st.info("Add employees to populate the dashboard.")


# PDF_PERFORMANCE_REPORT_MODULE
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

st.divider()
st.header("Download Employee Performance Report")

report_employees = list_employees()

if report_employees:
    report_options = {
        f"{e['employee_id']} - {e['employee_name']}": e
        for e in report_employees
    }

    report_choice = st.selectbox(
        "Choose Employee for PDF Report",
        list(report_options.keys()),
        key="pdf_report_employee",
    )
    report_employee = report_options[report_choice]
    report_reviews = list_reviews(report_employee["employee_id"])

    if report_reviews:
        report_average = sum(
            float(r["rating"]) for r in report_reviews
        ) / len(report_reviews)
    else:
        report_average = None

    st.write(f"Employee: **{report_employee['employee_name']}**")
    st.write(
        "Average rating: "
        + (f"**{report_average:.1f}/5**" if report_average is not None else "**Not rated**")
    )
    st.write(f"Reviews available: **{len(report_reviews)}**")

    if st.button("Generate PDF Report", type="primary"):
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.65 * inch,
            bottomMargin=0.65 * inch,
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Employee Performance Report", styles["Title"]),
            Spacer(1, 14),
            Paragraph("Employee Details", styles["Heading2"]),
        ]

        employee_data = [
            ["Employee ID", str(report_employee["employee_id"])],
            ["Name", str(report_employee["employee_name"])],
            ["Department", str(report_employee["department"])],
            ["Designation", str(report_employee["designation"])],
            ["Experience", f"{report_employee['years_experience']} years"],
            ["Primary Skills", str(report_employee["primary_skills"])],
            ["Average Rating", f"{report_average:.1f}/5" if report_average is not None else "Not rated"],
            ["Total Reviews", str(len(report_reviews))],
        ]

        details_table = Table(employee_data, colWidths=[1.6 * inch, 4.8 * inch])
        details_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ]))
        story.extend([details_table, Spacer(1, 18)])

        story.append(Paragraph("Performance Review History", styles["Heading2"]))

        if report_reviews:
            review_data = [[
                "Date", "Rating", "Reviewer",
                "Achievements", "Areas for Improvement"
            ]]

            for review in report_reviews:
                review_data.append([
                    str(review.get("review_date") or ""),
                    str(review.get("rating") or ""),
                    str(review.get("reviewer") or ""),
                    str(review.get("achievements") or ""),
                    str(review.get("improvement_areas") or ""),
                ])

            review_table = Table(
                review_data,
                colWidths=[0.85 * inch, 0.5 * inch, 0.85 * inch,
                           2.0 * inch, 2.0 * inch],
                repeatRows=1,
            )
            review_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24476B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(review_table)
        else:
            story.append(Paragraph(
                "No performance reviews have been recorded for this employee.",
                styles["BodyText"],
            ))

        document.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        safe_employee_id = "".join(
            char for char in str(report_employee["employee_id"])
            if char.isalnum() or char in "-_"
        ) or "employee"

        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name=f"performance_report_{safe_employee_id}.pdf",
            mime="application/pdf",
            key="download_performance_pdf",
        )
else:
    st.info("Add an employee before generating a performance report.")

import sqlite3
from pathlib import Path

CAREER_DB_PATH = Path(__file__).resolve().parent / "data" / "talentsphere_healthy.db"

CAREER_ROLE_CATALOG = {
    "Data Analyst": {"Python": 2, "SQL": 2, "Pandas": 2, "Excel": 1},
    "Data Scientist": {"Python": 3, "SQL": 2, "Pandas": 3, "Machine Learning": 2},
    "Software Engineer": {"Python": 2, "Git": 2, "SQL": 1},
}
CAREER_LEVELS = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Expert": 4}

def init_employee_career_tables():
    CAREER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(CAREER_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employee_career_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Technical',
                proficiency TEXT NOT NULL,
                years REAL NOT NULL DEFAULT 0,
                UNIQUE(employee_id, skill_name)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employee_career_goals (
                employee_id TEXT PRIMARY KEY,
                target_role TEXT NOT NULL,
                career_goal TEXT DEFAULT '',
                timeline TEXT DEFAULT ''
            )
        """)

def get_employee_career_skills(employee_id):
    with sqlite3.connect(CAREER_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM employee_career_skills WHERE employee_id=? ORDER BY skill_name",
            (employee_id,)
        ).fetchall()
    return [dict(row) for row in rows]

def add_employee_career_skill(employee_id, skill_name, category, proficiency, years):
    try:
        with sqlite3.connect(CAREER_DB_PATH) as conn:
            conn.execute("""
                INSERT INTO employee_career_skills
                (employee_id, skill_name, category, proficiency, years)
                VALUES (?, ?, ?, ?, ?)
            """, (employee_id, skill_name.strip(), category, proficiency, years))
        return True, "Skill added successfully."
    except sqlite3.IntegrityError:
        return False, "This skill is already saved for the selected employee."

def delete_employee_career_skill(skill_id, employee_id):
    with sqlite3.connect(CAREER_DB_PATH) as conn:
        conn.execute(
            "DELETE FROM employee_career_skills WHERE id=? AND employee_id=?",
            (skill_id, employee_id)
        )

def get_employee_career_goal(employee_id):
    with sqlite3.connect(CAREER_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM employee_career_goals WHERE employee_id=?", (employee_id,)
        ).fetchone()
    return dict(row) if row else {}

def save_employee_career_goal(employee_id, target_role, career_goal, timeline):
    with sqlite3.connect(CAREER_DB_PATH) as conn:
        conn.execute("""
            INSERT INTO employee_career_goals(employee_id, target_role, career_goal, timeline)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(employee_id) DO UPDATE SET
                target_role=excluded.target_role,
                career_goal=excluded.career_goal,
                timeline=excluded.timeline
        """, (employee_id, target_role, career_goal.strip(), timeline))

init_employee_career_tables()

st.divider()
st.header("Career Growth & Skill Gap Analysis")
st.caption("Create an employee-specific career goal, track skills, and compare skills against a target role.")

career_employees = list_employees()

if not career_employees:
    st.info("Add an employee first to use Career Growth.")
else:
    career_employee_options = {
        f"{e['employee_id']} - {e['employee_name']}": e for e in career_employees
    }
    career_selected_label = st.selectbox(
        "Select employee for career planning",
        list(career_employee_options.keys()),
        key="career_employee_selector"
    )
    career_employee = career_employee_options[career_selected_label]
    career_employee_id = career_employee["employee_id"]

    st.subheader("1. Career Goal")
    saved_goal = get_employee_career_goal(career_employee_id)
    role_names = list(CAREER_ROLE_CATALOG.keys())
    saved_role = saved_goal.get("target_role", role_names[0])
    role_index = role_names.index(saved_role) if saved_role in role_names else 0

    with st.form("career_goal_form"):
        target_role = st.selectbox("Target role", role_names, index=role_index)
        career_goal_text = st.text_area(
            "Career goal",
            value=saved_goal.get("career_goal", ""),
            placeholder="Example: Become a Data Analyst and build strong SQL and reporting skills."
        )
        career_timeline = st.selectbox(
            "Target timeline",
            ["3 months", "6 months", "12 months", "18 months", "2 years"],
            index=["3 months", "6 months", "12 months", "18 months", "2 years"].index(
                saved_goal.get("timeline", "6 months")
            ) if saved_goal.get("timeline", "6 months") in
                 ["3 months", "6 months", "12 months", "18 months", "2 years"] else 1
        )
        save_career_goal = st.form_submit_button("Save Career Goal", type="primary")

    if save_career_goal:
        clean_goal = career_goal_text.strip()
        prefix = "Career goal mein likho:"

        if clean_goal.lower().startswith(prefix.lower()):
            clean_goal = clean_goal[len(prefix):].strip()

        save_employee_career_goal(
            career_employee_id, target_role, clean_goal, career_timeline
        )
        st.success("Career goal saved.")
        st.rerun()

    st.subheader("2. Employee Skills")
    with st.form("career_skill_form"):
        skill_name = st.text_input("Skill name", placeholder="e.g., Python")
        skill_category = st.selectbox(
            "Category", ["Technical", "Communication", "Leadership", "Analytical", "Other"]
        )
        skill_proficiency = st.selectbox("Proficiency", list(CAREER_LEVELS.keys()))
        skill_years = st.number_input(
            "Years using this skill", min_value=0.0, max_value=60.0, step=0.5, value=0.0
        )
        add_skill_clicked = st.form_submit_button("Add Skill")

    if add_skill_clicked:
        if not skill_name.strip():
            st.error("Enter a skill name.")
        else:
            added, add_message = add_employee_career_skill(
                career_employee_id, skill_name, skill_category, skill_proficiency, skill_years
            )
            if added:
                st.success(add_message)
                st.rerun()
            else:
                st.warning(add_message)

    career_skills = get_employee_career_skills(career_employee_id)
    if career_skills:
        career_skill_df = pd.DataFrame(career_skills).rename(columns={
            "skill_name": "Skill",
            "category": "Category",
            "proficiency": "Proficiency",
            "years": "Years of Experience",
            "id": "Skill Record ID",
            "employee_id": "Employee ID"
        })
        st.dataframe(
            career_skill_df[["Skill Record ID", "Skill", "Category", "Proficiency", "Years of Experience"]],
            use_container_width=True,
            hide_index=True
        )
        skill_to_delete = st.selectbox(
            "Select skill record to delete",
            ["Select skill"] + [
                f"{s['id']} - {s['skill_name']} ({s['proficiency']})" for s in career_skills
            ],
            key="career_skill_delete_selector"
        )
        if skill_to_delete != "Select skill" and st.button("Delete Selected Skill"):
            delete_employee_career_skill(int(skill_to_delete.split(" - ", 1)[0]), career_employee_id)
            st.success("Skill deleted.")
            st.rerun()
    else:
        st.info("No career skills added yet. Add skills above to see the analysis.")

    st.subheader("3. Role Match & Skill Gaps")
    current_goal = get_employee_career_goal(career_employee_id)
    analysis_role = current_goal.get("target_role", "Data Analyst")
    required_skills = CAREER_ROLE_CATALOG[analysis_role]
    current_levels = {
        s["skill_name"].strip().lower(): CAREER_LEVELS.get(s["proficiency"], 1)
        for s in career_skills
    }
    role_match_percent = round(
        sum(min(current_levels.get(skill.lower(), 0) / required_level, 1)
            for skill, required_level in required_skills.items())
        / len(required_skills) * 100
    )
    match_col, skill_col = st.columns(2)
    match_col.metric(f"Estimated match: {analysis_role}", f"{role_match_percent}%")
    skill_col.metric("Skills recorded", len(career_skills))
    st.progress(role_match_percent / 100)

    gap_rows = []
    for required_skill, required_level in required_skills.items():
        current_level = current_levels.get(required_skill.lower(), 0)
        gap = max(0, required_level - current_level)
        gap_rows.append({
            "Required Skill": required_skill,
            "Current Level": (
                next((label for label, level in CAREER_LEVELS.items() if level == current_level), "Not added")
                if current_level else "Not added"
            ),
            "Target Level": next(label for label, level in CAREER_LEVELS.items() if level == required_level),
            "Gap": gap,
            "Priority": "High" if gap >= 2 else ("Medium" if gap == 1 else "Ready")
        })
    st.dataframe(pd.DataFrame(gap_rows), use_container_width=True, hide_index=True)
    st.caption("Role match is a simple rule-based estimate based on the selected role's required skills, not an AI prediction.")
st.divider()
st.header("Career Roadmap & Learning Recommendations")
st.caption(
    "A practical learning plan based on the employee's saved target role "
    "and recorded skills. Recommendations are rule-based."
)

# These variables/functions are created by the existing Career Growth module:
# CAREER_ROLE_CATALOG, CAREER_LEVELS, get_employee_career_goal,
# get_employee_career_skills, list_employees.

roadmap_employees = list_employees()

if not roadmap_employees:
    st.info("Add an employee first to build a career roadmap.")
else:
    roadmap_employee_options = {
        f"{e['employee_id']} - {e['employee_name']}": e
        for e in roadmap_employees
    }
    roadmap_selected_label = st.selectbox(
        "Choose employee for roadmap",
        list(roadmap_employee_options.keys()),
        key="roadmap_employee_selector"
    )
    roadmap_employee = roadmap_employee_options[roadmap_selected_label]
    roadmap_employee_id = roadmap_employee["employee_id"]

    roadmap_goal = get_employee_career_goal(roadmap_employee_id)
    roadmap_role = roadmap_goal.get("target_role", "Data Analyst")
    roadmap_timeline = roadmap_goal.get("timeline", "6 months")
    roadmap_skills = get_employee_career_skills(roadmap_employee_id)

    # Ensure a valid role exists in the configured role catalog.
    if roadmap_role not in CAREER_ROLE_CATALOG:
        roadmap_role = list(CAREER_ROLE_CATALOG.keys())[0]

    required_for_roadmap = CAREER_ROLE_CATALOG[roadmap_role]
    current_for_roadmap = {
        s["skill_name"].strip().lower(): CAREER_LEVELS.get(s["proficiency"], 1)
        for s in roadmap_skills
    }

    roadmap_gaps = []
    for required_skill, required_level in required_for_roadmap.items():
        current_level = current_for_roadmap.get(required_skill.lower(), 0)
        if current_level < required_level:
            roadmap_gaps.append({
                "skill": required_skill,
                "current": current_level,
                "target": required_level,
                "gap": required_level - current_level
            })

    st.subheader(f"Roadmap for {roadmap_role}")
    info_col1, info_col2, info_col3 = st.columns(3)
    info_col1.metric("Target role", roadmap_role)
    info_col2.metric("Target timeline", roadmap_timeline)
    info_col3.metric("Skills to improve", len(roadmap_gaps))

    if not roadmap_goal:
        st.warning(
            "No career goal is saved for this employee yet. Go to the Career "
            "Growth section above and save a target role and timeline first."
        )

    if not roadmap_gaps:
        st.success(
            "All skills in this simple role checklist meet the configured target "
            "levels. Consider adding projects, certifications, and real work examples."
        )
    else:
        # Map the selected timeline to a reasonable number of learning phases.
        timeline_months = {
            "3 months": 3, "6 months": 6, "12 months": 12,
            "18 months": 18, "2 years": 24
        }.get(roadmap_timeline, 6)

        phase_count = min(4, max(1, timeline_months // 2))
        phases = [
            ("Phase 1 - Foundations", "Learn the basics and practise with small exercises."),
            ("Phase 2 - Practical Skills", "Complete guided exercises and work with real datasets."),
            ("Phase 3 - Projects", "Build a portfolio project and document your decisions."),
            ("Phase 4 - Job Readiness", "Polish the portfolio, revise interview topics, and practise explaining results.")
        ]
        active_phases = phases[:phase_count]

        st.subheader("Recommended action plan")
        roadmap_rows = []
        for index, gap_item in enumerate(roadmap_gaps):
            if gap_item["gap"] >= 2:
                level_action = "Start with fundamentals, then practise progressively."
                priority = "High"
            else:
                level_action = "Practise with a small project to reach the target level."
                priority = "Medium"

            skill_lower = gap_item["skill"].lower()
            resource_map = {
                "python": "https://docs.python.org/3/tutorial/",
                "sql": "https://www.sqlbolt.com/",
                "pandas": "https://pandas.pydata.org/docs/getting_started/",
                "excel": "https://support.microsoft.com/excel",
                "machine learning": "https://scikit-learn.org/stable/tutorial/",
                "git": "https://git-scm.com/doc",
            }
            resource = resource_map.get(skill_lower, "Search for a beginner course and practise with a small project.")

            roadmap_rows.append({
                "Priority": priority,
                "Skill to learn": gap_item["skill"],
                "Current level": (
                    next((label for label, level in CAREER_LEVELS.items()
                          if level == gap_item["current"]), "Not added")
                    if gap_item["current"] else "Not added"
                ),
                "Target level": next(
                    label for label, level in CAREER_LEVELS.items()
                    if level == gap_item["target"]
                ),
                "Next action": level_action,
                "Learning resource": resource
            })

        roadmap_df = pd.DataFrame(roadmap_rows)
        st.dataframe(roadmap_df, use_container_width=True, hide_index=True)

        st.subheader("Timeline milestones")
        for phase_title, phase_description in active_phases:
            with st.expander(phase_title, expanded=(phase_title == active_phases[0][0])):
                st.write(phase_description)
                if "Foundations" in phase_title:
                    st.write("Focus: understand the concepts behind your highest-priority skill gaps.")
                elif "Practical Skills" in phase_title:
                    st.write("Focus: practise weekly and save notes or exercises.")
                elif "Projects" in phase_title:
                    st.write("Focus: create one portfolio project that demonstrates the target skills.")
                else:
                    st.write("Focus: update your CV/portfolio and practise role-specific interview questions.")

        st.download_button(
            "Download Career Roadmap (CSV)",
            data=roadmap_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{roadmap_employee_id}_career_roadmap.csv",
            mime="text/csv"
        )

    st.caption(
        "Note: this roadmap uses the role requirements configured in the app. "
        "It is guidance, not an AI-generated assessment or a guarantee of job readiness."
    )


    # CAREER_GROWTH_PDF_REPORT_MODULE
    st.divider()
    st.header("Download Career Growth Report (PDF)")
    st.caption("Generate a PDF summary of this employee's career goal, skills, and roadmap.")

    from io import BytesIO
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )

    pdf_employee_options = {
        f"{e['employee_id']} - {e['employee_name']}": e
        for e in roadmap_employees
    }

    if pdf_employee_options:
        pdf_selected_label = st.selectbox(
            "Choose employee for career PDF",
            list(pdf_employee_options.keys()),
            key="career_pdf_employee_selector"
        )
        pdf_employee = pdf_employee_options[pdf_selected_label]
        pdf_employee_id = pdf_employee["employee_id"]

        pdf_goal = get_employee_career_goal(pdf_employee_id) or {}
        pdf_role = pdf_goal.get("target_role", "Not set")
        pdf_timeline = pdf_goal.get("timeline", "Not set")
        pdf_goal_text = (
            pdf_goal.get("career_goal")
            or pdf_goal.get("goal")
            or "No career goal description saved."
        )
        pdf_goal_text = str(pdf_goal_text).replace("Career goal mein likho: ", "").strip()
        pdf_skills = get_employee_career_skills(pdf_employee_id) or []

        pdf_buffer = BytesIO()    
        pdf_doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.65 * inch,
            bottomMargin=0.65 * inch
        )

        pdf_styles = getSampleStyleSheet()
        pdf_styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=pdf_styles["Title"],
            alignment=TA_CENTER,
            fontSize=19,
            leading=24,
            spaceAfter=14
        ))
        pdf_styles.add(ParagraphStyle(
            name="SectionHeading",
            parent=pdf_styles["Heading2"],
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=6
        ))
        pdf_styles.add(ParagraphStyle(
            name="SmallCell",
            parent=pdf_styles["BodyText"],
            fontSize=8,
            leading=10
        ))

        story = [
            Paragraph("Career Growth Report", pdf_styles["ReportTitle"]),
            Paragraph(
                f"<b>Employee:</b> {escape(str(pdf_employee.get('employee_name', '')))}",
                pdf_styles["BodyText"]
            ),
            Paragraph(
                f"<b>Employee ID:</b> {escape(str(pdf_employee_id))}",
                pdf_styles["BodyText"]
            ),
            Paragraph(
                f"<b>Department:</b> {escape(str(pdf_employee.get('department', 'Not available')))}",
                pdf_styles["BodyText"]
            ),
            Paragraph(
                f"<b>Designation:</b> {escape(str(pdf_employee.get('designation', 'Not available')))}",
                pdf_styles["BodyText"]
            ),
            Spacer(1, 10),
            Paragraph("Career Goal", pdf_styles["SectionHeading"]),
            Paragraph(f"<b>Target role:</b> {escape(str(pdf_role))}", pdf_styles["BodyText"]),
            Paragraph(f"<b>Target timeline:</b> {escape(str(pdf_timeline))}", pdf_styles["BodyText"]),
            Paragraph(f"<b>Goal:</b> {escape(str(pdf_goal_text))}", pdf_styles["BodyText"]),
            Spacer(1, 8),
            Paragraph("Recorded Skills", pdf_styles["SectionHeading"])
        ]

        skill_rows = [[
            Paragraph("<b>Skill</b>", pdf_styles["SmallCell"]),
            Paragraph("<b>Category</b>", pdf_styles["SmallCell"]),
            Paragraph("<b>Proficiency</b>", pdf_styles["SmallCell"]),
            Paragraph("<b>Years</b>", pdf_styles["SmallCell"])
        ]]

        for skill in pdf_skills:
            skill_rows.append([
                Paragraph(escape(str(skill.get("skill_name", ""))), pdf_styles["SmallCell"]),
                Paragraph(escape(str(skill.get("category", ""))), pdf_styles["SmallCell"]),
                Paragraph(escape(str(skill.get("proficiency", ""))), pdf_styles["SmallCell"]),
                Paragraph(escape(str(skill.get("years_experience") or skill.get("years_using_skill") or "N/A")), pdf_styles["SmallCell"])
            ])

        if len(skill_rows) == 1:
            skill_rows.append([
                Paragraph("No skills recorded", pdf_styles["SmallCell"]), "", "", ""
            ])

        skill_table = Table(skill_rows, colWidths=[2.0*inch, 1.5*inch, 1.5*inch, 1.0*inch], repeatRows=1)
        skill_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F1")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
        ]))
        story.append(skill_table)
        story.append(Spacer(1, 8))

        role_catalog = CAREER_ROLE_CATALOG
        if pdf_role in role_catalog:
            required_skills = role_catalog[pdf_role]
            current_levels = {
                str(s.get("skill_name", "")).strip().lower():
                CAREER_LEVELS.get(s.get("proficiency", ""), 0)
                for s in pdf_skills
            }
            missing_skills = [
                skill for skill, required_level in required_skills.items()
                if current_levels.get(skill.lower(), 0) < required_level
            ]
        else:
            missing_skills = []

        story.append(Paragraph("Skill Gap Analysis", pdf_styles["SectionHeading"]))
        story.append(Paragraph(
            f"<b>Skills to improve:</b> {len(missing_skills)}",
            pdf_styles["BodyText"]
        ))

        if missing_skills:
            for index, skill_name in enumerate(missing_skills, start=1):
                story.append(Paragraph(f"{index}. {escape(str(skill_name))}", pdf_styles["BodyText"]))
        else:
            story.append(Paragraph(
                "No gaps identified in the configured role checklist, or the target role is not set.",
                pdf_styles["BodyText"]
            ))

        story.append(Paragraph("Career Roadmap", pdf_styles["SectionHeading"]))
        story.append(Paragraph(
            "Phase 1 - Foundations: Review concepts and practise the highest-priority skill gaps.",
            pdf_styles["BodyText"]
        ))
        story.append(Paragraph(
            "Phase 2 - Practical Skills: Complete exercises and practise with realistic datasets or tasks.",
            pdf_styles["BodyText"]
        ))
        story.append(Paragraph(
            "Phase 3 - Projects: Build a portfolio project that demonstrates the target role's skills.",
            pdf_styles["BodyText"]
        ))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "Note: This report uses the skills and role requirements configured in the application. "
            "Recommendations are guidance and are not a guarantee of job readiness.",
            pdf_styles["Italic"]
        ))

        pdf_doc.build(story)
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()

        safe_id = "".join(
            char for char in str(pdf_employee_id)
            if char.isalnum() or char in "-_"
        ) or "employee"

        st.download_button(
            "Download Career Growth Report (PDF)",
            data=pdf_bytes,
            file_name=f"career_growth_report_{safe_id}.pdf",
            mime="application/pdf",
            key="download_career_growth_pdf"
        )
    else:
        st.info("Add an employee first to generate a career growth report.")



