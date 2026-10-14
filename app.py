
import streamlit as st
import pandas as pd
from services.core import init_db, save_employee, list_employees, delete_employee

st.set_page_config(
    page_title="Talent Management Platform",
    page_icon="👥",
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
            f"{r['employee_id']} — {r['employee_name']}"
            for r in rows
        ]
    )

    if selected != "Select Employee":
        if st.button("Delete Selected Employee"):
            delete_employee(selected.split(" — ", 1)[0])
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
