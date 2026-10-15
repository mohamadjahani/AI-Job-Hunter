
from matching.job_matcher import match_jobs
from matching.location_filter import check_job_location
from matching.language_filter import check_job_language
from matching.skill_matcher import match_skills
from matching.job_skills_extractor import extract_job_skills


def evaluate_jobs(jobs):
    matched_jobs = match_jobs(jobs)
    results = []

    for job in matched_jobs:
        location_status = check_job_location(job)
        language_result = check_job_language(job)

        evaluated_job = job.copy()

        evaluated_job["location_status"] = location_status
        evaluated_job["language_status"] = language_result["status"]
        evaluated_job["detected_languages"] = language_result["languages"]

        required_skills = job.get("required_skills")

        if required_skills is not None:
            skills = required_skills
            skill_source = "provided"
        else:
            skills = extract_job_skills(
                job.get("description", "")
            )
            skill_source = "description"

        evaluated_job["detected_job_skills"] = skills
        evaluated_job["skill_source"] = skill_source

        if skills:
            evaluated_job["skill_match"] = match_skills(skills)
            evaluated_job["skill_match_status"] = "evaluated"
        else:
            evaluated_job["skill_match"] = None
            evaluated_job["skill_match_status"] = "not_available"

        if (
            location_status == "rejected"
            or language_result["status"] == "rejected"
        ):
            evaluated_job["final_status"] = "rejected"

        elif (
            location_status == "accepted"
            and language_result["status"] == "accepted"
        ):
            evaluated_job["final_status"] = "candidate"

        else:
            evaluated_job["final_status"] = "manual_review"

        results.append(evaluated_job)

    return results
