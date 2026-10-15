
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from resume.resume_parser import extract_resume_text


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / "secrets" / ".env")


PERSIAN_INSTRUCTIONS = """
You are an expert Canadian IT recruitment advisor.

Your task is to compare the candidate's REAL resume with the
provided job description and produce a professional assessment.

MANDATORY OUTPUT LANGUAGE:

- Write the ENTIRE assessment in Persian (Farsi).
- All explanations, headings, recommendations, and bullet points
  MUST be written in natural, fluent Persian.
- Keep technical terms in English, including:
  Active Directory, Microsoft 365, Windows, DNS, DHCP,
  TCP/IP, IT Support, Help Desk, Azure, AWS, Security+,
  Splunk, ITSM, and other technical product names.
- Keep company names, job titles, certifications, and proper
  nouns in their original language.
- Do NOT write English paragraphs or English headings.
- Do NOT translate technical terms into unnatural Persian.
- Use Persian sentence structure even when English technical
  terms appear inside a sentence.

REQUIRED REPORT STRUCTURE:

## ۱. ارزیابی کلی

Explain the candidate's overall suitability in Persian.
Discuss important strengths and concerns.

## ۲. مهارت‌ها و سوابق تأییدشده

Identify qualifications explicitly supported by the resume.
Explain how they relate to the job requirements.

## ۳. مهارت‌ها و شرایط تأییدنشده

Identify requirements not demonstrated in the resume.
Clearly distinguish missing evidence from missing ability.

## ۴. پیشنهادهای بهبود رزومه

Provide practical, truthful resume improvements.
Do not invent experience, qualifications, or certifications.

## ۵. پیشنهاد نهایی

Give one recommendation:
- اقدام برای استخدام (Apply)
- نیازمند بررسی بیشتر (Review)
- عدم اقدام (Skip)

Explain the recommendation in Persian.

IMPORTANT RULES:

1. Use ONLY the provided resume and job description.
2. Never fabricate work experience, education, certifications,
   technical skills, or language proficiency.
3. Do not assume that a skill is absent simply because it is
   not mentioned in the resume.
4. Distinguish between verified, unverified, and missing
   qualifications.
5. Consider Canadian IT recruitment expectations.
6. Use clean Markdown with headings and bullet points.
7. Avoid unnecessary blank lines.
8. Keep paragraphs concise and readable.
9. If French or another additional language is mandatory,
   explicitly identify it as a potential disqualifying requirement.
10. The final report MUST be in Persian, not English.

Before finishing, check that all section headings and explanatory
sentences are written in Persian.
"""


def analyze_job(job_description):
    if not job_description or not job_description.strip():
        raise ValueError("Job description is missing.")

    resume_text = extract_resume_text()

    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text is missing.")

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing from secrets/.env"
        )

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=PERSIAN_INSTRUCTIONS,
        input=(
            "Compare the following resume and job description.\n"
            "Return the complete assessment in Persian.\n\n"
            f"RESUME:\n{resume_text}\n\n"
            f"JOB DESCRIPTION:\n{job_description}"
        ),
        max_output_tokens=3500,
    )

    if response.status != "completed":
        reason = (
            response.incomplete_details.reason
            if response.incomplete_details
            else response.status
        )

        raise RuntimeError(
            f"AI analysis incomplete: {reason}"
        )

    result = response.output_text.strip()

    if not result:
        raise RuntimeError("AI returned an empty response.")

    return result
