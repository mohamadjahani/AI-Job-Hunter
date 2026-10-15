import re
from bs4 import BeautifulSoup


def extract_job_details(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    jobs = []

    for heading in soup.find_all("h2"):
        link = heading.find("a", href=True)

        if not link:
            continue

        title = link.get_text(" ", strip=True)

        if not title:
            continue

        container = heading

        for _ in range(6):
            if container.parent is None:
                break
            container = container.parent

        fields = [
            p.get_text(" ", strip=True)
            for p in container.find_all("p")
            if p.get_text(" ", strip=True)
        ]

        company = fields[0] if len(fields) > 0 else None
        location = fields[1] if len(fields) > 1 else None

        salary = None

        for field in fields[2:]:
            if re.search(r"\$\s*[\d,]+", field):
                salary = field
                break

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "url": link["href"],
        })

    return jobs
