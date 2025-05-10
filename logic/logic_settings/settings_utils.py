import os
import json
import shutil
import time
import logging

class SettingsUtils:
    @staticmethod
    def clear_schedules():
        """Очищает файл schedules.json"""
        try:
            with open("schedules.json", "w", encoding="utf-8") as f:
                json.dump([], f)
            logging.info("Cleared schedules.json")
        except Exception as e:
            logging.error(f"Error clearing schedules.json: {e}")
            raise

    @staticmethod
    def copy_log_file():
        """Копирует лог-файл с временной меткой"""
        log_file = "app.log"
        if os.path.exists(log_file):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_log = f"app_log_{timestamp}.log"
            shutil.copyfile(log_file, output_log)
            logging.info(f"Log file copied to {output_log}")
            return os.path.abspath(output_log)
        else:
            logging.warning("Log file not found")
            raise FileNotFoundError("Лог-файл не найден")