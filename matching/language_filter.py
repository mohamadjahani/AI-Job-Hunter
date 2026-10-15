
import re

ADDITIONAL_LANGUAGES = {
    "spanish": "Spanish",
    "french": "French",
    "mandarin": "Mandarin",
    "cantonese": "Cantonese",
    "german": "German",
    "arabic": "Arabic",
}

REQUIRED_PATTERNS = [
    r"\bbilingual\b",
    r"\bfluent in french\b",
    r"\bfrench fluency\b",
    r"\bfluency in french\b",
    r"\bfrench proficiency required\b",
    r"\bfrench (?:is )?(?:required|mandatory|essential)\b",
    r"\b(?:required|mandatory|essential) (?:knowledge of )?french\b",
    r"\bmust (?:speak|know|be fluent in) french\b",
    r"\benglish and french (?:required|mandatory)\b",
    r"\b(?:french|spanish|mandarin|cantonese|german|arabic)[-\s]+speaking required\b",
]

OPTIONAL_PATTERNS = [
    r"\bfrench (?:is )?(?:an asset|a plus|preferred|optional)\b",
    r"\bfrench (?:would be )?(?:an asset|a plus)\b",
    r"\bfrench (?:is )?not required\b",
    r"\b(?:bilingual|french) (?:skills? )?(?:preferred|an asset|a plus)\b",
]


def check_job_language(job):
    title = str(job.get("title") or "")
    description = str(job.get("description") or "")

    text = f"{title}\n{description}".lower()

    detected = [
        language
        for keyword, language in ADDITIONAL_LANGUAGES.items()
        if re.search(rf"\b{keyword}\b", text)
    ]

    if re.search(r"\bbilingual\b", text):
        if "Bilingual" not in detected:
            detected.append("Bilingual")

    # Mandatory language in the job title is a strong signal.
    if re.search(r"\bbilingual\b", title, re.I):
        return {
            "status": "rejected",
            "languages": detected,
        }

    # Evaluate description line by line to distinguish
    # mandatory requirements from optional preferences.
    for line in description.splitlines():
        line = line.strip().lower()

        if not line:
            continue

        if any(re.search(p, line) for p in OPTIONAL_PATTERNS):
            continue

        if any(re.search(p, line) for p in REQUIRED_PATTERNS):
            return {
                "status": "rejected",
                "languages": detected,
            }

    if detected:
        return {
            "status": "manual_review",
            "languages": detected,
        }

    if description.strip():
        return {
            "status": "accepted",
            "languages": [],
        }

    return {
        "status": "manual_review",
        "languages": [],
    }
