import flet as ft
from views.schedule_view import ScheduleTab
from views.notes_view import NotesView
from views.settings_view import SettingsView
from views.group_selection_view import GroupSelectionView

class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Студенческое приложение"
        self.page.window_width = 400
        self.page.window_height = 800
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.settings = {}
        self.schedule_tab = ScheduleTab(self.page, self)
        self.notes_tab = NotesView(self.page, self.schedule_tab, self)
        self.settings_tab = SettingsView(self.page, self.schedule_tab, self)
        self.group_selection = GroupSelectionView(self.page, self.schedule_tab, self.show_main_view)
        self.show_group_selection()

    def show_group_selection(self):
        """Показываем экран выбора группы"""
        self.page.views.clear()
        self.page.views.append(
            ft.View(
                "/",
                [
                    self.group_selection.build()
                ],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

    def show_main_view(self):
        """Показываем основной интерфейс после выбора группы"""
        self.page.views.clear()
        self.page.views.append(
            ft.View(
                "/",
                [
                    ft.Tabs(
                        selected_index=0,
                        tabs=[
                            ft.Tab(text="Расписание", content=self.schedule_tab.build()),
                            ft.Tab(text="Заметки", content=self.notes_tab.ui_content),
                            ft.Tab(text="Настройки", content=self.settings_tab.build())
                        ],
                        expand=True
                    )
                ]
            )
        )
        self.page.update()

def main(page: ft.Page):
    App(page)

if __name__ == "__main__":
    ft.app(target=main)