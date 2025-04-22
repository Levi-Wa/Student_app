import flet as ft
from views.schedule_view import ScheduleTab
from views.notes_view import NotesView
from views.settings_view import SettingsView
from views.group_selection_view import GroupSelectionView

class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Студенческое приложение"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 400
        self.page.window_height = 800
        self.settings = {}
        self.schedule_tab = ScheduleTab(page)
        self.notes_tab = NotesView(page, self.schedule_tab,self)
        self.group_selection_view = GroupSelectionView(page, self.schedule_tab, self.show_main_view)
        self.settings_tab = SettingsView(page, self, self.schedule_tab, self.group_selection_view)
        self.show_group_selection()

    def show_group_selection(self):
        """Показываем экран выбора группы"""
        self.page.views.clear()
        self.page.views.append(
            ft.View(
                "/",
                [
                    self.group_selection_view.build()
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
                            ft.Tab(text="Заметки", content=self.notes_tab.ui_content),
                            ft.Tab(text="Расписание", content=self.schedule_tab.build()),
                            ft.Tab(text="Настройки", content=self.settings_tab.build())
                        ],
                        expand=True
                    )
                ]
            )
        )
        self.page.update()
        if self.schedule_tab.group_id:  # Проверяем, выбрана ли группа
            self.page.run_task(self.schedule_tab.display_schedules)

def main(page: ft.Page):
    App(page)

if __name__ == "__main__":
    ft.app(target=main)