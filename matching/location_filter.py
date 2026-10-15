from config.settings import (
    ALLOWED_CITIES,
    ALLOW_REMOTE_CANADA,
    UNKNOWN_LOCATION_POLICY,
)


def check_job_location(job):
    location = (job.get("location") or "").strip().lower()

    if not location:
        return "manual_review"

    for city in ALLOWED_CITIES:
        if city.lower() in location:
            return "accepted"

    if "remote" in location and ALLOW_REMOTE_CANADA:
        return "manual_review"

    if UNKNOWN_LOCATION_POLICY == "manual_review":
        if location in ("canada", "alberta", "ab"):
            return "manual_review"

    return "rejected"
