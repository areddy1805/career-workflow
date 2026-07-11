from html import escape
from nicegui import ui
from career_ui.shell import shell
from career_ui.components import page_header, metric_card, section, status_badge, callout, empty_state
from career_ui.services.control_center import collect_health_checks, health_summary


def _status(check: dict) -> str:
    return str(check.get("status", "UNKNOWN")).upper()


def _group(checks: list[dict], names: list[str]) -> list[dict]:
    return [c for c in checks if c.get("check") in names]


_RUNTIME_CHECKS = [
    "Runtime state", "Heartbeat", "Pipeline lock", "Scheduler",
    "Watchdog", "Current run", "Last successful run", "Recovery history",
]
_STORAGE_CHECKS = [
    "Application ledger", "Run artifacts", "External action queue",
    "Manual jobs database", "Workflow queue",
]
_ENV_CHECKS = ["Python", "NiceGUI package", "Pipeline entry point",
               "Working directory", "Dry-run environment"]


def _render_group(title: str, subtitle: str, checks: list[dict]) -> None:
    if not checks:
        return
    section(title, subtitle)
    with ui.element("div").classes("cw-health-grid w-full"):
        for check in checks:
            name = str(check.get("check") or "Unnamed check")
            detail = str(check.get("detail") or "No detail")
            status = _status(check)
            required = bool(check.get("required"))
            with ui.card().classes("cw-card cw-health cw-card-interactive w-full"):
                with ui.row().classes("w-full items-start justify-between gap-3"):
                    ui.html(
                        f"<div>"
                        f"<div class=\"cw-health-name\">{escape(name)}</div>"
                        f"<div class=\"cw-health-detail\">{escape(detail)}</div>"
                        f"<div class=\"cw-health-meta\">{'REQUIRED' if required else 'INFORMATIONAL'}</div>"
                        f"</div>"
                    )
                    status_badge(status)


@ui.page("/health")
def page() -> None:
    shell("/health")
    with ui.column().classes("cw-content gap-5"):
        checks = collect_health_checks()
        s = health_summary(checks)
        passed = int(s.get("pass", 0))
        warned = int(s.get("warn", 0))
        failed = int(s.get("fail", 0))
        required_failed = sum(1 for c in checks if c.get("required") and _status(c) == "FAIL")
        overall = (
            "UNHEALTHY" if required_failed else ("DEGRADED" if failed or warned else "HEALTHY")
        )
        page_header(
            "SYSTEM", "System Health",
            "Runtime, storage, configuration, and integration diagnostics.",
            overall,
        )
        with ui.element("div").classes("cw-grid-4 w-full"):
            metric_card("Checks", len(checks), "diagnostics executed")
            metric_card("Passing", passed, "healthy checks")
            metric_card("Warnings", warned, "review recommended")
            metric_card(
                "Required Gate",
                "BLOCKED" if required_failed else "READY",
                f"{required_failed} required failures",
            )
        if required_failed:
            callout(
                "Runtime gate blocked",
                f"{required_failed} required diagnostic check(s) failed. "
                "Resolve required failures before relying on pipeline execution.",
            )
        elif failed or warned:
            callout(
                "Non-blocking diagnostics need review",
                f"{failed} failed and {warned} warning check(s) are present. "
                "Required runtime checks are still passing.",
            )

        _render_group(
            "Runtime", "Scheduler, heartbeat, lock, watchdog, and recovery status",
            _group(checks, _RUNTIME_CHECKS),
        )
        _render_group(
            "Storage", "Data files, ledger, queue, and artifact directories",
            _group(checks, _STORAGE_CHECKS),
        )
        _render_group(
            "Environment", "Python, packages, and configuration",
            _group(checks, _ENV_CHECKS),
        )

        # Anything not in a named group
        ungrouped = [
            c for c in checks
            if c.get("check") not in _RUNTIME_CHECKS
            and c.get("check") not in _STORAGE_CHECKS
            and c.get("check") not in _ENV_CHECKS
        ]
        if ungrouped:
            _render_group("Other", "Additional diagnostics", ungrouped)
