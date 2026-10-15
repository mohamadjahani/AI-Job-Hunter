import base64

from job_sources.gmail_reader import authenticate_gmail
from job_sources.job_details_extractor import extract_job_details
from matching.job_pipeline import evaluate_jobs


def find_html(payload):
    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data")

        if data:
            return base64.urlsafe_b64decode(data).decode(
                "utf-8", errors="replace"
            )

    for part in payload.get("parts", []):
        html = find_html(part)
        if html:
            return html

    return None


def remove_duplicate_jobs(jobs):
    unique_jobs = []
    seen = set()

    for job in jobs:
        key = (
            str(job.get("title") or "").strip().casefold(),
            str(job.get("company") or "").strip().casefold(),
            str(job.get("location") or "").strip().casefold(),
        )

        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs


def print_job(job, number):
    print(f"\n{number}. {job.get('title', 'Unknown')}")
    print(f"   Company : {job.get('company', 'Unknown')}")
    print(f"   Location: {job.get('location', 'Unknown')}")
    print(f"   Status  : {job.get('final_status', 'Unknown')}")
    print(f"   Score   : {job.get('match_score', 'N/A')} (title only)")

    skill_match = job.get("skill_match")

    if skill_match is None:
        print("   Skills  : Not evaluated (job description missing)")
    else:
        print("   Skills  :", skill_match)


def main():
    print("\n=== AI JOB HUNTER ===")

    print("\nConnecting to Gmail...")
    service = authenticate_gmail()

    response = service.users().messages().list(
        userId="me",
        q=(
            "from:(donotreply@jobalert.indeed.com "
            "OR donotreply@match.indeed.com)"
        ),
        maxResults=10,
    ).execute()

    messages = response.get("messages", [])
    jobs = []

    for message in messages:
        email = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="full",
        ).execute()

        html = find_html(email["payload"])

        if html:
            jobs.extend(extract_job_details(html))

    extracted_count = len(jobs)
    jobs = remove_duplicate_jobs(jobs)
    results = evaluate_jobs(jobs)

    review_jobs = [
        job for job in results
        if job.get("final_status") != "rejected"
    ]

    rejected_jobs = [
        job for job in results
        if job.get("final_status") == "rejected"
    ]

    review_jobs.sort(
        key=lambda job: job.get("match_score") or 0,
        reverse=True,
    )

    print("\n" + "=" * 50)
    print("JOB SEARCH SUMMARY")
    print("=" * 50)
    print(f"Emails scanned   : {len(messages)}")
    print(f"Jobs extracted   : {extracted_count}")
    print(f"Unique jobs      : {len(jobs)}")
    print(f"Jobs evaluated   : {len(results)}")
    print(f"Review candidates: {len(review_jobs)}")
    print(f"Rejected jobs    : {len(rejected_jobs)}")

    print("\n" + "=" * 50)
    print("JOBS FOR REVIEW")
    print("=" * 50)

    if not review_jobs:
        print("No candidates found.")

    for number, job in enumerate(review_jobs, start=1):
        print_job(job, number)

    print("\n" + "=" * 50)
    print("REJECTED JOBS")
    print("=" * 50)

    for number, job in enumerate(rejected_jobs, start=1):
        print(
            f"{number}. {job.get('title', 'Unknown')} "
            f"| {job.get('location', 'Unknown')}"
        )

    print("\nAI Job Hunter finished.")


if __name__ == "__main__":
    main()
