import flet as ft
import requests
import json
import os

class GroupSelectionView:
    def __init__(self, page: ft.Page, schedule_tab, on_selection_complete):
        self.page = page
        self.schedule_tab = schedule_tab
        self.on_selection_complete = on_selection_complete
        self.course_dropdown = None
        self.group_dropdown = None
        self.groups_data = self.load_groups_data()

    def load_groups_data(self):
        """Возвращаем данные о курсах и группах"""
        # Это статические данные, можно заменить на загрузку из API, если есть такая возможность
        return {
            "1 курс": [
                {"name": "Группа 101", "id": "26616"},
                {"name": "Группа 102", "id": "26617"}
            ],
            "2 курс": [
                {"name": "Группа 201", "id": "26618"},
                {"name": "Группа 202", "id": "26619"}
            ],
            "3 курс": [
                {"name": "Группа 301", "id": "26620"},
                {"name": "Группа 302", "id": "26621"}
            ],
            "4 курс": [
                {"name": "Группа 401", "id": "26622"},
                {"name": "Группа 402", "id": "26623"}
            ]
        }

    async def on_course_change(self, e):
        """Обновляем список групп при выборе курса"""
        selected_course = e.control.value
        groups = self.groups_data.get(selected_course, [])
        self.group_dropdown.options = [ft.dropdown.Option(group["name"]) for group in groups]
        self.group_dropdown.value = None
        self.page.update()

    async def on_group_select(self, e):
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
            await self.schedule_tab.load_schedule_for_group(group_id)
            if all("error" in sched for sched in self.schedule_tab.schedules):
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Ошибка загрузки расписания. Попробуйте другую группу или проверьте подключение."),
                    duration=5000
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            self.on_selection_complete()

    def build(self):
        """Создаём интерфейс выбора курса и группы"""
        self.course_dropdown = ft.Dropdown(
            label="Курс",
            options=[ft.dropdown.Option(course) for course in self.groups_data.keys()],
            width=300,
            on_change=self.on_course_change
        )

        self.group_dropdown = ft.Dropdown(
            label="Группа",
            options=[],
            width=300
        )

        select_button = ft.ElevatedButton(
            "Выбрать",
            on_click=self.on_group_select,
            icon=ft.Icons.CHECK
        )

        return ft.Column([
            ft.Text("Выберите курс и группу", size=20, weight="bold"),
            self.course_dropdown,
            self.group_dropdown,
            select_button
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)