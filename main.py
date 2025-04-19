import flet as ft
from views.schedule_view import ScheduleTab

class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_groups = []
        self.current_course = None
        self.show_group_selector()

    def show_group_selector(self):
        """Показывает экран выбора группы"""
        self.page.controls.clear()
        
        # Элементы выбора курса
        self.course_dropdown = ft.Dropdown(
            label="Выберите курс",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 5)],
            width=200,
            on_change=self.update_groups
        )
        
        # Контейнер для чекбоксов групп
        self.groups_container = ft.Column()
        
        confirm_button = ft.ElevatedButton(
            "Продолжить",
            on_click=self.start_app_handler,
            icon=ft.icons.ARROW_FORWARD_IOS
        )

        self.page.add(
            ft.Column([
                ft.Text("Выбор группы", size=24),
                self.course_dropdown,
                ft.Text("Доступные группы:", weight="bold"),
                self.groups_container,
                confirm_button
            ], alignment=ft.MainAxisAlignment.CENTER)
        )
        self.page.update()

    def update_groups(self, e):
        """Обновляет список групп для выбранного курса"""
        self.current_course = self.course_dropdown.value
        groups = {
            "1": {"ИД-101": 26616, "ИД-102": 26617},
            "2": {"ИД-201": 26618},
            "3": {"ИД-301": 26619},
            "4": {"ИД-401": 26620}
        }.get(self.current_course, {})
        
        self.groups_container.controls = [
            ft.Checkbox(
                label=f"{name}",
                data=id_,
                on_change=self.update_selected_groups
            ) for name, id_ in groups.items()
        ]
        self.groups_container.update()

    def update_selected_groups(self, e):
        """Обновляет список выбранных групп"""
        if e.control.value:
            self.selected_groups.append(e.control.data)
        else:
            self.selected_groups.remove(e.control.data)

    async def start_app_handler(self, e):
        """Обработчик кнопки запуска"""
        if not self.selected_groups:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Выберите хотя бы одну группу!"),
                open=True
            )
            await self.page.update_async()
            return
            
        self.page.controls.clear()
        self.page.add(self.create_main_tabs())
        await self.page.update_async()

    def create_main_tabs(self):
        """Создает вкладки основного приложения"""
        return ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Расписание",
                    content=ScheduleTab(self.selected_groups)
                ),
                ft.Tab(
                    text="Заметки",
                    content=ft.Text("Вкладка заметок")
                ),
                ft.Tab(
                    text="Настройки",
                    content=ft.Text("Вкладка настроек")
                )
            ]
        )

def main(page: ft.Page):
    page.title = "Студенческое приложение"
    page.window_width = 400
    page.window_height = 800
    App(page)

ft.app(target=main)