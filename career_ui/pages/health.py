from html import escape
from nicegui import ui
from career_ui.shell import shell
from career_ui.components import page_header,metric_card,status_badge,callout
from career_ui.services.control_center import collect_health_checks,health_summary

def _status(check): return str(check.get('status','UNKNOWN')).upper()

@ui.page('/health')
def page():
    shell('/health')
    with ui.column().classes('cw-content gap-5'):
        checks=collect_health_checks(); s=health_summary(checks)
        passed=int(s.get('pass',0)); warned=int(s.get('warn',0)); failed=int(s.get('fail',0)); required_failed=sum(1 for c in checks if c.get('required') and _status(c)=='FAIL')
        overall='UNHEALTHY' if required_failed else ('DEGRADED' if failed or warned else 'HEALTHY')
        page_header('SYSTEM','System Health','Runtime, storage, configuration, and integration diagnostics.',overall)
        with ui.element('div').classes('cw-grid-4 w-full'):
            metric_card('Checks',len(checks),'diagnostics executed'); metric_card('Passing',passed,'healthy checks'); metric_card('Warnings',warned,'review recommended'); metric_card('Required Gate','BLOCKED' if required_failed else 'READY',f'{required_failed} required failures')
        if required_failed: callout('Runtime gate blocked',f'{required_failed} required diagnostic check(s) failed. Resolve required failures before relying on pipeline execution.')
        elif failed or warned: callout('Non-blocking diagnostics need review',f'{failed} failed and {warned} warning check(s) are present. Required runtime checks are still passing.')
        with ui.element('div').classes('cw-health-grid w-full'):
            for check in checks:
                name=str(check.get('check') or check.get('name') or 'Unnamed check'); detail=str(check.get('detail') or check.get('path') or 'No detail'); status=_status(check); required=bool(check.get('required'))
                with ui.card().classes('cw-card cw-health cw-card-interactive w-full'):
                    with ui.row().classes('w-full items-start justify-between gap-3'):
                        ui.html(f'<div><div class="cw-health-name">{escape(name)}</div><div class="cw-health-detail">{escape(detail)}</div><div class="cw-health-meta">{"REQUIRED" if required else "INFORMATIONAL"}</div></div>')
                        status_badge(status)
