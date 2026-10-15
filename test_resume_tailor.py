
from pathlib import Path

from matching.resume_tailor import tailor_resume


job_file = Path("test_job_description.txt")

if not job_file.exists():
    raise FileNotFoundError(
        "Create test_job_description.txt with the full job description."
    )

job_description = job_file.read_text(encoding="utf-8")

print("Generating tailored resume...")

result = tailor_resume(job_description)

output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

output_file = output_dir / "PCe_Systems_Administrator_DRAFT.md"

output_file.write_text(
    result["tailored_resume"],
    encoding="utf-8",
)

print("Status:", result["status"])
print("Saved to:", output_file)
print("Characters:", len(result["tailored_resume"]))
