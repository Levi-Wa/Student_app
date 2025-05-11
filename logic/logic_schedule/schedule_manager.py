import logging
import json
import asyncio
import datetime
import pytz
import requests
from typing import List, Dict
from .schedule_data import ScheduleData
from .schedule_validation import ScheduleValidation
from .schedule_notifications import ScheduleNotifications
from .schedule_utils import ScheduleUtils

class ScheduleManager:
    def __init__(self):
        self.data = ScheduleData()
        self.validation = ScheduleValidation()
        self.notifications = ScheduleNotifications()
        self.utils = ScheduleUtils()
        self.group_id = None

    async def check_schedule_on_open(self, display_callback):
        """Проверяет, нужно ли обновить расписание при открытии приложения."""
        logging.info("Checking schedule on open")
        now = datetime.datetime.now()
        if self.data.last_schedule_update is None:
            logging.info("No previous schedule update, fetching new schedule")
            await self.fetch_and_update_schedule(display_callback)
        else:
            # Приводим last_schedule_update к offset-naive
            last_update_naive = self.data.last_schedule_update.replace(tzinfo=None)
            logging.info(f"Comparing now: {now}, last_update_naive: {last_update_naive}")
            if (now - last_update_naive).total_seconds() > 24 * 3600:
                logging.info("Schedule is outdated, fetching new schedule")
                await self.fetch_and_update_schedule(display_callback)
            else:
                logging.info("Schedule is up-to-date, using cached data")
                await display_callback(self.data.schedules)

    async def load_schedule_for_group(self, group_id: str, display_callback, notify_callback):
        logging.basicConfig(level=logging.INFO, filename="app.log", encoding="utf-8",
                            format="%(asctime)s - %(levelname)s - %(message)s")
        self.group_id = group_id
        self.data.schedules = self.data.load_local_schedules()
        logging.info(f"Loaded schedules: {json.dumps(self.data.schedules, ensure_ascii=False, indent=2)[:2000]}")
        if self.data.schedules and any(self.validation.validate_schedule(sched) for sched in self.data.schedules):
            logging.info("Loaded valid schedules from local file")
            await self.check_schedule_on_open(display_callback)
            disciplines = self.utils.get_unique_disciplines(self.data.schedules)
            logging.info(f"Disciplines after local load: {disciplines}")
            return

        self.data.schedules = []
        try:
            url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
            response = requests.get(url, timeout=5)
            logging.info(f"API response for group {group_id}: status={response.status_code}, content={response.text[:2000]}")
            if response.status_code == 200 and response.text.strip():
                try:
                    schedule = response.json()
                    logging.info(f"Parsed schedule: {json.dumps(schedule, ensure_ascii=False, indent=2)[:2000]}")
                    if self.validation.validate_schedule(schedule):
                        self.data.schedules.append(schedule)
                        logging.info("Schedule validated and added")
                    else:
                        logging.warning(f"Invalid schedule structure for group {group_id}")
                        self.data.schedules.append({"error": f"Некорректная структура расписания для группы {group_id}"})
                except ValueError as e:
                    logging.error(f"Failed to parse JSON for group {group_id}: {e}")
                    self.data.schedules.append({"error": f"Ошибка парсинга JSON: {e}"})
            else:
                logging.warning(f"Invalid response for group {group_id}: status={response.status_code}")
                self.data.schedules.append({"error": f"Не удалось загрузить расписание для группы {group_id} (HTTP {response.status_code})"})
        except Exception as e:
            logging.error(f"Error fetching schedule for group {group_id}: {e}")
            self.data.schedules.append({"error": f"Ошибка загрузки расписания: {e}"})

        self.data.save_schedules(self.data.schedules)
        if all("error" in sched for sched in self.data.schedules):
            notify_callback("Не удалось загрузить расписание. Проверьте подключение или выберите другую группу.")
        disciplines = self.utils.get_unique_disciplines(self.data.schedules)
        logging.info(f"Disciplines after API load: {disciplines}")
        await display_callback()

    async def refresh_schedules(self, display_callback):
        if not self.group_id:
            logging.warning("No group_id set, skipping refresh")
            return

        self.data.previous_schedules = self.data.schedules.copy()
        self.data.save_previous_schedules()

        self.data.schedules = []
        try:
            url = f"https://ursei.su/asu/ssched.php?group={self.group_id}"
            response = requests.get(url, timeout=5)
            logging.info(f"API response for group {self.group_id}: {response.status_code} - {response.text[:200]}")
            if response.status_code == 200 and response.text.strip():
                try:
                    schedule = response.json()
                except ValueError:
                    schedule = self.data.parse_html_schedule(response.text)
                if self.validation.validate_schedule(schedule):
                    self.data.schedules.append(schedule)
                    self.data.last_schedule_update = datetime.datetime.now(pytz.timezone("Asia/Yekaterinburg"))
                    logging.info("Schedule refreshed successfully")
                else:
                    logging.warning(f"Invalid schedule structure for group {self.group_id}")
                    self.data.schedules.append({"error": f"Некорректная структура расписания для группы {self.group_id}"})
            else:
                logging.warning(f"Invalid response for group {self.group_id}: status={response.status_code}")
                self.data.schedules.append({"error": f"Не удалось загрузить расписание для группы {self.group_id}"})
        except Exception as e:
            logging.error(f"Error fetching schedule for group {self.group_id}: {e}")
            self.data.schedules.append({"error": f"Ошибка загрузки расписания: {e}"})

        self.data.save_schedules(self.data.schedules)
        await self.notifications.check_schedule_changes(self.data.previous_schedules, self.data.schedules, lambda msg: None)
        await display_callback()

    async def schedule_daily_check(self, display_callback):
        chelyabinsk_tz = pytz.timezone("Asia/Yekaterinburg")
        while True:
            now = datetime.datetime.now(chelyabinsk_tz)
            target_time = now.replace(hour=5, minute=0, second=0, microsecond=0)
            if now > target_time:
                target_time += datetime.timedelta(days=1)

            seconds_until_check = (target_time - now).total_seconds()
            logging.info(f"Next schedule check in {seconds_until_check} seconds")
            await asyncio.sleep(seconds_until_check)

            logging.info("Checking for schedule changes...")
            await self.refresh_schedules(display_callback)