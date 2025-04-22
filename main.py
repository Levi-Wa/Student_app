import flet as ft
import json
import os
import logging
from views.schedule_view import ScheduleTab
from views.notes_view import NotesView
from views.group_selection_view import GroupSelectionView
from views.settings_view import SettingsView

class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Студенческое приложение"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 400
        self.page.window_height = 800
        self.settings = {}
        self.load_settings()
        self.schedule_tab = ScheduleTab(page)
        self.notes_tab = NotesView(page, self.schedule_tab, self)
        self.group_selection_view = GroupSelectionView(page, self.schedule_tab, self.show_main_view, self)
        self.settings_tab = SettingsView(page, self, self.schedule_tab, self.group_selection_view)
        if self.settings.get("group_id"):
            self.schedule_tab.group_id = self.settings["group_id"]
            self.page.run_task(self.show_main_view)
        else:
            self.show_group_selection()

    def load_settings(self):
        """Загрузка настроек"""
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except Exception as e:
                logging.error(f"Error loading settings: {e}")

    def save_settings(self):
        """Сохранение настроек"""
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")

    def show_group_selection(self):
        """Показываем интерфейс выбора группы"""
        self.page.views.clear()
        self.page.views.append(
            ft.View(
                "/group_selection",
                [self.group_selection_view.build()]
            )
        )
        self.page.update()

    async def show_main_view(self):
        """Показываем основной интерфейс после выбора группы"""
        self.page.views.clear()
        self.page.views.append(
            ft.View(
                "/",
                [
                    ft.Tabs(
                        selected_index=1,
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
        if self.schedule_tab.group_id:
            await self.schedule_tab.load_schedule_for_group(self.schedule_tab.group_id)
            self.notes_tab.ui_content.controls.clear()
            self.notes_tab.ui_content.controls.append(self.notes_tab.build_note_form())
            self.notes_tab.ui_content.controls.append(self.notes_tab.notes_list)
            self.page.run_task(self.schedule_tab.display_schedules)
        self.page.update()

def main(page: ft.Page):
    logging.basicConfig(level=logging.INFO, filename="app.log", encoding="utf-8", format="%(asctime)s - %(levelname)s - %(message)s")
    app = App(page)

if __name__ == "__main__":
    ft.app(target=main)