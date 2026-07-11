from nicegui import ui
from career_ui.config import APP_TITLE,HOST,PORT
from career_ui.pages import dashboard,pipeline,jobs,applications,manual_queue,review_queue,analytics,runs,health,settings,workflow_queue
def main() -> None:
    ui.run(title=APP_TITLE,host=HOST,port=PORT,reload=True,dark=True,favicon='◇')
if __name__ in {'__main__','__mp_main__'}: main()
