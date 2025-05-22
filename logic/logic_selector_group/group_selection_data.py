import logging
from typing import Dict, List
from .group_api import GroupAPI

class GroupSelectionData:
    def __init__(self):
        self.api = GroupAPI()
        self.groups_data = {}
        logging.info("GroupSelectionData initialized")

    def update_groups(self) -> bool:
        """Update groups data from API"""
        try:
            self.api.fetch_groups()
            if self.api.has_data_changed(self.groups_data):
                self.groups_data = self.api.get_full_time_groups()
                logging.info("Groups data updated from API")
                return True
            logging.info("Groups data is up to date")
            return False
        except Exception as e:
            logging.error(f"Error updating groups: {e}")
            return False

    def get_courses(self) -> List[str]:
        """Возвращает список курсов"""
        return list(self.groups_data.keys())

    def get_groups_for_course(self, course: str) -> List[Dict]:
        """Возвращает список групп для курса"""
        return self.groups_data.get(course, [])