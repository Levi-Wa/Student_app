import logging
from typing import List, Dict
from .notes_data import NotesData
from .notes_validation import NotesValidation
from .notes_utils import NotesUtils

class NotesManager:
    def __init__(self, schedule_manager, app):
        self.data = NotesData()
        self.validation = NotesValidation()
        self.utils = NotesUtils(schedule_manager)
        self.app = app
        self.notes = self.data.load_notes()
        logging.info("NotesManager initialized")

    def add_note(self, discipline: str, mode: str, text: str, notify_callback):
        """Добавление новой заметки"""
        if not text or discipline == "Нет дисциплин":
            notify_callback("Заполните текст заметки и выберите дисциплину!")
            return False

        note = {
            "discipline": discipline,
            "mode": mode,
            "text": text,
            "valid_until": self.utils.get_next_lesson_date(discipline, mode)
        }
        if self.validation.validate_note(note):
            self.notes.append(note)
            self.data.save_notes(self.notes)
            logging.info(f"Note added: {note}")
            return True
        return False

    def edit_note(self, index: int, text: str, mode: str, notify_callback) -> bool:
        """Редактирование заметки"""
        try:
            note = self.notes[index]
            note["text"] = text
            note["mode"] = mode
            note["valid_until"] = self.utils.get_next_lesson_date(note["discipline"], mode, note["valid_until"])
            if self.validation.validate_note(note):
                self.data.save_notes(self.notes)
                logging.info(f"Note edited: {note}")
                return True
            else:
                notify_callback("Ошибка: некорректные данные заметки")
                return False
        except Exception as e:
            logging.error(f"Error editing note: {e}")
            notify_callback("Ошибка при сохранении изменений")
            return False

    def extend_validity(self, index: int, notify_callback) -> bool:
        """Продлевает актуальность заметки до следующей пары"""
        try:
            note = self.notes[index]
            if note["discipline"] == "Нет дисциплин":
                notify_callback("Невозможно продлить: дисциплина не выбрана")
                return False
            note["valid_until"] = self.utils.get_next_lesson_date(note["discipline"], "До следующей пары", note["valid_until"])
            self.data.save_notes(self.notes)
            logging.info(f"Extended validity for {note['discipline']} to next lesson: {note['valid_until']}")
            return True
        except Exception as e:
            logging.error(f"Error extending validity: {e}")
            notify_callback("Ошибка при продлении актуальности")
            return False

    def delete_note(self, index: int):
        """Удаляет заметку по индексу"""
        note = self.notes.pop(index)
        self.data.save_notes(self.notes)
        logging.info(f"Note deleted: {note}")