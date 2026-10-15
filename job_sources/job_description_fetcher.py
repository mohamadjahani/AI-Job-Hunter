
import json
import re
import sys

import requests
from bs4 import BeautifulSoup


MIN_DESCRIPTION_LENGTH = 200


def clean_description(text):
    text = re.sub(r"\r\n?", "\n", str(text or ""))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_json_ld(soup):
    """Extract structured JobPosting descriptions."""
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue

        items = data if isinstance(data, list) else [data]

        while items:
            item = items.pop()

            if not isinstance(item, dict):
                continue

            if isinstance(item.get("@graph"), list):
                items.extend(item["@graph"])

            job_type = item.get("@type", [])
            if isinstance(job_type, str):
                job_type = [job_type]

            if "JobPosting" not in job_type:
                continue

            description = item.get("description", "")

            if description:
                text = BeautifulSoup(
                    str(description), "html.parser"
                ).get_text(separator="\n", strip=True)

                text = clean_description(text)

                if len(text) >= MIN_DESCRIPTION_LENGTH:
                    return text

    return None


def fetch_job_description(url):
    if not url.startswith(("https://", "http://")):
        return {
            "status": "description_unavailable",
            "description": None,
            "reason": "Invalid URL",
        }

    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "AI-Job-Hunter/1.0"},
        )

        if response.status_code != 200:
            return {
                "status": "description_unavailable",
                "description": None,
                "reason": f"HTTP {response.status_code}",
            }

        soup = BeautifulSoup(response.text, "html.parser")

        selectors = [
            "#jobDescriptionText",
            "[data-testid='jobDescriptionText']",
            ".jobsearch-JobComponent-description",
            ".show-more-less-html__markup",
            ".description__text",
            ".jobs-description__content",
        ]

        for selector in selectors:
            element = soup.select_one(selector)

            if element:
                text = clean_description(
                    element.get_text(separator="\n", strip=True)
                )

                if len(text) >= MIN_DESCRIPTION_LENGTH:
                    return {
                        "status": "success",
                        "description": text,
                        "reason": None,
                    }

        structured_description = extract_json_ld(soup)

        if structured_description:
            return {
                "status": "success",
                "description": structured_description,
                "reason": None,
            }

        return {
            "status": "description_unavailable",
            "description": None,
            "reason": "No complete JobPosting description found",
        }

    except requests.RequestException as error:
        return {
            "status": "description_unavailable",
            "description": None,
            "reason": str(error),
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m job_sources.job_description_fetcher URL")
        sys.exit(1)

    result = fetch_job_description(sys.argv[1])

    print("Status:", result["status"])
    print("Reason:", result["reason"])

    if result["description"]:
        print("\nDescription length:", len(result["description"]))
        print("\nJOB DESCRIPTION:\n")
        print(result["description"][:4000])
