from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.components import page_header
from control_center.diagnostics import (
    collect_health_checks,
    health_summary,
    required_health_ok,
)


def render() -> None:
    page_header(
        "System Health",
        "Local preflight diagnostics for the Career Workflow control center.",
    )

    if st.button("Run Diagnostics", type="primary"):
        st.rerun()

    checks = collect_health_checks()
    summary = health_summary(checks)

    metrics = st.columns(4)
    metrics[0].metric("Checks", summary["total"])
    metrics[1].metric("Pass", summary["pass"])
    metrics[2].metric("Warnings", summary["warn"])
    metrics[3].metric("Failures", summary["fail"])

    if required_health_ok(checks):
        st.success("All required control-center checks passed.")
    else:
        st.error("One or more required checks failed.")

    frame = pd.DataFrame(checks)
    st.dataframe(
        frame[["check", "status", "detail", "required"]],
        use_container_width=True,
        hide_index=True,
    )

    failures = frame.loc[frame["status"].eq("FAIL")]
    if not failures.empty:
        st.subheader("Required Fixes")
        for _, row in failures.iterrows():
            st.error(f"{row['check']}: {row['detail']}")
