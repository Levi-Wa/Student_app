import flet as ft
import datetime
from views.schedule_view import ScheduleTab


class App:
    def __init__(self, page: ft.Page,):
        self.page = page
        self.selected_groups = []
        self.current_course = None
        self.selected_day = datetime.date.today()
        self.course_dropdown = None
        self.groups_container = None

        # Инициализация интерфейса
        self.page.on_view_pop = self.on_view_pop
        self.page.run_task(self.show_group_selector)

    async def show_group_selector(self):
        """Показываем выбор группы"""
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
            icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED
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
        """Обновляем список групп при выборе курса"""
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
        """Обновляем выбранные группы"""
        if e.control.value:
            self.selected_groups.append(e.control.data)
        else:
            self.selected_groups.remove(e.control.data)

    async def start_app_handler(self, e):
        """Обработчик кнопки продолжения"""
        if not self.selected_groups:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Выберите хотя бы одну группу!"),
                open=True
            )
            self.page.update()
            return

        await self.show_main_interface()

    async def show_main_interface(self):
        """Показываем основной интерфейс"""
        self.page.clean()
        schedule_tab = ScheduleTab(self.page)  # Передаем page в конструктор
        await schedule_tab.set_groups(self.selected_groups, self.selected_day)

        tabs = ft.Tabs(
            selected_index=1,
            expand=True,  # 👈 ВАЖНО: добавляем expand
            tabs=[
                ft.Tab(
                    text="Заметки",
                    content=ft.Container(
                        content=ft.Text("Вкладка заметок"),
                        expand=True
                    )
                ),
                ft.Tab(
                    text="Расписание",
                    content=ft.Container(  # 👈 обязательно оборачиваем в Container + expand
                        content=schedule_tab.build(),
                        expand=True
                    )
                ),
                ft.Tab(
                    text="Настройки",
                    content=ft.Container(
                        content=ft.Text("Вкладка настроек"),
                        expand=True
                    )
                ),
            ]
        )

        self.page.add(tabs)
        self.page.update()

    async def on_view_pop(self, view):
        """Обработчик возврата на предыдущий экран"""
        await self.show_group_selector()


async def main(page: ft.Page):
    """Точка входа в приложение"""
    page.title = "Студенческое приложение"
    page.window_width = 400
    page.window_height = 800
    app = App(page)


ft.app(target=main)