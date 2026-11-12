
import base64
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import markdown
import streamlit as st

from job_sources.gmail_reader import authenticate_gmail
from job_sources.job_details_extractor import extract_job_details
from job_sources.automatic_job_description import get_automatic_description
from matching.job_pipeline import evaluate_jobs
from matching.language_filter import check_job_language
from matching.ai_analyzer import analyze_job
from matching.job_workspace import (
    save_job_workspace,
    get_job_directory,
    verify_job_workspace,
)
from matching.resume_tailor import tailor_resume


BASE_DIR = Path(__file__).resolve().parent
WORKSPACES_DIR = BASE_DIR / "outputs" / "jobs"
MIN_DESCRIPTION_LENGTH = 200
REPORT_VERSION = "persian-v2"

st.set_page_config(
    page_title="AI Job Hunter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -------------------- DESIGN --------------------

st.markdown(
    """
<style>
.stApp {
    background: #f3f6fb;
    color: #172b4d;
}
[data-testid="stHeader"] {
    background: #f3f6fb;
}
.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}
.hero {
    background: linear-gradient(110deg,#ffffff,#eaf1ff);
    padding: 28px 32px;
    border: 1px solid #e0e8f4;
    border-radius: 22px;
    margin-bottom: 22px;
}
.hero h1 {
    color: #173c85;
    margin: 0;
    font-size: 34px;
}
.hero p {
    color: #64748b;
    margin: 7px 0 0;
}
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e1e8f2;
    border-radius: 16px;
    padding: 18px;
}
[data-testid="stMetricValue"] {
    color: #155eef;
}
[data-testid="stMetricLabel"] {
    color: #334155 !important;
}

[data-testid="stMetricLabel"] p {
    color: #334155 !important;
    font-weight: 700 !important;
}

[data-testid="stLinkButton"] a {
    background: #172b4d !important;
    color: #ffffff !important;
    border: 1px solid #172b4d !important;
    border-radius: 12px !important;
}

[data-testid="stLinkButton"] a:hover {
    background: #155eef !important;
    color: #ffffff !important;
    border-color: #155eef !important;
}

[data-testid="stLinkButton"] a:hover p {
    color: #ffffff !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: white;
    border: 1px solid #e1e8f2;
    border-radius: 20px;
    box-shadow: 0 5px 22px rgba(20,45,90,.04);
}
.job-title {
    color: #152b4f;
    font-size: 23px;
    font-weight: 750;
}
.job-meta {
    color: #68788e;
    margin: 6px 0 14px;
}
.status {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 30px;
    background: #e6f5ec;
    color: #087b42;
    font-size: 13px;
    font-weight: 700;
}
[data-testid="stButton"] button {
    border-radius: 12px;
    min-height: 46px;
    font-weight: 650;
}
[data-testid="stButton"] button[kind="primary"] {
    background: #155eef;
    color: white;
    border: none;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: #1048c4;
}
[data-testid="stTextArea"] textarea {
    background: white;
    color: #172b4d;
    border-radius: 12px;
}
[data-testid="stExpander"] {
    background: #f8faff;
    border-radius: 14px;
}
.persian-report {
    direction: rtl;
    text-align: right;
    background: #ffffff;
    color: #243450;
    border: 1px solid #e0e8f4;
    border-radius: 18px;
    padding: 24px 30px;
    font-family: Tahoma, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.9;
    overflow-wrap: anywhere;
}
.persian-report h1,
.persian-report h2,
.persian-report h3,
.persian-report h4 {
    direction: rtl;
    text-align: right;
    color: #174db0;
    margin: 17px 0 8px;
}
.persian-report p,
.persian-report li {
    direction: rtl;
    text-align: right;
    color: #243450;
}
.persian-report ul,
.persian-report ol {
    direction: rtl;
    text-align: right;
    padding-right: 26px;
    padding-left: 0;
}
.persian-report code {
    direction: ltr;
    unicode-bidi: isolate;
    background: #edf3ff;
    color: #155eef;
    padding: 2px 5px;
    border-radius: 5px;
}
.persian-report table {
    width: 100%;
    border-collapse: collapse;
}
.persian-report th,
.persian-report td {
    border: 1px solid #dce5f4;
    padding: 8px;
    text-align: right;
}

/* Fix Streamlit button contrast */
.stApp [data-testid="stButton"] button {
    background-color: #ffffff !important;
    color: #173c85 !important;
    border: 1px solid #b8c8df !important;
    font-weight: 650 !important;
}

.stApp [data-testid="stButton"] button * {
    color: inherit !important;
}

.stApp [data-testid="stButton"] button[kind="primary"] {
    background-color: #155eef !important;
    color: #ffffff !important;
    border-color: #155eef !important;
}

.stApp [data-testid="stDownloadButton"] button {
    background-color: #155eef !important;
    color: #ffffff !important;
    border: none !important;
}

.stApp [data-testid="stDownloadButton"] button * {
    color: #ffffff !important;
}

/* Fix success message readability */
.stApp [data-testid="stAlert"] {
    color: #17324d !important;
}

.stApp [data-testid="stAlert"] * {
    color: #17324d !important;
}

.stApp [data-testid="stAlert"] p {
    font-weight: 600 !important;
}

/* Fix expander heading readability */
.stApp [data-testid="stExpander"] summary {
    background-color: #ffffff !important;
    color: #173c85 !important;
}

.stApp [data-testid="stExpander"] summary * {
    color: #173c85 !important;
}


/* Base Resume Upload — light theme */
[data-testid="stFileUploader"] section {
    background-color: #EAF2FF !important;
    border: 2px dashed #2563EB !important;
    border-radius: 12px !important;
}

[data-testid="stFileUploader"] section button {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: 1px solid #2563EB !important;
    border-radius: 8px !important;
}

[data-testid="stFileUploader"] section button:hover {
    background-color: #1D4ED8 !important;
    color: #FFFFFF !important;
}

[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] section * {
    color: #17365D;
}


/* White text and icon on Upload button */
[data-testid="stFileUploader"] section button,
[data-testid="stFileUploader"] section button *,
[data-testid="stFileUploader"] section button svg {
    color: #FFFFFF !important;
    fill: none !important;
    stroke: #FFFFFF !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# -------------------- HELPERS --------------------

def find_html(payload):
    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode(
                "utf-8",
                errors="replace",
            )

    for part in payload.get("parts", []):
        found = find_html(part)
        if found:
            return found

    return None


def remove_duplicates(jobs):
    seen = set()
    result = []

    for job in jobs:
        key = (
            str(job.get("title") or "").strip().casefold(),
            str(job.get("company") or "").strip().casefold(),
            str(job.get("location") or "").strip().casefold(),
        )

        if key not in seen:
            seen.add(key)
            result.append(job)

    return result


def load_jobs():
    service = authenticate_gmail()

    response = service.users().messages().list(
        userId="me",
        q=(
            "from:(donotreply@jobalert.indeed.com "
            "OR donotreply@match.indeed.com)"
        ),
        maxResults=10,
    ).execute()

    jobs = []

    for item in response.get("messages", []):
        message = service.users().messages().get(
            userId="me",
            id=item["id"],
            format="full",
        ).execute()

        content = find_html(message["payload"])

        if content:
            received_at = datetime.fromtimestamp(
                int(message["internalDate"]) / 1000,
                tz=timezone.utc,
            ).isoformat()

            extracted_jobs = extract_job_details(content)

            for job in extracted_jobs:
                job["email_received_at"] = received_at

            jobs.extend(extracted_jobs)

    return evaluate_jobs(remove_duplicates(jobs))


def job_key(job):
    raw = "|".join(
        str(job.get(field) or "")
        for field in (
            "title",
            "company",
            "location",
            "url",
        )
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:16]


def is_persian(text):
    letters = re.findall(
        r"[A-Za-z\u0600-\u06FF]",
        text,
    )

    persian = re.findall(
        r"[\u0600-\u06FF]",
        text,
    )

    return (
        bool(letters)
        and len(persian) / len(letters) >= 0.20
    )


def render_report(text):
    safe_text = html.escape(text)

    rendered = markdown.markdown(
        safe_text,
        extensions=["extra", "sane_lists"],
    )

    st.markdown(
        '<div class="persian-report" dir="rtl">'
        + rendered
        + "</div>",
        unsafe_allow_html=True,
    )


def verified_language(job, description):
    return check_job_language({
        "title": job.get("title", ""),
        "description": description,
    })


# -------------------- JOB ANALYSIS --------------------

def run_analysis(job, description, key, source):
    description = (description or "").strip()

    if len(description) < MIN_DESCRIPTION_LENGTH:
        st.warning(
            "Please provide the complete Job Description."
        )
        return

    language = verified_language(
        job,
        description,
    )

    st.session_state[f"language_{key}"] = language

    if language["status"] == "rejected":
        st.error(
            "Rejected: This job requires an additional language."
        )
        return

    if (
        language["status"] == "manual_review"
        and not st.session_state.get(
            f"language_confirmed_{key}",
            False,
        )
    ):
        st.warning(
            "Additional language mentioned. "
            "Confirm that it is not mandatory."
        )
        return

    if key != job_key(job):
        st.error(
            "Job ID mismatch. Analysis stopped."
        )
        return

    try:
        job_dir = save_job_workspace(
            job_id=key,
            job=job,
            description=description,
        )
    except Exception as error:
        st.error(
            f"Job Workspace validation failed: {error}"
        )
        return

    full_description = (
        f"Job Title: {job.get('title', '')}\n"
        f"Company: {job.get('company', '')}\n"
        f"Location: {job.get('location', '')}\n\n"
        f"{description}"
    )

    with st.spinner("Analyzing your resume..."):
        try:
            result = analyze_job(
                full_description
            )

            if not is_persian(result):
                st.error(
                    "GPT returned an English report. "
                    "It was not accepted as a Persian analysis."
                )
                return

            st.session_state[
                f"analysis_{key}"
            ] = result

            st.session_state[
                f"source_{key}"
            ] = source

            st.session_state[
                f"version_{key}"
            ] = REPORT_VERSION

            st.session_state[
                f"workspace_{key}"
            ] = str(job_dir)

        except Exception as error:
            st.error(
                f"Analysis failed: {error}"
            )


# -------------------- RESUME WORKFLOW --------------------

def render_resume_workflow(
    job_id,
    description,
    view="saved",
    analysis=None,
):
    """
    Generate and review a tailored resume.

    Never submit a job application automatically.
    """

    description = (
        description or ""
    ).strip()

    if len(description) < 200:
        st.warning("A complete job description is required.")
        return

    folder = get_job_directory(job_id)

    approval_path = folder / "analysis_approval.json"
    approval_hash = hashlib.sha256(
        (description + "\n" + (analysis or "")).encode("utf-8")
    ).hexdigest()

    approved = False

    if analysis:
        try:
            record = json.loads(
                approval_path.read_text(encoding="utf-8")
            )
            approved = (
                record.get("job_id") == job_id
                and record.get("approval_hash") == approval_hash
            )
        except (OSError, ValueError, TypeError):
            pass

        if not approved:
            if st.button(
                "✅ Approve Analysis",
                key=f"approve_analysis_{view}_{job_id}",
            ):
                approval_path.write_text(
                    json.dumps({
                        "job_id": job_id,
                        "approval_hash": approval_hash,
                        "analysis": analysis,
                    }, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                st.rerun()
            return

        st.success("AI Analysis approved.")
    else:
        st.info("Run AI Analysis before generating a resume.")
        return

    draft_path = (
        folder / "tailored_resume_DRAFT.md"
    )

    review_path = (
        folder / "resume_review.json"
    )

    st.markdown(
        "### 📄 Tailored Resume"
    )

    st.caption("Uses verified facts from your original resume.")

    draft_marker = folder / "resume_analysis_hash.txt"

    base_resume_path = (
        Path(__file__).resolve().parent
        / "resume/Jahani_ATS_Resume.pdf"
    )
    base_resume_hash = hashlib.sha256(
        base_resume_path.read_bytes()
    ).hexdigest()

    resume_hash_marker = folder / "resume_base_hash.txt"
    saved_resume_hash = (
        resume_hash_marker.read_text(encoding="utf-8").strip()
        if resume_hash_marker.is_file()
        else None
    )

    base_resume_changed = (
        draft_path.is_file()
        and saved_resume_hash != base_resume_hash
    )

    if base_resume_changed:
        st.warning(
            "Base Resume has changed or this draft predates "
            "resume version tracking. Regeneration is recommended."
        )

    draft_valid = (
        draft_path.is_file()
        and draft_marker.is_file()
        and draft_marker.read_text(encoding="utf-8").strip()
        == approval_hash
    )

    if draft_path.is_file() and not draft_valid:
        st.warning(
            "This resume was generated from an earlier analysis. "
            "You can preview and download it, but review its "
            "content before applying."
        )

    if draft_path.is_file() and (base_resume_changed or not draft_valid):
        if st.button(
            "🔄 Regenerate Tailored Resume (uses API)",
            key=f"regenerate_resume_{view}_{job_id}",
        ):
            from datetime import datetime as ResumeDateTime

            with st.spinner("Regenerating from the active Base Resume..."):
                try:
                    result = tailor_resume(
                        job_id=job_id,
                        job_description=description,
                        approved_analysis=analysis,
                    )

                    if result.get("status") != "draft_pending_approval":
                        raise ValueError("Unexpected resume status.")

                    new_draft = result["tailored_resume"]
                    if not new_draft.strip():
                        raise ValueError("Generated resume is empty.")

                    backup_dir = folder / "resume_backups"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    backup_path = backup_dir / (
                        "tailored_resume_"
                        + ResumeDateTime.now().strftime("%Y%m%d_%H%M%S_%f")
                        + ".md"
                    )

                    backup_path.write_bytes(draft_path.read_bytes())
                    draft_path.write_text(new_draft, encoding="utf-8")

                    draft_marker.write_text(approval_hash, encoding="utf-8")
                    resume_hash_marker.write_text(
                        base_resume_hash, encoding="utf-8"
                    )

                    st.success("Resume regenerated. Previous draft backed up.")
                    st.rerun()

                except Exception as error:
                    st.error(f"Resume regeneration failed: {error}")

    if not draft_path.is_file():

        if st.button(
            "✨ Generate Tailored Resume (uses API)",
            key=f"generate_resume_{view}_{job_id}",
        ):
            with st.spinner(
                "Generating resume draft..."
            ):
                try:
                    result = tailor_resume(
                        job_id=job_id,
                        job_description=description,
                        approved_analysis=analysis,
                    )

                    if (
                        result.get("status")
                        != "draft_pending_approval"
                    ):
                        raise ValueError(
                            "Unexpected resume status."
                        )

                    # Exclusive creation prevents
                    # accidental overwriting.
                    with draft_path.open(
                        "x",
                        encoding="utf-8",
                    ) as output:
                        output.write(
                            result["tailored_resume"]
                        )

                    draft_marker.write_text(
                        approval_hash,
                        encoding="utf-8",
                    )

                    st.success(
                        "Draft saved. "
                        "Please review before approving."
                    )

                    st.rerun()

                except Exception as error:
                    st.error(
                        "Resume generation failed: "
                        f"{error}"
                    )

        return

    # Load existing draft without API.
    try:
        draft = draft_path.read_text(
            encoding="utf-8"
        )
    except OSError as error:
        st.error(
            f"Cannot read resume draft: {error}"
        )
        return

    draft_hash = hashlib.sha256(
        draft.encode("utf-8")
    ).hexdigest()

    st.success(
        "Existing resume draft loaded — "
        "no API call needed."
    )

    with st.expander(
        "👁️ Preview Resume",
        expanded=False,
    ):
        st.markdown(draft)

    from resume.pdf_export import resume_to_pdf

    st.download_button(
        "⬇️ Download Resume (PDF)",
        data=resume_to_pdf(draft),
        file_name=f"{job_id}_tailored_resume.pdf",
        mime="application/pdf",
        key=f"download_resume_{view}_{job_id}",
    )



# -------------------- HEADER --------------------

st.markdown(
    """
<div class="hero">
  <h1>🎯 AI Job Hunter</h1>
  <p>Your personal AI-powered IT career assistant</p>
</div>
""",
    unsafe_allow_html=True,
)

left, right = st.columns([3, 1])

with left:
    st.caption(
        "Discover jobs, verify requirements "
        "and analyze your resume."
    )

with right:
    scan = st.button(
        "🔄 Scan Gmail",
        type="primary",
        use_container_width=True,
    )

if scan:
    with st.spinner(
        "Scanning Gmail..."
    ):
        try:
            st.session_state[
                "jobs"
            ] = load_jobs()

        except Exception as error:
            st.error(
                f"Gmail scan failed: {error}"
            )



# -------------------- BASE RESUME MANAGER --------------------

with st.expander("📄 Upload Base Resume"):
    from io import BytesIO
    from datetime import datetime as ResumeDateTime
    from pypdf import PdfReader

    uploaded_resume = st.file_uploader(
        "Upload your updated base resume (PDF)",
        type=["pdf"],
        key="base_resume_upload",
    )

    if uploaded_resume is not None:
        resume_bytes = uploaded_resume.getvalue()

        try:
            reader = PdfReader(BytesIO(resume_bytes))
            extracted = "\\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

            if not extracted.strip():
                raise ValueError("PDF has no extractable text.")

            if len(extracted.strip()) < 100:
                raise ValueError(
                    "Resume text is too short to validate."
                )

            st.success(
                f"PDF validated. {len(reader.pages)} pages, "
                "Text extraction successful."
            )

            if st.button("✅ Set as Active Base Resume"):
                target = Path(__file__).resolve().parent / (
                    "resume/Jahani_ATS_Resume.pdf"
                )
                target.parent.mkdir(parents=True, exist_ok=True)

                if target.exists():
                    backup_dir = target.parent / "backups"
                    backup_dir.mkdir(exist_ok=True)
                    backup = backup_dir / (
                        "base_resume_"
                        + ResumeDateTime.now().strftime(
                            "%Y%m%d_%H%M%S_%f"
                        )
                        + ".pdf"
                    )
                    backup.write_bytes(target.read_bytes())

                target.write_bytes(resume_bytes)

                st.success(
                    "Active Base Resume updated successfully."
                )

        except Exception as error:
            st.error(f"Resume validation failed: {error}")


# -------------------- JOB LIST --------------------

jobs = st.session_state.get(
    "jobs",
    [],
)

if jobs:
    jobs = evaluate_jobs(jobs)

    st.session_state[
        "jobs"
    ] = jobs

    review = [
        job
        for job in jobs
        if job.get("final_status")
        != "rejected"
    ]

    rejected = [
        job
        for job in jobs
        if job.get("final_status")
        == "rejected"
    ]

    review.sort(
        key=lambda job: (
            job.get("match_score") or 0
        ),
        reverse=True,
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Jobs Evaluated",
        len(jobs),
    )

    c2.metric(
        "For Review",
        len(review),
    )

    c3.metric(
        "Rejected",
        len(rejected),
    )

    st.subheader(
        "Job Opportunities"
    )

    for job in review:
        key = job_key(job)

        with st.container(border=True):
            title = html.escape(
                str(
                    job.get("title")
                    or "Unknown"
                )
            )

            company = html.escape(
                str(
                    job.get("company")
                    or "Unknown"
                )
            )

            location = html.escape(
                str(
                    job.get("location")
                    or "Unknown"
                )
            )

            st.markdown(
                f'<div class="job-title">{title}</div>'
                f'<div class="job-meta">'
                f'{company} · {location}</div>'
                '<span class="status">For Review</span>',
                unsafe_allow_html=True,
            )

            received_at = job.get("email_received_at")

            if received_at:
                received_date = datetime.fromisoformat(
                    received_at
                ).strftime("%b %d, %Y")

                st.caption(
                    f"📅 Email Received: {received_date}"
                )

            st.caption(
                "Title Score: "
                f"{job.get('match_score', 'N/A')} "
                "(rule-based)"
            )

            if job.get("url"):
                st.link_button(
                    "View Original Job",
                    job["url"],
                )

            st.markdown(
                "##### Choose how to get the description"
            )

            auto_col, manual_col = (
                st.columns(2)
            )

            with auto_col:
                auto_clicked = st.button(
                    "🔎 Auto Fetch",
                    key=f"auto_{key}",
                    use_container_width=True,
                    type="primary",
                )

            with manual_col:
                manual_clicked = st.button(
                    "📋 Copy & Paste",
                    key=f"paste_{key}",
                    use_container_width=True,
                )

            if manual_clicked:
                st.session_state[
                    f"manual_open_{key}"
                ] = not st.session_state.get(
                    f"manual_open_{key}",
                    False,
                )

            if auto_clicked:
                with st.spinner(
                    "Finding description..."
                ):
                    try:
                        result = (
                            get_automatic_description(
                                job
                            )
                        )

                        if (
                            result.get("status")
                            == "success"
                            and result.get(
                                "description"
                            )
                        ):
                            st.session_state[
                                f"description_{key}"
                            ] = result[
                                "description"
                            ]

                            st.session_state[
                                f"description_source_{key}"
                            ] = result.get(
                                "source_url"
                            )

                            st.success(
                                "Job Description found."
                            )

                        else:
                            st.warning(
                                "Auto Fetch unavailable. "
                                "Use Copy & Paste."
                            )

                    except Exception as error:
                        st.warning(
                            "Auto Fetch failed: "
                            f"{error}"
                        )

            if st.session_state.get(
                f"manual_open_{key}",
                False,
            ):
                st.text_area(
                    "Full Job Description",
                    key=f"manual_description_{key}",
                    height=220,
                )

            description = (
                st.session_state.get(
                    f"description_{key}",
                    "",
                )
            )

            manual_description = (
                st.session_state.get(
                    f"manual_description_{key}",
                    "",
                )
            )

            if manual_description.strip():
                description = (
                    manual_description
                )
                source = (
                    "Manual copy/paste"
                )
            else:
                source = (
                    st.session_state.get(
                        f"description_source_{key}"
                    )
                )

            if description:
                st.caption(
                    "Description ready: "
                    f"{len(description)} characters"
                )

                language = verified_language(
                    job,
                    description,
                )

                if language["status"] == "rejected":
                    st.error(
                        "Rejected — Additional "
                        "language required."
                    )

                else:
                    if (
                        language["status"]
                        == "manual_review"
                    ):
                        st.checkbox(
                            "I verified that the additional "
                            "language is NOT mandatory.",
                            key=(
                                f"language_confirmed_{key}"
                            ),
                        )

                    if st.button(
                        "🧠 Analyze with GPT",
                        key=f"analyze_{key}",
                        type="primary",
                    ):
                        st.session_state.pop(
                            f"analysis_{key}",
                            None,
                        )

                        run_analysis(
                            job,
                            description,
                            key,
                            source,
                        )

            analysis = (
                st.session_state.get(
                    f"analysis_{key}"
                )
            )

            version = (
                st.session_state.get(
                    f"version_{key}"
                )
            )

            if (
                analysis
                and version == REPORT_VERSION
            ):
                st.divider()

                st.markdown(
                    "### AI Analysis · فارسی"
                )

                render_report(
                    analysis
                )

                render_resume_workflow(
                    key,
                    description,
                    view="listing",
                    analysis=analysis,
                )

    with st.expander(
        f"Rejected Jobs ({len(rejected)})"
    ):
        for job in rejected:
            st.write(
                f"**{job.get('title', 'Unknown')}** "
                f"— {job.get('location', 'Unknown')}"
            )

            st.caption(
                f"Location: {job.get('location_status', 'Unknown')} | "
                f"Language: {job.get('language_status', 'Unknown')}"
            )

else:
    st.info(
        "Click Scan Gmail to load job opportunities."
    )


# -------------------- SAVED WORKSPACES --------------------

st.divider()

with st.expander(
    "📁 Saved Job Workspaces & Resume Drafts"
):
    found = False

    if WORKSPACES_DIR.is_dir():
        metadata_files = sorted(
            WORKSPACES_DIR.glob(
                "*/job_metadata.json"
            )
        )

        for metadata_path in metadata_files:
            job_id = (
                metadata_path.parent.name
            )

            try:
                metadata = json.loads(
                    metadata_path.read_text(
                        encoding="utf-8"
                    )
                )

                description_path = (
                    metadata_path.parent
                    / "job_description.txt"
                )

                description = (
                    description_path.read_text(
                        encoding="utf-8"
                    ).strip()
                )

                if (
                    metadata.get("job_id")
                    != job_id
                ):
                    continue

                if not verify_job_workspace(
                    job_id,
                    description,
                ):
                    continue

            except (
                OSError,
                ValueError,
                KeyError,
                TypeError,
            ):
                continue

            found = True

            st.markdown(
                "**"
                + str(
                    metadata.get(
                        "title",
                        "Unknown",
                    )
                )
                + " — "
                + str(
                    metadata.get(
                        "company",
                        "Unknown",
                    )
                )
                + "**"
            )

            render_resume_workflow(
                job_id,
                description,
                view="saved",
            )

            st.divider()

    if not found:
        st.caption(
            "No saved job workspaces yet."
        )
