import logging
from typing import Dict

class ScheduleValidation:
    @staticmethod
    def validate_schedule(schedule: Dict) -> bool:
        if "error" in schedule:
            logging.error(f"Validation failed: {schedule['error']}")
            return False
        if not schedule.get("Month"):
            logging.error("Validation failed: No 'Month' key in schedule")
            return False
        for month in schedule["Month"]:
            if not month.get("Sched"):
                logging.error("Validation failed: No 'Sched' key in month")
                return False
            for day in month["Sched"]:
                if not day.get("datePair") or not day.get("mainSchedule"):
                    logging.error(f"Validation failed: Invalid day structure: {day}")
                    return False
                for lesson in day["mainSchedule"]:
                    if not lesson.get("SubjName") and not lesson.get("Dis"):
                        logging.error(f"Validation failed: Invalid lesson structure: {lesson}")
                        return False
        return True