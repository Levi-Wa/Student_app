import requests
import logging
from typing import Dict, List, Optional

class GroupAPI:
    def __init__(self):
        self.api_url = "https://api.ursei.su/public/schedule/rest/GetGSSchedIniData"
        self.cached_data = None
        logging.info("GroupAPI initialized")

    def fetch_groups(self) -> Optional[Dict]:
        """Fetch groups data from API"""
        try:
            response = requests.get(self.api_url)
            if response.status_code == 200:
                data = response.json()
                self.cached_data = data
                return data
            else:
                logging.error(f"API request failed with status {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching groups: {e}")
            return None

    def get_full_time_groups(self) -> Dict[str, List[Dict]]:
        """Get only full-time (очная) groups organized by course"""
        if not self.cached_data:
            return {}

        groups_by_course = {}
        
        # Find the full-time form of education
        for form in self.cached_data.get("FormEdu", []):
            if form.get("FormEduName") == "Очная":
                # Process each course
                for course_data in form.get("arr", []):
                    course_number = course_data.get("Curs")
                    if course_number:
                        course_key = f"{course_number} курс"
                        groups = []
                        for group in course_data.get("arr", []):
                            groups.append({
                                "name": group.get("GSName"),
                                "id": str(group.get("GS_ID"))
                            })
                        if groups:
                            groups_by_course[course_key] = groups
                break

        return groups_by_course

    def has_data_changed(self, current_groups: Dict[str, List[Dict]]) -> bool:
        """Check if the API data has changed compared to current groups"""
        if not self.cached_data:
            return False

        new_groups = self.get_full_time_groups()
        
        # Compare the structure and content
        if set(current_groups.keys()) != set(new_groups.keys()):
            return True

        for course in current_groups:
            current_group_ids = {group["id"] for group in current_groups[course]}
            new_group_ids = {group["id"] for group in new_groups[course]}
            if current_group_ids != new_group_ids:
                return True

        return False 