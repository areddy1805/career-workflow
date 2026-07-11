from nicegui import ui

from career_ui.config import APP_TITLE, HOST, PORT


def main() -> None:
    ui.run(title=APP_TITLE, host=HOST, port=PORT, reload=True, dark=True, favicon="◇")


if __name__ in {"__main__", "__mp_main__"}:
    main()
