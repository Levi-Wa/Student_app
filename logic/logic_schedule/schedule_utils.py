import datetime
import json
import logging
from typing import List, Dict

BELL_SCHEDULE = {
    "08:30": ["09:15", "10:00"],
    "10:15": ["11:00", "11:45"],
    "12:00": ["12:45", "13:30"],
    "13:45": ["14:30", "15:15"],
    "15:30": ["16:15", "17:00"],
    "17:15": ["18:00", "18:45"],
    "19:00": ["19:45", "20:30"]
}

class ScheduleUtils:
    def __init__(self):
        self._cached_disciplines = None
        self._cached_disciplines_timestamp = 0

    def get_unique_disciplines(self, schedules: List[Dict]) -> List[str]:
        if self._cached_disciplines is not None and self._cached_disciplines_timestamp == id(schedules):
            logging.info("Returning cached disciplines")
            return self._cached_disciplines

        disciplines = set()
        for schedule in schedules:
            if "error" in schedule:
                logging.warning(f"Skipping schedule with error: {schedule['error']}")
                continue
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    for lesson in day.get("mainSchedule", []):
                        subj_name = lesson.get("SubjName") or lesson.get("SubjSN")
                        if subj_name:
                            disciplines.add(subj_name)
                        else:
                            logging.warning(
                                f"Missing SubjName/SubjSN in lesson: {json.dumps(lesson, ensure_ascii=False)}")
        self._cached_disciplines = sorted(list(disciplines))
        self._cached_disciplines_timestamp = id(schedules)
        logging.info(f"Extracted disciplines: {self._cached_disciplines}")
        return self._cached_disciplines

    def get_next_lesson_date(self, schedules: List[Dict], discipline: str, mode: str) -> datetime.date:
        current_date = datetime.date.today()
        next_lesson_date = None
        for schedule in schedules:
            if "error" in schedule:
                continue
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    try:
                        day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                        if day_date < current_date:
                            continue
                        for lesson in day.get("mainSchedule", []):
                            lesson_discipline = lesson.get("Dis", "") or lesson.get("SubjName", "")
                            if lesson_discipline == discipline:
                                lesson_type = lesson.get("Type", "").lower() or lesson.get("LoadKindSN", "").lower()
                                if mode == "До следующей пары":
                                    if next_lesson_date is None or day_date < next_lesson_date:
                                        next_lesson_date = day_date
                                elif mode == "До следующей практики" and "практика" in lesson_type:
                                    if next_lesson_date is None or day_date < next_lesson_date:
                                        next_lesson_date = day_date
                    except ValueError:
                        continue
        return next_lesson_date if next_lesson_date else (current_date + datetime.timedelta(days=7))

    @staticmethod
    def get_date_color(day_date: datetime.date, current_date: datetime.date, tomorrow_date: datetime.date) -> str:
        """Возвращает цвет для даты в зависимости от её отношения к текущей дате"""
        if day_date < current_date:
            return "grey"
        elif day_date == current_date:
            return "green"
        elif day_date == tomorrow_date:
            return "blue"
        return "grey200"