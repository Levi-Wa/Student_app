import flet as ft
import datetime
import logging
from typing import List, Dict
from logic.logic_schedule.schedule_utils import BELL_SCHEDULE

class ScheduleUI:
    def __init__(self, page: ft.Page, manager):
        self.page = page
        self.manager = manager  # Теперь используем ScheduleManager вместо ScheduleLogic
        self.selected_period = "Сегодня"
        self.schedule_output = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
            auto_scroll=False,
            on_scroll=self.on_scroll
        )

    def on_scroll(self, e: ft.ScrollEvent):
        logging.info(f"Scroll event: delta={e.delta_y}, position={self.schedule_output.scroll_offset}")

    def create_lessons(self, main_schedule: List[Dict], day_date: datetime.date, highlight_current_pair: bool = False):
        lessons = ft.Column()
        current_time = datetime.datetime.now().time()

        for pair in main_schedule:
            time_start = pair.get("TimeStart", "") or pair.get("timeStart", "")
            time_end = pair.get("TimeEnd", "") or pair.get("timeEnd", "")
            discipline = pair.get("SubjName", "") or pair.get("Dis", "")
            lesson_type = pair.get("LoadKindSN", "") or pair.get("Type", "")
            room = pair.get("Aud", "") or pair.get("Room", "")
            teacher = pair.get("FIO", "") or pair.get("Teacher", "")

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
        try:
            date_str = day.get("datePair", "")
            if not date_str:
                return ft.Text("Дата не указана", color="red")

            day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            day_week = day.get("dayWeek", "")
            color = "blue" if force_blue else self.manager.utils.get_date_color(day_date, current_date, tomorrow_date)
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
        logging.info(f"Clearing schedule_output, current controls: {len(self.schedule_output.controls)}")
        self.schedule_output.controls.clear()

        if not self.manager.data.schedules:
            self.schedule_output.controls.append(ft.Text("Нет данных для отображения"))
            logging.info("No schedules to display")
            self.page.update()
            return

        today = datetime.datetime.now()
        today_date = today.date()
        tomorrow_date = today_date + datetime.timedelta(days=1)
        current_time = today.time()
        start_of_week = today_date - datetime.timedelta(days=today_date.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        start_of_month = today_date.replace(day=1)
        end_of_month = (today_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

        cards = []
        for schedule in self.manager.data.schedules:
            if "error" in schedule:
                logging.error(f"Schedule error: {schedule['error']}")
                self.schedule_output.controls.append(ft.Text(schedule["error"]))
                continue
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_pair = day.get("datePair", "")
                    try:
                        day_date = datetime.datetime.strptime(date_pair, "%d.%m.%Y").date()
                    except ValueError:
                        logging.error(f"Invalid date format: {date_pair}")
                        continue

                    if self.selected_period == "Сегодня" and day_date != today_date:
                        continue
                    elif self.selected_period == "Неделя" and (day_date < start_of_week or day_date > end_of_week):
                        continue
                    elif self.selected_period == "Месяц" and (day_date < start_of_month or day_date > end_of_month):
                        continue

                    logging.info(f"Processing day: {date_pair}")
                    if self.selected_period == "Сегодня":
                        for lesson in day.get("mainSchedule", []):
                            time_start = lesson.get("TimeStart", "") or lesson.get("timeStart", "")
                            try:
                                lesson_time = datetime.datetime.strptime(time_start, "%H:%M").time()
                            except ValueError:
                                logging.error(f"Invalid time format: {time_start}")
                                continue

                            is_current = (day_date == today_date and
                                          lesson_time <= current_time and
                                          lesson_time >= (datetime.datetime.combine(today_date,
                                                                                    current_time) - datetime.timedelta(
                                        minutes=90)).time())
                            is_past = day_date < today_date or (
                                        day_date == today_date and lesson_time < current_time and not is_current)
                            color = "green" if is_current else "red" if is_past else "blue"

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
                                        ft.Text(
                                            f"{lesson.get('SubjName', '') or lesson.get('Dis', '')} ({lesson.get('LoadKindSN', '') or lesson.get('Type', '')})",
                                            size=14),
                                        ft.Text(f"Ауд: {lesson.get('Aud', '') or lesson.get('Room', '')}", size=12),
                                        ft.Text(f"Преп: {lesson.get('FIO', '') or lesson.get('Teacher', '')}", size=12)
                                    ], spacing=5),
                                    padding=15,
                                    margin=10
                                ),
                                elevation=2,
                                shape=ft.RoundedRectangleBorder(radius=10),
                                color="white",
                                key=f"lesson_{date_pair}_{time_start}"
                            )
                            cards.append(lesson_card)
                            logging.info(f"Added lesson card: {lesson_card.key}")
                    else:
                        is_past = day_date < today_date
                        is_current = day_date == today_date
                        is_tomorrow = day_date == tomorrow_date
                        indicator_color = "grey" if is_past else "green" if is_current else "blue" if is_tomorrow else "grey200"

                        day_card = ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Text(
                                            f"{date_pair} ({day.get('dayWeek', '')})",
                                            weight="bold",
                                            size=16,
                                            color=ft.colors.BLACK87
                                        ),
                                        ft.Container(
                                            content=ft.CircleAvatar(bgcolor=indicator_color, radius=10),
                                            alignment=ft.alignment.center,
                                            margin=ft.margin.only(right=10)
                                        )
                                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                    ft.Divider(),
                                    ft.Column([
                                        ft.ListTile(
                                            leading=ft.CircleAvatar(
                                                content=ft.Text(
                                                    lesson.get("TimeStart", "")[:5] or lesson.get("timeStart", "")[:5]),
                                                bgcolor=ft.colors.BLUE_100,
                                                radius=25
                                            ),
                                            title=ft.Text(lesson.get("SubjName", "") or lesson.get("Dis", ""),
                                                          weight="bold"),
                                            subtitle=ft.Column([
                                                ft.Text(
                                                    f"Тип: {lesson.get('LoadKindSN', '') or lesson.get('Type', '')}"),
                                                ft.Text(f"Ауд: {lesson.get('Aud', '') or lesson.get('Room', '')}"),
                                                ft.Text(f"Преп: {lesson.get('FIO', '') or lesson.get('Teacher', '')}")
                                            ])
                                        )
                                        for lesson in day.get("mainSchedule", [])
                                    ])
                                ], spacing=5),
                                padding=15,
                                margin=ft.margin.all(10)
                            ),
                            elevation=4,
                            shape=ft.RoundedRectangleBorder(radius=12),
                            color=ft.colors.WHITE,
                            key=f"day_{date_pair}"
                        )
                        cards.append(day_card)
                        logging.info(f"Added day card: {day_card.key}")

        self.schedule_output.controls.extend(cards)
        logging.info(f"Total cards added: {len(cards)}")

        if not cards:
            self.schedule_output.controls.append(ft.Text("Нет занятий для выбранного периода"))
            logging.info("No cards added, showing placeholder")

        self.page.update()
        logging.info(f"Schedule output controls after update: {len(self.schedule_output.controls)}")

        if cards:
            target_key = None
            if self.selected_period == "Сегодня":
                for card in cards:
                    if hasattr(card, 'key') and card.key.startswith("lesson_"):
                        try:
                            lesson_time_str = card.key.split('_')[-1]
                            lesson_time = datetime.datetime.strptime(lesson_time_str, "%H:%M").time()
                            lesson_datetime = datetime.datetime.combine(today_date, lesson_time)
                            if lesson_datetime <= datetime.datetime.now() <= lesson_datetime + datetime.timedelta(
                                    minutes=90):
                                target_key = card.key
                                break
                            if target_key is None and lesson_datetime >= datetime.datetime.now() - datetime.timedelta(
                                    minutes=90):
                                target_key = card.key
                        except ValueError:
                            logging.error(f"Invalid lesson time format in key: {card.key}")
                            continue
                if target_key is None:
                    target_key = cards[0].key if cards else None
            else:
                target_key = f"day_{today_date.strftime('%d.%m.%Y')}"
                if target_key not in [card.key for card in cards if hasattr(card, 'key')]:
                    min_future_diff = float('inf')
                    for card in cards:
                        if hasattr(card, 'key') and card.key.startswith("day_"):
                            try:
                                card_date = datetime.datetime.strptime(card.key[4:], "%d.%m.%Y").date()
                                if card_date >= today_date:
                                    diff = (card_date - today_date).days
                                    if diff < min_future_diff:
                                        min_future_diff = diff
                                        target_key = card.key
                            except ValueError:
                                logging.error(f"Invalid date format in key: {card.key}")
                                continue
                    if target_key not in [card.key for card in cards if hasattr(card, 'key')]:
                        target_key = cards[0].key if cards else None

            if target_key:
                try:
                    self.schedule_output.scroll_to(key=target_key, duration=1000)
                    logging.info(f"Scrolled to key: {target_key}")
                except Exception as e:
                    logging.error(f"Scroll error: {e}")
            else:
                logging.info("Scroll skipped: No valid target found")

    def build(self):
        period_dropdown = ft.Dropdown(
            label="Период",
            options=[
                ft.dropdown.Option("Сегодня"),
                ft.dropdown.Option("Неделя"),
                ft.dropdown.Option("Месяц"),
                ft.dropdown.Option("Все")
            ],
            value=self.selected_period,
            on_change=lambda e: self.page.run_task(self.update_period, e.control.value),
            width=200
        )

        layout = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row([period_dropdown], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.only(top=40, bottom=10)
                ),
                self.schedule_output
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        return layout

    async def update_period(self, period: str):
        print(f"Updating period to: {period}")
        self.selected_period = period
        await self.display_schedules()