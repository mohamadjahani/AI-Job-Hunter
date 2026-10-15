
import re
import sys
from urllib.parse import urlparse

from ddgs import DDGS

from job_sources.job_description_fetcher import fetch_job_description


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def is_indeed_url(url):
    hostname = (urlparse(url).hostname or "").lower()
    return hostname == "indeed.com" or hostname.endswith(".indeed.com")


def search_job_sources(title, company, location="", max_results=8):
    """
    Search public web results for matching job advertisements.
    Search snippets are leads, NOT complete job descriptions.
    """
    title = clean_text(title)
    company = clean_text(company)
    location = clean_text(location)

    if not title or not company:
        return []

    query = f'"{title}" "{company}" {location}'

    try:
        results = DDGS().text(
            query,
            max_results=max_results,
        )
    except Exception as error:
        print(f"Search failed: {error}")
        return []

    candidates = []

    for result in results or []:
        url = result.get("href") or result.get("url") or ""
        heading = clean_text(result.get("title"))
        snippet = clean_text(result.get("body"))

        if not url.startswith("https://"):
            continue

        if is_indeed_url(url):
            continue

        candidates.append({
            "title": heading,
            "url": url,
            "snippet": snippet,
        })

    return candidates


def find_job_description(title, company, location=""):
    candidates = search_job_sources(
        title=title,
        company=company,
        location=location,
    )

    return {
        "status": "manual_review",
        "description": None,
        "candidates": candidates,
        "reason": (
            "Search results found. Full job description "
            "has not yet been verified."
            if candidates
            else "No alternative sources found."
        ),
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python -m job_sources.job_search_fallback "
            '"JOB TITLE" "COMPANY" "LOCATION"'
        )
        sys.exit(1)

    title = sys.argv[1]
    company = sys.argv[2]
    location = sys.argv[3] if len(sys.argv) > 3 else ""

    result = find_job_description(
        title,
        company,
        location,
    )

    print("\nSTATUS:", result["status"])
    print("REASON:", result["reason"])
    print("\nPOSSIBLE SOURCES:\n")

    for index, candidate in enumerate(result["candidates"], 1):
        print(f"{index}. {candidate['title']}")
        print(f"   URL: {candidate['url']}")
        print(f"   Snippet: {candidate['snippet'][:250]}")
        print()
