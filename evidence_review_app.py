
import streamlit as st

from matching.evidence_review import (
    load_review,
    save_review,
    export_approved_evidence,
    classify_review_priority,
)

st.set_page_config(
    page_title="AI Job Hunter | Smart Evidence Review",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 AI Job Hunter")
st.subheader("Smart Evidence Review")

st.caption(
    "Risk-based review of resume evidence. "
    "No evidence is automatically approved."
)

try:
    review = load_review()
except Exception as exc:
    st.error(f"Cannot load evidence review: {exc}")
    st.stop()

requirements = review["requirements"]

for item in requirements:
    item["review_priority"] = classify_review_priority(item)

total = len(requirements)
standard = sum(
    item["review_priority"] == "standard"
    for item in requirements
)
needs_review = sum(
    item["review_priority"] == "needs_review"
    for item in requirements
)
excluded = sum(
    item["review_priority"] == "excluded"
    for item in requirements
)
approved = sum(
    item.get("approved") is True
    for item in requirements
)

st.write(
    "**Job:**",
    review.get("job_title", "Unknown"),
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total", total)
c2.metric("Needs Review", needs_review)
c3.metric("Standard", standard)
c4.metric("Excluded", excluded)
c5.metric("Approved", approved)

st.divider()

st.info(
    "Start with Needs Review. Standard items are "
    "lower-priority candidates, not verified approvals. "
    "Excluded items cannot be approved without evidence."
)

filter_choice = st.selectbox(
    "Show requirements",
    [
        "Needs Review",
        "Standard",
        "Excluded",
        "All",
        "Approved",
        "Not Approved",
    ],
)

visible_items = []

for item in requirements:
    priority = item["review_priority"]
    is_approved = item.get("approved") is True

    if filter_choice == "Needs Review" and priority != "needs_review":
        continue
    if filter_choice == "Standard" and priority != "standard":
        continue
    if filter_choice == "Excluded" and priority != "excluded":
        continue
    if filter_choice == "Approved" and not is_approved:
        continue
    if filter_choice == "Not Approved" and is_approved:
        continue

    visible_items.append(item)

st.caption(
    f"Showing {len(visible_items)} of {total} requirements."
)

for item in visible_items:
    item_id = item["id"]
    match = item.get("reviewed_match", "not_verified")
    priority = item["review_priority"]
    is_approved = item.get("approved") is True

    label = (
        f"#{item_id} | {priority.upper()} | "
        f"{match.upper()} | {item['requirement']}"
    )

    with st.expander(label, expanded=False):
        st.markdown("**Job Requirement**")
        st.write(item["requirement"])

        st.markdown("**Original Resume Evidence**")
        st.code(
            item.get("resume_evidence", "").strip()
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

        options = ["direct", "related", "not_verified"]

        selected_match = st.selectbox(
            "Reviewed Match",
            options,
            index=options.index(match)
            if match in options else 2,
            key=f"match_{item_id}",
        )

        has_evidence = bool(
            str(item.get("resume_evidence", "")).strip()
        )

        can_approve = (
            selected_match != "not_verified"
            and has_evidence
        )

        approved_value = st.checkbox(
            "Approve this evidence",
            value=is_approved if can_approve else False,
            disabled=not can_approve,
            key=f"approved_{item_id}",
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
            item["reviewed_match"] = selected_match
            item["approved"] = (
                approved_value if can_approve else False
            )
            item["review_note"] = note

            try:
                save_review(review)
                st.success("Review saved.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

st.divider()

st.subheader("Export Approved Evidence")

st.warning(
    "Only explicitly approved evidence will be exported. "
    "Exporting does not apply for jobs."
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
            "outputs/PCe_APPROVED_EVIDENCE.json",
            language=None,
        )
    except Exception as exc:
        st.error(str(exc))
