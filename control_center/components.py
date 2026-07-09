from __future__ import annotations

from collections.abc import Iterable

import streamlit as st


def page_header(title: str, caption: str) -> None:
    st.title(title)
    st.caption(caption)


def empty_state(message: str) -> None:
    st.info(message)


def metric_row(items: Iterable[tuple[str, object]]) -> None:
    values = list(items)
    if not values:
        return
    columns = st.columns(len(values))
    for column, (label, value) in zip(columns, values, strict=True):
        column.metric(label, value)


def status_banner(status: str) -> None:
    normalized = str(status or "UNKNOWN").upper()
    if normalized in {"SUCCESS", "COMPLETED"}:
        st.success(f"Process state: {normalized}")
    elif normalized in {"FAILED", "ERROR", "UNKNOWN"}:
        st.error(f"Process state: {normalized}")
    elif normalized == "RUNNING":
        st.warning("Process state: RUNNING")
    else:
        st.info(f"Process state: {normalized}")
