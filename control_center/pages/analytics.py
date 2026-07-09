from __future__ import annotations

import streamlit as st

from control_center.data import (
    lifecycle_distribution,
    priority_distribution,
    subtrack_distribution,
)


def render() -> None:
    st.title("Analytics")

    st.caption("Application distribution and recruiting lifecycle visibility.")

    lifecycle = lifecycle_distribution()
    priority = priority_distribution()
    subtrack = subtrack_distribution()

    st.subheader("Lifecycle Distribution")

    if lifecycle.empty:
        st.info("Insufficient application data.")
    else:
        st.bar_chart(lifecycle.set_index("lifecycle_stage"))

    st.subheader("Priority Distribution")

    if not priority.empty:
        st.bar_chart(priority.set_index("priority"))

    st.subheader("Subtrack Distribution")

    if not subtrack.empty:
        st.bar_chart(subtrack.set_index("subtrack"))
