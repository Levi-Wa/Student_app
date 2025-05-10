import os
import json
import logging
from typing import List, Dict

class NotesData:
    def __init__(self):
        self.notes_file = os.path.join(os.getenv("HOME", "."), "notes.json")
        self.notes = []

    def load_notes(self) -> List[Dict]:
        """Загрузка заметок из файла"""
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading notes: {e}")
        return []

    def save_notes(self, notes: List[Dict]):
        """Сохранение заметок в файл"""
        try:
            with open(self.notes_file, "w", encoding="utf-8") as f:
                json.dump(notes, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Error saving notes: {e}")