import flet as ft
import httpx

# ✍️ Тут можно добавить свои группы и их ID
GROUPS_BY_COURSE = {
    "1": {
        "ИД-101": 26616,
        "ИД-102": 26617
    },
    "2": {
        "ИД-201": 26618
    },
    "3": {
        "ИД-301": 26619
    },
    "4": {
        "ИД-401": 26620
    }
}

class ScheduleTab(ft.Column):
    def __init__(self):
        super().__init__()

        self.course_dropdown = ft.Dropdown(
            label="Выберите курс",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 5)],
            on_change=self.on_course_change
        )

        self.group_checkboxes_container = ft.Column()

        self.schedule_output = ft.Text("Выберите группу, чтобы отобразить расписание")

        self.controls = [
            ft.Text("📅 Расписание", size=24, weight="bold"),
            self.course_dropdown,
            self.group_checkboxes_container,
            self.schedule_output
        ]

    def on_course_change(self, e):
        self.group_checkboxes_container.controls.clear()

        course = self.course_dropdown.value
        groups = GROUPS_BY_COURSE.get(course, {})

        for group_name, group_id in groups.items():
            checkbox = ft.Checkbox(label=group_name, on_change=self.on_group_checkbox)
            checkbox.data = group_id  # сохраняем ID группы в поле data
            self.group_checkboxes_container.controls.append(checkbox)

        self.schedule_output.value = "Выберите группу, чтобы отобразить расписание"
        self.group_checkboxes_container.update()
        self.update()

    def on_group_checkbox(self, e):
        selected_ids = [
            cb.data
            for cb in self.group_checkboxes_container.controls
            if cb.value
        ]

        if not selected_ids:
            self.schedule_output.value = "Выберите хотя бы одну группу"
            self.update()
            return

        self.schedule_output.value = "Загрузка расписания..."
        self.update()
        self.load_schedules(selected_ids)

    def load_schedules(self, group_ids):
        all_schedules = ""

        for group_id in group_ids:
            try:
                url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
                response = httpx.get(url, timeout=10)
                data = response.json()

                all_schedules += f"\n📘 Группа ID: {group_id}\n"
                for day in data.get("data", []):
                    all_schedules += f"\n📅 {day['day']}\n"
                    for lesson in day["schedule"]:
                        time = lesson.get("time", "")
                        subject = lesson.get("subject", "")
                        all_schedules += f"  ⏰ {time} — {subject}\n"

            except Exception as ex:
                all_schedules += f"\n⚠️ Ошибка загрузки для группы {group_id}: {ex}\n"

        self.schedule_output.value = all_schedules or "Нет данных"
        self.update()
