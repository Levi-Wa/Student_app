import flet as ft
import requests

# Группы с ID по курсам
CUSTOM_GROUPS = {
    1: {"ИД-101": 26616, "ИД-102": 26617},
    2: {"ИД-201": 26618, "ИД-202": 26619},
    3: {"ИД-301": 26620, "ИД-302": 26621},
    4: {"ИД-401": 26622, "ИД-402": 26623},
}

class ScheduleTab(ft.Column):
    def __init__(self):
        super().__init__()
        self.course_selector = ft.Dropdown(
            label="Выберите курс",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 5)],
            on_change=self.on_course_change,
        )

        self.group_radio = ft.RadioGroup(content=ft.Column([]), on_change=self.on_group_change)
        self.schedule_display = ft.Column()

        self.controls = [
            ft.Text("Расписание", style="headlineMedium"),
            self.course_selector,
            self.group_radio,
            ft.Divider(),
            self.schedule_display,
        ]

    def on_course_change(self, e):
        selected_course = int(self.course_selector.value)
        self.load_groups_for_course(selected_course)

    def load_groups_for_course(self, course):
        groups = CUSTOM_GROUPS.get(course, {})
        radio_buttons = [
            ft.Radio(value=str(group_id), label=group_name)
            for group_name, group_id in groups.items()
        ]
        self.group_radio.content.controls = radio_buttons
        self.group_radio.value = None  # сброс выбора
        self.schedule_display.controls.clear()
        self.update()

    def on_group_change(self, e):
        group_id = self.group_radio.value
        if group_id:
            self.load_schedule(int(group_id))

    def load_schedule(self, group_id):
        self.schedule_display.controls.clear()
        try:
            url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
            response = requests.get(url)
            data = response.json()

            for item in data.get("data", []):
                self.schedule_display.controls.append(
                    ft.Text(f"{item.get('subject')} - {item.get('aud')} ({item.get('starttime')})")
                )

        except Exception as err:
            self.schedule_display.controls.append(ft.Text(f"Ошибка загрузки: {err}"))
        self.update()
