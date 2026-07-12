from __future__ import annotations
from nicegui import ui
from career_ui.theme import apply_theme
from career_ui.components.badges import status_badge

NAV = [
    (
        "OPERATE",
        [
            ("Command Center", "/", "space_dashboard"),
            ("Pipeline", "/pipeline", "play_circle"),
        ],
    ),
    (
        "WORK",
        [
            ("Jobs", "/jobs", "work"),
            ("Applications", "/applications", "send"),
            ("Workflow Queue", "/workflow-queue", "account_tree"),
            ("Manual Queue", "/manual-queue", "task_alt"),
            ("Review Queue", "/review-queue", "rule"),
        ],
    ),
    (
        "INSPECT",
        [
            ("Analytics", "/analytics", "analytics"),
            ("Run Inspector", "/runs", "manage_search"),
            ("System Health", "/health", "health_and_safety"),
        ],
    ),
    ("SYSTEM", [("Settings", "/settings", "settings")]),
]

def command_palette():
    """Global command palette dialog."""
    with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] bg-[var(--panel)] p-0 border border-[var(--border)]'):
        with ui.row().classes('w-full items-center p-3 border-b border-[var(--border)]'):
            ui.icon('search').classes('text-[var(--muted)] text-xl ml-2')
            search_input = ui.input(placeholder="Search jobs, run IDs, or navigation...").props('borderless autofocus').classes('flex-grow ml-3').style('font-size:16px; color:var(--text)')
            ui.html('<span class="cw-badge" style="font-size:10px">ESC</span>').classes('mr-2')

        results_container = ui.column().classes('w-full p-2 max-h-[50vh] overflow-y-auto')

        def update_search(e):
            q = (e.value or "").lower()
            results_container.clear()
            with results_container:
                if not q:
                    ui.html('<div class="text-[10px] uppercase font-bold text-[var(--muted)] ml-2 mb-2 tracking-wider">Navigation</div>')
                    for group, items in NAV:
                        for label, path, icon in items:
                            with ui.row().classes('w-full items-center p-2 rounded hover:bg-[var(--hover)] cursor-pointer').on('click', lambda p=path: [dialog.close(), ui.navigate.to(p)]):
                                ui.icon(icon).classes('text-[var(--muted)] text-lg mr-3')
                                ui.label(label).classes('text-[var(--text)] text-sm font-medium')
                else:
                    ui.html('<div class="text-[10px] uppercase font-bold text-[var(--muted)] ml-2 mb-2 tracking-wider">Jobs & Applications</div>')
                    from career_ui.services.control_center import read_applications
                    from career_ui.components.job_drawer import show_job_drawer
                    try:
                        df = read_applications()
                        if not df.empty:
                            search_cols = [c for c in ("company", "title", "job_id", "run_id", "id") if c in df.columns]

                            mask = None
                            for col in search_cols:
                                col_mask = df[col].astype(str).str.lower().str.contains(q, na=False, regex=False)
                                mask = col_mask if mask is None else mask | col_mask

                            matches = df[mask].head(15).to_dict('records') if mask is not None else []

                            if not matches:
                                ui.label("No matches found").classes('text-[var(--muted)] text-sm p-2')

                            for match in matches:
                                title = match.get('title', 'Unknown')
                                company = match.get('company', 'Unknown')
                                jid = match.get('job_id') or match.get('id')

                                def _open(m=match):
                                    dialog.close()
                                    show_job_drawer(m)

                                with ui.row().classes('w-full items-center p-2 rounded hover:bg-[var(--hover)] cursor-pointer gap-3').on('click', lambda m=match: _open(m)):
                                    ui.icon('work').classes('text-[var(--primary)] text-lg flex-shrink-0')
                                    with ui.column().classes('gap-0 min-w-0 flex-grow'):
                                        ui.label(title).classes('text-[var(--text)] text-sm font-medium truncate w-full')
                                        ui.label(f"{company} • {jid}").classes('text-[var(--muted)] text-xs truncate w-full')
                    except Exception as exc:
                        ui.label(f"Search error: {exc}").classes('text-red-400 text-sm p-2')

        search_input.on('update:model-value', update_search)
        update_search(type('obj', (object,), {'value': ''}))

    return dialog

def shell(active: str):
    apply_theme()

    # Expose the command palette globally
    cmd_pal = command_palette()
    ui.keyboard(on_key=lambda e: cmd_pal.open() if e.action.keydown and (e.key.name == 'k' and (e.modifiers.ctrl or e.modifiers.meta)) else None)

    with ui.header().classes("cw-header items-center px-4 gap-4"):
        ui.button(icon="menu", on_click=lambda: drawer.toggle()).props(
            'flat round color=grey-5 size=sm aria-label="Toggle navigation"'
        )

        # Breadcrumbs / Current path
        with ui.row().classes("items-center gap-2"):
            ui.html('<div class="cw-brand text-base">Career Workflow</div>')
            ui.icon("chevron_right").classes("text-[var(--muted)] text-sm")
            active_label = next((l for g, items in NAV for l, p, i in items if p == active), "Dashboard")
            ui.html(f'<div class="text-[var(--text)] text-sm font-medium">{active_label}</div>')

        ui.space()

        # Search / Command trigger
        with ui.row().classes("items-center bg-[var(--bg)] border border-[var(--border)] rounded px-3 py-1.5 cursor-text hover:border-[var(--muted)] transition-colors").on('click', cmd_pal.open):
            ui.icon('search').classes("text-[var(--muted)] text-sm mr-2")
            ui.label('Search or jump...').classes('text-[var(--muted)] text-xs mr-8')
            ui.html('<span class="cw-badge" style="font-size:10px; padding:2px 4px; background:var(--panel)">⌘K</span>')

        ui.html('<div class="w-px h-5 bg-[var(--border)] mx-2"></div>')
        status_badge("ONLINE", "min-w-0")

    with ui.left_drawer(value=True, bordered=True).classes("cw-drawer").props('show-if-above') as drawer:
        with ui.row().classes("items-center gap-3 px-4 pt-5 pb-4"):
            ui.html(
                '<div style="width:32px;height:32px;border-radius:8px;display:grid;place-items:center;background:linear-gradient(145deg,#7368f4,#45cdec);font-weight:850;font-size:12px;box-shadow:0 10px 28px rgba(100,110,255,.22)">CW</div>'
            )
            ui.html(
                '<div><div class="cw-brand" style="font-size:13px">Career Workflow</div><div class="cw-brand-sub" style="font-size:10px">OPERATIONS CONSOLE</div></div>'
            )

        with ui.list().classes("cw-nav w-full"):
            for group, items in NAV:
                ui.html(f'<div class="cw-nav-label mt-4">{group}</div>')
                for label, path, icon in items:
                    item = ui.item(on_click=lambda p=path: ui.navigate.to(p)).classes(
                        "cw-nav-active" if path == active else ""
                    )
                    with item:
                        with ui.item_section().props("avatar min-width=32px"):
                            ui.icon(icon).classes("text-[18px]")
                        with ui.item_section():
                            ui.label(label).classes("text-[13px] font-medium")
        ui.space()
        ui.html(
            '<div style="margin:16px;padding:12px;border:1px solid var(--border);border-radius:8px;background:var(--bg)"><div style="font-size:9px;color:var(--muted);letter-spacing:.1em;font-weight:700;margin-bottom:6px">RUNTIME</div><div style="font-size:11px;color:var(--text)">Artifact Engine</div><div style="font-size:10px;color:var(--success);margin-top:4px">● v2.0 Operational</div></div>'
        )
    return drawer

