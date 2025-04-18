import flet as ft
#from views.settings_view import SettingsTab
from views.schedule_view import ScheduleTab
#from views.notes_view import NotesTab

class App:
    def __init__(self, page: ft.Page):
        self.page = page

    def build(self):
        return ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Расписание", content=ScheduleTab()),
                ft.Tab(text="Заметки", content=ft.Text("Вкладка заметок")),
                ft.Tab(text="Настройки", content=ft.Text("Вкладка настроек")),
            ]
        )

def main(page: ft.Page):
    page.title = "Студенческое приложение"
    page.window_width = 400
    page.window_height = 800

    page.add(
        ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Расписание", content=ScheduleTab()),
                ft.Tab(text="Заметки", content=ft.Text("Вкладка заметок")),
                ft.Tab(text="Настройки", content=ft.Text("Вкладка настроек")),
            ]
        )
    )

ft.app(target=main)
