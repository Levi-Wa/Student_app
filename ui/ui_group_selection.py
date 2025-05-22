import flet as ft
import logging
from logic.logic_selector_group.group_selection_manager import GroupSelectionManager

class GroupSelectionUI:
    def __init__(self, page: ft.Page, manager, schedule_ui, on_selection_complete):
        self.page = page
        self.manager = manager
        self.schedule_ui = schedule_ui
        self.on_selection_complete = on_selection_complete
        self.selection_output = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )
        self.course_dropdown = None
        self.group_dropdown = None
        self.build_dropdowns()

    def build_dropdowns(self):
        """Создает выпадающие списки для выбора курса и группы"""
        courses = self.manager.get_courses()
        self.course_dropdown = ft.Dropdown(
            label="Курс",
            options=[ft.dropdown.Option(course) for course in courses],
            on_change=self.on_course_change,
            width=300
        )
        self.group_dropdown = ft.Dropdown(
            label="Группа",
            options=[],
            on_change=self.on_group_change,
            width=300
        )

    def on_course_change(self, e):
        """Обработчик изменения курса"""
        course = e.control.value
        if course:
            groups = self.manager.data.get_groups_for_course(course)
            self.group_dropdown.options = [ft.dropdown.Option(group["name"]) for group in groups]
            self.group_dropdown.value = None
            self.page.update()

    def on_group_change(self, e):
        """Обработчик изменения группы"""
        if e.control.value:
            self.select_group(e.control.value)

    def select_group(self, group_name: str):
        """Выбор группы"""
        course = self.course_dropdown.value
        if course and group_name:
            self.page.run_task(
                self.manager.select_group,
                course,
                group_name,
                lambda: None,  # display_callback
                lambda msg: self.show_notification(msg),  # notify_callback
                self.on_selection_complete
            )

    def show_notification(self, message: str):
        """Показывает уведомление"""
        self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
        self.page.snack_bar.open = True
        self.page.update()

    def update_course_dropdown(self):
        """Обновляет список курсов в выпадающем списке и сбрасывает выбор группы"""
        courses = self.manager.get_courses()
        self.course_dropdown.options = [ft.dropdown.Option(course) for course in courses]
        self.course_dropdown.value = None
        self.group_dropdown.options = []
        self.group_dropdown.value = None
        self.page.update()

    def build(self):
        """Создает интерфейс выбора группы"""
        self.selection_output.controls = [
            ft.Text(
                "Выберите вашу группу",
                weight=ft.FontWeight.BOLD,
                size=20,
                color=ft.Colors.ON_SURFACE
            ),
            ft.Container(
                content=ft.Column([
                    self.course_dropdown,
                    self.group_dropdown
                ], spacing=10),
                padding=20
            )
        ]
        return self.selection_output