import pandas as pd
from nicegui import ui

from career_ui.components import (
    dataframe_table,
    empty_state,
    metric_card,
    page_header,
    section,
)
from career_ui.services.control_center import (
    application_summary,
    average_time_to_first_response_hours,
    lifecycle_distribution,
    read_applications,
    run_history,
    run_outcome_totals,
    segment_funnel,
)
from career_ui.shell import shell


def _compact_segment(frame):
    if frame is None or frame.empty:
        return frame
    cols = [
        c
        for c in frame.columns
        if c
        in {
            "priority",
            "subtrack",
            "applications",
            "response_rate",
            "interview_rate",
            "offer_rate",
        }
    ]
    return frame[cols]


def _compact_runs(frame):
    if frame is None or frame.empty:
        return frame
    cols = [
        c
        for c in (
            "run_id",
            "status",
            "dry_run",
            "max_applications",
            "acquired",
            "classified",
            "selected",
            "submitted",
            "failed",
            "started_at",
        )
        if c in frame.columns
    ]
    return frame[cols]


@ui.page("/analytics")
def page():
    shell("/analytics")
    with ui.column().classes("cw-content gap-5"):
        page_header(
            "INSIGHTS",
            "Analytics",
            "Conversion, response velocity, portfolio mix, and execution throughput.",
        )
        apps = read_applications()
        s = application_summary()
        total = int(s.get("total", 0))
        responded = sum(
            int(s.get(k, 0))
            for k in ("viewed", "shortlisted", "interview", "rejected", "offer")
        )
        avg = average_time_to_first_response_hours(apps)
        with ui.element("div").classes("cw-grid-4 w-full"):
            metric_card("Applications", total, "ledger total")
            metric_card(
                "Response Rate",
                f"{responded/total*100:.1f}%" if total else "0.0%",
                "any recruiter response",
            )
            metric_card(
                "Interview Rate",
                (
                    f'{(int(s.get("interview",0))+int(s.get("offer",0)))/total*100:.1f}%'
                    if total
                    else "0.0%"
                ),
                "interview or offer",
            )
            metric_card(
                "Avg Response",
                f"{avg:.1f}h" if avg is not None else "—",
                "time to first response",
            )
        runs = run_history(100)
        outcomes = run_outcome_totals(runs)
        section(
            "Automation outcomes",
            "Aggregate execution outcomes from recent run artifacts",
        )
        with ui.element("div").classes("cw-grid-4 w-full"):
            metric_card("Submitted", outcomes["submitted"], "successful submissions")
            metric_card("Failed", outcomes["failed"], "application failures")
            metric_card(
                "External", outcomes["skipped_external"], "manual external apply"
            )
            metric_card(
                "Manual Review", outcomes["manual_review"], "questionnaire backlog"
            )
        lifecycle = lifecycle_distribution()
        with ui.element("div").classes("cw-grid-2 w-full"):
            with ui.column().classes("gap-3"):
                section("Lifecycle distribution", "Current recruiting outcomes")
                if not lifecycle.empty:
                    cats = lifecycle.iloc[:, 0].astype(str).tolist()
                    vals = lifecycle.iloc[:, 1].fillna(0).astype(int).tolist()
                    ui.echart(
                        {
                            "backgroundColor": "transparent",
                            "tooltip": {
                                "trigger": "axis",
                                "axisPointer": {"type": "shadow"},
                            },
                            "grid": {"left": 48, "right": 24, "top": 24, "bottom": 48},
                            "xAxis": {
                                "type": "category",
                                "data": cats,
                                "axisLine": {"lineStyle": {"color": "#263548"}},
                                "axisLabel": {"color": "#77869a", "fontSize": 10},
                            },
                            "yAxis": {
                                "type": "value",
                                "axisLabel": {"color": "#77869a"},
                                "splitLine": {"lineStyle": {"color": "#1d2734"}},
                            },
                            "series": [
                                {
                                    "type": "bar",
                                    "data": vals,
                                    "barMaxWidth": 42,
                                    "itemStyle": {
                                        "color": "#7c8cff",
                                        "borderRadius": [6, 6, 0, 0],
                                    },
                                    "label": {
                                        "show": True,
                                        "position": "top",
                                        "color": "#aab7c8",
                                        "fontSize": 10,
                                    },
                                }
                            ],
                        }
                    ).classes("cw-card w-full h-80 p-3")
                else:
                    empty_state("No lifecycle data")
            with ui.column().classes("gap-3"):
                section("Application velocity", "Submissions over time")
                if not apps.empty and "applied_at" in apps:
                    ts = pd.to_datetime(apps.applied_at, errors="coerce", utc=True)
                    v = ts.dropna().dt.date.value_counts().sort_index()
                    if not v.empty:
                        ui.echart(
                            {
                                "backgroundColor": "transparent",
                                "tooltip": {"trigger": "axis"},
                                "grid": {
                                    "left": 48,
                                    "right": 24,
                                    "top": 24,
                                    "bottom": 48,
                                },
                                "xAxis": {
                                    "type": "category",
                                    "data": [str(x) for x in v.index],
                                    "axisLine": {"lineStyle": {"color": "#263548"}},
                                    "axisLabel": {"color": "#77869a"},
                                },
                                "yAxis": {
                                    "type": "value",
                                    "minInterval": 1,
                                    "axisLabel": {"color": "#77869a"},
                                    "splitLine": {"lineStyle": {"color": "#1d2734"}},
                                },
                                "series": [
                                    {
                                        "type": "line",
                                        "smooth": True,
                                        "data": v.astype(int).tolist(),
                                        "lineStyle": {"color": "#48d7ff", "width": 3},
                                        "areaStyle": {"color": "rgba(72,215,255,.10)"},
                                        "symbol": "circle",
                                        "symbolSize": 7,
                                        "itemStyle": {"color": "#48d7ff"},
                                    }
                                ],
                            }
                        ).classes("cw-card w-full h-80 p-3")
                    else:
                        empty_state(
                            "No dated application activity",
                            "Application records exist, but no valid applied_at timestamps are available.",
                        )
                else:
                    empty_state("No velocity data")
        with ui.element("div").classes("cw-grid-2 w-full"):
            with ui.column().classes("gap-3"):
                section("Performance by priority", "Segment conversion")
                dataframe_table(
                    _compact_segment(segment_funnel(apps, "priority")), pagination=10
                )
            with ui.column().classes("gap-3"):
                section("Performance by subtrack", "Role-family conversion")
                dataframe_table(
                    _compact_segment(segment_funnel(apps, "subtrack")), pagination=10
                )
        section(
            "Pipeline throughput",
            "Recent execution history · projected operational columns",
        )
        dataframe_table(_compact_runs(run_history(20)), pagination=10)
