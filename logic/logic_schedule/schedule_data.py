import os
import json
import requests
import logging
from typing import List, Dict
from bs4 import BeautifulSoup
import datetime

class ScheduleData:
    def __init__(self):
        self.schedules_file = os.path.join(os.getenv("HOME", "."), "schedules.json")
        self.previous_schedules_file = os.path.join(os.getenv("HOME", "."), "previous_schedules.json")
        self.last_valid_schedules_file = os.path.join(os.getenv("HOME", "."), "last_valid_schedules.json")
        self.schedules = []
        self.previous_schedules = []
        self.last_schedule_update = None

    def load_local_schedules(self) -> List[Dict]:
        if os.path.exists(self.schedules_file):
            try:
                with open(self.schedules_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        logging.warning(f"{self.schedules_file} is empty")
                        return []
                    data = json.loads(content)
                    if isinstance(data, dict) and "last_update" in data:
                        self.last_schedule_update = datetime.datetime.fromisoformat(data["last_update"])
                        return data.get("schedules", [])
                    return data
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse {self.schedules_file}: {e}")
                if os.path.exists(self.last_valid_schedules_file):
                    try:
                        with open(self.last_valid_schedules_file, "r", encoding="utf-8") as f:
                            return json.loads(f.read().strip())
                    except Exception as e:
                        logging.error(f"Error loading last valid schedules: {e}")
                return []
        return []

    def save_schedules(self, schedules: List[Dict]):
        try:
            if not isinstance(schedules, list):
                logging.error(f"Error: schedules is not a list: {type(schedules)}")
                schedules = []
            data_to_save = {
                "last_update": datetime.datetime.now().isoformat(),
                "schedules": schedules
            }
            with open(self.schedules_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            if any(self.validate_schedule(sched) for sched in schedules):
                with open(self.last_valid_schedules_file, "w", encoding="utf-8") as f:
                    json.dump(schedules, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Error: Failed to save schedules to {self.schedules_file}: {e}")

    def load_previous_schedules(self):
        if os.path.exists(self.previous_schedules_file):
            with open(self.previous_schedules_file, "r", encoding="utf-8") as f:
                self.previous_schedules = json.load(f)
        else:
            self.previous_schedules = []

    def save_previous_schedules(self):
        with open(self.previous_schedules_file, "w", encoding="utf-8") as f:
            json.dump(self.previous_schedules, f, ensure_ascii=False, indent=4)

    def parse_html_schedule(self, html_content: str) -> Dict:
        soup = BeautifulSoup(html_content, "html.parser")
        schedule_data = {"Month": []}
        current_month = {"Sched": []}

        table = soup.find("table")
        if not table:
            logging.error("No table found in HTML")
            return {"error": "Не удалось найти таблицу с расписанием"}

        rows = table.find_all("tr")
        if len(rows) <= 1:
            logging.error("Table has no data rows")
            return {"error": "Таблица не содержит данных"}

        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 5:
                logging.warning(f"Row has insufficient columns: {len(cols)}")
                continue

            date_pair = cols[0].text.strip() if len(cols) > 0 else ""
            day_week = cols[1].text.strip() if len(cols) > 1 else ""
            time_text = cols[2].text.strip() if len(cols) > 2 else ""
            time_start = time_text.split("-")[0] if "-" in time_text else ""
            time_end = time_text.split("-")[1] if "-" in time_text and len(time_text.split("-")) > 1 else ""
            discipline = cols[3].text.strip() if len(cols) > 3 else ""
            lesson_type = cols[4].text.strip() if len(cols) > 4 else ""
            room = cols[5].text.strip() if len(cols) > 5 else ""
            teacher = cols[6].text.strip() if len(cols) > 6 else ""

            if not (date_pair and discipline and time_start):
                logging.warning(f"Skipping row with missing critical data: {date_pair}, {discipline}, {time_start}")
                continue

            day_schedule = {
                "datePair": date_pair,
                "dayWeek": day_week,
                "mainSchedule": [{
                    "timeStart": time_start,
                    "timeEnd": time_end,
                    "Dis": discipline,
                    "Type": lesson_type,
                    "Room": room,
                    "Teacher": teacher
                }]
            }
            current_month["Sched"].append(day_schedule)

        if not current_month["Sched"]:
            logging.error("No valid schedule data parsed")
            return {"error": "Не удалось извлечь данные расписания"}

        schedule_data["Month"].append(current_month)
        return schedule_data