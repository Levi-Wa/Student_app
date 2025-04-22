import flet as ft
import json
import os

class SettingsView:
    def __init__(self, page: ft.Page, schedule_tab, app):
        self.page = page
        self.schedule_tab = schedule_tab
        self.app = app
        self.settings_file = "settings.json"
        self.load_settings()

    def load_settings(self):
        """Загрузка настроек из файла"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r", encoding="utf-8") as f:
                self.app.settings = json.load(f)
        else:
            self.app.settings = {
                "schedule_notifications": True,
                "expiry_notification_days": 3
            }

    def save_settings(self):
        """Сохранение настроек в файл"""
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.app.settings, f, ensure_ascii=False, indent=4)

    async def update_expiry_days(self, e):
        """Обновление количества дней для уведомлений о сроках актуальности"""
        try:
            days = int(e.control.value)
            if days < 1:
                raise ValueError("Количество дней должно быть больше 0")
            self.app.settings["expiry_notification_days"] = days
            self.save_settings()
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Количество дней для уведомлений обновлено!"),
                duration=3000
            )
        except ValueError:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Ошибка: введите целое число больше 0"),
                duration=3000
            )
        self.page.snack_bar.open = True
        self.page.update()

    async def toggle_schedule_notifications(self, e):
        """Включение/выключение уведомлений об изменениях в расписании"""
        self.app.settings["schedule_notifications"] = e.control.value
        self.save_settings()
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Настройки уведомлений обновлены!"),
            duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()

    def build(self):
        """Создаём интерфейс вкладки настроек"""
        expiry_days_input = ft.TextField(
            label="Дни до уведомления о сроке заметки",
            value=str(self.app.settings.get("expiry_notification_days", 3)),
            width=300,
            on_blur=self.update_expiry_days
        )

        schedule_notifications_switch = ft.Switch(
            label="Уведомления об изменениях в расписании",
            value=self.app.settings.get("schedule_notifications", True),
            on_change=self.toggle_schedule_notifications
        )

        return ft.Column([
            ft.Text("Настройки", size=20, weight="bold"),
            expiry_days_input,
            schedule_notifications_switch
        ], scroll=ft.ScrollMode.AUTO)