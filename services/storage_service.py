import json
import os

class StorageService:
    def __init__(self, filename="app_data.json"):
        self.filename = filename
        if not os.path.exists(self.filename):
            self.save({"settings": {}, "notes": [], "schedule": {}})

    def load(self):
        with open(self.filename, "r") as f:
            return json.load(f)

    def save(self, data):
        with open(self.filename, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def save_to_json(self):
        try:
            with open(self.data_path, 'w') as f:
                json.dump({
                    "notes": [note.__dict__ for note in self.notes],
                    "events": [event.__dict__ for event in self.schedule_events]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
