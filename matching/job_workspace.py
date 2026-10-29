
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_DIR = BASE_DIR / "outputs" / "jobs"

JOB_ID_PATTERN = re.compile(r"^[0-9a-f]{16}$")


def description_hash(description):
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Job description cannot be empty.")

    normalized = description.strip()
    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def get_job_directory(job_id):
    if not isinstance(job_id, str) or not JOB_ID_PATTERN.fullmatch(job_id):
        raise ValueError("Invalid Job ID.")

    return JOBS_DIR / job_id


def save_job_workspace(job_id, job, description):
    if not isinstance(job, dict):
        raise ValueError("Job must be a dictionary.")

    if not isinstance(description, str) or not description.strip():
        raise ValueError("Job description cannot be empty.")

    job_dir = get_job_directory(job_id)
    fingerprint = description_hash(description)

    metadata_path = job_dir / "job_metadata.json"
    description_path = job_dir / "job_description.txt"

    if metadata_path.exists() or description_path.exists():
        if not metadata_path.is_file() or not description_path.is_file():
            raise ValueError("Incomplete existing job workspace.")

        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
        existing_description = description_path.read_text(
            encoding="utf-8"
        )

        if (
            metadata.get("job_id") != job_id
            or metadata.get("description_sha256")
            != description_hash(existing_description)
        ):
            raise ValueError("Existing workspace integrity check failed.")

        if (
            metadata.get("description_sha256") != fingerprint
            or any(
                metadata.get(field) != str(job.get(field) or "").strip()
                for field in ("title", "company", "location", "url")
            )
        ):
            raise ValueError(
                "Job details or description changed. "
                "A new review is required; existing evidence "
                "must not be reused."
            )

        return job_dir

    job_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "job_id": job_id,
        "title": str(job.get("title") or "").strip(),
        "company": str(job.get("company") or "").strip(),
        "location": str(job.get("location") or "").strip(),
        "url": str(job.get("url") or "").strip(),
        "description_sha256": fingerprint,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    description_path.write_text(
        description.strip() + "\n",
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return job_dir


def verify_job_workspace(job_id, description):
    job_dir = get_job_directory(job_id)

    metadata_path = job_dir / "job_metadata.json"
    description_path = job_dir / "job_description.txt"

    if not metadata_path.is_file() or not description_path.is_file():
        return False

    metadata = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )
    saved_description = description_path.read_text(
        encoding="utf-8"
    )

    expected_hash = description_hash(description)

    return (
        metadata.get("job_id") == job_id
        and metadata.get("description_sha256") == expected_hash
        and description_hash(saved_description) == expected_hash
    )
