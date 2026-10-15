ROLE_KEYWORDS = {
    "IT Support": 90,
    "Help Desk": 90,
    "Service Desk": 85,
    "User Support": 85,
    "IT Service Technician": 85,
    "Systems Support": 80,
    "IT Operations": 80,
    "Data Center": 90,
    "Systems Administrator": 70,
    "Network Administrator": 65,
}

def match_jobs(jobs, target_roles=None):
    matched_jobs = []

    for job in jobs:
        title = job["title"].lower()
        score = 0

        for keyword, points in ROLE_KEYWORDS.items():
            if keyword.lower() in title:
                score = max(score, points)

        if "senior" in title:
            score -= 30

        if score >= 60:
            matched_job = job.copy()
            matched_job["match_score"] = score
            matched_jobs.append(matched_job)

    matched_jobs.sort(
        key=lambda job: job["match_score"],
        reverse=True
    )

    return matched_jobs
