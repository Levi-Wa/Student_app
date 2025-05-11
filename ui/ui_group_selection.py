import flet as ft
import logging
from logic.logic_selector_group.group_selection_manager import GroupSelectionManager

class GroupSelectionUI:
    def __init__(self, page: ft.Page, manager, schedule_ui, on_selection_complete):
        self.page = page
        self.manager = manager
        self.schedule_ui = schedule_ui
        self.on_selection_complete = on_selection_complete
        self.course_dropdown = ft.Dropdown(
            label="Курс",
            options=[ft.dropdown.Option(course) for course in self.manager.data.get_courses()],
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
        if self.manager.data.get_courses():
            self.update_groups(None)
        logging.info("GroupSelectionUI initialized")

    def update_groups(self, e):
        """Обновляем выпадающий список групп на основе выбранного курса"""
        selected_course = self.course_dropdown.value or self.manager.data.get_courses()[0]
        groups = self.manager.data.get_groups_for_course(selected_course)
        self.group_dropdown.options = [ft.dropdown.Option(group["name"]) for group in groups]
        self.group_dropdown.value = groups[0]["name"] if groups else None
        self.page.update()
        logging.info(f"Updated groups for course {selected_course}: {[g['name'] for g in groups]}")

    async def on_group_select(self, e):
        """Обработчик выбора группы"""
        def notify_callback(message):
            self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
            self.page.snack_bar.open = True
            self.page.update()

        await self.manager.select_group(
            course=self.course_dropdown.value,
            group_name=self.group_dropdown.value,
            display_callback=self.schedule_ui.display_schedules,
            notify_callback=notify_callback,
            on_selection_complete=self.on_selection_complete
        )

    def build(self):
        """Создаём интерфейс выбора группы"""
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