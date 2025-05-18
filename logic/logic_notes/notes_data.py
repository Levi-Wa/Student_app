import os
import json
import logging
from typing import List, Dict
from pathlib import Path
from platform import system
from plyer import storagepath

class NotesData:
    def __init__(self):
        if system() == "Android":
            self.notes_file = Path(storagepath.get_files_dir()) / "data" / "notes.json"
        else:
            self.notes_file = Path(__file__).parent.parent / "data" / "notes.json"
        self.notes = []
        try:
            self.notes_file.parent.mkdir(parents=True, exist_ok=True)
            logging.info(f"Notes directory created: {self.notes_file.parent}")
        except Exception as e:
            logging.error(f"Failed to create notes directory {self.notes_file.parent}: {e}")
        self.notes = self.load_notes()

    def load_notes(self) -> List[Dict]:
        """Загрузка заметок из файла"""
        if self.notes_file.exists():
            try:
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    notes = json.load(f)
                    logging.info(f"Loaded {len(notes)} notes from {self.notes_file}")
                    return notes
            except Exception as e:
                logging.error(f"Error loading notes from {self.notes_file}: {e}")
        else:
            logging.warning(f"Notes file does not exist: {self.notes_file}")
        return []

    def save_notes(self, notes: List[Dict]):
        """Сохранение заметок в файл"""
        try:
            self.notes_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.notes_file, "w", encoding="utf-8") as f:
                json.dump(notes, f, ensure_ascii=False, indent=4)
            logging.info(f"Saved {len(notes)} notes to {self.notes_file}")
        except Exception as e:
            logging.error(f"Error saving notes to {self.notes_file}: {e}")