import flet as ft
import datetime
from views.schedule_view import ScheduleTab  # Импортируем ваш ScheduleTab

class App:
    def __init__(self):
        self.selected_groups = []
        self.current_course = None
        self.selected_day = datetime.date.today()
        self.course_dropdown = None
        self.groups_container = None

    async def build(self):
        # Инициализация интерфейса с выбором группы
        await self.show_group_selector()

    async def show_group_selector(self):
        # Очищаем текущую страницу перед отрисовкой нового интерфейса
        self.page.clean()

        # Выпадающий список для выбора курса
        self.course_dropdown = ft.Dropdown(
            label="Выберите курс",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 5)],
            width=200,
            on_change=self.update_groups
        )

        # Контейнер для групп
        self.groups_container = ft.Column()

        # Кнопка подтверждения
        confirm_button = ft.ElevatedButton(
            "Продолжить",
            on_click=self.start_app_handler,
            icon=ft.Icons.ARROW_FORWARD
        )

        # Добавляем элементы на страницу
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
        # Обновление списка групп в зависимости от выбранного курса
        self.current_course = self.course_dropdown.value
        groups = {
            "1": {"ИД-101": 26616, "ИД-102": 26617},
            "2": {"ИД-201": 26618},
            "3": {"ИД-301": 26619},
            "4": {"ИД-401": 26620}
        }.get(self.current_course, {})

        # Обновляем список доступных групп
        self.groups_container.controls = [
            ft.Checkbox(
                label=f"{name} (ID: {id_})",
                data=id_,
                on_change=self.update_selected_groups
            ) for name, id_ in groups.items()
        ]
        self.groups_container.update()

    def update_selected_groups(self, e):
        # Добавление или удаление групп в выбранные
        if e.control.value:
            self.selected_groups.append(e.control.data)
        else:
            self.selected_groups.remove(e.control.data)

    async def start_app_handler(self, e):
        # Проверка, чтобы была выбрана хотя бы одна группа
        if not self.selected_groups:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Выберите хотя бы одну группу!"),
                open=True
            )
            self.page.update()
            return

        # Переход к основному интерфейсу
        await self.show_main_interface()

    async def show_main_interface(self):
        self.page.clean()
        schedule_tab = ScheduleTab()  # Создаем без передачи page
        await schedule_tab.set_groups(self.selected_groups, self.selected_day)

        tabs = ft.Tabs(
            selected_index=1,
            tabs=[
                ft.Tab(text="Заметки", content=ft.Text("Вкладка заметок")),
                ft.Tab(text="Расписание", content=schedule_tab),
                ft.Tab(text="Настройки", content=ft.Text("Вкладка настроек")),
            ]
        )
        self.page.add(tabs)


# Основная функция для запуска приложения
async def main(page: ft.Page):
    print(ft.__version__)
    page.title = "Студенческое приложение"
    page.window_width = 400
    page.window_height = 800
    app = App(page)
    await app.build()

# Запуск приложения
ft.app(target=main)
