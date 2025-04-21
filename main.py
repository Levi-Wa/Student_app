import flet as ft
import datetime
import json
import os
from views.schedule_view import ScheduleTab
from views.notes_view import NotesView
from views.settings_view import SettingsView

class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_groups = []
        self.current_course = None
        self.selected_day = datetime.date.today()
        self.course_dropdown = None
        self.groups_container = None
        self.settings_file = "settings.json"
        self.settings = {
            "theme": "light",
            "schedule_notifications": True,
            "expiry_notification_days": 3
        }
        self.schedule_tab = None  # Добавляем атрибут для хранения schedule_tab

        self.load_settings()
        self.apply_theme()

        self.page.on_view_pop = self.on_view_pop
        if self.selected_groups:
            self.page.run_task(self.show_main_interface)
        else:
            self.page.run_task(self.show_group_selector)

    def load_settings(self):
        """Загрузка настроек из файла"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)
                self.selected_groups = loaded_settings.get("selected_groups", [])
                self.current_course = loaded_settings.get("current_course", None)
                self.settings.update(loaded_settings.get("settings", {}))

    def save_settings(self):
        """Сохранение настроек в файл"""
        settings = {
            "selected_groups": self.selected_groups,
            "current_course": self.current_course,
            "settings": self.settings
        }
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def apply_theme(self):
        """Применение темы"""
        theme_mode = self.settings.get("theme", "light")
        self.page.theme_mode = ft.ThemeMode.LIGHT if theme_mode == "light" else ft.ThemeMode.DARK
        self.page.update()

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

        self.save_settings()
        await self.show_main_interface()

    async def show_main_interface(self):
        """Показываем основной интерфейс"""
        self.page.clean()

        self.schedule_tab = ScheduleTab(self.page, self)
        await self.schedule_tab.set_groups(self.selected_groups)

        notes_view = NotesView(self.page, self.schedule_tab, self)
        settings_view = SettingsView(self.page, self)

        tabs = ft.Tabs(
            selected_index=1,
            expand=True,
            tabs=[
                ft.Tab(
                    text="Заметки",
                    icon=ft.Icons.NOTE,
                    content=ft.Container(
                        content=notes_view.ui_content,
                        expand=True,
                        padding=10
                    )
                ),
                ft.Tab(
                    text="Расписание",
                    icon=ft.Icons.BOOK,
                    content=ft.Container(
                        content=self.schedule_tab.build(),
                        expand=True,
                        padding=10
                    )
                ),
                ft.Tab(
                    text="Настройки",
                    icon=ft.Icons.SETTINGS,
                    content=ft.Container(
                        content=settings_view.build(),
                        expand=True,
                        padding=10
                    )
                ),
            ]
        )

        self.page.app_bar = ft.AppBar(
            title=ft.Text("Студенческое приложение"),
            bgcolor=ft.Colors.ON_SURFACE_VARIANT,
            center_title=True
        )

        self.page.add(tabs)
        self.page.update()

        await self.schedule_tab.load_schedules()

    async def on_view_pop(self, view):
        """Обработчик возврата на предыдущий экран"""
        if self.selected_groups:
            await self.show_main_interface()
        else:
            await self.show_group_selector()


async def main(page: ft.Page):
    """Точка входа в приложение"""
    page.title = "Студенческое приложение"
    page.window_width = 400
    page.window_height = 800
    app = App(page)


ft.app(target=main)