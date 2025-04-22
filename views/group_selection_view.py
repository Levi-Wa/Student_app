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
                {"name": "БДД-101", "id": "26627"},
                {"name": "БДД-102", "id": "26640"},
                {"name": "ИД-101", "id": "26616"},
                {"name": "ИСПД-101", "id": "26628"},
                {"name": "ИСПД-102", "id": "26629"},
                {"name": "ИСПД-103", "id": "26639"},
                {"name": "МД-101", "id": "26615"},
                {"name": "РД-101", "id": "26630"},
                {"name": "РД-102", "id": "26806"},
                {"name": "РСОД-101", "id": "26617"},
                {"name": "УПД-101", "id": "26618"},
                {"name": "ЭБД-101", "id": "26626"},
                {"name": "ЭБД-102", "id": "26807"},
                {"name": "ЭД-101", "id": "26619"},
                {"name": "ЮД-101", "id": "26785"},
            ],
            "2 курс": [
                {"name": "БДД-201", "id": "26641"},
                {"name": "БДД-202", "id": "26642"},
                {"name": "ИД-201ис", "id": "26582"},
                {"name": "ИСПД-201", "id": "26643"},
                {"name": "ИСПД-202", "id": "26644"},
                {"name": "ИСПД-203", "id": "26646"},
                {"name": "РД-201", "id": "26658"},
                {"name": "РСОД-201", "id": "26583"},
                {"name": "УПД-201", "id": "26585"},
                {"name": "ЭБД-201", "id": "26646"},
                {"name": "ЭД-201бу", "id": "26587"},
            ],
            "3 курс": [
                {"name": "БДД-301", "id": "26648"},
                {"name": "ИД-301кис", "id": "26584"},
                {"name": "ИСПД-301", "id": "26653"},
                {"name": "МД-301мо", "id": "26586"},
                {"name": "РСОД-301", "id": "26588"},
                {"name": "УПД-301", "id": "26593"},
                {"name": "ЭБД-301", "id": "26654"},
                {"name": "ЭД-301эпо", "id": "26595"},
            ],
            "4 курс": [
                {"name": "ИД-401кис", "id": "26589"},
                {"name": "РСОД-401", "id": "26890"},
                {"name": "УПД-401", "id": "26591"},
                {"name": "ЭД-401эпо", "id": "26592"},
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