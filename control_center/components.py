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
        column.metric(label, value)  # type: ignore


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


def header(title: str, subtitle: str, kicker: str = "OPERATIONS") -> None:
    from html import escape

    st.markdown(
        f"""
        <div class="cw-kicker">{escape(kicker)}</div>
        <h1>{escape(title)}</h1>
        <div class="cw-sub">{escape(subtitle)}</div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    from html import escape

    st.markdown(
        f"""
        <div class="cw-section">
            <div class="cw-section-title">{escape(title)}</div>
            <div class="cw-section-sub">{escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, detail: str, status: str) -> None:
    from html import escape

    st.markdown(
        f"""
        <div class="cw-hero">
            <div class="cw-row">
                <div>
                    <div class="cw-kicker">SYSTEM SNAPSHOT</div>
                    <div style="font-size:1.25rem;font-weight:730;color:#f3f6fb">
                        {escape(title)}
                    </div>
                    <div style="font-size:.8rem;color:#718096;margin-top:.25rem">
                        {escape(detail)}
                    </div>
                </div>
                <span class="cw-status">
                    <span class="cw-dot"></span>
                    {escape(status.upper())}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stages(data: dict[str, object]) -> None:
    from html import escape

    rows: list[str] = []

    for name, value in data.items():
        state = str(value or "PENDING").upper()

        css_class = (
            "ok"
            if state == "SUCCESS"
            else (
                "run"
                if state == "RUNNING"
                else "bad" if state in {"FAILED", "ORPHANED", "PARTIAL"} else ""
            )
        )

        display_name = escape(str(name).replace("_", " ").title())
        display_state = escape(state)

        rows.append(
            f'<div class="cw-stage">'
            f'<span class="cw-stage-dot {css_class}"></span>'
            f'<span class="cw-stage-name">{display_name}</span>'
            f'<span class="cw-stage-state">{display_state}</span>'
            f"</div>"
        )

    html = '<div class="cw-panel">' + "".join(rows) + "</div>"

    st.markdown(html, unsafe_allow_html=True)


def funnel(items: list[tuple[str, int]]) -> None:
    from html import escape

    peak = max([value for _, value in items] or [1]) or 1
    rows: list[str] = []

    for name, value in items:
        width = int(value / peak * 100) if value else 0

        rows.append(
            f'<div class="cw-funnel">'
            f'<div class="cw-funnel-name">{escape(name)}</div>'
            f'<div class="cw-track">'
            f'<div class="cw-fill" style="width:{width}%"></div>'
            f"</div>"
            f'<div class="cw-value">{value:,}</div>'
            f"</div>"
        )

    html = '<div class="cw-panel">' + "".join(rows) + "</div>"

    st.markdown(html, unsafe_allow_html=True)
