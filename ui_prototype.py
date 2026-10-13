import streamlit as st

st.set_page_config(page_title="TalentSphere | Career Growth", page_icon="🎯", layout="wide")

st.markdown("""
<style>
.stApp {background:#0b1020}
[data-testid="stSidebar"] {background:#111827}
[data-testid="stSidebar"] * {color:#eef2ff}
.hero {padding:1.4rem 1.6rem;border-radius:18px;background:linear-gradient(120deg,#172554,#312e81,#164e63);border:1px solid #334155;margin-bottom:1.2rem}
.hero h1 {color:white;margin-bottom:.3rem}
.hero p {color:#dbeafe;margin-bottom:0}
div[data-testid="stMetric"] {background:#111827;border:1px solid #263449;padding:16px;border-radius:14px}
</style>
""", unsafe_allow_html=True)

DEFAULT_EMPLOYEE = {
    "name": "Harsh Sharma", "email": "harsh.sharma@example.com",
    "employee_id": "EMP001", "department": "Data Science",
    "designation": "Data Science Trainee", "experience": 1,
    "interests": "Data Science, Machine Learning, AI",
    "profile_completion": 80, "career_progress": 60
}
if "employee" not in st.session_state:
    st.session_state.employee = DEFAULT_EMPLOYEE.copy()
if "skills" not in st.session_state:
    st.session_state.skills = [
        {"name":"Python","level":"Intermediate","progress":70},
        {"name":"SQL","level":"Intermediate","progress":65},
        {"name":"Data Analysis","level":"Intermediate","progress":60},
        {"name":"Communication","level":"Beginner","progress":45},
    ]
if "goals" not in st.session_state:
    st.session_state.goals = [
        {"name":"Complete a Machine Learning course","progress":50},
        {"name":"Build a portfolio project","progress":35},
        {"name":"Improve presentation skills","progress":25},
    ]

employee = st.session_state.employee
st.sidebar.markdown("# 🎯 TalentSphere")
st.sidebar.caption("Employee Performance & Career Growth")
st.sidebar.divider()
page = st.sidebar.radio("NAVIGATION", [
    "Login / Registration", "Dashboard", "Employee Profile",
    "Skills & Goals", "Career Development"
])
st.sidebar.divider()
st.sidebar.markdown("**Employee profile**")
st.sidebar.write(f"👤 {employee['name']}")
st.sidebar.caption("Employee Career Platform")

if page == "Login / Registration":
    st.markdown("""<div class="hero"><h1>Welcome to TalentSphere 👋</h1>
    <p>Your skills, goals, and next career opportunity — all in one place.</p></div>""", unsafe_allow_html=True)
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        st.subheader("Grow with purpose")
        st.write("Track your skills, plan career goals, and explore learning opportunities.")
        st.write("✨ Review your career dashboard")
        st.write("🧠 Track skills and proficiency")
        st.write("🎯 Monitor goals and progress")
        st.write("🚀 Plan your next career step")
        st.info("Authentication is not connected yet.")
    with right:
        login_tab, register_tab = st.tabs(["🔐 Login", "📝 Register"])
        with login_tab:
            with st.form("login_form"):
                login_email = st.text_input("Email address", placeholder="you@example.com")
                login_password = st.text_input("Password", type="password")
                login_submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            if login_submit:
                if login_email.strip() and login_password:
                    st.success("Login form validated. Authentication will be connected later.")
                else:
                    st.warning("Please enter both email and password.")
        with register_tab:
            with st.form("register_form"):
                reg_name = st.text_input("Full name")
                reg_email = st.text_input("Email address")
                reg_password = st.text_input("Create password", type="password")
                register_submit = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if register_submit:
                if reg_name.strip() and reg_email.strip() and reg_password:
                    st.success("Registration form validated. Account creation will be connected later.")
                else:
                    st.warning("Please complete all fields.")

elif page == "Dashboard":
    st.markdown(f"""<div class="hero"><h1>Good to see you, {employee['name']}! 👋</h1>
    <p>Here is your career growth overview. Keep learning and moving forward.</p></div>""", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profile Completion", f"{employee['profile_completion']}%")
    c2.metric("Skills Tracked", len(st.session_state.skills))
    c3.metric("Career Progress", f"{employee['career_progress']}%")
    c4.metric("Active Goals", len(st.session_state.goals))
    st.subheader("Your progress")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("**Profile completion**")
        st.progress(employee["profile_completion"] / 100)
        st.caption(f"{employee['profile_completion']}% complete")
    with p2:
        st.markdown("**Career development**")
        st.progress(employee["career_progress"] / 100)
        st.caption(f"{employee['career_progress']}% of your sample plan")
    st.subheader("Skills snapshot")
    cols = st.columns(4)
    for col, skill in zip(cols, st.session_state.skills[:4]):
        with col:
            st.markdown(f"**{skill['name']}**")
            st.caption(skill["level"])
            st.progress(skill["progress"] / 100)
            st.caption(f"{skill['progress']}% proficiency")
    st.subheader("Recent goals")
    for goal in st.session_state.goals:
        st.write(f"**{goal['name']}** — {goal['progress']}%")
        st.progress(goal["progress"] / 100)

elif page == "Employee Profile":
    st.markdown('<div class="hero"><h1>Employee Profile</h1><p>Review and update your professional information.</p></div>', unsafe_allow_html=True)
    departments = ["Data Science", "Engineering", "Information Technology", "Human Resources", "Finance", "Marketing", "Other"]
    with st.form("profile_form"):
        a, b = st.columns(2)
        with a:
            name = st.text_input("Full name", value=employee["name"])
            email = st.text_input("Email", value=employee["email"])
            emp_id = st.text_input("Employee ID", value=employee["employee_id"])
        with b:
            department = st.selectbox("Department", departments, index=departments.index(employee["department"]) if employee["department"] in departments else 0)
            designation = st.text_input("Designation", value=employee["designation"])
            experience = st.number_input("Years of experience", min_value=0, max_value=60, value=int(employee["experience"]))
        interests = st.text_area("Career interests", value=employee["interests"])
        save_profile = st.form_submit_button("Save profile changes", type="primary")
    if save_profile:
        if name.strip() and email.strip() and emp_id.strip() and designation.strip():
            st.session_state.employee.update({"name":name.strip(),"email":email.strip(),"employee_id":emp_id.strip(),"department":department,"designation":designation,"experience":experience,"interests":interests.strip()})
            st.success("Profile updated for this session.")
            st.rerun()
        else:
            st.error("Please complete the required fields.")
    st.subheader("Profile completion")
    st.progress(employee["profile_completion"] / 100)
    st.caption(f"{employee['profile_completion']}% complete")

elif page == "Skills & Goals":
    st.markdown('<div class="hero"><h1>Skills & Goals</h1><p>Understand your strengths and keep your goals moving.</p></div>', unsafe_allow_html=True)
    st.subheader("Current skills")
    for skill in st.session_state.skills:
        with st.container(border=True):
            st.markdown(f"**{skill['name']}** · {skill['level']}")
            st.progress(skill["progress"] / 100)
            st.caption(f"{skill['progress']}% proficiency")
    with st.expander("➕ Add a skill"):
        with st.form("add_skill_form"):
            new_skill = st.text_input("Skill name", placeholder="e.g. Machine Learning")
            level = st.selectbox("Proficiency level", ["Beginner", "Intermediate", "Advanced"])
            progress = st.slider("Current proficiency", 0, 100, 40)
            add_skill = st.form_submit_button("Add skill", type="primary")
        if add_skill:
            if not new_skill.strip():
                st.warning("Enter a skill name.")
            elif any(s["name"].casefold() == new_skill.strip().casefold() for s in st.session_state.skills):
                st.warning("This skill is already listed.")
            else:
                st.session_state.skills.append({"name":new_skill.strip(),"level":level,"progress":progress})
                st.success("Skill added successfully.")
                st.rerun()
    st.subheader("Career goals")
    for goal in st.session_state.goals:
        st.write(f"**{goal['name']}**")
        st.progress(goal["progress"] / 100)
        st.caption(f"{goal['progress']}% complete")
    with st.expander("➕ Add a career goal"):
        with st.form("add_goal_form"):
            goal_name = st.text_input("Goal title")
            goal_progress = st.slider("Goal progress", 0, 100, 0)
            add_goal = st.form_submit_button("Add goal", type="primary")
        if add_goal:
            if goal_name.strip():
                st.session_state.goals.append({"name":goal_name.strip(),"progress":goal_progress})
                st.success("Goal added successfully.")
                st.rerun()
            else:
                st.warning("Enter a goal title.")

elif page == "Career Development":
    st.markdown('<div class="hero"><h1>Career Development 🚀</h1><p>Build a practical learning path toward your target role.</p></div>', unsafe_allow_html=True)
    target_role = st.selectbox("Target career role", ["Data Scientist","Machine Learning Engineer","Data Analyst","Software Developer","AI Engineer"])
    st.markdown(f"### Your target: {target_role}")
    areas = [
        ("Python & problem solving","Practice coding, functions, data structures, and clean code."),
        ("Statistics & machine learning","Learn statistics, model evaluation, and ML workflows."),
        ("SQL & data handling","Practice joins, aggregation, cleaning, and data preparation."),
        ("Projects & communication","Build portfolio projects and explain your results clearly."),
    ]
    st.subheader("Development areas")
    for title, description in areas:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(description)
    st.subheader("Suggested learning activities")
    a1 = st.checkbox("Complete one relevant online course")
    a2 = st.checkbox("Build and document a portfolio project")
    a3 = st.checkbox("Practice explaining a project in 3 minutes")
    done = sum([a1, a2, a3])
    st.progress(done / 3)
    st.caption(f"{done} of 3 activities completed in this session")
    st.subheader("Recommended learning")
    st.markdown("- Python: core concepts and data structures")
    st.markdown("- SQL: query practice and database fundamentals")
    st.markdown("- Machine Learning: training, validation, and evaluation")
    st.info("Learning recommendations for your career development.")

st.sidebar.divider()
st.sidebar.caption("TalentSphere • Career Growth Platform")
st.caption("Login, registration, and profile data are not connected to a backend yet.")
