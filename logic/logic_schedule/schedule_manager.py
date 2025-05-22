import logging
import json
import asyncio
import datetime
import requests
import aiohttp
from typing import List, Dict
from logic.logic_schedule.schedule_data import ScheduleData
from logic.logic_schedule.schedule_validation import ScheduleValidation
from logic.logic_schedule.schedule_notifications import ScheduleNotifications
from logic.logic_schedule.schedule_utils import ScheduleUtils


class ScheduleManager:
    def __init__(self):
        self.data = ScheduleData()
        self.validation = ScheduleValidation()
        self.notifications = ScheduleNotifications()
        self.utils = ScheduleUtils()
        self.group_id = None
        logging.info("ScheduleManager initialized")

    async def check_schedule_on_open(self, display_callback):
        """Проверяет, нужно ли обновить расписание при открытии приложения."""
        logging.info("Checking schedule on open")
        now = datetime.datetime.now()
        if self.data.last_schedule_update is None:
            logging.info("No previous schedule update, fetching new schedule")
            await self.fetch_and_update_schedule(display_callback)
        else:
            last_update_naive = self.data.last_schedule_update.replace(tzinfo=None)
            logging.info(f"Comparing now: {now}, last_update_naive: {last_update_naive}")
            if (now - last_update_naive).total_seconds() > 24 * 3600:
                logging.info("Schedule is outdated, fetching new schedule")
                await self.fetch_and_update_schedule(display_callback)
            else:
                logging.info("Schedule is up-to-date, using cached data")
                if display_callback:
                    await display_callback()

    async def load_schedule_for_group(self, group_id: str, display_callback, notify_callback):
        """Load schedule for a specific group with improved error handling"""
        self.group_id = group_id
        self.data.group_id = group_id
        
        # Загружаем локальные данные и API параллельно
        local_load_task = asyncio.create_task(self._load_local_schedules())
        api_load_task = asyncio.create_task(self._load_api_schedules(group_id))
        
        # Ждем загрузку локальных данных (они быстрее)
        await local_load_task
        
        # Если локальные данные валидны, используем их
        if self.data.schedules and any(self.validation.validate_schedule(sched) for sched in self.data.schedules):
            logging.info("Using valid local schedules")
            await self.check_schedule_on_open(display_callback)
            return
        
        # Иначе ждем загрузку с API
        await api_load_task
        
        # Сохраняем данные
        try:
            self.data.save_schedules()
            logging.info(f"Schedules saved for group {group_id}")
        except Exception as e:
            logging.error(f"Failed to save schedules: {e}")
            notify_callback(f"Ошибка сохранения расписания: {str(e)}")

        # Обновляем отображение
        try:
            await display_callback()
        except Exception as e:
            logging.error(f"Error updating display: {e}")
            notify_callback("Ошибка обновления интерфейса")

    async def _load_local_schedules(self):
        """Загрузка локальных данных расписания"""
        try:
            self.data.load_schedules()
            logging.info("Loaded schedules from local storage")
        except Exception as e:
            logging.error(f"Error loading local schedules: {e}")

    async def _load_api_schedules(self, group_id: str):
        """Загрузка расписания с API"""
        max_retries = 2  # Уменьшаем количество попыток
        retry_delay = 1  # Уменьшаем задержку между попытками
        
        for attempt in range(max_retries):
            try:
                url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
                logging.info(f"Fetching schedule from {url} (attempt {attempt + 1}/{max_retries})")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            text = await response.text()
                            if text.strip():
                                try:
                                    schedule = json.loads(text)
                                    if self.validation.validate_schedule(schedule):
                                        self.data.schedules = [schedule]  # Заменяем все расписания
                                        logging.info("Schedule validated and added")
                                        return
                                except json.JSONDecodeError as e:
                                    logging.error(f"Failed to parse schedule JSON: {e}")
                        else:
                            logging.warning(f"Server returned status {response.status}")
                
            except Exception as e:
                logging.error(f"Error fetching schedule: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)

    async def refresh_schedules(self, display_callback):
        if not self.group_id:
            logging.warning("No group_id set, skipping refresh")
            return

        self.data.previous_schedules = self.data.schedules.copy()
        self.data.save_previous_schedules()

        self.data.schedules = []
        try:
            url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={self.group_id}"
            logging.info(f"Fetching schedule from {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        text = await response.text()
                        if text.strip():
                            try:
                                schedule = json.loads(text)
                                if self.validation.validate_schedule(schedule):
                                    self.data.schedules.append(schedule)
                                    self.data.last_schedule_update = datetime.datetime.now()
                                    logging.info("Schedule refreshed successfully")
                                else:
                                    logging.warning(f"Invalid schedule structure for group {self.group_id}")
                                    self.data.schedules.append(
                                        {"error": f"Некорректная структура расписания для группы {self.group_id}"})
                            except json.JSONDecodeError:
                                logging.warning(f"Failed to parse JSON for group {self.group_id}")
                                self.data.schedules.append({"error": f"Ошибка парсинга JSON для группы {self.group_id}"})
                        else:
                            logging.warning(f"Empty response for group {self.group_id}")
                            self.data.schedules.append({"error": f"Пустой ответ от сервера для группы {self.group_id}"})
                    else:
                        logging.warning(f"Invalid response for group {self.group_id}: status={response.status}")
                        self.data.schedules.append({"error": f"Не удалось загрузить расписание для группы {self.group_id}"})
        except Exception as e:
            logging.error(f"Error fetching schedule for group {self.group_id}: {e}")
            self.data.schedules.append({"error": f"Ошибка загрузки расписания: {e}"})

        try:
            self.data.save_schedules()
            logging.info(f"Schedules saved during refresh for group {self.group_id}")
        except Exception as e:
            logging.error(f"Failed to save schedules during refresh: {e}")

        await self.notifications.check_schedule_changes(self.data.previous_schedules, self.data.schedules,
                                                        lambda msg: None)
        await display_callback()

    async def schedule_daily_check(self, display_callback):
        while True:
            now = datetime.datetime.now()
            target_time = now.replace(hour=5, minute=0, second=0, microsecond=0)
            if now > target_time:
                target_time += datetime.timedelta(days=1)

            seconds_until_check = (target_time - now).total_seconds()
            logging.info(f"Next schedule check in {seconds_until_check} seconds")
            await asyncio.sleep(seconds_until_check)

            logging.info("Checking for schedule changes...")
            await self.refresh_schedules(display_callback)

    async def fetch_and_update_schedule(self, display_callback):
        """Получает и обновляет расписание."""
        await self.refresh_schedules(display_callback)

    async def load_local_schedules(self):
        """Загружает расписание из локального хранилища"""
        try:
            schedules = await self.data.load_schedules()
            if schedules:
                self.data.schedules = schedules
                logging.info("Local schedules loaded successfully")
            else:
                logging.warning("No local schedules found")
        except Exception as e:
            logging.error(f"Error loading local schedules: {e}")
            self.data.schedules = []