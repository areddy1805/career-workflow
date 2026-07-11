from nicegui import ui

from career_ui.config import APP_TITLE, HOST, PORT
from career_ui.pages import (
    analytics,  # noqa: F401
    applications,  # noqa: F401
    dashboard,  # noqa: F401
    health,  # noqa: F401
    jobs,  # noqa: F401
    manual_queue,  # noqa: F401
    pipeline,  # noqa: F401
    review_queue,  # noqa: F401
    runs,  # noqa: F401
    settings,  # noqa: F401
    workflow_queue,  # noqa: F401
)

def main() -> None:
    ui.run(title=APP_TITLE, host=HOST, port=PORT, reload=True, dark=True, favicon="◇")


if __name__ in {"__main__", "__mp_main__"}:
    main()
