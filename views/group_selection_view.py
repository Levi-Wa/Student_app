import flet as ft
import json
import logging

class GroupSelectionView:
    def __init__(self, page: ft.Page, schedule_tab, on_selection_complete, app):
        self.page = page
        self.schedule_tab = schedule_tab
        self.on_selection_complete = on_selection_complete
        self.app = app
        self.groups_data = {
            "1 курс": [
                {"name": "Группа 101", "id": "26616"},
                {"name": "Группа 102", "id": "26617"}
            ],
            "2 курс": [
                {"name": "Группа 201", "id": "26618"},
                {"name": "Группа 202", "id": "26619"}
            ]
        }
        self.course_dropdown = ft.Dropdown(
            label="Курс",
            options=[ft.dropdown.Option(course) for course in self.groups_data.keys()],
            on_change=self.update_groups,
            width=300
        )
        self.group_dropdown = ft.Dropdown(
            label="Группа",
            width=300
        )
        self.select_button = ft.ElevatedButton(
            text="Выбрать",
            on_click=self.on_group_select
        )
        # Инициализируем group_dropdown для первого курса, если он есть
        if self.groups_data:
            self.update_groups(None)

    def update_groups(self, e):
        """Обновляем выпадающий список групп на основе выбранного курса"""
        selected_course = self.course_dropdown.value or list(self.groups_data.keys())[0]
        groups = self.groups_data.get(selected_course, [])
        self.group_dropdown.options = [ft.dropdown.Option(group["name"]) for group in groups]
        self.group_dropdown.value = groups[0]["name"] if groups else None
        self.page.update()
        logging.info(f"Updated groups for course {selected_course}: {[g['name'] for g in groups]}")

    def build(self):
        return ft.Column(
            [
                ft.Text("Выберите курс и группу", size=20, weight="bold"),
                self.course_dropdown,
                self.group_dropdown,
                self.select_button
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    async def on_group_select(self, e):
        import logging
        selected_course = self.course_dropdown.value
        selected_group = self.group_dropdown.value
        if not selected_course or not selected_group:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Выберите курс и группу!"),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        group_id = None
        for group in self.groups_data[selected_course]:
            if group["name"] == selected_group:
                group_id = group["id"]
                break

        if group_id:
            self.schedule_tab.group_id = group_id
            self.app.settings["group_id"] = group_id
            self.app.save_settings()
            logging.info(f"Saved group_id: {group_id}")
            await self.schedule_tab.load_schedule_for_group(group_id)
            if all("error" in sched for sched in self.schedule_tab.schedules):
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Ошибка загрузки расписания. Попробуйте другую группу или проверьте подключение."),
                    duration=5000
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            logging.info("Calling on_selection_complete")
            await self.on_selection_complete()