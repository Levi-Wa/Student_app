import json
from pathlib import Path
import datetime
import logging
from platform import system
from plyer import storagepath

class ScheduleData:
    def __init__(self):
        if system() == "Android":
            base_dir = Path(storagepath.get_files_dir())
        else:
            base_dir = Path(__file__).parent.parent
        self.schedules_file = base_dir / "data" / "schedules.json"
        self.previous_schedules_file = base_dir / "data" / "previous_schedules.json"
        self.schedules = []
        self.group_id = None
        self.last_schedule_update = None
        # Создаём директорию при инициализации
        try:
            self.schedules_file.parent.mkdir(parents=True, exist_ok=True)
            logging.info(f"Schedule directory created: {self.schedules_file.parent}")
        except Exception as e:
            logging.error(f"Failed to create schedule directory {self.schedules_file.parent}: {e}")
        self.load_schedules()

    def load_schedules(self):
        """Загружает расписание из файла."""
        if self.schedules_file.exists():
            try:
                with open(self.schedules_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.schedules = data.get("schedules", [])
                    self.group_id = data.get("group_id", None)
                    last_update_str = data.get("last_fetched", None)
                    if last_update_str:
                        try:
                            self.last_schedule_update = datetime.datetime.fromisoformat(last_update_str)
                            self.last_schedule_update = self.last_schedule_update.replace(tzinfo=None)
                            logging.info(f"Loaded last_schedule_update: {self.last_schedule_update}")
                        except ValueError as e:
                            logging.error(f"Error parsing last_fetched: {e}")
                            self.last_schedule_update = None
                logging.info(f"Loaded schedules from {self.schedules_file}")
            except Exception as e:
                logging.error(f"Error loading schedules from {self.schedules_file}: {e}")
        else:
            logging.warning(f"Schedules file does not exist: {self.schedules_file}")

    def save_schedules(self):
        """Сохраняет расписание в файл."""
        data = {
            "schedules": self.schedules,
            "group_id": self.group_id,
            "last_fetched": datetime.datetime.now().isoformat()
        }
        try:
            self.schedules_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.schedules_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logging.info(f"Schedules saved successfully to {self.schedules_file}")
        except Exception as e:
            logging.error(f"Error saving schedules to {self.schedules_file}: {e}")

    def save_previous_schedules(self):
        """Сохраняет текущие расписания в отдельный файл перед обновлением."""
        if not self.schedules:
            logging.info("No schedules to save as previous")
            return
        try:
            data = {
                "schedules": self.schedules,
                "group_id": self.group_id,
                "last_fetched": self.last_schedule_update.isoformat() if self.last_schedule_update else None
            }
            self.previous_schedules_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.previous_schedules_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logging.info(f"Previous schedules saved to {self.previous_schedules_file}")
        except Exception as e:
            logging.error(f"Error saving previous schedules to {self.previous_schedules_file}: {e}")