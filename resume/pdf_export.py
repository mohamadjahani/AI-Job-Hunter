from io import BytesIO
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, KeepTogether
)

SECTION_HEADINGS = {
    "PROFESSIONAL SUMMARY", "PROFESSIONAL PROFILE",
    "TECHNICAL SKILLS", "TECHNICAL & PROFESSIONAL SKILLS",
    "PROFESSIONAL EXPERIENCE", "WORK EXPERIENCE",
    "EDUCATION", "EDUCATION & CERTIFICATES",
    "CYBERSECURITY EDUCATION",
    "CYBERSECURITY TRAINING & APPLIED PROJECTS",
    "CERTIFICATIONS", "SELECTED RECOGNITION",
    "SELECTED PROFESSIONAL TRAINING",
    "ADDITIONAL TECHNICAL PROJECTS", "LANGUAGES",
}

def format_inline(text):
    text = escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

def resume_to_pdf(markdown_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=46, rightMargin=46,
        topMargin=42, bottomMargin=42,
        title="Professional Resume",
    )

    normal = ParagraphStyle(
        "ResumeBody",
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    heading = ParagraphStyle(
        "ResumeSection",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        spaceBefore=10,
        spaceAfter=5,
        textColor=colors.HexColor("#17365D"),
        keepWithNext=True,
    )
    name_style = ParagraphStyle(
        "ResumeName",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=5,
    )
    bullet = ParagraphStyle(
        "ResumeBullet",
        parent=normal,
        leftIndent=13,
        firstLineIndent=-9,
        spaceAfter=3,
    )

    story = []
    first_line = True
    previous_blank = False

    for raw in markdown_text.splitlines():
        line = raw.strip()

        if not line:
            if story and not previous_blank:
                last = story[-1]
                if not (
                    isinstance(last, Paragraph)
                    and last.style.name == "ResumeJobTitle"
                ):
                    story.append(Spacer(1, 3))
            previous_blank = True
            continue

        previous_blank = False

        clean = re.sub(r"^#{1,6}\s*", "", line).strip()
        is_heading = (
            line.startswith("#")
            or clean.upper().rstrip(":") in SECTION_HEADINGS
        )

        if is_heading:
            story.append(Paragraph(format_inline(clean), heading))
            first_line = False
            continue

        bullet_match = re.match(r"^(?:[-*•]|\d+[.)])\s+(.+)$", line)
        if bullet_match:
            story.append(
                Paragraph(
                    "&#8226; " + format_inline(bullet_match.group(1)),
                    bullet,
                )
            )
            first_line = False
            continue

        style = name_style if first_line else normal

        if (
            not first_line
            and "|" in line
            and not line.startswith(("http", "www."))
        ):
            job_style = ParagraphStyle(
                "ResumeJobTitle",
                parent=normal,
                fontName="Helvetica-Bold",
                spaceBefore=5,
                spaceAfter=3,
                keepWithNext=True,
            )
            story.append(Paragraph(format_inline(line), job_style))
        else:
            story.append(Paragraph(format_inline(line), style))

        first_line = False

    if not story:
        raise ValueError("Cannot export an empty resume.")

    doc.build(story)
    return buffer.getvalue()
