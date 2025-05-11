import datetime
import json
import logging
from typing import List, Dict

BELL_SCHEDULE = {
    "08:30": ["–9:15", "9:20–10:05"],
    "10:15": ["10:15–11:00", "11:05–11:50"],
    "12:00": ["12:00–12:45", "12:50–13:35"],
    "14:05": ["14:05–14:50", "14:55–15:40"],
    "15:50": ["15:50–16:35", "16:40–17:25"],
    "17:35": ["17:35–18:20", "18:25–19:10"],
    "19:15": ["19:15–20:00", "20:05–20:50"],
    "20:55": ["20:55–21:40", "21:45–22:30"]
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

    def get_date_color(self, day_date: datetime.date, current_date: datetime.date, tomorrow_date: datetime.date) -> str:
        return "blue" if day_date == tomorrow_date else "red" if day_date == current_date else "black"