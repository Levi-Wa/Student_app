import datetime
import logging
from typing import List, Dict

class NotesUtils:
    def __init__(self, schedule_manager):
        self.schedule_manager = schedule_manager

    def get_next_lesson_date(self, discipline: str, mode: str, current_valid_until: str = None) -> str:
        """Находим дату следующего занятия по дисциплине и режиму после текущей даты или valid_until"""
        today = datetime.datetime.now().date()
        reference_date = today
        if current_valid_until and current_valid_until != "Неизвестно":
            try:
                reference_date = datetime.datetime.strptime(current_valid_until, "%d.%m.%Y").date()
            except ValueError:
                logging.error(f"Invalid current_valid_until format: {current_valid_until}")

        next_date = None
        mode_mapping = {
            "Лекция": "Лекция",
            "Практика": "Практ зан",
            "Лабораторная": "Лабор",
            "До следующей пары": None  # Любой тип занятия
        }
        target_mode = mode_mapping.get(mode)

        for schedule in self.schedule_manager.data.schedules:
            if "error" in schedule:
                continue
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_pair = day.get("datePair", "")
                    try:
                        day_date = datetime.datetime.strptime(date_pair, "%d.%m.%Y").date()
                        if day_date <= reference_date:
                            continue
                        for lesson in day.get("mainSchedule", []):
                            if lesson.get("SubjName") == discipline:
                                if target_mode is None or lesson.get("LoadKindSN") == target_mode:
                                    if not next_date or day_date < next_date:
                                        next_date = day_date
                    except ValueError:
                        logging.error(f"Invalid date format: {date_pair}")

        if next_date is None:
            logging.warning(f"No upcoming lessons found for {discipline} ({mode}) after {reference_date}")
            return "Неизвестно"
        return next_date.strftime("%d.%m.%Y")