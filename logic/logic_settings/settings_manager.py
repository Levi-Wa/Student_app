import flet as ft
import logging
from logic.logic_settings.settings_data import SettingsData
from logic.logic_settings.settings_utils import SettingsUtils

class SettingsManager:
    def __init__(self, app, schedule_manager, group_selection_manager, notes_manager):
        self.data = SettingsData()
        self.utils = SettingsUtils()
        self.app = app
        self.schedule_manager = schedule_manager
        self.group_selection_manager = group_selection_manager
        self.notes_manager = notes_manager
        self.data.load_settings(app)
        logging.info("SettingsManager initialized")

    async def change_group(self, notify_callback):
        """Очищает данные и переключает на выбор группы"""
        try:
            self.utils.clear_schedules()
            self.app.settings.pop("group_id", None)
            self.data.save_settings(self.app)
            self.schedule_manager.data.schedules = []
            self.schedule_manager.group_id = None
            self.notes_manager.notes = []
            await self.notes_manager.data.save_notes(self.notes_manager.notes)
            logging.info("Group changed, data cleared")
            return True
        except Exception as e:
            logging.error(f"Error changing group: {e}")
            notify_callback("Ошибка при смене группы")
            return False

    def report_issue(self, page, notify_callback):
        """Копирует лог-файл и открывает Google Форму"""
        try:
            log_path = self.utils.copy_log_file()
            page.launch_url(f"file://{log_path}")
            form_url = "https://docs.google.com/forms/d/e/1FAIpQLSfxrzBgkLRYaj4Ntp2I4FOAJdmKttq5qyleUqK6LOJLdIi_IQ/viewform?usp=dialog"
            page.launch_url(form_url)
            logging.info(f"Opened Google Form: {form_url}")
        except FileNotFoundError as e:
            notify_callback(str(e))
        except Exception as e:
            logging.error(f"Error reporting issue: {e}")
            notify_callback("Ошибка при отправке отчета")

    def toggle_theme(self, page):
        """Переключает тему приложения между светлой и тёмной."""
        try:
            current_theme = self.app.settings.get("theme", "light")
            new_theme = "dark" if current_theme == "light" else "light"
            self.app.settings["theme"] = new_theme
            self.data.save_settings(self.app)
            page.theme_mode = ft.ThemeMode.DARK if new_theme == "dark" else ft.ThemeMode.LIGHT
            page.update()
            logging.info(f"Theme switched to {new_theme}")
        except Exception as e:
            logging.error(f"Error toggling theme: {e}")

    async def update_expiry_days(self, days: str, notify_callback):
        """Обновление количества дней для уведомления"""
        try:
            self.app.settings["expiry_days"] = int(days)
            await self.data.save_settings(self.app)
            logging.info(f"Expiry days updated to {days}")
        except ValueError:
            await notify_callback("Ошибка: выберите значение")