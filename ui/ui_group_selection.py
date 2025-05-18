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
            width=None,  # Адаптивная ширина
            expand=True,  # Растягиваем на всю ширину
            value=None,
            text_size=16
        )
        self.group_dropdown = ft.Dropdown(
            label="Группа",
            options=[],  # Изначально пустой список
            on_change=lambda e: self.page.update(),  # Обновляем страницу при изменении
            width=None,  # Адаптивная ширина
            expand=True,  # Растягиваем на всю ширину
            value=None,
            text_size=16
        )
        self.select_button = ft.ElevatedButton(
            text="Выбрать",
            on_click=self.on_group_select,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            ),
            width=200,
            height=50
        )
        logging.info("GroupSelectionUI initialized")

    async def update_groups(self, e):
        """Обновляет список групп при выборе курса"""
        if self.course_dropdown.value:
            groups = self.manager.data.get_groups_for_course(self.course_dropdown.value)
            self.group_dropdown.options = [ft.dropdown.Option(group["name"]) for group in groups]
            self.group_dropdown.value = None
            self.page.update()
            logging.info(f"Updated groups for course {self.course_dropdown.value}: {len(groups)} groups found")

    async def on_group_select(self, e):
        """Обработчик выбора группы"""
        async def notify_callback(message):
            self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
            self.page.snack_bar.open = True
            self.page.update()

        if not self.course_dropdown.value or not self.group_dropdown.value:
            await notify_callback("Выберите курс и группу!")
            return

        logging.info(f"Selecting group: course={self.course_dropdown.value}, group_name={self.group_dropdown.value}")
        await self.manager.select_group(
            course=self.course_dropdown.value,
            group_name=self.group_dropdown.value,
            display_callback=self.schedule_ui.display_schedules,
            notify_callback=notify_callback,
            on_selection_complete=self.on_selection_complete
        )

    def build(self):
        """Создаём интерфейс выбора группы"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Выберите курс и группу", size=24, weight="bold", text_align=ft.TextAlign.CENTER),
                    ft.Container(height=20),  # Отступ
                    ft.Container(
                        content=self.course_dropdown,
                        padding=ft.padding.symmetric(horizontal=20)
                    ),
                    ft.Container(height=20),  # Отступ
                    ft.Container(
                        content=self.group_dropdown,
                        padding=ft.padding.symmetric(horizontal=20)
                    ),
                    ft.Container(height=40),  # Отступ
                    ft.Container(
                        content=self.select_button,
                        alignment=ft.alignment.center
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
            ),
            expand=True,
            padding=20
        )