import logging
from typing import List, Dict

class GroupSelectionUtils:
    @staticmethod
    def get_group_id(groups: List[Dict], group_name: str) -> str:
        """Возвращает ID группы по её имени"""
        for group in groups:
            if group["name"] == group_name:
                return group["id"]
        logging.warning(f"Group ID not found for group: {group_name}")
        return None