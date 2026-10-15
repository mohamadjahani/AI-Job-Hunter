
import streamlit as st

from matching.evidence_review import (
    load_review,
    save_review,
    export_approved_evidence,
)

st.set_page_config(
    page_title="AI Job Hunter | Evidence Review",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 AI Job Hunter")
st.subheader("Evidence Review & Human Approval")

st.caption(
    "Review resume evidence before generating a tailored resume."
)

try:
    review = load_review()
except Exception as exc:
    st.error(f"Cannot load evidence review: {exc}")
    st.stop()

requirements = review["requirements"]

total = len(requirements)
approved = sum(
    1 for item in requirements
    if item.get("approved") is True
)
pending = total - approved

c1, c2, c3 = st.columns(3)
c1.metric("Total Requirements", total)
c2.metric("Approved", approved)
c3.metric("Not Approved", pending)

st.divider()

st.write(
    "**Job:**",
    review.get("job_title", "Unknown"),
)

st.info(
    "Only approve evidence that accurately represents "
    "your real skills, education, and experience."
)

filter_choice = st.selectbox(
    "Filter requirements",
    [
        "All",
        "Direct",
        "Related",
        "Not Verified",
        "Approved",
        "Not Approved",
    ],
)

for item in requirements:
    match = item.get(
        "reviewed_match", "not_verified"
    )
    is_approved = item.get("approved", False)

    if filter_choice == "Direct" and match != "direct":
        continue
    if filter_choice == "Related" and match != "related":
        continue
    if (
        filter_choice == "Not Verified"
        and match != "not_verified"
    ):
        continue
    if filter_choice == "Approved" and not is_approved:
        continue
    if filter_choice == "Not Approved" and is_approved:
        continue

    item_id = item["id"]

    with st.expander(
        f"#{item_id} | {match.upper()} | "
        f"{item['requirement']}",
        expanded=False,
    ):
        st.markdown("**Requirement**")
        st.write(item["requirement"])

        st.markdown("**Original Resume Evidence**")
        st.code(
            item.get("resume_evidence", "")
            or "No verified evidence",
            language=None,
        )

        if item.get("supported_scope"):
            st.markdown("**Supported Scope**")
            st.write(item["supported_scope"])

        if item.get("unsupported_scope"):
            st.markdown("**Unsupported Scope**")
            st.write(item["unsupported_scope"])

        if item.get("explanation_fa"):
            st.markdown("**AI Explanation**")
            st.write(item["explanation_fa"])

        match_options = [
            "direct",
            "related",
            "not_verified",
        ]

        selected_match = st.selectbox(
            "Reviewed Match",
            match_options,
            index=match_options.index(match),
            key=f"match_{item_id}",
        )

        approved_value = st.checkbox(
            "Approve this evidence",
            value=is_approved,
            key=f"approved_{item_id}",
            disabled=(
                selected_match == "not_verified"
                or not item.get(
                    "resume_evidence", ""
                ).strip()
            ),
        )

        note = st.text_area(
            "Review Note",
            value=item.get("review_note", ""),
            key=f"note_{item_id}",
            height=80,
        )

        if st.button(
            "Save Review",
            key=f"save_{item_id}",
            type="primary",
        ):
            if (
                selected_match != "not_verified"
                and not item.get(
                    "resume_evidence", ""
                ).strip()
            ):
                st.error(
                    "Cannot approve a match "
                    "without verified evidence."
                )
            else:
                item["reviewed_match"] = selected_match
                item["approved"] = (
                    approved_value
                    and selected_match != "not_verified"
                )
                item["review_note"] = note

                save_review(review)
                st.success("Review saved.")
                st.rerun()

st.divider()

st.subheader("Export Approved Evidence")

st.warning(
    "Only approved requirements will be exported. "
    "Exporting does not submit any job application."
)

if st.button(
    "Export Approved Evidence",
    type="primary",
):
    try:
        result = export_approved_evidence()
        st.success(
            f"Export completed: "
            f"{result['approved_count']} "
            f"approved requirements."
        )
        st.code(
            "outputs/PCe_APPROVED_EVIDENCE.json"
        )
    except Exception as exc:
        st.error(str(exc))
