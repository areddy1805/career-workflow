import pandas as pd
from nicegui import ui

from career_ui.shell import shell
from career_ui.layouts.page import page_header, section_header, metrics_grid
from career_ui.components.cards import panel_p, metric_card
from career_ui.tables.data_table import DataTable
from career_ui.charts.echarts import Chart

from career_ui.services.control_center import (
    application_summary,
    average_time_to_first_response_hours,
    lifecycle_distribution,
    read_applications,
    run_history,
    run_outcome_totals,
    segment_funnel,
)

def _compact_segment(frame):
    if frame is None or frame.empty: return frame
    cols = [c for c in frame.columns if c in {"priority", "subtrack", "applications", "response_rate", "interview_rate", "offer_rate"}]
    return frame[cols]

def _compact_runs(frame):
    if frame is None or frame.empty: return frame
    cols = [c for c in ("run_id", "status", "dry_run", "max_applications", "acquired", "classified", "selected", "submitted", "failed", "started_at") if c in frame.columns]
    return frame[cols]

@ui.page("/analytics")
def page():
    shell("/analytics")
    with ui.column().classes("w-full max-w-[1600px] mx-auto p-4 gap-6 pb-20"):
        page_header("Analytics", "Conversion, response velocity, portfolio mix, and execution throughput.", kicker="Inspect")
        
        apps = read_applications()
        s = application_summary()
        total = int(s.get("total", 0))
        responded = sum(int(s.get(k, 0)) for k in ("viewed", "shortlisted", "interview", "rejected", "offer"))
        avg = average_time_to_first_response_hours(apps)
        
        with metrics_grid(cols=4):
            metric_card("Applications", total, "ledger total")
            metric_card("Response Rate", f"{responded/total*100:.1f}%" if total else "0.0%", "any recruiter response")
            metric_card("Interview Rate", f'{(int(s.get("interview",0))+int(s.get("offer",0)))/total*100:.1f}%' if total else "0.0%", "interview or offer")
            metric_card("Avg Response", f"{avg:.1f}h" if avg is not None else "—", "time to first response")
            
        runs = run_history(100)
        outcomes = run_outcome_totals(runs)
        
        with panel_p("w-full gap-4"):
            section_header("Automation Outcomes", "Aggregate execution outcomes from recent run artifacts")
            with metrics_grid(cols=4):
                metric_card("Submitted", outcomes["submitted"], "successful submissions", classes="border-none shadow-none bg-[var(--bg)]")
                metric_card("Failed", outcomes["failed"], "application failures", classes="border-none shadow-none bg-[var(--bg)]")
                metric_card("External", outcomes["skipped_external"], "manual external apply", classes="border-none shadow-none bg-[var(--bg)]")
                metric_card("Manual Review", outcomes["manual_review"], "questionnaire backlog", classes="border-none shadow-none bg-[var(--bg)]")
                
        with ui.element("div").classes("grid grid-cols-2 gap-6 w-full h-[400px]"):
            with panel_p("w-full min-w-0 overflow-hidden flex flex-col"):
                section_header("Lifecycle Distribution", "Current recruiting outcomes")
                lifecycle = lifecycle_distribution()
                if not lifecycle.empty:
                    cats = lifecycle.iloc[:, 0].astype(str).tolist()
                    vals = lifecycle.iloc[:, 1].fillna(0).astype(int).tolist()
                    Chart({
                        "grid": {"left": 40, "right": 20, "top": 20, "bottom": 30},
                        "xAxis": {"type": "category", "data": cats, "axisLabel": {"color": "var(--muted)"}},
                        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "var(--border)"}}, "axisLabel": {"color": "var(--muted)"}},
                        "series": [{"type": "bar", "data": vals, "itemStyle": {"color": "var(--primary)", "borderRadius": [4, 4, 0, 0]}}]
                    }, classes="w-full h-full min-h-[300px]")
                else:
                    from career_ui.components.feedback import empty_state
                    empty_state("No data")
                    
            with panel_p("w-full min-w-0 overflow-hidden flex flex-col"):
                section_header("Application Velocity", "Submissions over time")
                if not apps.empty and "applied_at" in apps:
                    ts = pd.to_datetime(apps.applied_at, errors="coerce", utc=True)
                    v = ts.dropna().dt.date.value_counts().sort_index()
                    if not v.empty:
                        Chart({
                            "grid": {"left": 40, "right": 20, "top": 20, "bottom": 30},
                            "xAxis": {"type": "category", "data": [str(x) for x in v.index], "axisLabel": {"color": "var(--muted)"}},
                            "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "var(--border)"}}, "axisLabel": {"color": "var(--muted)"}},
                            "series": [{"type": "line", "smooth": True, "data": v.astype(int).tolist(), "lineStyle": {"color": "var(--primary)", "width": 3}, "areaStyle": {"color": "rgba(115, 104, 244, 0.1)"}, "symbolSize": 0}]
                        }, classes="w-full h-full min-h-[300px]")
                    else:
                        from career_ui.components.feedback import empty_state
                        empty_state("No velocity data")
                else:
                    from career_ui.components.feedback import empty_state
                    empty_state("No velocity data")
                    
        with ui.element("div").classes("grid grid-cols-2 gap-6 w-full h-[450px]"):
            with panel_p("w-full min-w-0 overflow-hidden flex flex-col gap-2"):
                section_header("Performance by Priority", "Segment conversion")
                DataTable(_compact_segment(segment_funnel(apps, "priority")), classes="flex-1")
            with panel_p("w-full min-w-0 overflow-hidden flex flex-col gap-2"):
                section_header("Performance by Subtrack", "Role-family conversion")
                DataTable(_compact_segment(segment_funnel(apps, "subtrack")), classes="flex-1")
                
        with panel_p("w-full h-[400px] flex flex-col gap-2"):
            section_header("Pipeline Throughput", "Recent execution history")
            DataTable(_compact_runs(run_history(20)), classes="h-full flex-grow")
