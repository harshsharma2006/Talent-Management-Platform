# Talent Management Platform for Employee Performance and Career Growth

## Project Overview
TalentSphere is a Python and Streamlit-based platform prototype designed to support employee profile management, skills tracking, goal setting, and career development.

## Features
- Login / Registration interface
- Dashboard with profile summary and career progress
- Employee Profile management interface
- Skills & Goals tracking
- Career Development with target roles and learning activities
- Employee management with SQLite backend in the separate employee-management application

## Technologies Used
- Python
- Streamlit
- SQLite
- Git and GitHub

## Project Files
- `app.py` — Employee management application
- `ui_prototype.py` — Five-screen TalentSphere UI/UX prototype
- `services/` — Backend and service functions
- `data/` — Local database storage, where configured
- `requirements.txt` — Python dependencies

## Run the Application

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the TalentSphere UI prototype:

```bash
python -m streamlit run ui_prototype.py
```

Run the employee management application:

```bash
python -m streamlit run app.py
```

## Current Scope
The five-screen UI prototype includes Login / Registration, Dashboard, Employee Profile, Skills & Goals, and Career Development. Real authentication and database integration for the UI prototype are planned for a later phase.

## Author
Harsh Sharma

## GitHub Repository
https://github.com/harshsharma2006/Talent-Management-Platform