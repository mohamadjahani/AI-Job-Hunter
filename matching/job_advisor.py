from matching.skill_matcher import match_skills


def generate_job_advice(job):
    title = job.get("title", "Unknown")
    company = job.get("company", "Unknown")
    skills = job.get("required_skills", [])

    if not skills:
        return (
            f"شغل: {title}\n"
            f"شرکت: {company}\n"
            "اطلاعات مهارت‌های موردنیاز کافی نیست.\n"
            "بررسی توضیحات کامل آگهی ضروری است."
        )

    result = match_skills(skills)

    lines = [
        f"شغل: {title}",
        f"شرکت: {company}",
        f"تطبیق دقیق: {result['skill_coverage']}٪",
        f"تطبیق وزنی: {result['weighted_coverage']}٪",
        "",
        "مهارت‌های ثبت‌شده در رزومه:",
    ]

    lines.extend(
        f"✓ {skill}"
        for skill in result["matched_skills"]
    )

    lines.append("\nدانش پایه:")

    lines.extend(
        f"~ {item['required']} "
        f"(رزومه: {item['resume_evidence']})"
        for item in result["foundational_skills"]
    )

    lines.append("\nمهارت‌های نیازمند بررسی:")

    lines.extend(
        f"? {skill}"
        for skill in result["unverified_skills"]
    )

    return "\n".join(lines)


if __name__ == "__main__":
    sample_job = {
        "title": "IT Support Technician",
        "company": "Test Company",
        "required_skills": [
            "Windows",
            "Linux",
            "DNS",
            "Active Directory",
            "Microsoft 365",
        ],
    }

    print(generate_job_advice(sample_job))
