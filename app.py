
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
