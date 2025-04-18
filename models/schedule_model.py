class ScheduleModel:
    def __init__(self):
        # Пример данных
        self._data = {
            "today": ["Математика", "Физика"],
            "week": ["Математика", "Физика", "Химия", "История"],
        }

    def get_schedule(self, mode="today"):
        return self._data.get(mode, [])
