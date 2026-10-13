from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def create_report(profile, skills, analysis, gaps, recommendations, assessments, progress):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    y = 800

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(45, y, "TalentSphere Career Growth Report")
    y -= 30

    pdf.setFont("Helvetica", 10)

    lines = [
        f"Profile completion: {analysis.get('completion', 0)}%",
        f"Profile strength: {analysis.get('score', 0)}/100",
        "",
        "Skills: " + ", ".join(
            skill.get("name", "") for skill in skills
        ),
        "",
        "Skill gaps:"
    ]

    for gap in gaps:
        lines.append(
            f"- {gap.get('skill', '')}: "
            f"gap {gap.get('gap', 0)} "
            f"({gap.get('priority', 'Normal')})"
        )

    for line in lines:
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = 800

        pdf.drawString(45, y, line[:110])
        y -= 16

    pdf.save()

    return buffer.getvalue()