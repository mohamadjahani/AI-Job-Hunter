
import re
from pathlib import Path

from resume.resume_profile import build_resume_profile


REQUIRED_SECTIONS = [
    "PROFESSIONAL SUMMARY",
    "TECHNICAL SKILLS",
    "EDUCATION & CERTIFICATES",
    "CYBERSECURITY TRAINING & APPLIED PROJECTS",
    "PROFESSIONAL EXPERIENCE",
    "LANGUAGES",
]


def normalize(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def validate_resume(tailored_text):
    profile = build_resume_profile()
    original = profile["original_text"]

    errors = []
    warnings = []

    if not tailored_text or not tailored_text.strip():
        return {
            "status": "failed",
            "errors": ["Tailored resume is empty."],
            "warnings": [],
        }

    original_normalized = normalize(original)
    tailored_normalized = normalize(tailored_text)

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section.lower() not in tailored_normalized:
            errors.append(f"Missing section: {section}")

    # Check header preservation
    header = profile["header"]

    if header:
        header_lines = [
            line.strip()
            for line in header.splitlines()
            if line.strip()
        ]

        for line in header_lines:
            if normalize(line) not in tailored_normalized:
                warnings.append(
                    f"Header information may be missing: {line}"
                )

    # Check important education and employer names
    important_terms = [
        "Amazon",
        "Irancell",
        "Correlation One",
    ]

    for term in important_terms:
        if (
            term.lower() in original_normalized
            and term.lower() not in tailored_normalized
        ):
            errors.append(
                f"Important original information missing: {term}"
            )

    # Detect potential unsupported technology keywords
    technology_terms = [
        "Microsoft 365",
        "Exchange",
        "SharePoint",
        "Intune",
        "Active Directory",
        "Azure AD",
        "VMware",
        "Hyper-V",
        "ESXi",
        "Cisco",
        "AWS",
        "Azure",
    ]

    for term in technology_terms:
        if (
            term.lower() in tailored_normalized
            and term.lower() not in original_normalized
        ):
            warnings.append(
                f"Technology requires verification: {term}"
            )

    status = (
        "failed" if errors
        else "review_required" if warnings
        else "preliminary_pass"
    )

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


if __name__ == "__main__":
    draft_path = Path(
        "outputs/PCe_Systems_Administrator_DRAFT.md"
    )

    if not draft_path.exists():
        raise FileNotFoundError(
            f"Draft not found: {draft_path}"
        )

    draft = draft_path.read_text(encoding="utf-8")
    result = validate_resume(draft)

    print("VALIDATION STATUS:", result["status"])

    print("\nERRORS:")
    for error in result["errors"]:
        print("-", error)

    print("\nWARNINGS:")
    for warning in result["warnings"]:
        print("-", warning)
