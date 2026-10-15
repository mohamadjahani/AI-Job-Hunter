from resume.resume_profile import build_resume_profile


def extract_resume_skills():
    profile = build_resume_profile()

    skills_text = profile["sections"].get(
        "TECHNICAL SKILLS", ""
    )

    skills = {}
    current_category = None
    previous_line_ended_with_semicolon = True
    for line in skills_text.splitlines():
        line = line.strip()

        if not line:
            continue

        if ":" in line:
            category, values = line.split(":", 1)
            current_category = category.strip()
            skills[current_category] = []
        else:
            if current_category is None:
                continue
            values = line

        parts = [
            part.strip()
            for part in values.split(";")
            if part.strip()
        ]

        if not parts:
            continue

        if (
            skills[current_category]
            and not previous_line_ended_with_semicolon
        ):
            skills[current_category][-1] += " " + parts[0]
            parts = parts[1:]

        skills[current_category].extend(parts)

        previous_line_ended_with_semicolon = (
            line.endswith(";")
        )

    return skills


if __name__ == "__main__":
    skills = extract_resume_skills()

    for category, items in skills.items():
        print(f"\n{category}")
        for skill in items:
            print(f"  - {skill}")
