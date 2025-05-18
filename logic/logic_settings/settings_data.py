import json
import logging
from pathlib import Path
from platform import system
from plyer import storagepath

class SettingsData:
    def __init__(self):
        if system() == "Android":
            base_dir = Path(storagepath.get_files_dir())
            self.settings_file = base_dir / "data" / "settings.json"
        else:
            self.settings_file = Path(__file__).parent.parent.parent / "data" / "settings.json"

    def load_settings(self, app):
        """Загрузка настроек из файла"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    app.settings = json.load(f)
            except Exception as e:
                logging.error(f"Error loading settings from {self.settings_file}: {e}")
        app.settings.setdefault("schedule_notifications", True)
        app.settings.setdefault("expiry_days", 1)
        app.settings.setdefault("theme", "light")

    def save_settings(self, app):
        """Сохранение настроек в файл"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            logging.info(f"Saving settings to: {self.settings_file}")
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(app.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Error saving settings to {self.settings_file}: {e}")