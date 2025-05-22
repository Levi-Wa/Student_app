import logging
from typing import Dict

class NotesValidation:
    @staticmethod
    def validate_note(note: Dict) -> bool:
        """Проверка корректности структуры заметки"""
        required_fields = ["discipline", "mode", "text", "valid_until"]
        for field in required_fields:
            if field not in note or not note[field]:
                logging.error(f"Missing or empty field '{field}' in note: {note}")
                return False
        if note["discipline"] == "Нет дисциплин":
            logging.warning("Note has 'Нет дисциплин' as discipline")
            return False
        return True