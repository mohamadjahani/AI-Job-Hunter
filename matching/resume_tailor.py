
import os
import re
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from resume.resume_profile import build_resume_profile


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "secrets" / ".env")


TAILORING_INSTRUCTIONS = """
You are an expert Canadian ATS resume editor.

Tailor the original resume to the supplied job description.

STRICT RULES:
1. Use ONLY facts explicitly supported by the original resume.
2. Never invent skills, work experience, achievements, metrics,
   certifications, employment dates, or responsibilities.
3. Job requirements are NOT evidence of candidate experience.
4. Preserve employers, job titles, dates, and education.
5. Highlight relevant experience and transferable skills.
6. Do not present training as professional work experience.
7. Use clear professional Canadian English.
8. Do not generate the candidate's name or contact header.
9. Return ONLY the resume body in Markdown.

Required sections:
# PROFESSIONAL SUMMARY
# TECHNICAL SKILLS
# EDUCATION & CERTIFICATES
# CYBERSECURITY TRAINING & APPLIED PROJECTS
# PROFESSIONAL EXPERIENCE

Optional sections:
# LANGUAGES

Include optional sections ONLY when the original resume
explicitly provides relevant information.

Never output placeholders such as:
"Not specified", "Not available", "N/A",
"Not specified in the original resume", or "To be confirmed".

If information is missing, omit the entire optional section.

No tables, icons, graphics, or decorative elements.
"""


def tailor_resume(job_id, job_description, approved_analysis):
    if (
        not isinstance(job_description, str)
        or len(job_description.strip()) < 200
    ):
        raise ValueError("A complete job description is required.")

    job_description = job_description.strip()

    if not isinstance(approved_analysis, str) or not approved_analysis.strip():
        raise ValueError("Approved AI Analysis is required.")


    profile = build_resume_profile()
    original_resume = profile["original_text"]
    original_header = profile["header"].strip()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing.")

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=TAILORING_INSTRUCTIONS,
        input=(
            "ORIGINAL RESUME:\\n"
            + original_resume
            + "\\n\\nJOB ID: "
            + str(job_id)
            + "\\n\\nJOB DESCRIPTION:\\n"
            + job_description
            + "\n\nAPPROVED AI ANALYSIS AND RESUME RECOMMENDATIONS:\n"
            + approved_analysis
            + "\n\nApply the approved recommendations where supported "
              "by the original resume. Do not invent any experience.\n"
            + "\\n\\nTailor the resume using only verified "
            "facts from the original resume."
        ),
        max_output_tokens=4500,
    )

    if response.status != "completed":
        raise RuntimeError("Resume tailoring was not completed.")

    body = response.output_text.strip()

    if not body:
        raise RuntimeError("Empty tailored resume.")

    first_heading = re.search(
        r"(?im)^#{1,6}\s*PROFESSIONAL SUMMARY\s*$",
        body,
    )

    if not first_heading:
        raise ValueError(
            "Generated resume is missing PROFESSIONAL SUMMARY."
        )

    body = body[first_heading.start():].strip()

    tailored_resume = original_header + "\n\n" + body

    return {
        "job_id": job_id,
        "description_sha256": hashlib.sha256(job_description.encode("utf-8")).hexdigest(),
        "original_resume": original_resume,
        "tailored_resume": tailored_resume,
        "approved_requirements_used": 0,
        "status": "draft_pending_approval",
    }
