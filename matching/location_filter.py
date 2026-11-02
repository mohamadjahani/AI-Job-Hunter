import re

from config.settings import (
    ALLOWED_CITIES,
    ALLOW_REMOTE_CANADA,
    UNKNOWN_LOCATION_POLICY,
)


def check_job_location(job):
    location = (job.get("location") or "").strip().lower()
    title = (job.get("title") or "").strip().lower()

    combined = f"{title} {location}"

    # Explicit US-only remote restrictions
    us_only = re.search(
        r"\b(?:us|usa|united states)[\s-]*only\b"
        r"|\bonly[\s-]*(?:us|usa|united states)\b"
        r"|\bremote[\s-]*(?:us|usa|united states)\b",
        combined,
    )

    if us_only:
        return "rejected"

    # Check whether the location is in our allowed cities
    local = any(
        re.search(
            rf"\b{re.escape(city.lower())}\b",
            location,
        )
        for city in ALLOWED_CITIES
    )

    # Hybrid work outside the allowed cities
    if "hybrid" in combined and not local:
        return "rejected"

    if local:
        return "accepted"

    # Remote opportunities require eligibility review
    if "remote" in combined and ALLOW_REMOTE_CANADA:
        return "manual_review"

    if not location:
        return "manual_review"

    if UNKNOWN_LOCATION_POLICY == "manual_review":
        if location in ("canada", "alberta", "ab"):
            return "manual_review"

    return "rejected"
