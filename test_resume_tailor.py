
from pathlib import Path

from matching.resume_tailor import tailor_resume
from matching.job_workspace import verify_job_workspace


JOB_ID = "2c8b837375e4b049"

BASE_DIR = Path(__file__).resolve().parent
JOB_FILE = BASE_DIR / "test_job_description.txt"

OUTPUT_DIR = BASE_DIR / "outputs" / "jobs" / JOB_ID
OUTPUT_FILE = OUTPUT_DIR / "tailored_resume_DRAFT.md"


def main():
    if not JOB_FILE.is_file():
        raise FileNotFoundError(
            "test_job_description.txt was not found."
        )

    job_description = JOB_FILE.read_text(
        encoding="utf-8"
    ).strip()

    # Verify the correct job before generating anything.
    if not verify_job_workspace(JOB_ID, job_description):
        raise ValueError(
            "Job Workspace verification failed."
        )

    print("Job Workspace verified.")
    print("Generating tailored resume draft...")

    result = tailor_resume(
        job_id=JOB_ID,
        job_description=job_description,
    )

    if result["status"] != "draft_pending_approval":
        raise ValueError("Unexpected resume status.")

    if result["approved_requirements_used"] != 1:
        raise ValueError("Unexpected approved evidence count.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        raise FileExistsError(
            "Draft already exists. Refusing to overwrite it."
        )

    OUTPUT_FILE.write_text(
        result["tailored_resume"],
        encoding="utf-8",
    )

    print("Status:", result["status"])
    print("Approved requirements:", result["approved_requirements_used"])
    print("Saved to:", OUTPUT_FILE)
    print("Characters:", len(result["tailored_resume"]))


if __name__ == "__main__":
    main()
