import flet as ft
import logging
from logic.logic_settings.settings_data import SettingsData
from logic.logic_settings.settings_utils import SettingsUtils

class SettingsManager:
    def __init__(self, app, schedule_manager, group_selection_manager, notes_manager, page, nav_bar):
        self.data = SettingsData()
        self.utils = SettingsUtils()
        self.app = app
        self.schedule_manager = schedule_manager
        self.group_selection_manager = group_selection_manager
        self.notes_manager = notes_manager
        self.page = page
        self.nav_bar = nav_bar
        self.data.load_settings(app)
        logging.info("SettingsManager initialized")

    async def change_group(self, notify_callback):
        """Смена группы с сбросом настроек"""
        try:
            # Сбрасываем все настройки к значениям по умолчанию
            self.app.settings = {
                "schedule_notifications": True,
                "expiry_days": 1,
                "theme": "light"
            }
            
            # Сохраняем сброшенные настройки
            self.app.save_settings()
            
            # Очищаем сохраненный group_id
            if "group_id" in self.app.settings:
                del self.app.settings["group_id"]
            
            # Очищаем расписание
            self.schedule_manager.data.schedules = []
            self.schedule_manager.data.save_schedules()
            
            # Очищаем заметки
            self.notes_manager.notes = []
            self.notes_manager.save_notes()
            
            # Переходим к экрану выбора группы
            self.page.views.clear()
            self.page.views.append(
                ft.View(
                    "/group_selection",
                    [self.group_selection_manager.ui.build()],
                    padding=10
                )
            )
            self.page.update()
            
            logging.info("Settings reset and navigated to group selection")
            return True
        except Exception as e:
            logging.error(f"Error changing group: {e}")
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
            self.app.toggle_theme(page, self.nav_bar)
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