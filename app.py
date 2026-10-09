
import streamlit as st
import pandas as pd
from services.core import init_db, save_employee, list_employees, delete_employee

st.set_page_config(page_title="Talent Management Platform - Day 3", page_icon="👥", layout="wide")
init_db()

st.title("Talent Management Platform")
st.caption("Day 3 — Employee Management Feature")
st.divider()

st.header("Create Employee Profile")

with st.form("employee_form"):
    left,right=st.columns(2)
    with left:
        name=st.text_input("Employee Name *",placeholder="e.g. Harsh Sharma")
        emp_id=st.text_input("Employee ID *",placeholder="e.g. EMP001")
        dept=st.selectbox("Department *",["Select Department","Data Science","Engineering","Human Resources","Finance","Marketing","Sales","Operations","IT","Other"])
    with right:
        designation=st.text_input("Designation *",placeholder="e.g. Data Analyst")
        experience=st.number_input("Years of Experience *",min_value=0.0,max_value=60.0,value=0.0,step=0.5)
        skills=st.text_input("Primary Skills *",placeholder="e.g. Python, SQL, Pandas")
    a,b=st.columns(2)
    save=a.form_submit_button("Save Employee",type="primary",use_container_width=True)
    clear=b.form_submit_button("Clear Form",use_container_width=True)

if clear: st.rerun()
if save:
    if dept=="Select Department":
        st.error("Please select a department.")
    else:
        ok,msg=save_employee(emp_id,name,dept,designation,experience,skills)
        if ok: st.success(msg); st.rerun()
        else: st.error(msg)

st.divider()
st.header("Saved Employees")
rows=list_employees()
if rows:
    df=pd.DataFrame(rows)
    df.columns=["Employee ID","Employee Name","Department","Designation","Years of Experience","Primary Skills","Created At"]
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.caption(f"Total employees: {len(df)} — stored in SQLite and available after refresh.")
    st.download_button("Download Employee Data CSV",df.to_csv(index=False).encode("utf-8"),"employees.csv","text/csv")
    selected=st.selectbox("Delete Employee (optional)",["Select Employee"]+[f"{r['employee_id']} — {r['employee_name']}" for r in rows])
    if selected!="Select Employee":
        if st.button("Delete Selected Employee"):
            delete_employee(selected.split(" — ",1)[0]); st.success("Employee deleted."); st.rerun()
else:
    st.info("No employees saved yet. Add an employee using the form above.")

with st.expander("Day 3 Testing Checklist"):
    st.markdown("- Save valid employee\n- Refresh and verify persistence\n- Try empty required fields\n- Try invalid experience\n- Try duplicate Employee ID\n- Confirm employee appears in table")
