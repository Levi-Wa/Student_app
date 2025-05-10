import os
import json
import logging

class SettingsData:
    def __init__(self):
        self.settings_file = os.path.join(os.getenv("HOME", "."), "settings.json")

    def load_settings(self, app):
        """Загрузка настроек из файла"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    app.settings = json.load(f)
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
        app.settings.setdefault("schedule_notifications", True)
        app.settings.setdefault("expiry_days", 1)
        app.settings.setdefault("theme", "light")

    def save_settings(self, app):
        """Сохранение настроек в файл"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(app.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")