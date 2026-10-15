
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from resume.resume_profile import build_resume_profile


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "secrets" / ".env")


TAILORING_INSTRUCTIONS = """
You are an expert Canadian ATS resume editor.

Your task is to tailor an existing resume for a specific job.

STRICT RULES:

1. Use ONLY verified facts from the original resume.
2. Never invent skills, experience, certifications,
   responsibilities, achievements, or employment dates.
3. Preserve all employers, job titles, dates, and education.
4. Rewrite existing bullet points for relevance and clarity.
5. Prioritize skills that match the job description.
6. Do not present training as professional work experience.
7. Never claim expertise in technologies absent from the resume.
8. Do not omit important employment history.
9. Use professional Canadian English.
10. Do not generate the candidate's name or contact header.
11. Do not invent a new professional headline.
12. Return ONLY the resume body in Markdown.

Required sections:

# PROFESSIONAL SUMMARY
# TECHNICAL SKILLS
# EDUCATION & CERTIFICATES
# CYBERSECURITY TRAINING & APPLIED PROJECTS
# PROFESSIONAL EXPERIENCE
# LANGUAGES

No tables, icons, graphics, or decorative elements.
No explanations outside the resume.
"""


def tailor_resume(job_description):
    if not job_description or len(job_description.strip()) < 200:
        raise ValueError(
            "A complete job description is required."
        )

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
            "ORIGINAL RESUME:\n"
            + original_resume
            + "\n\nJOB DESCRIPTION:\n"
            + job_description
            + "\n\nTailor the resume body only."
        ),
        max_output_tokens=4500,
    )

    if response.status != "completed":
        raise RuntimeError(
            "Resume tailoring was not completed."
        )

    body = response.output_text.strip()

    if not body:
        raise RuntimeError("Empty tailored resume.")

    # Remove an accidentally generated contact header.
    first_heading = re.search(
        r"(?im)^#{1,6}\s*PROFESSIONAL SUMMARY\s*$",
        body,
    )

    if first_heading:
        body = body[first_heading.start():].strip()

    # Preserve the exact original header.
    tailored_resume = (
        original_header
        + "\n\n"
        + body
    )

    return {
        "original_resume": original_resume,
        "tailored_resume": tailored_resume,
        "status": "draft_pending_approval",
    }
