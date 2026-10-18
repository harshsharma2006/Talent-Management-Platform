\# Talent Management Platform for Employee Performance and Career Growth



A Streamlit-based application for managing employee information, tracking performance, and supporting career development.



\## Features



\- \*\*Employee Management:\*\* Add and manage employee records.

\- \*\*Performance Tracking:\*\* Review employee performance and display performance data.

\- \*\*Career Development:\*\* Record employee skills, define career goals, and identify skill gaps.

\- \*\*Learning Roadmaps:\*\* Generate phased development plans based on selected career goals and timelines.

\- \*\*PDF Reports:\*\* Download career-related reports.



\## Tech Stack



\- Python

\- Streamlit

\- Pandas

\- SQLite

\- ReportLab



\## Project Structure



```text

Talent-Management-Platform/

├── app.py

├── ui\_prototype.py

├── requirements.txt

├── README.md

├── services/

│   ├── core.py

│   ├── performance\_service.py

│   └── reports.py

└── data/

&#x20;   └── SQLite database files

```



\## Setup



1\. Clone or download this repository.

2\. Open the project folder in a terminal.

3\. Create and activate a Python virtual environment.

4\. Install the dependencies:



&#x20;  ```bash

&#x20;  pip install -r requirements.txt

&#x20;  ```



5\. Start the application:



&#x20;  ```bash

&#x20;  python -m streamlit run app.py

&#x20;  ```



6\. Open the local URL displayed in the terminal.



\## Notes



\- The application uses SQLite for data storage.

\- Keep database files and employee information protected.

\- Review configuration and security before deploying publicly.

\- `ui\_prototype.py` contains a separate UI prototype.



\## Status



This project is under active development. Features and documentation may change as the application evolves.



