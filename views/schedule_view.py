import flet as ft
import datetime
import requests
import json
import os
from typing import List, Dict
import asyncio
import pytz

class ScheduleTab:
    def __init__(self, page: ft.Page, app):
        self.page = page
        self.app = app
        self.group_ids = []
        self.schedules = []
        self.previous_schedules = []
        self.selected_period = "Сегодня"
        self.schedule_output = ft.Column(scroll=ft.ScrollMode.AUTO)
        self.schedules_file = "schedules.json"
        self.previous_schedules_file = "previous_schedules.json"
        self.load_previous_schedules()
        self.page.run_task(self.schedule_daily_check)

    async def set_groups(self, group_ids: List[int]):
        """Устанавливаем группы"""
        self.group_ids = [str(gid) for gid in group_ids]

    def load_local_schedules(self) -> List[Dict]:
        """Загрузка расписания из локального файла"""
        if os.path.exists(self.schedules_file):
            with open(self.schedules_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_schedules(self):
        """Сохранение расписания в локальный файл"""
        with open(self.schedules_file, "w", encoding="utf-8") as f:
            json.dump(self.schedules, f, ensure_ascii=False, indent=4)

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

    async def load_schedules(self):
        """Загружаем расписание для всех групп"""
        self.schedules = self.load_local_schedules()
        if self.schedules and any("error" not in sched for sched in self.schedules):
            print("Loaded schedules from local file")
            await self.display_schedules()
            return

        self.schedules = []
        api_error = False
        for group_id in self.group_ids:
            try:
                url = f"https://ursei.su/asu/ssched.php?group={group_id}"
                response = requests.get(url, timeout=5)
                print(f"API response for group {group_id}: {response.status_code} - {response.text[:200]}")
                if response.status_code == 200 and response.text.strip():
                    try:
                        schedule = response.json()
                        self.schedules.append(schedule)
                    except ValueError as e:
                        print(f"Error fetching schedule for group {group_id}: {e}")
                        self.schedules.append({"error": f"Не удалось загрузить расписание для группы {group_id}"})
                        api_error = True
                else:
                    print(f"Invalid response for group {group_id}: {response.status_code}")
                    self.schedules.append({"error": f"Не удалось загрузить расписание для группы {group_id}"})
                    api_error = True
            except Exception as e:
                print(f"Error fetching schedule for group {group_id}: {e}")
                self.schedules.append({"error": f"Ошибка загрузки расписания: {e}"})
                api_error = True

        if api_error and not any("error" not in sched for sched in self.schedules):
            print("Using fallback schedule due to API failure")
            today = datetime.date.today()
            tomorrow = today + datetime.timedelta(days=1)
            next_week = today + datetime.timedelta(days=7)
            self.schedules = [{
                "Month": [{
                    "Sched": [
                        {
                            "datePair": today.strftime("%d.%m.%Y"),
                            "dayWeek": "Пн",
                            "mainSchedule": [
                                {"timeStart": "09:00", "timeEnd": "10:30", "Dis": "Философия", "Type": "Лекция", "Room": "101", "Teacher": "Иванов И.И."},
                                {"timeStart": "10:40", "timeEnd": "12:10", "Dis": "Математика", "Type": "Практика", "Room": "102", "Teacher": "Петров П.П."}
                            ]
                        },
                        {
                            "datePair": tomorrow.strftime("%d.%m.%Y"),
                            "dayWeek": "Вт",
                            "mainSchedule": [
                                {"timeStart": "09:00", "timeEnd": "10:30", "Dis": "Программирование", "Type": "Лекция", "Room": "103", "Teacher": "Сидоров С.С."},
                                {"timeStart": "10:40", "timeEnd": "12:10", "Dis": "Физика", "Type": "Лекция", "Room": "104", "Teacher": "Смирнова А.А."}
                            ]
                        },
                        {
                            "datePair": next_week.strftime("%d.%m.%Y"),
                            "dayWeek": "Пн",
                            "mainSchedule": [
                                {"timeStart": "09:00", "timeEnd": "10:30", "Dis": "История", "Type": "Семинар", "Room": "105", "Teacher": "Козлов В.В."},
                                {"timeStart": "10:40", "timeEnd": "12:10", "Dis": "Литература", "Type": "Лекция", "Room": "106", "Teacher": "Фёдорова Е.Е."}
                            ]
                        }
                    ]
                }]
            }]
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Не удалось загрузить расписание с сервера. Используется тестовое расписание."),
                duration=5000
            )
            self.page.snack_bar.open = True
            self.page.update()

        self.save_schedules()
        await self.display_schedules()

    async def load_schedule_from_url(self, url: str, group_id: str):
        """Загрузка расписания по URL и сохранение в schedules.json"""
        try:
            response = requests.get(url, timeout=5)
            print(f"Manual API response for group {group_id}: {response.status_code} - {response.text[:200]}")
            if response.status_code == 200 and response.text.strip():
                schedule = response.json()
                # Проверяем, есть ли уже расписание для этой группы
                self.schedules = [s for s in self.schedules if not s.get("error", "").endswith(f"группы {group_id}")]
                self.schedules.append(schedule)
                self.save_schedules()
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Расписание для группы {group_id} успешно загружено!"),
                    duration=5000
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Не удалось загрузить расписание для группы {group_id}: код {response.status_code}"),
                    duration=5000
                )
        except ValueError as e:
            print(f"Error parsing JSON for group {group_id}: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Ошибка: сервер вернул невалидный JSON для группы {group_id}"),
                duration=5000
            )
        except Exception as e:
            print(f"Error fetching schedule for group {group_id}: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Ошибка загрузки расписания для группы {group_id}: {e}"),
                duration=5000
            )
        self.page.snack_bar.open = True
        self.page.update()
        await self.display_schedules()

    async def refresh_schedules(self):
        """Метод оставлен для совместимости, но больше не используется"""
        self.previous_schedules = self.schedules.copy()
        self.save_previous_schedules()

        self.schedules = []
        api_error = False
        for group_id in self.group_ids:
            try:
                url = f"https://ursei.su/asu/ssched.php?group={group_id}"
                response = requests.get(url, timeout=5)
                print(f"API response for group {group_id}: {response.status_code} - {response.text[:200]}")
                if response.status_code == 200 and response.text.strip():
                    try:
                        schedule = response.json()
                        self.schedules.append(schedule)
                    except ValueError as e:
                        print(f"Error fetching schedule for group {group_id}: {e}")
                        self.schedules.append({"error": f"Не удалось загрузить расписание для группы {group_id}"})
                        api_error = True
                else:
                    print(f"Invalid response for group {group_id}: {response.status_code}")
                    self.schedules.append({"error": f"Не удалось загрузить расписание для группы {group_id}"})
                    api_error = True
            except Exception as e:
                print(f"Error fetching schedule for group {group_id}: {e}")
                self.schedules.append({"error": f"Ошибка загрузки расписания: {e}"})
                api_error = True

        if api_error and not any("error" not in sched for sched in self.schedules):
            print("Using fallback schedule due to API failure")
            today = datetime.date.today()
            tomorrow = today + datetime.timedelta(days=1)
            next_week = today + datetime.timedelta(days=7)
            self.schedules = [{
                "Month": [{
                    "Sched": [
                        {
                            "datePair": today.strftime("%d.%m.%Y"),
                            "dayWeek": "Пн",
                            "mainSchedule": [
                                {"timeStart": "09:00", "timeEnd": "10:30", "Dis": "Философия", "Type": "Лекция", "Room": "101", "Teacher": "Иванов И.И."},
                                {"timeStart": "10:40", "timeEnd": "12:10", "Dis": "Математика", "Type": "Практика", "Room": "102", "Teacher": "Петров П.П."}
                            ]
                        },
                        {
                            "datePair": tomorrow.strftime("%d.%m.%Y"),
                            "dayWeek": "Вт",
                            "mainSchedule": [
                                {"timeStart": "09:00", "timeEnd": "10:30", "Dis": "Программирование", "Type": "Лекция", "Room": "103", "Teacher": "Сидоров С.С."},
                                {"timeStart": "10:40", "timeEnd": "12:10", "Dis": "Физика", "Type": "Лекция", "Room": "104", "Teacher": "Смирнова А.А."}
                            ]
                        },
                        {
                            "datePair": next_week.strftime("%d.%m.%Y"),
                            "dayWeek": "Пн",
                            "mainSchedule": [
                                {"timeStart": "09:00", "timeEnd": "10:30", "Dis": "История", "Type": "Семинар", "Room": "105", "Teacher": "Козлов В.В."},
                                {"timeStart": "10:40", "timeEnd": "12:10", "Dis": "Литература", "Type": "Лекция", "Room": "106", "Teacher": "Фёдорова Е.Е."}
                            ]
                        }
                    ]
                }]
            }]
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Не удалось обновить расписание с сервера. Используется тестовое расписание."),
                duration=5000
            )
            self.page.snack_bar.open = True
            self.page.update()

        self.save_schedules()
        await self.check_schedule_changes()
        await self.display_schedules()
        if not api_error:
            self.page.snack_bar = ft.SnackBar(ft.Text("Расписание обновлено!"))
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
        for old_sched, new_sched, group_id in zip(self.previous_schedules, self.schedules, self.group_ids):
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
                    changes.append(f"Группа {group_id}: Новое занятие: {new_lesson['Dis']} ({new_lesson['datePair']})")
                    continue

                change_details = []
                if old_lesson.get("Type", "") != new_lesson.get("Type", ""):
                    change_details.append(f"Тип занятия: {old_lesson['Type']} → {new_lesson['Type']}")
                if old_lesson.get("Room", "") != new_lesson.get("Room", ""):
                    change_details.append(f"Аудитория: {old_lesson['Room']} → {new_lesson['Room']}")
                if old_lesson.get("timeStart", "") != new_lesson.get("timeStart", "") or old_lesson.get("timeEnd", "") != new_lesson.get("timeEnd", ""):
                    change_details.append(f"Время: {old_lesson['timeStart']}-{old_lesson['timeEnd']} → {new_lesson['timeStart']}-{new_lesson['timeEnd']}")

                if change_details:
                    changes.append(f"Группа {group_id}: {new_lesson['Dis']} ({new_lesson['datePair']}): {', '.join(change_details)}")

        if changes:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Изменения в расписании: " + "; ".join(changes)),
                duration=10000
            )
            self.page.snack_bar.open = True
            self.page.update()

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
        return sorted(list(disciplines)) if disciplines else [
            "Философия", "Математика", "Программирование", "Физика", "История", "Литература", "Экономика"
        ]

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

        for group_id, schedule in zip(self.group_ids, self.schedules):
            if "error" in schedule:
                self.schedule_output.controls.append(
                    ft.Text(f"Ошибка для группы {group_id}: {schedule['error']}", color="red")
                )
                continue

            group_column = ft.Column()
            group_column.controls.append(
                ft.Text(f"Группа ID: {group_id}", size=16, weight="bold")
            )

            if not schedule.get("Month"):
                self.schedule_output.controls.append(
                    ft.Text(f"Нет данных для группы {group_id}", color="orange")
                )
                continue

            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    if not date_str:
                        print(f"Skipping empty date for group {group_id}")
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
                    ft.Text(f"Нет расписания для группы {group_id} в выбранном периоде", color="orange")
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
            on_change=lambda e: self.page.run_task(self.update_period, e.control.value)  # Исправлено
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