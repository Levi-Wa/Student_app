# Перенесите логику в ViewModel
class NotesViewModel():
    def __init__(self, storage):
        self.storage = storage

    def add_note(self, text, subject):
        self.storage.notes.append(Note(text, subject))
        self.storage.save_to_json()