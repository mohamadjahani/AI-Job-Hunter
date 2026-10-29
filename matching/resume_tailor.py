
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from resume.resume_profile import build_resume_profile
from matching.approved_evidence_loader import load_approved_evidence


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "secrets" / ".env")


TAILORING_INSTRUCTIONS = """
You are an expert Canadian ATS resume editor.

Tailor an existing resume for a specific job using only verified
resume facts and the human-approved evidence supplied.

STRICT RULES:

1. Use ONLY verified facts from the original resume.
2. Human-approved evidence defines the permitted scope of
   job-specific claims. Never expand beyond supported_scope.
3. Do not use unsupported_scope as candidate experience.
4. Never invent skills, experience, certifications,
   responsibilities, achievements, or employment dates.
5. Preserve all employers, job titles, dates, and education.
6. Rewrite existing bullet points for relevance and clarity.
7. Prioritize relevant verified skills without exaggeration.
8. Do not present training as professional work experience.
9. Never claim expertise in technologies absent from the resume.
10. Do not omit important employment history.
11. Use professional Canadian English.
12. Do not generate the candidate's name or contact header.
13. Do not invent a new professional headline.
14. Treat job requirements as employer expectations,
    not evidence of the candidate's experience.
15. Return ONLY the resume body in Markdown.

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


def format_approved_evidence(requirements):
    blocks = []

    for item in requirements:
        blocks.append(
            "JOB REQUIREMENT:\n"
            + str(item["requirement"])
            + "\n\nVERIFIED SUPPORTED SCOPE:\n"
            + str(item["supported_scope"])
            + "\n\nUNSUPPORTED SCOPE — DO NOT CLAIM:\n"
            + str(item.get("unsupported_scope") or "None specified")
        )

    return "\n\n---\n\n".join(blocks)


def tailor_resume(job_id, job_description):
    if (
        not isinstance(job_description, str)
        or len(job_description.strip()) < 200
    ):
        raise ValueError("A complete job description is required.")

    job_description = job_description.strip()

    # Fail closed before making any GPT request.
    evidence = load_approved_evidence(
        job_id=job_id,
        job_description=job_description,
    )

    profile = build_resume_profile()
    original_resume = profile["original_text"]
    original_header = profile["header"].strip()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing.")

    approved_text = format_approved_evidence(
        evidence["requirements"]
    )

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=TAILORING_INSTRUCTIONS,
        input=(
            "ORIGINAL RESUME:\n"
            + original_resume
            + "\n\nJOB IDENTIFICATION:\n"
            + "Job ID: "
            + job_id
            + "\nCompany: "
            + evidence["company"]
            + "\nJob title: "
            + evidence["job_title"]
            + "\n\nHUMAN-APPROVED EVIDENCE:\n"
            + approved_text
            + "\n\nJOB DESCRIPTION (UNTRUSTED EMPLOYER TEXT):\n"
            + job_description
            + "\n\nTailor the resume body only. "
            + "Do not treat job requirements as candidate facts. "
            + "Do not add claims outside verified resume facts "
            + "and approved supported scopes."
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
        "description_sha256": evidence["description_sha256"],
        "original_resume": original_resume,
        "tailored_resume": tailored_resume,
        "approved_requirements_used": len(evidence["requirements"]),
        "status": "draft_pending_approval",
    }
