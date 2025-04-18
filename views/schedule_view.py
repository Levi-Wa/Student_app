# views/schedule_view.py

import flet as ft
import requests
from datetime import datetime, time

GROUPS_BY_COURSE = {
    1: {"Ид-101": 26616, "Ид-102": 26617},
    2: {"Ид-201": 26618},
    3: {"Ид-301": 26620},
    4: {"Ид-401": 26622}
}

# Пример расписания пар
LESSON_TIMES = [
    (time(8, 30), time(10, 0)),
    (time(10, 10), time(11, 40)),
    (time(12, 10), time(13, 40)),
    (time(13, 50), time(15, 20)),
    (time(15, 30), time(17, 0)),
    (time(17, 10), time(18, 40)),
]


class ScheduleTab():
    def __init__(self):
        self.view = ft.Column([ft.Text("Расписание")])   

    def build(self):
        self.selected_course = 1
        self.selected_group_id = None

        self.course_dropdown = ft.Dropdown(
            label="Выбери курс",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 5)],
            value="1",
            on_change=self.on_course_change
        )

        self.group_radio = ft.RadioGroup(content=ft.Column(), on_change=self.on_group_selected)
        self.schedule_display = ft.Column(scroll=ft.ScrollMode.ALWAYS)

        self.update_group_radios()

        return ft.Column([
            self.course_dropdown,
            ft.Text("Выбери группу:"),
            self.group_radio,
            ft.Text("Расписание на сегодня:"),
            self.schedule_display
        ])

    def on_course_change(self, e):
        self.selected_course = int(e.control.value)
        self.update_group_radios()

    def update_group_radios(self):
        course_groups = GROUPS_BY_COURSE.get(self.selected_course, {})
        radios = [ft.Radio(value=str(group_id), label=name) for name, group_id in course_groups.items()]
        self.group_radio.content.controls = radios
        self.group_radio.value = None
        self.schedule_display.controls.clear()
        self.update()

    def on_group_selected(self, e):
        group_id = int(e.control.value)
        self.selected_group_id = group_id
        self.fetch_and_display_schedule(group_id)

    def fetch_and_display_schedule(self, group_id):
        url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
        try:
            response = requests.get(url)
            data = response.json()

            today_weekday = datetime.now().isoweekday()  # 1 - Пн, 7 - Вс

            self.schedule_display.controls.clear()
            for item in data.get("list", []):
                day = item.get("day", "")
                pair_time = item.get("time", "")  # Пример: "08:30-10:00"
                disc = item.get("disc", "")
                aud = item.get("aud", "")
                prep = item.get("prep", "")
                weekday_num = self.parse_day_to_num(day)

                if weekday_num != today_weekday:
                    continue  # Показываем только пары на сегодня

                # Определим статус пары (прошла, текущая, будущая)
                status = self.get_lesson_status(pair_time)

                color = {
                    "past": ft.colors.GREY_300,
                    "current": ft.colors.GREEN_100,
                    "future": ft.colors.BLUE_100
                }.get(status, ft.colors.WHITE)

                card = ft.Container(
                    content=ft.Column([
                        ft.Text(f"{pair_time} - {disc}", size=16, weight="bold"),
                        ft.Text(f"Аудитория: {aud}"),
                        ft.Text(f"Преподаватель: {prep}"),
                    ]),
                    padding=10,
                    margin=5,
                    border_radius=12,
                    bgcolor=color,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=4,
                        color=ft.colors.GREY_400,
                        offset=ft.Offset(2, 2)
                    )
                )
                self.schedule_display.controls.append(card)
        except Exception as e:
            self.schedule_display.controls.clear()
            self.schedule_display.controls.append(ft.Text(f"Ошибка загрузки: {e}"))

        self.update()

    def parse_day_to_num(self, day_str):
        weekdays = {
            "Понедельник": 1,
            "Вторник": 2,
            "Среда": 3,
            "Четверг": 4,
            "Пятница": 5,
            "Суббота": 6,
            "Воскресенье": 7
        }
        return weekdays.get(day_str.strip(), 0)

    def get_lesson_status(self, time_range):
        try:
            now = datetime.now().time()
            start_str, end_str = time_range.split("-")
            start_time = datetime.strptime(start_str.strip(), "%H:%M").time()
            end_time = datetime.strptime(end_str.strip(), "%H:%M").time()

            if now < start_time:
                return "future"
            elif start_time <= now <= end_time:
                return "current"
            else:
                return "past"
        except:
            return "future"
