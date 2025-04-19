import flet as ft
import datetime
from views.schedule_view import ScheduleTab

class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_groups = []
        self.current_course = None
        self.selected_day = datetime.date.today()
        self.course_dropdown = None
        self.groups_container = None

    async def build(self):
        await self.show_group_selector()

    async def show_group_selector(self):
        self.page.clean()

        self.course_dropdown = ft.Dropdown(
            label="Выберите курс",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 5)],
            width=200,
            on_change=self.update_groups
        )

        self.groups_container = ft.Column()

        confirm_button = ft.ElevatedButton(
            "Продолжить",
            on_click=self.start_app_handler,
            icon=ft.Icons.ARROW_FORWARD  # исправлено на Icons с большой буквы
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
        self.current_course = self.course_dropdown.value
        groups = {
            "1": {"ИД-101": 26616, "ИД-102": 26617},
            "2": {"ИД-201": 26618},
            "3": {"ИД-301": 26619},
            "4": {"ИД-401": 26620}
        }.get(self.current_course, {})

        self.groups_container.controls = [
            ft.Checkbox(
                label=f"{name} (ID: {id_})",
                data=id_,
                on_change=self.update_selected_groups
            ) for name, id_ in groups.items()
        ]
        self.groups_container.update()

    def update_selected_groups(self, e):
        if e.control.value:
            self.selected_groups.append(e.control.data)
        else:
            self.selected_groups.remove(e.control.data)

    async def start_app_handler(self, e):
        if not self.selected_groups:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Выберите хотя бы одну группу!"),
                open=True
            )
            self.page.update()
            return

        await self.show_main_interface()

    async def show_main_interface(self):
        """Показывает основной интерфейс с вкладками"""
        self.page.clean()

        # Создаем вкладку расписания
        schedule_tab = ScheduleTab(self.page)  # Передаем page в конструктор

        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Заметки", content=ft.Text("Вкладка заметок")),
                ft.Tab(text="Расписание", content=schedule_tab),
                ft.Tab(text="Настройки", content=ft.Text("Вкладка настроек")),
            ]
        )

        self.page.add(tabs)
        self.page.update()

        # Устанавливаем группы после добавления на страницу
        await schedule_tab.set_groups(self.selected_groups, self.selected_day)


async def main(page: ft.Page):
    page.title = "Студенческое приложение"
    page.window_width = 400
    page.window_height = 800
    app = App(page)
    await app.build()

ft.app(target=main)
