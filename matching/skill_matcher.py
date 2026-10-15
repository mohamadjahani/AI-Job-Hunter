from resume.skills_extractor import extract_resume_skills


SKILL_ALIASES = {
    "office 365": "microsoft 365",
    "m365": "microsoft 365",
    "ms 365": "microsoft 365",
    "active directory domain services": "active directory",
    "ad ds": "active directory",
}


def normalize_skill(skill):
    normalized = " ".join(skill.lower().strip().split())
    return SKILL_ALIASES.get(normalized, normalized)


def match_skills(required_skills):
    resume_skills = extract_resume_skills()

    all_resume_skills = [
        skill
        for category_skills in resume_skills.values()
        for skill in category_skills
    ]

    normalized_resume_skills = {
        normalize_skill(skill): skill
        for skill in all_resume_skills
    }

    matched = []
    foundational = []
    unverified = []

    for required_skill in required_skills:
        normalized_required = normalize_skill(required_skill)

        # Exact skill matching
        if normalized_required in normalized_resume_skills:
            matched.append(required_skill)
            continue

        # Foundational knowledge matching
        foundational_match = next(
            (
                resume_skill
                for resume_skill in all_resume_skills
                if normalize_skill(resume_skill)
                == normalized_required + " fundamentals"
            ),
            None,
        )

        if foundational_match:
            foundational.append({
                "required": required_skill,
                "resume_evidence": foundational_match,
            })
        else:
            unverified.append(required_skill)

    total = len(required_skills)

    # Exact skill coverage
    coverage = (
        round(len(matched) / total * 100)
        if total
        else 0
    )

    # Weighted skill coverage
    # Exact match = 1 point
    # Foundational knowledge = 0.5 point
    weighted_coverage = (
        round(
            (len(matched) + 0.5 * len(foundational))
            / total * 100
        )
        if total
        else 0
    )

    return {
        "matched_skills": matched,
        "foundational_skills": foundational,
        "unverified_skills": unverified,
        "skill_coverage": coverage,
        "weighted_coverage": weighted_coverage,
    }


if __name__ == "__main__":
    requirements = [
        "Windows",
        "Linux",
        "DNS",
        "Active Directory",
        "Microsoft 365",
    ]

    result = match_skills(requirements)

    print("Matched:", result["matched_skills"])
    print("Foundational:", result["foundational_skills"])
    print("Unverified:", result["unverified_skills"])
    print("Coverage:", result["skill_coverage"], "%")
    print("Weighted Coverage:", result["weighted_coverage"], "%")
