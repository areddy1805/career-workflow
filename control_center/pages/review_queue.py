from __future__ import annotations

import streamlit as st

from control_center.data import read_manual_action_queue, review_cases


def render() -> None:
    st.title("Review Queue")
    st.caption("Failures, manual-review cases, and pending external actions.")

    failures = review_cases()
    external = read_manual_action_queue()

    pending_external = 0
    if not external.empty:
        if "status" in external.columns:
            pending_external = int(
                external["status"]
                .fillna("")
                .astype(str)
                .str.upper()
                .eq("PENDING")
                .sum()
            )
        else:
            pending_external = len(external)

    c1, c2 = st.columns(2)
    c1.metric("Application Review Cases", len(failures))
    c2.metric("Pending External Actions", pending_external)

    st.subheader("Application Failures and Manual Review")
    if failures.empty:
        st.info("No application failures or manual-review cases found.")
    else:
        columns = [
            "job_id", "title", "company", "location", "score",
            "priority", "status", "last_error", "last_updated_at",
            "lifecycle_stage",
        ]
        st.dataframe(
            failures[[c for c in columns if c in failures.columns]],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Pipeline External Actions")
    if external.empty:
        st.info("No external application actions found.")
    else:
        st.dataframe(external, use_container_width=True, hide_index=True)
