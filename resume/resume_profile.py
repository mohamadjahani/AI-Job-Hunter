import re

from resume.resume_parser import extract_resume_text


SECTION_NAMES = [
    "PROFESSIONAL PROFILE",
    "PROFESSIONAL EXPERIENCE",
    "EDUCATION",
    "CYBERSECURITY EDUCATION",
    "TECHNICAL & PROFESSIONAL SKILLS",
    "SELECTED RECOGNITION",
    "SELECTED PROFESSIONAL TRAINING",
]


def build_resume_profile():
    text = extract_resume_text()

    if not text or not text.strip():
        raise ValueError("Resume text is empty.")

    profile = {
        "header": "",
        "sections": {},
        "original_text": text,
    }

    pattern = (
        r"(?m)^\s*("
        + "|".join(re.escape(name) for name in SECTION_NAMES)
        + r")\s*$"
    )

    matches = list(re.finditer(pattern, text))

    if not matches:
        profile["header"] = "\n".join(
            text.splitlines()[:4]
        ).strip()
        profile["sections"]["FULL RESUME"] = text
        return profile

    profile["header"] = text[:matches[0].start()].strip()

    # Keep only identity/contact lines in the header.
    # Some uploaded PDFs use headings not listed in SECTION_NAMES.
    header_lines = profile["header"].splitlines()
    stop_headings = {
        "PROFESSIONAL SUMMARY",
        "PROFESSIONAL PROFILE",
        "TECHNICAL SKILLS",
        "TECHNICAL & PROFESSIONAL SKILLS",
        "WORK EXPERIENCE",
        "PROFESSIONAL EXPERIENCE",
        "EDUCATION",
        "EDUCATION & CERTIFICATES",
    }

    clean_header = []
    for line in header_lines:
        if line.strip().upper().lstrip("# ").rstrip(":") in stop_headings:
            break
        clean_header.append(line)

    profile["header"] = "\n".join(clean_header).strip()

    for index, match in enumerate(matches):
        section_name = match.group(1)

        start = match.end()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )

        profile["sections"][section_name] = text[start:end].strip()

    return profile


if __name__ == "__main__":
    profile = build_resume_profile()

    print("Header found:", bool(profile["header"]))
    print("Sections found:", len(profile["sections"]))
    print("=" * 50)

    for name, content in profile["sections"].items():
        print(f"{name}: {len(content)} characters")

    print("=" * 50)
    print("Original resume preserved:", bool(profile["original_text"]))
