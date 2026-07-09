from __future__ import annotations

import streamlit as st

from control_center.data import review_cases


def render() -> None:
    st.title("Review Queue")

    st.caption("Application failures and cases requiring human attention.")

    cases = review_cases()

    if cases.empty:
        st.success("No jobs currently require manual review.")
        return

    st.dataframe(
        cases,
        use_container_width=True,
        hide_index=True,
    )
