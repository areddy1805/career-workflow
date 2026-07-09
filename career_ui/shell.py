from __future__ import annotations
from nicegui import ui
from career_ui.theme import apply_theme
NAV=[('OPERATE',[('Command Center','/','space_dashboard'),('Pipeline','/pipeline','play_circle')]),('WORK',[('Jobs','/jobs','work'),('Applications','/applications','send'),('Manual Queue','/manual-queue','task_alt'),('Review Queue','/review-queue','rule')]),('INSPECT',[('Analytics','/analytics','analytics'),('Run Inspector','/runs','manage_search'),('System Health','/health','health_and_safety')]),('SYSTEM',[('Settings','/settings','settings')])]
def shell(active:str):
    apply_theme()
    with ui.header().classes('cw-header items-center px-5 gap-3'):
        ui.button(icon='menu',on_click=lambda: drawer.toggle()).props('flat round color=grey-5 aria-label="Toggle navigation"')
        ui.html('<div class="cw-brand">Career Workflow</div>')
        ui.space()
        search=ui.input(placeholder='Search or jump…').props('dense borderless prepend-icon=search').classes('cw-top-search w-64 max-sm:hidden')
        search.on('keydown.enter',lambda: ui.navigate.to('/jobs'))
        ui.html('<span class="cw-command">⌘ K</span>')
        ui.html('<span class="cw-status cw-good">ENGINE READY</span>')
    with ui.left_drawer(value=True).classes('cw-drawer') as drawer:
        with ui.row().classes('items-center gap-3 px-4 pt-5 pb-4'):
            ui.html('<div style="width:40px;height:40px;border-radius:12px;display:grid;place-items:center;background:linear-gradient(145deg,#7368f4,#45cdec);font-weight:850;box-shadow:0 10px 28px rgba(100,110,255,.22)">CW</div>')
            ui.html('<div><div class="cw-brand">Career Workflow</div><div class="cw-brand-sub">OPERATIONS CONTROL PLANE</div></div>')
        with ui.list().classes('cw-nav w-full'):
            for group,items in NAV:
                ui.html(f'<div class="cw-nav-label">{group}</div>')
                for label,path,icon in items:
                    item=ui.item(on_click=lambda p=path: ui.navigate.to(p)).classes('cw-nav-active' if path==active else '')
                    with item:
                        with ui.item_section().props('avatar'): ui.icon(icon).classes('text-lg')
                        with ui.item_section(): ui.label(label).classes('text-sm font-medium')
        ui.space()
        ui.html('<div style="margin:18px;padding:13px;border:1px solid #1d2938;border-radius:12px;background:#0b1017"><div style="font-size:8px;color:#536176;letter-spacing:.14em;font-weight:800">LOCAL RUNTIME</div><div style="font-size:11px;color:#9dacbf;margin-top:7px">Artifact-driven state</div><div style="font-size:10px;color:#42e6a4;margin-top:4px">● Operational</div></div>')
    return drawer
