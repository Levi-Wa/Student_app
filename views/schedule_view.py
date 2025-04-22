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

class ScheduleTab:
    def __init__(self, page: ft.Page, app):
        self.page = page
        self.app = app
        self.group_id = None
        self.schedules = []
        self.previous_schedules = []
        self.selected_period = "Сегодня"
        self.schedule_output = ft.Column(scroll=ft.ScrollMode.AUTO)
        self.schedules_file = "schedules.json"
        self.previous_schedules_file = "previous_schedules.json"
        self.load_previous_schedules()

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
            # Проверяем, что self.schedules является списком
            if not isinstance(self.schedules, list):
                print(f"Error: self.schedules is not a list: {type(self.schedules)}")
                self.schedules = []
            with open(self.schedules_file, "w", encoding="utf-8") as f:
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
            return False
        if not schedule.get("Month"):
            return False
        for month in schedule["Month"]:
            if not month.get("Sched"):
                return False
            for day in month["Sched"]:
                if not day.get("datePair") or not day.get("mainSchedule"):
                    return False
                for lesson in day["mainSchedule"]:
                    if not lesson.get("Dis") or not lesson.get("timeStart"):
                        return False
        return True

    async def load_schedule_for_group(self, group_id: str):
        self.group_id = group_id
        self.schedules = self.load_local_schedules()
        if self.schedules and any(self.validate_schedule(sched) for sched in self.schedules):
            print("Loaded schedules from local file")
            await self.display_schedules()
            self.page.run_task(self.schedule_daily_check)
            return

        self.schedules = []
        try:
            url = f"https://ursei.su/asu/ssched.php?group={group_id}"
            response = requests.get(url, timeout=5)
            print(
                f"API response for group {group_id}: {response.status_code} - {response.text[:1000]}")  # Логируем больше данных
            with open("api_response.html", "w", encoding="utf-8") as f:  # Сохраняем ответ для анализа
                f.write(response.text)
            if response.status_code == 200 and response.text.strip():
                try:
                    schedule = response.json()
                except ValueError:
                    schedule = self.parse_html_schedule(response.text)
                if self.validate_schedule(schedule):
                    self.schedules.append(schedule)
                else:
                    print(f"Invalid schedule structure for group {group_id}")
                    self.schedules.append({"error": f"Некорректная структура расписания для группы {group_id}"})
            else:
                print(f"Invalid response for group {group_id}: {response.status_code}")
                self.schedules.append({"error": f"Не удалось загрузить расписание для группы {group_id}"})
        except Exception as e:
            print(f"Error fetching schedule for group {group_id}: {e}")
            self.schedules.append({"error": f"Ошибка загрузки расписания: {e}"})

        self.save_schedules()
        await self.display_schedules()
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

    def get_unique_disciplines(self) -> List[str]:
        """Получение уникальных дисциплин из загруженного расписания"""
        disciplines = set()
        for schedule in self.schedules:
            if "error" in schedule:
                continue
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    for lesson in day.get("mainSchedule", []):
                        discipline = lesson.get("Dis", "")
                        if discipline:
                            disciplines.add(discipline)
        return sorted(list(disciplines))

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
        """Отображение расписания на основе выбранного периода"""
        print(f"Clearing schedule_output, current controls: {len(self.schedule_output.controls)}")
        self.schedule_output.controls.clear()
        current_date = datetime.date.today()
        tomorrow = current_date + datetime.timedelta(days=1)
        all_day_cards = []

        print(f"Displaying schedules for period: {self.selected_period}")

        for schedule in self.schedules:
            if "error" in schedule:
                self.schedule_output.controls.append(
                    ft.Text(f"Ошибка: {schedule['error']}", color="red")
                )
                continue

            group_column = ft.Column()

            if not schedule.get("Month"):
                self.schedule_output.controls.append(
                    ft.Text("Нет данных", color="orange")
                )
                continue

            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    if not date_str:
                        print("Skipping empty date")
                        continue

                    try:
                        day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                    except ValueError as ve:
                        print(f"Invalid date format: {date_str}, error: {ve}")
                        continue

                    if self.selected_period == "Сегодня" and day_date != current_date:
                        continue
                    elif self.selected_period == "Неделя" and not (0 <= (day_date - current_date).days < 7):
                        continue
                    elif self.selected_period == "Месяц" and (
                            day_date.month != current_date.month or day_date.year != current_date.year):
                        continue
                    elif self.selected_period == "Все":
                        pass
                    else:
                        print(f"Unknown period: {self.selected_period}")
                        continue

                    print(f"Adding day: {date_str} for period: {self.selected_period}")

                    highlight_current_pair = (self.selected_period == "Сегодня")
                    force_blue = (self.selected_period == "Неделя" and day_date == tomorrow)

                    day_card = self.create_day_card(day, current_date, tomorrow, highlight_current_pair, force_blue)
                    all_day_cards.append((day_card, date_str))
                    group_column.controls.append(day_card)

            if group_column.controls:
                self.schedule_output.controls.append(
                    ft.Container(content=group_column, padding=10, bgcolor="#f9f9f9", border_radius=10, margin=5)
                )
            else:
                self.schedule_output.controls.append(
                    ft.Text("Нет расписания в выбранном периоде", color="orange")
                )

        if not self.schedule_output.controls:
            self.schedule_output.controls.append(
                ft.Text("Нет расписания для выбранного периода", color="orange")
            )

        print(f"Total cards added: {len(all_day_cards)}")
        print(f"Schedule output controls after update: {len(self.schedule_output.controls)}")

        self.schedule_output.update()
        self.page.update()

        print(f"Attempting to scroll to current date: {current_date.strftime('%d.%m.%Y')}")
        if all_day_cards:
            current_date_str = current_date.strftime("%d.%m.%Y")
            current_card_key = f"date_{current_date_str}"
            try:
                await asyncio.sleep(0.5)
                self.page.update()
                print(f"Scrolling to card with key: {current_card_key}")
                self.page.scroll_to(key=current_card_key, duration=1000)
            except AttributeError as e:
                print(f"Error: scroll_to with key not supported, falling back to index-based scrolling: {e}")
                card_index = next((i for i, (_, date) in enumerate(all_day_cards) if date == current_date_str), -1)
                if card_index >= 0:
                    estimated_offset = card_index * 150 + 50
                    print(f"Scrolling to estimated offset: {estimated_offset}")
                    self.page.scroll_to(offset=estimated_offset, duration=1000)
                else:
                    print("Current date card not found, scrolling to top")
                    self.page.scroll_to(offset=0, duration=1000)
            except Exception as e:
                print(f"Error during scroll attempt: {e}")
                self.page.scroll_to(offset=0, duration=1000)
        else:
            print("No cards to scroll to, scrolling to top")
            self.page.scroll_to(offset=0, duration=1000)

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
            width=200,
            on_change=lambda e: self.page.run_task(self.update_period, e.control.value)
        )

        return ft.Column([
            ft.Row([
                period_dropdown
            ], alignment=ft.MainAxisAlignment.CENTER),
            self.schedule_output
        ], scroll=ft.ScrollMode.AUTO)

    async def update_period(self, period: str):
        """Обновляем период отображения"""
        print(f"Updating period to: {period}")
        self.selected_period = period
        await self.display_schedules()