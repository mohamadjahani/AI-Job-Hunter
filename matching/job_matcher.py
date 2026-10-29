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
    "System Administrator": 70,
    "Network Administrator": 65,
    "IT Technician": 85,
    "Desktop Support": 90,
    "Technical Support": 80,
    "Support Technician": 85,
    "IT Systems": 80,
    "Computer Technician": 80,
    "Field Service Technician": 75,
    "IT Coordinator": 85,
    "Junior IT Analyst": 90,
    "IT Analyst": 80,
    "Infrastructure Technician": 80,
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
