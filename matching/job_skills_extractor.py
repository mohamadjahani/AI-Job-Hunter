import re


SKILL_KEYWORDS = {
    "Windows": [r"\bwindows\b"],
    "Linux": [r"\blinux\b"],
    "TCP/IP": [r"\btcp/ip\b"],
    "DNS": [r"\bdns\b"],
    "DHCP": [r"\bdhcp\b"],
    "Active Directory": [
        r"\bactive directory\b",
        r"\bAD DS\b",
    ],
    "Microsoft 365": [
        r"\bmicrosoft 365\b",
        r"\boffice 365\b",
        r"\bm365\b",
    ],
    "Python": [r"\bpython\b"],
    "SQL": [r"\bsql\b"],
    "Splunk": [r"\bsplunk\b"],
    "Azure": [r"\bazure\b"],
    "AWS": [r"\baws\b"],
    "Networking": [r"\bnetworking\b"],
    "Troubleshooting": [r"\btroubleshooting\b"],
    "Hardware Support": [r"\bhardware support\b"],
}


def extract_job_skills(description):
    if not description or not description.strip():
        return []

    found_skills = []

    for skill, patterns in SKILL_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, description, re.IGNORECASE):
                found_skills.append(skill)
                break

    return found_skills


if __name__ == "__main__":
    sample_description = """
    We are hiring an IT Support Technician.

    Requirements:
    Experience with Windows and Linux.
    Knowledge of DNS, DHCP and TCP/IP.
    Familiarity with Active Directory and Office 365.
    Strong troubleshooting skills.
    """

    skills = extract_job_skills(sample_description)

    print("Extracted Job Skills:")
    for skill in skills:
        print("-", skill)
