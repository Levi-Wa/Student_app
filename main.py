import flet as ft
import json
import os
import logging
import asyncio
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
        self.group_selection_view = GroupSelectionView(page, self.schedule_tab, self.show_main_view, self)
        self.notes_tab = None
        self.settings_tab = None
        self.current_tab = "schedule"  # Текущая вкладка по умолчанию
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
        import logging
        self.page.views.clear()
        self.notes_tab = NotesView(self.page, self.schedule_tab, self)
        self.settings_tab = SettingsView(self.page, self, self.schedule_tab, self.group_selection_view, self.notes_tab)

        # Контейнер для содержимого текущей вкладки
        content_container = ft.Container(content=self.schedule_tab.build())

        def on_tab_change(e):
            selected_tab = e.control.selected_index
            if selected_tab == 0:
                self.current_tab = "notes"
                content_container.content = self.notes_tab.ui_content
            elif selected_tab == 1:
                self.current_tab = "schedule"
                content_container.content = self.schedule_tab.build()
            elif selected_tab == 2:
                self.current_tab = "settings"
                content_container.content = self.settings_tab.build()
            self.page.update()

        navigation_bar = ft.NavigationBar(
            selected_index=1,  # По умолчанию выбрана вкладка "Расписание"
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.NOTE, label="Заметки"),
                ft.NavigationBarDestination(icon=ft.Icons.SCHEDULE, label="Расписание"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Настройки"),
            ],
            on_change=on_tab_change
        )

        self.page.views.append(
            ft.View(
                "/",
                [
                    content_container,
                    navigation_bar
                ],
                vertical_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                padding=0
            )
        )
        self.page.update()
        logging.info("Main view displayed")
        if self.schedule_tab.group_id:
            await self.schedule_tab.load_schedule_for_group(self.schedule_tab.group_id)
            self.notes_tab.ui_content.controls.clear()
            self.notes_tab.ui_content.controls.append(self.notes_tab.build_note_form())
            self.notes_tab.ui_content.controls.append(self.notes_tab.notes_list)
            logging.info("Notes form rebuilt after schedule load")
            self.page.run_task(self.schedule_tab.display_schedules)
        self.page.update()

def main(page: ft.Page):
    logging.basicConfig(level=logging.INFO, filename="app.log", encoding="utf-8", format="%(asctime)s - %(levelname)s - %(message)s")
    app = App(page)

if __name__ == "__main__":
    ft.app(target=main)