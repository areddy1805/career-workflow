from nicegui import ui
from career_ui_legacy.shell import shell
from career_ui_legacy.layouts.page import page_header
from career_ui_legacy.components.cards import panel_p

def work_queue_layout(active_route: str, content_builder):
    shell(active_route)
    with ui.column().classes("w-full max-w-[1600px] mx-auto p-4 gap-4 h-[calc(100vh-60px)]"):
        page_header("Work Queues", "Unified queue management and lifecycle operations.", kicker="Work")

        with ui.row().classes("w-full h-full min-h-0 gap-4 flex-nowrap items-stretch pb-10"):

            # Unified Sidebar
            with panel_p("w-56 flex-shrink-0 flex flex-col gap-2 bg-[var(--panel)]"):
                ui.html('<div class="text-[10px] uppercase font-bold text-[var(--muted)] tracking-wider mb-2 ml-2">Queues</div>')

                queues = [
                    ("Workflow Queue", "/workflow-queue", "account_tree"),
                    ("Manual Queue", "/manual-queue", "task_alt"),
                    ("Review Queue", "/review-queue", "rule"),
                    ("Applications", "/applications", "send"),
                ]

                for label, route, icon in queues:
                    is_active = route == active_route
                    bg = "bg-[#1d2938]" if is_active else "hover:bg-[var(--hover)]"
                    color = "text-[var(--text)]" if is_active else "text-[var(--muted)]"
                    weight = "font-semibold" if is_active else "font-medium"

                    with ui.row().classes(f"w-full p-2 rounded cursor-pointer items-center {bg}").on('click', lambda r=route: ui.navigate.to(r)):
                        ui.icon(icon).classes(f"text-[18px] {color} mr-3")
                        ui.label(label).classes(f"text-[13px] {weight} {color}")

            # Main Content Area
            with ui.column().classes("flex-grow min-w-0 h-full overflow-hidden"):
                content_builder()
