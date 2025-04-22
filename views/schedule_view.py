import flet as ft
import datetime
import requests
import json
import os
from typing import List, Dict
import asyncio
import pytz
from plyer import notification
from bs4 import BeautifulSoup

BELL_SCHEDULE = {
    "08:30": ["8:30–9:15", "9:20–10:05"],  # 1 пара
    "10:15": ["10:15–11:00", "11:05–11:50"],  # 2 пара
    "12:00": ["12:00–12:45", "12:50–13:35"],  # 3 пара
    "14:05": ["14:05–14:50", "14:55–15:40"],  # 4 пара
    "15:50": ["15:50–16:35", "16:40–17:25"],  # 5 пара
    "17:35": ["17:35–18:20", "18:25–19:10"],  # 6 пара
    "19:15": ["19:15–20:00", "20:05–20:50"],  # 7 пара
    "20:55": ["20:55–21:40", "21:45–22:30"]  # 8 пара
}

class ScheduleTab:
    def __init__(self, page: ft.Page):
        self.page = page
        self.schedules_file = "schedules.json"
        self.previous_schedules_file = "previous_schedules.json"
        self.schedules = []
        self.group_id = None
        self.selected_period = "Сегодня"
        self.schedule_output = ft.Column(scroll=ft.ScrollMode.AUTO)
        self._cached_disciplines = None  # Кэш для дисциплин
        self._cached_disciplines_timestamp = 0

    def get_unique_disciplines(self) -> List[str]:
        """Получаем уникальные дисциплины из расписания"""
        # Проверяем, актуален ли кэш
        if self._cached_disciplines is not None and self._cached_disciplines_timestamp == id(self.schedules):
            return self._cached_disciplines

        disciplines = set()
        for schedule in self.schedules:
            if "error" in schedule:
                continue
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    for lesson in day.get("mainSchedule", []):
                        subj_name = lesson.get("SubjName")
                        if subj_name:
                            disciplines.add(subj_name)
        self._cached_disciplines = sorted(list(disciplines))
        self._cached_disciplines_timestamp = id(self.schedules)
        print(f"Extracted disciplines: {self._cached_disciplines}")
        return self._cached_disciplines

    def load_local_schedules(self) -> List[Dict]:
        """Загрузка расписания из локального файла"""
        if os.path.exists(self.schedules_file):
            try:
                with open(self.schedules_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()  # Читаем и удаляем пробелы
                    if not content:  # Проверяем, пустой ли файл
                        print(f"Warning: {self.schedules_file} is empty")
                        return []
                    return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Error: Failed to parse {self.schedules_file}: {e}")
                return []
            except Exception as e:
                print(f"Error: Failed to read {self.schedules_file}: {e}")
                return []
        return []

    def save_schedules(self):
        """Сохранение расписания в локальный файл"""
        try:
            if not isinstance(self.schedules, list):
                print(f"Error: self.schedules is not a list: {type(self.schedules)}")
                self.schedules = []
            with open(self.schedules_file, "w", encoding="utf-8") as f:
                json.dump(self.schedules, f, ensure_ascii=False, indent=4)
            # Сохраняем последнее валидное расписание
            if any(self.validate_schedule(sched) for sched in self.schedules):
                with open("last_valid_schedules.json", "w", encoding="utf-8") as f:
                    json.dump(self.schedules, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error: Failed to save schedules to {self.schedules_file}: {e}")

    def load_previous_schedules(self):
        """Загрузка предыдущего расписания"""
        if os.path.exists(self.previous_schedules_file):
            with open(self.previous_schedules_file, "r", encoding="utf-8") as f:
                self.previous_schedules = json.load(f)
        else:
            self.previous_schedules = []

    def save_previous_schedules(self):
        """Сохранение предыдущего расписания"""
        with open(self.previous_schedules_file, "w", encoding="utf-8") as f:
            json.dump(self.previous_schedules, f, ensure_ascii=False, indent=4)

    def parse_html_schedule(self, html_content: str) -> Dict:
        """Парсим HTML-страницу с расписанием"""
        soup = BeautifulSoup(html_content, "html.parser")
        schedule_data = {"Month": []}
        current_month = {"Sched": []}

        table = soup.find("table")
        if not table:
            print("Error: No table found in HTML")
            return {"error": "Не удалось найти таблицу с расписанием"}

        rows = table.find_all("tr")
        if len(rows) <= 1:
            print("Error: Table has no data rows")
            return {"error": "Таблица не содержит данных"}

        for row in rows[1:]:  # Пропускаем заголовок
            cols = row.find_all("td")
            if len(cols) < 5:
                print(f"Warning: Row has insufficient columns: {len(cols)}")
                continue

            # Безопасное извлечение данных
            date_pair = cols[0].text.strip() if len(cols) > 0 else ""
            day_week = cols[1].text.strip() if len(cols) > 1 else ""
            time_text = cols[2].text.strip() if len(cols) > 2 else ""
            time_start = time_text.split("-")[0] if "-" in time_text else ""
            time_end = time_text.split("-")[1] if "-" in time_text and len(time_text.split("-")) > 1 else ""
            discipline = cols[3].text.strip() if len(cols) > 3 else ""
            lesson_type = cols[4].text.strip() if len(cols) > 4 else ""
            room = cols[5].text.strip() if len(cols) > 5 else ""
            teacher = cols[6].text.strip() if len(cols) > 6 else ""

            # Пропускаем пустые строки
            if not (date_pair and discipline and time_start):
                print(f"Warning: Skipping row with missing critical data: {date_pair}, {discipline}, {time_start}")
                continue

            day_schedule = {
                "datePair": date_pair,
                "dayWeek": day_week,
                "mainSchedule": [{
                    "timeStart": time_start,
                    "timeEnd": time_end,
                    "Dis": discipline,
                    "Type": lesson_type,
                    "Room": room,
                    "Teacher": teacher
                }]
            }
            current_month["Sched"].append(day_schedule)

        if not current_month["Sched"]:
            print("Error: No valid schedule data parsed")
            return {"error": "Не удалось извлечь данные расписания"}

        schedule_data["Month"].append(current_month)
        return schedule_data

    def validate_schedule(self, schedule: Dict) -> bool:
        """Проверка структуры расписания"""
        if "error" in schedule:
            print(f"Validation failed: {schedule['error']}")
            return False
        if not schedule.get("Month"):
            print("Validation failed: No 'Month' key in schedule")
            return False
        for month in schedule["Month"]:
            if not month.get("Sched"):
                print("Validation failed: No 'Sched' key in month")
                return False
            for day in month["Sched"]:
                if not day.get("datePair") or not day.get("mainSchedule"):
                    print(f"Validation failed: Invalid day structure: {day}")
                    return False
                for lesson in day["mainSchedule"]:
                    if not lesson.get("SubjName") or not lesson.get("TimeStart"):
                        print(f"Validation failed: Invalid lesson structure: {lesson}")
                        return False
        return True

    async def load_schedule_for_group(self, group_id: str):
        """Загружаем расписание для выбранной группы"""
        self.group_id = group_id
        self.schedules = self.load_local_schedules()
        if self.schedules and any(self.validate_schedule(sched) for sched in self.schedules):
            print("Loaded schedules from local file")
            self.page.run_task(self.schedule_daily_check)
            return

        self.schedules = []
        try:
            url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
            response = requests.get(url, timeout=5)
            print(f"API response for group {group_id}: {response.status_code} - {response.text[:1000]}")
            if response.status_code == 200 and response.text.strip():
                try:
                    schedule = response.json()
                    if self.validate_schedule(schedule):
                        self.schedules.append(schedule)
                    else:
                        print(f"Invalid schedule structure for group {group_id}: {schedule}")
                        self.schedules.append({"error": f"Некорректная структура расписания для группы {group_id}"})
                except ValueError as e:
                    print(f"Failed to parse JSON for group {group_id}: {e}")
                    self.schedules.append({"error": f"Ошибка парсинга JSON: {e}"})
            else:
                print(f"Invalid response for group {group_id}: {response.status_code}")
                self.schedules.append({"error": f"Не удалось загрузить расписание для группы {group_id}"})
        except Exception as e:
            print(f"Error fetching schedule for group {group_id}: {e}")
            self.schedules.append({"error": f"Ошибка загрузки расписания: {e}"})

        self.save_schedules()
        if all("error" in sched for sched in self.schedules):
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Не удалось загрузить расписание. Проверьте подключение или выберите другую группу."),
                duration=5000
            )
            self.page.snack_bar.open = True
            self.page.update()
        self.page.run_task(self.schedule_daily_check)

    async def refresh_schedules(self):
        """Обновление расписания"""
        if not self.group_id:
            return

        self.previous_schedules = self.schedules.copy()
        self.save_previous_schedules()

        self.schedules = []
        try:
            url = f"https://ursei.su/asu/ssched.php?group={self.group_id}"
            response = requests.get(url, timeout=5)
            print(f"API response for group {self.group_id}: {response.status_code} - {response.text[:200]}")
            if response.status_code == 200 and response.text.strip():
                try:
                    schedule = response.json()
                except ValueError:
                    schedule = self.parse_html_schedule(response.text)
                if self.validate_schedule(schedule):
                    self.schedules.append(schedule)
                else:
                    print(f"Invalid schedule structure for group {self.group_id}")
                    self.schedules.append({"error": f"Некорректная структура расписания для группы {self.group_id}"})
            else:
                print(f"Invalid response for group {self.group_id}: {response.status_code}")
                self.schedules.append({"error": f"Не удалось загрузить расписание для группы {self.group_id}"})
        except Exception as e:
            print(f"Error fetching schedule for group {self.group_id}: {e}")
            self.schedules.append({"error": f"Ошибка загрузки расписания: {e}"})

        self.save_schedules()
        await self.check_schedule_changes()
        await self.display_schedules()

    def notify(self, title: str, message: str):
        """Отправка push-уведомления"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Студенческое приложение",
                timeout=10
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(message),
                duration=10000
            )
            self.page.snack_bar.open = True
            self.page.update()

    async def check_schedule_changes(self):
        """Проверка изменений в расписании"""
        if not self.app.settings.get("schedule_notifications", True):
            print("Schedule change notifications are disabled")
            return

        if not self.previous_schedules or not self.schedules:
            return

        changes = []
        for old_sched, new_sched in zip(self.previous_schedules, self.schedules):
            if "error" in old_sched or "error" in new_sched:
                continue

            old_lessons = {}
            new_lessons = {}

            for month in old_sched.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    for lesson in day.get("mainSchedule", []):
                        key = (date_str, lesson.get("Dis", ""), lesson.get("timeStart", ""))
                        old_lessons[key] = lesson

            for month in new_sched.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    for lesson in day.get("mainSchedule", []):
                        key = (date_str, lesson.get("Dis", ""), lesson.get("timeStart", ""))
                        new_lessons[key] = lesson

            for key, new_lesson in new_lessons.items():
                old_lesson = old_lessons.get(key)
                if not old_lesson:
                    changes.append(f"Новое занятие: {new_lesson['Dis']} ({new_lesson['datePair']})")
                    continue

                change_details = []
                if old_lesson.get("Type", "") != new_lesson.get("Type", ""):
                    change_details.append(f"Тип занятия: {old_lesson['Type']} → {new_lesson['Type']}")
                if old_lesson.get("Room", "") != new_lesson.get("Room", ""):
                    change_details.append(f"Аудитория: {old_lesson['Room']} → {new_lesson['Room']}")
                if old_lesson.get("timeStart", "") != new_lesson.get("timeStart", "") or old_lesson.get("timeEnd", "") != new_lesson.get("timeEnd", ""):
                    change_details.append(f"Время: {old_lesson['timeStart']}-{old_lesson['timeEnd']} → {new_lesson['timeStart']}-{new_lesson['timeEnd']}")

                if change_details:
                    changes.append(f"{new_lesson['Dis']} ({new_lesson['datePair']}): {', '.join(change_details)}")

        if changes:
            self.notify("Изменения в расписании", "; ".join(changes))

    async def schedule_daily_check(self):
        """Планировщик проверки расписания в 5 утра по челябинскому времени"""
        chelyabinsk_tz = pytz.timezone("Asia/Yekaterinburg")
        while True:
            now = datetime.datetime.now(chelyabinsk_tz)
            target_time = now.replace(hour=5, minute=0, second=0, microsecond=0)
            if now > target_time:
                target_time += datetime.timedelta(days=1)

            seconds_until_check = (target_time - now).total_seconds()
            print(f"Next schedule check in {seconds_until_check} seconds")
            await asyncio.sleep(seconds_until_check)

            print("Checking for schedule changes...")
            await self.refresh_schedules()

    def get_next_lesson_date(self, discipline: str, mode: str) -> datetime.date:
        """Определение даты следующего занятия по дисциплине"""
        current_date = datetime.date.today()
        next_lesson_date = None
        for schedule in self.schedules:
            if "error" in schedule:
                continue
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    try:
                        day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                        if day_date < current_date:
                            continue
                        for lesson in day.get("mainSchedule", []):
                            if lesson.get("Dis", "") == discipline:
                                lesson_type = lesson.get("Type", "").lower()
                                if mode == "До следующего занятия":
                                    if next_lesson_date is None or day_date < next_lesson_date:
                                        next_lesson_date = day_date
                                elif mode == "До следующей практики" and "практика" in lesson_type:
                                    if next_lesson_date is None or day_date < next_lesson_date:
                                        next_lesson_date = day_date
                    except ValueError:
                        continue
        return next_lesson_date if next_lesson_date else (current_date + datetime.timedelta(days=7))

    def get_date_color(self, day_date: datetime.date, current_date: datetime.date, tomorrow_date: datetime.date) -> str:
        """Определяем цвет даты"""
        return "blue" if day_date == tomorrow_date else "red" if day_date == current_date else "black"

    def create_lessons(self, main_schedule: List[Dict], day_date: datetime.date, highlight_current_pair: bool = False):
        """Создаём список уроков для дня"""
        lessons = ft.Column()
        current_time = datetime.datetime.now().time()

        for pair in main_schedule:
            time_start = pair.get("timeStart", "")
            time_end = pair.get("timeEnd", "")
            discipline = pair.get("Dis", "")
            lesson_type = pair.get("Type", "")
            room = pair.get("Room", "")
            teacher = pair.get("Teacher", "")

            if not all([time_start, time_end, discipline]):
                continue

            status = "future"
            if highlight_current_pair:
                try:
                    start_time = datetime.datetime.strptime(time_start, "%H:%M").time()
                    end_time = datetime.datetime.strptime(time_end, "%H:%M").time()
                    if start_time <= current_time <= end_time:
                        status = "current"
                    elif current_time > end_time:
                        status = "past"
                except ValueError:
                    pass

            indicator_color = {
                "past": "red",
                "current": "green",
                "future": "blue"
            }.get(status, "black")

            lesson_card = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(time_start, size=16, weight="bold"),
                        ft.Text(f"{discipline} {lesson_type}", size=12),
                        ft.Text(f"Ауд. {room}", size=12),
                        ft.Text(teacher, size=12)
                    ], expand=True),
                    ft.Container(
                        width=15,
                        height=15,
                        bgcolor=indicator_color,
                        border_radius=7.5
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=10,
                margin=5,
                bgcolor="#ffffff",
                border=ft.border.all(1, "#ddd"),
                border_radius=8
            )

            lessons.controls.append(lesson_card)

        return lessons

    def create_day_card(self, day: Dict, current_date: datetime.date, tomorrow_date: datetime.date,
                        highlight_current_pair: bool = False, force_blue: bool = False):
        """Создаём карточку дня"""
        try:
            date_str = day.get("datePair", "")
            if not date_str:
                return ft.Text("Дата не указана", color="red")

            day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            day_week = day.get("dayWeek", "")
            color = "blue" if force_blue else self.get_date_color(day_date, current_date, tomorrow_date)
            lessons = self.create_lessons(day.get("mainSchedule", []), day_date, highlight_current_pair)

            return ft.Container(
                key=f"date_{date_str}",
                content=ft.Column([
                    ft.Text(f"\ud83d\uddd5\ufe0f {date_str} ({day_week})", weight="bold", color=color),
                    lessons
                ]),
                padding=10,
                margin=5,
                bgcolor="#ffffff",
                border=ft.border.all(1, "#ddd"),
                border_radius=8
            )
        except Exception as ex:
            return ft.Text(f"Ошибка дня: {str(ex)}", color="red")

    async def display_schedules(self):
        """Отображаем расписание для выбранного периода"""
        print(f"Clearing schedule_output, current controls: {len(self.schedule_output.controls)}")
        self.schedule_output.controls.clear()

        if not self.schedules:
            self.schedule_output.controls.append(ft.Text("Нет данных для отображения"))
            print("No schedules to display")
            self.page.update()
            return

        today = datetime.datetime.now()
        today_date = today.date()
        tomorrow_date = today_date + datetime.timedelta(days=1)  # Завтра
        current_time = today.time()
        start_of_week = today_date - datetime.timedelta(days=today_date.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        start_of_month = today_date.replace(day=1)
        end_of_month = (today_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(
            days=1)

        cards = []
        for schedule in self.schedules:
            if "error" in schedule:
                self.schedule_output.controls.append(ft.Text(schedule["error"]))
                continue
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_pair = day.get("datePair", "")
                    try:
                        day_date = datetime.datetime.strptime(date_pair, "%d.%m.%Y").date()
                    except ValueError:
                        print(f"Invalid date format: {date_pair}")
                        continue

                    # Фильтрация по периоду
                    if self.selected_period == "Сегодня" and day_date != today_date:
                        continue
                    elif self.selected_period == "Неделя" and (day_date < start_of_week or day_date > end_of_week):
                        continue
                    elif self.selected_period == "Месяц" and (day_date < start_of_month or day_date > end_of_month):
                        continue

                    if self.selected_period == "Сегодня":
                        # Режим "Сегодня" — отдельные контейнеры для каждой пары
                        for lesson in day.get("mainSchedule", []):
                            time_start = lesson.get("TimeStart", "")
                            try:
                                lesson_time = datetime.datetime.strptime(time_start, "%H:%M").time()
                            except ValueError:
                                print(f"Invalid time format: {time_start}")
                                continue

                            is_past = day_date < today_date or (day_date == today_date and lesson_time < current_time)
                            is_current = (day_date == today_date and
                                          lesson_time <= current_time and
                                          lesson_time >= (datetime.datetime.combine(today_date,
                                                                                    current_time) - datetime.timedelta(
                                        minutes=90)).time())
                            color = "red" if is_past else "green" if is_current else "blue"

                            bell_times = BELL_SCHEDULE.get(time_start, ["", ""]) if is_current else ["", ""]
                            time_display = f"{time_start} – {bell_times[0]} / {bell_times[1]}" if is_current else time_start

                            lesson_card = ft.Card(
                                content=ft.Container(
                                    content=ft.Column([
                                        ft.Container(
                                            content=ft.CircleAvatar(bgcolor=color, radius=10),
                                            alignment=ft.alignment.top_left
                                        ),
                                        ft.Text(f"{time_display}", weight="bold", size=16),
                                        ft.Text(f"{lesson.get('SubjName', '')} ({lesson.get('LoadKindSN', '')})",
                                                size=14),
                                        ft.Text(f"Ауд: {lesson.get('Aud', '')}", size=12),
                                        ft.Text(f"Преп: {lesson.get('FIO', '')}", size=12)
                                    ], spacing=5),
                                    padding=15,
                                    margin=10
                                ),
                                elevation=2,
                                shape=ft.RoundedRectangleBorder(radius=10),
                                color="white"
                            )
                            cards.append(lesson_card)
                    else:
                        # Режимы "Неделя", "Месяц", "Все" — карточка на день
                        is_past = day_date < today_date
                        is_current = day_date == today_date
                        is_tomorrow = day_date == tomorrow_date
                        indicator_color = "grey" if is_past else "green" if is_current else "blue" if is_tomorrow else "grey200"

                        day_card = ft.Card(
                            content=ft.Container(
                                content=ft.Row([
                                    ft.Column([
                                        ft.Text(f"{date_pair} ({day.get('dayWeek', '')})", weight="bold", size=16,
                                                color=ft.colors.BLACK87),
                                        *[
                                            ft.Text(
                                                f"{lesson.get('TimeStart', '')} - {lesson.get('SubjName', '')} ({lesson.get('LoadKindSN', '')}) "
                                                f"Ауд: {lesson.get('Aud', '')}, Преп: {lesson.get('FIO', '')}",
                                                size=14,
                                                color=ft.colors.BLACK54
                                            )
                                            for lesson in day.get("mainSchedule", [])
                                        ]
                                    ], expand=True, spacing=8),
                                    ft.Container(
                                        content=ft.CircleAvatar(bgcolor=indicator_color, radius=10),
                                        alignment=ft.alignment.center,
                                        margin=ft.margin.only(right=10)
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                padding=15,
                                margin=ft.margin.all(10)
                            ),
                            elevation=4,  # Увеличенная тень
                            shape=ft.RoundedRectangleBorder(radius=12),
                            color=ft.colors.WHITE,
                            key=date_pair
                        )
                        cards.append(day_card)

        self.schedule_output.controls.extend(cards)
        print(f"Total cards added: {len(cards)}")

        if not cards:
            self.schedule_output.controls.append(ft.Text("Нет занятий для выбранного периода"))

        self.page.update()
        print(f"Schedule output controls after update: {len(self.schedule_output.controls)}")

        # Прокрутка к текущей дате
        if self.selected_period in ["Сегодня", "Неделя", "Месяц", "Все"] and cards:
            target_key = today_date.strftime("%d.%m.%Y")
            if any(card.key == target_key for card in cards if hasattr(card, 'key')):
                try:
                    self.schedule_output.scroll_to(key=target_key, duration=1000)
                except Exception as e:
                    print(f"Scroll error: {e}")
            else:
                print(f"Scroll skipped: No card found for {target_key}")

    def build(self):
        """Создаём интерфейс вкладки расписания"""
        period_dropdown = ft.Dropdown(
            label="Период",
            options=[
                ft.dropdown.Option("Сегодня"),
                ft.dropdown.Option("Неделя"),
                ft.dropdown.Option("Месяц"),
                ft.dropdown.Option("Все")
            ],
            value=self.selected_period,
            on_change=lambda e: self.page.run_task(self.update_period, e.control.value)
        )

        return ft.Column([
            ft.Row([
                period_dropdown
            ], alignment=ft.MainAxisAlignment.CENTER),
            self.schedule_output  # Убедитесь, что schedule_output включен
        ], scroll=ft.ScrollMode.AUTO)

    async def update_period(self, period: str):
        """Обновляем период отображения"""
        print(f"Updating period to: {period}")
        self.selected_period = period
        await self.display_schedules()