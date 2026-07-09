from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.data import (
    ledger_path,
    manual_queue_path,
    runs_path,
    safe_settings,
)
from control_center.manual_jobs import MANUAL_JOBS_DB


def render() -> None:
    st.title("Settings")
    st.caption("Read-only operational configuration and storage paths.")

    st.subheader("Operational Configuration")
    settings = safe_settings()
    rows = [
        {"Setting": key, "Value": value or "DEFAULT / NOT SET"}
        for key, value in settings.items()
    ]
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Storage")
    storage = pd.DataFrame(
        [
            {
                "Store": "Application Ledger",
                "Path": str(ledger_path()),
                "Exists": ledger_path().exists(),
            },
            {
                "Store": "Run Artifacts",
                "Path": str(runs_path()),
                "Exists": runs_path().exists(),
            },
            {
                "Store": "Pipeline External Action Queue",
                "Path": str(manual_queue_path()),
                "Exists": manual_queue_path().exists(),
            },
            {
                "Store": "Manual External Jobs",
                "Path": str(MANUAL_JOBS_DB),
                "Exists": MANUAL_JOBS_DB.exists(),
            },
        ]
    )
    st.dataframe(storage, use_container_width=True, hide_index=True)

    st.info("Secret configuration is intentionally excluded from this page.")
