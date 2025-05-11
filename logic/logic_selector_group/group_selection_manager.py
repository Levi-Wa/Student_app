import logging
from .group_selection_data import GroupSelectionData
from .group_selection_utils import GroupSelectionUtils

class GroupSelectionManager:
    def __init__(self, schedule_manager, app):
        self.data = GroupSelectionData()
        self.utils = GroupSelectionUtils()
        self.schedule_manager = schedule_manager
        self.app = app
        logging.info("GroupSelectionManager initialized")

    async def select_group(self, course: str, group_name: str, display_callback, notify_callback, on_selection_complete):
        """Обработка выбора группы"""
        if not course or not group_name:
            notify_callback("Выберите курс и группу!")
            return

        groups = self.data.get_groups_for_course(course)
        group_id = self.utils.get_group_id(groups, group_name)

        if group_id:
            self.schedule_manager.group_id = group_id
            self.app.settings["group_id"] = group_id
            self.app.save_settings()
            logging.info(f"Saved group_id: {group_id}")

            try:
                await self.schedule_manager.load_schedule_for_group(
                    group_id=group_id,
                    display_callback=display_callback,
                    notify_callback=notify_callback
                )

                if all("error" in sched for sched in self.schedule_manager.data.schedules):
                    notify_callback("Ошибка загрузки расписания. Попробуйте другую группу или проверьте подключение.")
                    return

                logging.info("Calling on_selection_complete")
                await on_selection_complete()
            except Exception as e:
                logging.error(f"Error loading schedule for group {group_id}: {e}")
                notify_callback(f"Ошибка: {str(e)}")
        else:
            notify_callback("Не удалось найти ID группы")
            logging.warning(f"Group ID not found for course {course}, group_name {group_name}")