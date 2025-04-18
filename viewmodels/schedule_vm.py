from models.schedule_model import ScheduleModel
from flet import Reactive

class ScheduleViewModel:
    def __init__(self):
        self._model = ScheduleModel()
        self.schedule = Reactive([])

    def load_schedule(self, mode="today"):
        self.schedule.value = self._model.get_schedule(mode)

    def refresh(self):
        self.schedule.value = self._model.get_schedule("today")


