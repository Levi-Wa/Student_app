import flet as ft
import json
import os

class SettingsView:
    def __init__(self, page: ft.Page, app):
        self.page = page
        self.app = app
        self.course_dropdown = None
        self.groups_container = ft.Column()
        self.theme_dropdown = None
        self.schedule_notifications_checkbox = None
        self.expiry_notification_days_dropdown = None
        self.url_input = None  # Поле для ввода URL

    def build(self):
        """Создаём интерфейс настроек"""
        self.course_dropdown = ft.Dropdown(
            label="Выберите курс",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 5)],
            width=200,
            value=self.app.current_course,
            on_change=self.update_groups
        )

        groups = {
            "1": {"ИД-101": 26616, "ИД-102": 26617},
            "2": {"ИД-201": 26618},
            "3": {"ИД-301": 26619},
            "4": {"ИД-401": 26620}
        }.get(self.app.current_course, {})
        self.groups_container.controls = [
            ft.Checkbox(
                label=f"{name} (ID: {id_})",
                data=id_,
                value=id_ in self.app.selected_groups,
                on_change=self.update_selected_groups
            ) for name, id_ in groups.items()
        ]

        self.theme_dropdown = ft.Dropdown(
            label="Тема приложения",
            options=[
                ft.dropdown.Option(text="Светлая", key="light"),
                ft.dropdown.Option(text="Тёмная", key="dark")
            ],
            value=self.app.settings.get("theme", "light"),
            width=200,
            on_change=self.update_theme
        )

        self.schedule_notifications_checkbox = ft.Checkbox(
            label="Уведомления о изменениях в расписании",
            value=self.app.settings.get("schedule_notifications", True),
            on_change=self.update_schedule_notifications
        )

        self.expiry_notification_days_dropdown = ft.Dropdown(
            label="Оповещать о сроке актуальности за",
            options=[
                ft.dropdown.Option(text="1 день", key="1"),
                ft.dropdown.Option(text="3 дня", key="3"),
                ft.dropdown.Option(text="7 дней", key="7")
            ],
            value=str(self.app.settings.get("expiry_notification_days", 3)),
            width=200,
            on_change=self.update_expiry_notification_days
        )

        # Добавляем поле для ввода URL и кнопку для загрузки расписания
        self.url_input = ft.TextField(
            label="URL расписания (например, https://ursei.su/asu/ssched.php?group=26616)",
            width=300,
            text_size=14,
            content_padding=10
        )

        load_schedule_button = ft.ElevatedButton(
            "Загрузить расписание из URL",
            on_click=self.load_schedule_from_url,
            icon=ft.Icons.DOWNLOAD
        )

        save_button = ft.ElevatedButton(
            "Сохранить изменения",
            on_click=self.save_changes,
            icon=ft.Icons.SAVE
        )

        return ft.Column([
            ft.Text("Настройки", size=20, weight="bold"),
            ft.Text("Смена группы", size=16, weight="bold"),
            self.course_dropdown,
            ft.Text("Доступные группы:", weight="bold"),
            self.groups_container,
            ft.Text("Оформление", size=16, weight="bold"),
            self.theme_dropdown,
            ft.Text("Уведомления", size=16, weight="bold"),
            self.schedule_notifications_checkbox,
            self.expiry_notification_days_dropdown,
            ft.Text("Загрузка расписания", size=16, weight="bold"),
            self.url_input,
            load_schedule_button,
            save_button
        ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def update_groups(self, e):
        """Обновляем список групп при выборе курса"""
        course = self.course_dropdown.value
        groups = {
            "1": {"ИД-101": 26616, "ИД-102": 26617},
            "2": {"ИД-201": 26618},
            "3": {"ИД-301": 26619},
            "4": {"ИД-401": 26620}
        }.get(course, {})

        self.groups_container.controls = [
            ft.Checkbox(
                label=f"{name} (ID: {id_})",
                data=id_,
                value=id_ in self.app.selected_groups,
                on_change=self.update_selected_groups
            ) for name, id_ in groups.items()
        ]
        self.groups_container.update()

    def update_selected_groups(self, e):
        """Обновляем выбранные группы"""
        if e.control.value:
            self.app.selected_groups.append(e.control.data)
        else:
            self.app.selected_groups.remove(e.control.data)

    def update_theme(self, e):
        """Обновляем тему приложения"""
        theme_mode = e.control.value
        self.app.settings["theme"] = theme_mode
        self.page.theme_mode = ft.ThemeMode.LIGHT if theme_mode == "light" else ft.ThemeMode.DARK
        self.page.update()

    def update_schedule_notifications(self, e):
        """Обновляем настройку уведомлений о расписании"""
        self.app.settings["schedule_notifications"] = e.control.value

    def update_expiry_notification_days(self, e):
        """Обновляем настройку периода уведомлений о сроке актуальности"""
        self.app.settings["expiry_notification_days"] = int(e.control.value)

    def load_schedule_from_url(self, e):
        """Загружаем расписание по указанному URL"""
        url = self.url_input.value
        if not url:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Введите URL для загрузки расписания!"),
                duration=5000
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Извлекаем group_id из URL
        group_id = url.split("group=")[-1] if "group=" in url else "unknown"
        self.page.run_task(self.app.schedule_tab.load_schedule_from_url, url, group_id)

    def save_changes(self, e):
        """Сохраняем изменения и перезапускаем интерфейс"""
        if not self.app.selected_groups:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Выберите хотя бы одну группу!"),
                open=True
            )
            self.page.update()
            return

        self.app.current_course = self.course_dropdown.value
        self.app.save_settings()
        self.page.snack_bar = ft.SnackBar(ft.Text("Настройки сохранены! Перезапустите приложение."))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.run_task(self.app.show_main_interface)