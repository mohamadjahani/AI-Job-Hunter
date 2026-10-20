
import json
import re
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

EVIDENCE_FILE = BASE_DIR / "outputs" / "PCe_EVIDENCE_MAP.json"
REVIEW_FILE = BASE_DIR / "outputs" / "PCe_EVIDENCE_REVIEW.json"
APPROVED_FILE = BASE_DIR / "outputs" / "PCe_APPROVED_EVIDENCE.json"

VALID_MATCHES = {"direct", "related", "not_verified"}

HIGH_RISK_PATTERNS = [
    r"\b\d+\+?\s+years?\b",
    r"\bcertif(?:ied|ication|ications)\b",
    r"\bactive directory\b",
    r"\bmicrosoft 365\b",
    r"\bazure\b",
    r"\baws\b",
    r"\bserver administration\b",
    r"\bvmware\b",
    r"\bcisco\b",
    r"\bmanage(?:d|ment|s)?\b",
    r"\badminist(?:er|ered|ration|rator)\b",
]


def read_json(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_evidence():
    if not EVIDENCE_FILE.exists():
        raise FileNotFoundError(
            f"Evidence map not found: {EVIDENCE_FILE}"
        )

    data = read_json(EVIDENCE_FILE)

    if not isinstance(data.get("requirements"), list):
        raise ValueError("Invalid requirements format.")

    return data


def is_high_risk(item):
    text = " ".join([
        str(item.get("requirement", "")),
        str(item.get("unsupported_scope", "")),
    ]).lower()

    return any(
        re.search(pattern, text)
        for pattern in HIGH_RISK_PATTERNS
    )


def classify_review_priority(item):
    match = item.get("reviewed_match", "not_verified")
    evidence = str(item.get("resume_evidence", "")).strip()

    if match == "not_verified" or not evidence:
        return "excluded"

    if match == "related":
        return "needs_review"

    if is_high_risk(item):
        return "needs_review"

    return "standard"


def create_review():
    evidence = load_evidence()

    existing = {}
    if REVIEW_FILE.exists():
        old_review = read_json(REVIEW_FILE)
        existing = {
            item.get("requirement"): item
            for item in old_review.get("requirements", [])
        }

    requirements = []

    for index, source in enumerate(
        evidence["requirements"], start=1
    ):
        requirement = source.get("requirement", "")
        match = source.get("match", "not_verified")

        if match not in VALID_MATCHES:
            match = "not_verified"

        item = {
            "id": index,
            "requirement": requirement,
            "original_match": match,
            "reviewed_match": match,
            "resume_evidence": source.get("resume_evidence", ""),
            "supported_scope": source.get("supported_scope", ""),
            "unsupported_scope": source.get("unsupported_scope", ""),
            "explanation_fa": source.get("explanation_fa", ""),
            "approved": False,
            "review_note": "",
        }

        previous = existing.get(requirement)

        # Preserve approval only when the evidence is unchanged.
        if previous and all(
            previous.get(key) == item.get(key)
            for key in (
                "original_match",
                "resume_evidence",
                "supported_scope",
                "unsupported_scope",
            )
        ):
            item["reviewed_match"] = previous.get(
                "reviewed_match", match
            )
            item["approved"] = previous.get("approved") is True
            item["review_note"] = previous.get("review_note", "")

        item["review_priority"] = classify_review_priority(item)

        if item["review_priority"] == "excluded":
            item["approved"] = False

        requirements.append(item)

    review = {
        "job_title": evidence.get("job_title", ""),
        "review_status": "pending",
        "requirements": requirements,
    }

    write_json(REVIEW_FILE, review)
    return review


def load_review():
    if not REVIEW_FILE.exists():
        return create_review()

    return read_json(REVIEW_FILE)


def save_review(data):
    requirements = data.get("requirements")

    if not isinstance(requirements, list):
        raise ValueError("Invalid review requirements.")

    for item in requirements:
        match = item.get("reviewed_match", "not_verified")

        if match not in VALID_MATCHES:
            raise ValueError("Invalid reviewed match.")

        evidence = str(item.get("resume_evidence", "")).strip()

        if item.get("approved") is True:
            if match == "not_verified" or not evidence:
                raise ValueError(
                    "Cannot approve unsupported evidence."
                )

        item["review_priority"] = classify_review_priority(item)

    write_json(REVIEW_FILE, data)


def approve_requirement(
    requirement_id,
    reviewed_match,
    approved,
    note="",
):
    if reviewed_match not in VALID_MATCHES:
        raise ValueError("Invalid reviewed match.")

    data = load_review()

    target = next(
        (
            item for item in data["requirements"]
            if item["id"] == requirement_id
        ),
        None,
    )

    if target is None:
        raise ValueError(
            f"Requirement ID {requirement_id} not found."
        )

    target["reviewed_match"] = reviewed_match
    target["approved"] = bool(approved)
    target["review_note"] = note

    save_review(data)
    return target


def export_approved_evidence():
    data = load_review()

    approved_items = [
        item
        for item in data["requirements"]
        if (
            item.get("approved") is True
            and item.get("reviewed_match") in {"direct", "related"}
            and str(item.get("resume_evidence", "")).strip()
        )
    ]

    export = {
        "job_title": data.get("job_title", ""),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "approval_status": "human_reviewed",
        "approved_count": len(approved_items),
        "requirements": approved_items,
    }

    write_json(APPROVED_FILE, export)
    return export
