
import json
from pathlib import Path

from matching.evidence_mapper import map_job_evidence


BASE_DIR = Path(__file__).resolve().parent

job_file = BASE_DIR / "test_job_description.txt"
output_dir = BASE_DIR / "outputs"
output_file = output_dir / "PCe_EVIDENCE_MAP.json"

if not job_file.exists():
    raise FileNotFoundError(
        "test_job_description.txt not found."
    )

job_description = job_file.read_text(encoding="utf-8")

print("Analyzing job requirements...")
print("Mapping requirements to original resume evidence...")

result = map_job_evidence(job_description)

output_dir.mkdir(parents=True, exist_ok=True)

output_file.write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("\nEvidence mapping completed!")
print("Job:", result.get("job_title", "Unknown"))
print("Requirements:", len(result["requirements"]))

for match_type in ["direct", "related", "not_verified"]:
    count = sum(
        1
        for item in result["requirements"]
        if item["match"] == match_type
    )
    print(f"{match_type}: {count}")

print("\nSaved to:", output_file)
