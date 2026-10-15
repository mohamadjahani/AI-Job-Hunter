
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from resume.resume_profile import build_resume_profile


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "secrets" / ".env")

CACHE_DIR = BASE_DIR / "outputs" / "evidence_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "gpt-5.4-mini"
CACHE_VERSION = "evidence-v4"
VALIDATION_VERSION = "semantic-v1"


INSTRUCTIONS = """
You are a Canadian IT recruitment evidence analyst.

Compare the ORIGINAL RESUME with the FULL JOB DESCRIPTION.

Do NOT rewrite the resume.

CRITICAL RULES:

1. The original resume is the ONLY source of candidate facts.
2. Never invent skills, certifications, experience, or dates.
3. Separate required and preferred job qualifications.
4. Direct means the complete requirement is supported.
5. Related means relevant evidence exists but the complete
   requirement is NOT established.
6. Not_verified means there is insufficient reliable evidence.
7. Coursework is NOT professional production experience.
8. Working at Amazon Fulfillment is NOT AWS experience.
9. Telecommunications experience alone is NOT proof of
   VoIP, Cisco, network administration, or server experience.
10. A technology keyword alone does not establish years
    of professional experience.
11. For compound requirements, distinguish supported
    and unsupported components.
12. Copy ONE short continuous verbatim resume quotation
    for direct or related matches.
13. Never combine separate quotations.
14. If evidence is unavailable, use an empty string.
15. All explanations must be in Persian.
16. Return valid JSON only.

Allowed priorities: required, preferred.
Allowed matches: direct, related, not_verified.

Return JSON:

{
  "job_title": "string",
  "requirements": [
    {
      "requirement": "string",
      "priority": "required",
      "match": "related",
      "resume_evidence": "exact resume quotation",
      "supported_scope": "what is actually established",
      "unsupported_scope": "what remains unverified",
      "explanation_fa": "توضیح فارسی"
    }
  ],
  "tailoring_strategy_fa": [
    "پیشنهاد فارسی"
  ],
  "critical_gaps_fa": [
    "فاصله مهم فارسی"
  ]
}

Include all significant job requirements.
"""


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00ad", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip().casefold()


def verify_evidence(evidence, original_resume):
    return (
        isinstance(evidence, str)
        and bool(evidence.strip())
        and normalize_text(evidence)
        in normalize_text(original_resume)
    )


def cache_path_for(resume, job_description):
    payload = json.dumps(
        {
            "cache_version": CACHE_VERSION,
            "model": MODEL,
            "resume": resume,
            "job": job_description,
        },
        sort_keys=True,
        ensure_ascii=False,
    )

    key = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()

    return CACHE_DIR / f"{key}.json"


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def semantic_safety_checks(item, original_resume):
    requirement = item["requirement"].casefold()
    evidence = item["resume_evidence"].casefold()

    warnings = []

    if item["match"] == "not_verified":
        return warnings

    # Amazon employment must never imply AWS expertise.
    if (
        re.search(r"\baws\b|amazon web services", requirement)
        and "amazon" in evidence
        and not re.search(
            r"\baws\b|amazon web services",
            evidence,
        )
    ):
        warnings.append(
            "Amazon employment does not prove AWS experience."
        )

    # Telecom experience alone is not VoIP/Cisco experience.
    if re.search(r"\bvoip\b|ip telephony|cisco", requirement):
        if not re.search(
            r"\bvoip\b|ip telephony|cisco",
            evidence,
        ):
            warnings.append(
                "Telecommunications background alone does not "
                "prove VoIP or Cisco experience."
            )

    # Explicit experience-duration requirements.
    years_match = re.search(
        r"(?:minimum of\s*)?(\d+)\s*(?:\+)?\s*years?",
        requirement,
    )

    if years_match and item["match"] == "direct":
        warnings.append(
            "Years of relevant professional experience "
            "require independent verification."
        )

    # Compound OS requirements.
    if (
        "windows" in requirement
        and ("mac" in requirement or "server" in requirement)
        and item["match"] == "direct"
    ):
        warnings.append(
            "Windows knowledge does not establish Mac "
            "or Windows Server experience."
        )

    return warnings


def validate_mapping(result, original_resume):
    if not isinstance(result, dict):
        raise ValueError("Mapping must be a JSON object.")

    requirements = result.get("requirements")

    if not isinstance(requirements, list):
        raise ValueError("Invalid requirements format.")

    valid_matches = {"direct", "related", "not_verified"}
    valid_priorities = {"required", "preferred"}

    warnings = []

    for index, item in enumerate(requirements, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"Requirement {index} must be an object."
            )

        if item.get("priority") not in valid_priorities:
            raise ValueError(
                f"Invalid priority at requirement {index}."
            )

        if item.get("match") not in valid_matches:
            raise ValueError(
                f"Invalid match at requirement {index}."
            )

        if not isinstance(item.get("requirement"), str):
            raise ValueError(
                f"Invalid requirement text at {index}."
            )

        evidence = item.get("resume_evidence", "")

        if not isinstance(evidence, str):
            evidence = ""

        item["resume_evidence"] = evidence
        item.setdefault("supported_scope", "")
        item.setdefault("unsupported_scope", "")

        if item["match"] == "not_verified":
            item["resume_evidence"] = ""
            item["supported_scope"] = ""
            continue

        if not verify_evidence(evidence, original_resume):
            warnings.append(
                f"Requirement {index}: quotation not verified."
            )

            item["match"] = "not_verified"
            item["resume_evidence"] = ""
            item["supported_scope"] = ""
            item["unsupported_scope"] = (
                "Original evidence quotation could not "
                "be verified."
            )
            continue

        semantic_warnings = semantic_safety_checks(
            item,
            original_resume,
        )

        if semantic_warnings:
            for warning in semantic_warnings:
                warnings.append(
                    f"Requirement {index}: {warning}"
                )

            # Do not permit questionable matches
            # to enter the tailoring evidence set.
            item["match"] = "not_verified"
            item["resume_evidence"] = ""
            item["supported_scope"] = ""
            item["unsupported_scope"] = (
                "Requires manual semantic verification."
            )

    result["validation_warnings"] = warnings
    result["validation_status"] = (
        "review_required" if warnings
        else "preliminary_pass"
    )
    result["validation_version"] = VALIDATION_VERSION

    return result


def map_job_evidence(job_description):
    if not isinstance(job_description, str):
        raise ValueError("Job description must be text.")

    if len(job_description.strip()) < 200:
        raise ValueError(
            "A complete job description is required."
        )

    profile = build_resume_profile()
    original_resume = profile["original_text"]

    cache_path = cache_path_for(
        original_resume,
        job_description,
    )

    if cache_path.exists():
        print("Loading cached GPT evidence response...")

        cached = json.loads(
            cache_path.read_text(encoding="utf-8")
        )
        raw_result = cached["raw_result"]

    else:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing.")

        client = OpenAI(api_key=api_key)

        print("Requesting evidence mapping from GPT...")

        response = client.responses.create(
            model=MODEL,
            instructions=INSTRUCTIONS,
            input=(
                "ORIGINAL RESUME:\n"
                + original_resume
                + "\n\nFULL JOB DESCRIPTION:\n"
                + job_description
                + "\n\nReturn the result as valid JSON."
            ),
            text={
                "format": {
                    "type": "json_object"
                }
            },
            max_output_tokens=6000,
        )

        if response.status != "completed":
            raise RuntimeError(
                f"GPT response incomplete: {response.status}"
            )

        raw_text = response.output_text.strip()

        if not raw_text:
            raise RuntimeError("Empty GPT response.")

        raw_path = cache_path.with_suffix(".raw.txt")
        raw_path.write_text(raw_text, encoding="utf-8")

        raw_result = json.loads(raw_text)

        save_json(
            cache_path,
            {
                "cache_version": CACHE_VERSION,
                "model": MODEL,
                "raw_result": raw_result,
            },
        )

        print("GPT response cached.")

    result = json.loads(
        json.dumps(raw_result, ensure_ascii=False)
    )

    result = validate_mapping(
        result,
        original_resume,
    )

    validated_path = cache_path.with_suffix(
        ".validated.json"
    )
    save_json(validated_path, result)

    print(
        "Validation status:",
        result["validation_status"],
    )

    for warning in result["validation_warnings"]:
        print("WARNING:", warning)

    return result
