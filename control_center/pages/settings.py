from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.data import safe_settings


def render() -> None:
    st.title("Settings")

    st.caption("Read-only operational configuration.")

    settings = safe_settings()

    rows = [
        {
            "Setting": key,
            "Value": value or "DEFAULT / NOT SET",
        }
        for key, value in settings.items()
    ]

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    st.info("Secret configuration is intentionally excluded.")
