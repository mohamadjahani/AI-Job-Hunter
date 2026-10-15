
import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

EVIDENCE_FILE = (
    BASE_DIR / "outputs" / "PCe_EVIDENCE_MAP.json"
)

REVIEW_FILE = (
    BASE_DIR / "outputs" / "PCe_EVIDENCE_REVIEW.json"
)

APPROVED_FILE = (
    BASE_DIR / "outputs" / "PCe_APPROVED_EVIDENCE.json"
)


def load_evidence():
    if not EVIDENCE_FILE.exists():
        raise FileNotFoundError(
            f"Evidence map not found: {EVIDENCE_FILE}"
        )

    with EVIDENCE_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    requirements = data.get("requirements", [])

    if not isinstance(requirements, list):
        raise ValueError("Invalid requirements format.")

    return data


def create_review():
    data = load_evidence()

    review = {
        "job_title": data.get("job_title", ""),
        "review_status": "pending",
        "requirements": [],
    }

    for index, item in enumerate(
        data["requirements"], start=1
    ):
        match = item.get("match", "not_verified")

        review["requirements"].append({
            "id": index,
            "requirement": item.get("requirement", ""),
            "original_match": match,
            "reviewed_match": match,
            "resume_evidence": item.get(
                "resume_evidence", ""
            ),
            "supported_scope": item.get(
                "supported_scope", ""
            ),
            "unsupported_scope": item.get(
                "unsupported_scope", ""
            ),
            "explanation_fa": item.get(
                "explanation_fa", ""
            ),
            "approved": False,
            "review_note": "",
        })

    REVIEW_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )

    with REVIEW_FILE.open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(
            review,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return review


def load_review():
    if not REVIEW_FILE.exists():
        return create_review()

    with REVIEW_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def save_review(data):
    with REVIEW_FILE.open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )


def approve_requirement(
    requirement_id,
    reviewed_match,
    approved,
    note="",
):
    valid_matches = {
        "direct",
        "related",
        "not_verified",
    }

    if reviewed_match not in valid_matches:
        raise ValueError("Invalid reviewed match.")

    data = load_review()

    target = next(
        (
            item
            for item in data["requirements"]
            if item["id"] == requirement_id
        ),
        None,
    )

    if target is None:
        raise ValueError(
            f"Requirement ID {requirement_id} not found."
        )

    if (
        reviewed_match != "not_verified"
        and not target["resume_evidence"].strip()
    ):
        raise ValueError(
            "Cannot approve a match without evidence."
        )

    target["reviewed_match"] = reviewed_match
    target["approved"] = (
        bool(approved)
        and reviewed_match != "not_verified"
    )
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
            and item.get("reviewed_match")
            in {"direct", "related"}
            and item.get("resume_evidence", "").strip()
        )
    ]

    export = {
        "job_title": data["job_title"],
        "exported_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "approval_status": "human_reviewed",
        "approved_count": len(approved_items),
        "requirements": approved_items,
    }

    with APPROVED_FILE.open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(
            export,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return export
