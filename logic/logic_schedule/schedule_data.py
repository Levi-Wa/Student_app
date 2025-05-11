import json
from pathlib import Path
import datetime
import logging

class ScheduleData:
    def __init__(self):
        self.schedules_file = Path(__file__).parent.parent.parent / "data" / "schedules.json"
        self.schedules = []
        self.group_id = None
        self.last_schedule_update = None
        self.load_schedules()

    def load_schedules(self):
        """Загружает расписание из файла."""
        if self.schedules_file.exists():
            try:
                with open(self.schedules_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.schedules = data.get("schedules", [])
                    last_update_str = data.get("last_fetched", None)
                    if last_update_str:
                        self.last_schedule_update = datetime.datetime.fromisoformat(last_update_str)
                        # Удаляем временную зону, если она есть
                        self.last_schedule_update = self.last_schedule_update.replace(tzinfo=None)
                        logging.info(f"Loaded last_schedule_update: {self.last_schedule_update}")
                logging.info("Loaded valid schedules from local file")
            except Exception as e:
                logging.error(f"Error loading schedules: {e}")

    def save_schedules(self):
        """Сохраняет расписание в файл."""
        data = {
            "schedules": self.schedules,
            "group_id": self.group_id,
            "last_fetched": datetime.datetime.now().isoformat()  # Сохраняем без временной зоны
        }
        try:
            self.schedules_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.schedules_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logging.info("Schedules saved successfully")
        except Exception as e:
            logging.error(f"Error saving schedules: {e}")