# AI Job Hunter

**AI-Powered Job Search, Matching & Resume Tailoring Assistant**

A Python-based application designed to streamline job discovery, evaluate job requirements against verified resume evidence, and support responsible, human-reviewed resume tailoring.
## Overview

AI Job Hunter combines job discovery, Gmail job-alert processing, AI-assisted job analysis, and resume evidence validation in a Streamlit interface.

The project follows a **human-in-the-loop** approach: AI-generated recommendations and evidence matches are reviewed before being used for resume customization.

## Key Features

- **Job Discovery:** Process job opportunities from Gmail alerts and supported job sources.
- **Job Description Analysis:** Extract and analyze job requirements using AI.
- **Job Matching:** Compare job requirements with a candidate's resume and technical background.
- **Evidence Mapping:** Identify direct, related, and unverified qualifications.
- **Evidence Validation:** Check whether quoted evidence appears in the original resume.
- **Human Review:** Approve, reject, or reclassify evidence through a Streamlit review interface.
- **Resume Tailoring:** Generate draft resumes for individual job descriptions.
- **PDF Export:** Generate downloadable PDF resumes from tailored resume drafts using ReportLab.
- **Privacy Controls:** Exclude credentials, personal resumes, and generated outputs from version control.

## Technology Stack

- Python
- Streamlit
- OpenAI API
- Gmail API / OAuth
- Git and GitHub
- JSON-based evidence mapping and review

## Project Workflow
The project workflow is documented with Mermaid diagrams.

**[View Project Workflow Diagram](docs/workflow.md)**

1. Collect job opportunities.
2. Retrieve and analyze job descriptions.
3. Compare requirements against the original resume.
4. Validate extracted evidence.
5. Review evidence manually.
6. Export approved evidence.
7. Generate a tailored resume draft for further review.

**Note:** The approved-evidence export and resume-tailoring components are currently separate. Their integration is planned.

## Project Status

**Active Development**

The application currently includes a working Streamlit dashboard, AI-assisted analysis, evidence mapping, and a separate evidence-review interface.

Planned improvements include tighter integration between human-approved evidence and resume tailoring, automated testing, and enhanced job matching.

## Responsible AI Principles

The application is designed to avoid fabricating professional experience, qualifications, certifications, or technical skills.

AI-generated evidence matches are not treated as definitive proof of qualifications. Human review remains an essential part of the workflow.

## Security & Privacy

API credentials, OAuth tokens, private resumes, and generated outputs are excluded from Git version control using `.gitignore`.

Users must configure their own credentials locally.

## Author

**Mohammadhossein Jahani**

Calgary, Alberta, Canada

## License

No open-source license has been selected yet. All rights reserved.
