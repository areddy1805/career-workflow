import html
import json
import pandas as pd
from nicegui import ui
from typing import Callable
from career_ui_legacy.layouts.page import section_header
from career_ui_legacy.components.badges import status_badge
from career_ui_legacy.components.cards import panel_p
from career_ui_legacy.services.control_center import (
    update_external_action_status,
    update_manual_job_status,
    workflow_queue_transition,
    workflow_queue_retry,
)
from src.application.workflow import WorkflowStatus

def show_job_drawer(job_data: dict, on_change: Callable | None = None):
    """
    Displays a universal job detail dialog / drawer for a given job record.
    Provides context-aware actions, pipeline timeline, and detailed inspection.
    """
    job_id = job_data.get('job_id') or job_data.get('id') or "Unknown ID"
    title = job_data.get('title', 'Unknown Title')
    company = job_data.get('company', 'Unknown Company')

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-6xl p-0 h-[85vh] flex flex-col bg-[var(--bg)] shadow-2xl'):
        # Header
        with ui.row().classes('w-full justify-between items-center p-4 border-b border-[var(--border)] bg-[var(--panel)] shrink-0'):
            with ui.column().classes('gap-1'):
                ui.label(title).classes('text-xl font-bold leading-tight')
                ui.label(f"{company} • {job_data.get('location', 'Remote/Unknown')}").classes('text-sm text-[var(--primary)] font-medium')
            with ui.row().classes('gap-2 items-center'):
                status_badge(job_data.get('status') or job_data.get('workflow_status') or 'UNKNOWN')
                ui.button(icon='close', on_click=dialog.close).props('flat dense').classes('ml-2')

        # Body
        with ui.row().classes('w-full flex-grow min-h-0 flex-nowrap'):

            # Left pane (Main Info & Actions)
            with ui.column().classes('flex-[2] h-full overflow-y-auto p-6 border-r border-[var(--border)] gap-6'):

                # Actions Toolbar
                with ui.row().classes('w-full gap-2 p-3 bg-[var(--panel)] rounded border border-[var(--border)] items-center flex-wrap shadow-sm'):
                    ui.label("Operations").classes("text-xs uppercase tracking-wider font-bold text-[var(--muted)] mr-2")

                    url = job_data.get('url') or job_data.get('source_url')
                    if url and (pd.notna(url) if 'pd' in globals() else True):
                        ui.button("Open Link [O]", icon="open_in_new", on_click=lambda: ui.navigate.to(url, new_tab=True)).props('outline dense size=sm')

                    ui.button("Copy ID [J]", icon="content_copy", on_click=lambda: (ui.clipboard.write(str(job_id)), ui.notify("Copied ID"))).props('outline dense size=sm')

                    jd = job_data.get('description') or job_data.get('jd')
                    if jd and (pd.notna(jd) if 'pd' in globals() else True):
                        ui.button("Copy JD", icon="content_copy", on_click=lambda: (ui.clipboard.write(str(jd)), ui.notify("Copied JD"))).props('outline dense size=sm')

                    # Context actions depending on the queue
                    # Workflow Queue actions
                    if 'workflow_status' in job_data:
                        def do_wf_transition(status: str):
                            if workflow_queue_transition(str(job_id), WorkflowStatus(status)):
                                ui.notify(f"Moved to {status}", type="positive")
                                if on_change: on_change()
                                dialog.close()

                        ui.button("Apply Now [A]", icon="send", on_click=lambda: do_wf_transition("APPLYING")).props('unelevated dense size=sm color=primary')
                        ui.button("Prioritize [P]", icon="star", on_click=lambda: do_wf_transition("READY")).props('outline dense size=sm color=primary')
                        ui.button("Skip [R]", icon="skip_next", on_click=lambda: do_wf_transition("SKIPPED")).props('outline dense size=sm color=warning')
                        ui.button("Retry", icon="replay", on_click=lambda: (workflow_queue_retry(str(job_id)), dialog.close())).props('outline dense size=sm color=secondary')

                    # Manual/Auto Queue actions
                    if job_data.get('status') in ['PENDING', 'TO_APPLY', 'SHORTLISTED']:
                        def do_manual_update(status: str):
                            if 'source' in job_data and job_data['source'] != 'Auto':
                                update_manual_job_status(int(job_id), status)
                            else:
                                update_external_action_status(str(job_id), status, note="From UI Drawer")
                            ui.notify(f"Updated to {status}", type="positive")
                            if on_change: on_change()
                            dialog.close()

                        ui.button("Approve / Apply [A]", icon="check_circle", on_click=lambda: do_manual_update("APPLIED")).props('unelevated dense size=sm color=positive')
                        ui.button("Archive [R]", icon="archive", on_click=lambda: do_manual_update("SKIPPED")).props('outline dense size=sm color=warning')
                        ui.button("Ignore Forever", icon="block", on_click=lambda: do_manual_update("EXPIRED")).props('outline dense size=sm color=negative')

                # AI & Reasoning
                score = job_data.get('score') or job_data.get('ai_score')
                reason = job_data.get('reasoning') or job_data.get('ai_reasoning') or job_data.get('explanation')
                if pd.notna(score) if 'pd' in globals() else score is not None:
                    with panel_p("w-full"):
                        section_header("AI Assessment")
                        ui.html(f'<div class="text-3xl font-black text-[var(--primary)]">{score}/100</div>')
                        if reason and pd.notna(reason) if 'pd' in globals() else reason:
                            ui.html(f'<div class="mt-3 text-sm text-[var(--text)] whitespace-pre-wrap leading-relaxed">{html.escape(str(reason))}</div>')

                # Attributes Grid
                section_header("Attributes")
                with ui.grid(columns=3).classes('w-full gap-4'):
                    def _attr(label, val):
                        if val and (pd.notna(val) if 'pd' in globals() else True):
                            with ui.column().classes('gap-0'):
                                ui.html(f'<div class="text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">{label}</div>')
                                ui.html(f'<div class="text-sm font-medium">{html.escape(str(val))}</div>')

                    _attr("Job ID", job_id)
                    _attr("Work Mode", job_data.get("work_mode") or job_data.get("workplace_type"))
                    _attr("Experience", job_data.get("experience"))
                    _attr("Salary", job_data.get("salary"))
                    _attr("Priority", job_data.get("priority"))
                    _attr("Run ID", job_data.get("run_id"))
                    _attr("Source", job_data.get("source"))
                    _attr("Discovery", job_data.get("discovered_at") or job_data.get("created_at"))
                    _attr("Updated", job_data.get("updated_at"))

                # Full JD
                if jd and pd.notna(jd) if 'pd' in globals() else jd:
                    section_header("Job Description")
                    with ui.element('div').classes('text-sm text-[var(--text)] whitespace-pre-wrap font-mono p-4 bg-[var(--panel)] rounded border border-[var(--border)] max-h-[400px] overflow-y-auto'):
                        ui.html(html.escape(str(jd)))

            # Right pane (Timeline & Raw Data)
            with ui.column().classes('flex-[1] h-full overflow-y-auto p-6 gap-6 bg-[var(--panel)]'):
                section_header("Pipeline Timeline")

                stages = [
                    ("Acquired", job_data.get("discovered_at") or job_data.get("created_at")),
                    ("Classified", job_data.get("classified_at")),
                    ("Selected", job_data.get("selected_at")),
                    ("Applied", job_data.get("applied_at")),
                    ("Rejected", job_data.get("rejected_at"))
                ]
                has_timeline = False
                with ui.timeline(color='primary').classes('w-full'):
                    for name, ts in stages:
                        if ts and (pd.notna(ts) if 'pd' in globals() else True):
                            ui.timeline_entry(name, subtitle=str(ts)[:19])
                            has_timeline = True

                if not has_timeline:
                    ui.label("No timeline events recorded").classes('text-sm text-[var(--muted)] italic')

                rej_reason = job_data.get('rejection_reason') or job_data.get('reject_reason')
                if rej_reason and (pd.notna(rej_reason) if 'pd' in globals() else True):
                    from career_ui_legacy.components.feedback import callout
                    callout("Rejected", str(rej_reason), type="error")

                section_header("Raw Record")
                with ui.expansion("View JSON", icon="data_object").classes("w-full"):
                    # Use a safer dict generation for json
                    safe_data = {k: str(v) for k, v in job_data.items() if pd.notna(v)}
                    ui.code(json.dumps(safe_data, indent=2), language="json").classes("w-full text-xs")

    # Keyboard shortcuts
    keyboard_listener = None
    def handle_key(e):
        key = e.args.get('key', '').lower()
        if key == 'escape':
            dialog.close()
        elif key == 'o':
            url = job_data.get('url') or job_data.get('source_url')
            if url: ui.navigate.to(url, new_tab=True)
        elif key == 'j':
            ui.clipboard.write(str(job_id))
            ui.notify("Copied ID")
        elif key == 'a':
            if 'workflow_status' in job_data:
                workflow_queue_transition(str(job_id), WorkflowStatus("APPLYING"))
                ui.notify("Moved to APPLYING", type="positive")
                if on_change: on_change()
                dialog.close()
            elif job_data.get('status') in ['PENDING', 'TO_APPLY', 'SHORTLISTED']:
                if 'source' in job_data and job_data['source'] != 'Auto':
                    update_manual_job_status(int(job_id), "APPLIED")
                else:
                    update_external_action_status(str(job_id), "APPLIED")
                ui.notify("Marked APPLIED", type="positive")
                if on_change: on_change()
                dialog.close()
        elif key == 'p':
            if 'workflow_status' in job_data:
                workflow_queue_transition(str(job_id), WorkflowStatus("READY"))
                ui.notify("Prioritized", type="positive")
                if on_change: on_change()
                dialog.close()
        elif key == 'r':
            if 'workflow_status' in job_data:
                workflow_queue_transition(str(job_id), WorkflowStatus("SKIPPED"))
                ui.notify("Skipped", type="positive")
                if on_change: on_change()
                dialog.close()
            elif job_data.get('status') in ['PENDING', 'TO_APPLY', 'SHORTLISTED']:
                if 'source' in job_data and job_data['source'] != 'Auto':
                    update_manual_job_status(int(job_id), "SKIPPED")
                else:
                    update_external_action_status(str(job_id), "SKIPPED")
                ui.notify("Archived", type="positive")
                if on_change: on_change()
                dialog.close()

    keyboard_listener = ui.keyboard(on_key=handle_key)

    # Clean up keyboard listener when dialog closes
    def cleanup():
        keyboard_listener.delete()

    dialog.on('hide', cleanup)

    dialog.open()
