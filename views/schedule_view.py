import flet as ft
import requests

class ScheduleTab(ft.Control):
    def __init__(self, page):
        super().__init__()
        self.page = page  # Сохраняем ссылку на страницу
        self.selected_course = None
        self.selected_group_id = None
        self.schedule_output = ft.Column()

    def build(self):
        # Радиокнопки для выбора курса
        self.course_radio = ft.RadioGroup(
            content=ft.Column([
                ft.Text("Выберите курс:", size=20, weight="bold"),
                *[ft.Radio(value=course, label=course) for course in ["1 курс", "2 курс", "3 курс", "4 курс"]],
            ]),
            on_change=self.on_course_change
        )

        # Радиокнопки для выбора группы
        self.group_radio = ft.RadioGroup(
            content=ft.Column([]),
            on_change=self.on_group_change
        )

        # Контейнер для вывода расписания
        return ft.Column([
            self.course_radio,
            self.group_radio,
            ft.Divider(),
            self.schedule_output
        ])

    def on_course_change(self, e):
        self.selected_course = e.control.value
        self.selected_group_id = None
        self.group_radio.value = None
        self.schedule_output.controls.clear()

        # Пример групп по курсу
        groups = {
            "1 курс": [("Ид-101", 26616), ("Ид-102", 26617)],
            "2 курс": [("Ид-201", 26618), ("Ид-202", 26619)],
            "3 курс": [("Ид-301", 26620), ("Ид-302", 26621)],
            "4 курс": [("Ид-401", 26622), ("Ид-402", 26623)],
        }

        selected_groups = groups.get(self.selected_course, [])
        self.group_radio.content = ft.Column([
            ft.Text("Выберите группу:", size=18, weight="bold"),
            *[ft.Radio(value=str(group_id), label=group_name) for group_name, group_id in selected_groups]
        ])
        self.update()

    def on_group_change(self, e):
        self.selected_group_id = e.control.value
        self.load_schedule(int(self.selected_group_id))

    def load_schedule(self, group_id):
        self.schedule_output.controls.clear()
        self.schedule_output.controls.append(ft.Text("Загрузка расписания..."))
        self.update()

        try:
            # Запрос данных расписания
            url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
            response = requests.get(url)
            data = response.json()

            self.schedule_output.controls.clear()
            if not data or "data" not in data:
                self.schedule_output.controls.append(ft.Text("Нет данных о расписании."))
            else:
                for day in data["data"]:
                    day_title = ft.Text(day["day_string"], size=16, weight="bold")
                    lessons = []
                    for lesson in day.get("lessons", []):
                        lesson_info = f"{lesson['time_start']} - {lesson['time_end']} | {lesson['subject']} ({lesson['type']})"
                        lessons.append(ft.Text(lesson_info))

                    self.schedule_output.controls.append(ft.Column([day_title, *lessons]))

        except Exception as ex:
            self.schedule_output.controls.clear()
            self.schedule_output.controls.append(ft.Text(f"Ошибка загрузки: {ex}"))

        self.update()

    # Переопределение метода _get_control_name для класса
    def _get_control_name(self):
        return "ScheduleTab"

