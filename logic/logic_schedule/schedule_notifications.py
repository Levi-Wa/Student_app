import logging
from typing import List, Dict
from plyer import notification

class ScheduleNotifications:
    def __init__(self):
        self.app = None  # Placeholder for app settings
        self.changed_lessons = set()  # Множество для хранения измененных занятий

    async def notify(self, title: str, message: str, notify_callback):
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

    def get_changed_lessons(self):
        """Возвращает множество измененных занятий"""
        return self.changed_lessons

    def clear_changed_lessons(self):
        """Очищает множество измененных занятий"""
        self.changed_lessons.clear()

    async def check_schedule_changes(self, previous_schedules: List[Dict], schedules: List[Dict], notify_callback):
        if not self.app or not self.app.settings.get("schedule_notifications", True):
            logging.info("Schedule change notifications are disabled")
            return

        if not previous_schedules or not schedules:
            return

        changes = []
        self.changed_lessons.clear()  # Очищаем предыдущие изменения

        for old_sched, new_sched in zip(previous_schedules, schedules):
            if "error" in old_sched or "error" in new_sched:
                continue

            old_lessons = {}
            new_lessons = {}

            # Собираем старые занятия
            for month in old_sched.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    for lesson in day.get("mainSchedule", []):
                        key = (date_str, lesson.get("Dis", ""), lesson.get("timeStart", ""))
                        old_lessons[key] = lesson

            # Собираем новые занятия
            for month in new_sched.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    for lesson in day.get("mainSchedule", []):
                        key = (date_str, lesson.get("Dis", ""), lesson.get("timeStart", ""))
                        new_lessons[key] = lesson

            # Проверяем изменения
            for key, new_lesson in new_lessons.items():
                old_lesson = old_lessons.get(key)
                if not old_lesson:
                    changes.append(f"Новое занятие: {new_lesson['Dis']} ({new_lesson['datePair']})")
                    self.changed_lessons.add((new_lesson['datePair'], new_lesson['timeStart']))
                    continue

                change_details = []
                if old_lesson.get("Type", "") != new_lesson.get("Type", ""):
                    change_details.append(f"Тип занятия: {old_lesson['Type']} → {new_lesson['Type']}")
                if old_lesson.get("Room", "") != new_lesson.get("Room", ""):
                    change_details.append(f"Аудитория: {old_lesson['Room']} → {new_lesson['Room']}")
                if old_lesson.get("timeStart", "") != new_lesson.get("timeStart", "") or old_lesson.get("timeEnd", "") != new_lesson.get("timeEnd", ""):
                    change_details.append(f"Время: {old_lesson['timeStart']}-{old_lesson['timeEnd']} → {new_lesson['timeStart']}-{new_lesson['timeEnd']}")

                if change_details:
                    changes.append(f"{new_lesson['Dis']} ({new_lesson['datePair']}): {', '.join(change_details)}")
                    self.changed_lessons.add((new_lesson['datePair'], new_lesson['timeStart']))

        if changes:
            await self.notify("Изменения в расписании", "; ".join(changes), notify_callback)