
from urllib.parse import urlparse

from job_sources.job_description_fetcher import fetch_job_description
from job_sources.job_search_fallback import search_job_sources


def normalize(value):
    return " ".join(str(value or "").lower().split())


def source_matches_job(candidate, job):
    """
    Check whether a search result appears to match
    the requested job title and employer.
    """
    heading = normalize(candidate.get("title"))
    snippet = normalize(candidate.get("snippet"))

    title = normalize(job.get("title"))
    company = normalize(job.get("company"))

    if not title or not company:
        return False

    combined = heading + " " + snippet

    title_words = [
        word for word in title.split()
        if len(word) > 2
    ]

    if not title_words:
        return False

    title_match = all(
        word in combined for word in title_words
    )

    company_match = company in combined

    return title_match and company_match


def get_automatic_description(job):
    """
    Try the original job URL first.
    If unavailable, search for alternative public sources.

    Never return a search snippet as a full description.
    """
    original_url = job.get("url", "")

    if original_url:
        result = fetch_job_description(original_url)

        if result["status"] == "success":
            return {
                "status": "success",
                "description": result["description"],
                "source_url": original_url,
                "reason": None,
            }

    candidates = search_job_sources(
        title=job.get("title", ""),
        company=job.get("company", ""),
        location=job.get("location", ""),
    )

    for candidate in candidates:
        if not source_matches_job(candidate, job):
            continue

        candidate_url = candidate.get("url", "")

        if not candidate_url:
            continue

        result = fetch_job_description(candidate_url)

        if result["status"] != "success":
            continue

        return {
            "status": "success",
            "description": result["description"],
            "source_url": candidate_url,
            "reason": None,
        }

    return {
        "status": "description_unavailable",
        "description": None,
        "source_url": None,
        "reason": (
            "No verified full job description "
            "was available from public sources."
        ),
    }


if __name__ == "__main__":
    job = {
        "title": "IT Support Specialist",
        "company": "Transdev Canada",
        "location": "Calgary",
        "url": "https://ca.indeed.com/viewjob?jk=d368c11f16172ce0",
    }

    result = get_automatic_description(job)

    print("STATUS:", result["status"])
    print("SOURCE:", result["source_url"])
    print("REASON:", result["reason"])

    if result["description"]:
        print("DESCRIPTION LENGTH:", len(result["description"]))
        print("\nPREVIEW:\n")
        print(result["description"][:1000])
