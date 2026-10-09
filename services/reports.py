
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def create_report(profile, skills, analysis, gaps, recommendations, assessments, progress):
    buf=BytesIO(); c=canvas.Canvas(buf,pagesize=A4)
    y=800
    c.setFont("Helvetica-Bold",18); c.drawString(45,y,"TalentSphere Career Growth Report"); y-=30
    c.setFont("Helvetica",10)
    lines=[
        f"Profile completion: {analysis.get('completion',0)}%",
        f"Profile strength: {analysis.get('score',0)}/100",
        "",
        "Skills: "+", ".join(s.get("name","") for s in skills),
        "",
        "Skill gaps:"
    ]
    lines += [f"- {g['skill']}: gap {g['gap']} ({g['priority']})" for g in gaps]
    for line in lines:
        if y<50: c.showPage(); y=800
        c.drawString(45,y,line[:110]); y-=16
    c.save(); return buf.getvalue()
