import logging
import datetime
from typing import List, Dict
from plyer import notification

class NotesNotifications:
    def __init__(self, app):
        self.app = app

    async def notify(self, title: str, message: str, notify_callback):
        """Отправляет уведомление"""
        try:
            from plyer import storage
            storage.request_permissions(["android.permission.POST_NOTIFICATIONS"])
            notification.notify(
                title=title,
                message=message,
                app_name="Студенческое приложение",
                timeout=10
            )
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")
            notify_callback(message)

    async def check_notes_expiry(self, notes: List[Dict], notify_callback):
        """Проверяет сроки действия заметок и отправляет уведомления"""
        if not self.app or not self.app.settings.get("schedule_notifications", True):
            logging.info("Note expiry notifications are disabled")
            return

        today = datetime.datetime.now().date()
        expiry_days = self.app.settings.get("expiry_days", 1)
        warning_date = today + datetime.timedelta(days=expiry_days)

        for note in notes:
            valid_until = note.get("valid_until", "Неизвестно")
            if valid_until == "Неизвестно":
                continue

            try:
                valid_date = datetime.datetime.strptime(valid_until, "%d.%m.%Y").date()
                if valid_date <= warning_date and valid_date >= today:
                    message = f"Заметка по предмету '{note['discipline']}' истекает {valid_until}"
                    await self.notify("Срок действия заметки", message, notify_callback)
            except ValueError:
                logging.error(f"Invalid valid_until format: {valid_until}") 