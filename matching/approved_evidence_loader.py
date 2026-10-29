
import json
from pathlib import Path

from matching.job_workspace import (
    description_hash,
    get_job_directory,
    verify_job_workspace,
)


def load_approved_evidence(job_id, job_description):
    """
    Load human-approved evidence for one specific job.

    Fail closed if the job identity, description hash,
    workspace, or approval metadata does not match.
    """

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError("Job description is required.")

    if not verify_job_workspace(job_id, job_description):
        raise ValueError(
            "Job Workspace verification failed. "
            "The description may have changed."
        )

    job_dir = get_job_directory(job_id)
    metadata_path = job_dir / "job_metadata.json"
    evidence_path = job_dir / "approved_evidence.json"

    if not evidence_path.is_file():
        raise FileNotFoundError(
            "No Approved Evidence found for this job."
        )

    metadata = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )
    evidence = json.loads(
        evidence_path.read_text(encoding="utf-8")
    )

    expected_hash = description_hash(job_description)

    if evidence.get("job_id") != job_id:
        raise ValueError("Approved Evidence Job ID mismatch.")

    if evidence.get("description_sha256") != expected_hash:
        raise ValueError(
            "Approved Evidence description hash mismatch."
        )

    if evidence.get("job_title") != metadata.get("title"):
        raise ValueError("Approved Evidence job title mismatch.")

    if evidence.get("approval_status") != "human_reviewed":
        raise ValueError(
            "Evidence has not been marked as human reviewed."
        )

    requirements = evidence.get("requirements")

    if not isinstance(requirements, list):
        raise ValueError("Invalid requirements format.")

    if not requirements:
        raise ValueError("No approved requirements available.")

    if evidence.get("approved_count") != len(requirements):
        raise ValueError("Approved Evidence count mismatch.")

    for item in requirements:
        if not isinstance(item, dict):
            raise ValueError("Invalid requirement entry.")

        if item.get("approved") is not True:
            raise ValueError(
                "Unapproved requirement found in Approved Evidence."
            )

        if not isinstance(item.get("requirement"), str):
            raise ValueError("Invalid requirement text.")

        if item["requirement"] not in job_description:
            raise ValueError(
                "Approved requirement is absent from Job Description."
            )

        if not str(item.get("supported_scope") or "").strip():
            raise ValueError(
                "Approved requirement has no supported scope."
            )

    return {
        "job_id": job_id,
        "description_sha256": expected_hash,
        "job_title": metadata["title"],
        "company": metadata.get("company", ""),
        "requirements": requirements,
        "approval_status": "human_reviewed",
    }
