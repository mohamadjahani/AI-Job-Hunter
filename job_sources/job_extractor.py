from bs4 import BeautifulSoup


def extract_links_from_email(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    links = []

    for tag in soup.find_all("a", href=True):
        title = tag.get_text(" ", strip=True)
        url = tag["href"]

        if title and url.startswith(("http://", "https://")):
            links.append({
                "title": title,
                "url": url
            })

    return links

from urllib.parse import urlparse, parse_qs


def filter_job_links(links):
    jobs = []
    seen = set()

    for link in links:
        url = link["url"]
        parsed = urlparse(url)

        if parsed.hostname not in ("ca.indeed.com", "www.indeed.com", "indeed.com"):
            continue

        job_id = parse_qs(parsed.query).get("jk", [None])[0]

        if not job_id or job_id in seen:
            continue

        seen.add(job_id)

        jobs.append({
            "title": link["title"],
            "job_id": job_id,
            "url": url
        })

    return jobs
