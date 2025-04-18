import flet as ft
from views.settings_view import SettingsTab
from views.schedule_view import ScheduleTab
from views.notes_view import NotesTab

class App(ft.UserControl):
    def build(self):
        self.tabs = ft.Tabs(
            selected_index=1,
            tabs=[
                ft.Tab(text="Настройки", content=SettingsTab()),
                ft.Tab(text="Расписание", content=ScheduleTab()),
                ft.Tab(text="Заметки", content=NotesTab())
            ],
            expand=1,
        )
        return ft.Column([self.tabs])

def main(page: ft.Page):
    page.title = "Студенческое приложение"
    page.window_width = 400
    page.window_height = 800
    app = App()
    page.add(app)

ft.app(target=main)
