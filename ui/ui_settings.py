import flet as ft
import logging
from logic.logic_settings.settings_manager import SettingsManager

class SettingsUI:
    def __init__(self, page: ft.Page, manager):
        self.page = page
        self.manager = manager

    def change_group(self, e):
        """Показывает диалог подтверждения перед сменой группы"""
        def confirm_change(e):
            def notify_callback(message):
                self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
                self.page.snack_bar.open = True
                self.page.update()

            if self.manager.change_group(notify_callback):
                self.page.views.clear()
                self.page.views.append(
                    ft.View(
                        "/group_selection",
                        [self.manager.group_selection_manager.build()]
                    )
                )
                self.page.dialog.open = False
                self.page.update()
                logging.info("Group selection view displayed")

        def cancel_change(e):
            self.page.dialog.open = False
            self.page.update()
            logging.info("Group change cancelled")

        dialog = ft.AlertDialog(
            title=ft.Text("Вы уверены?"),
            content=ft.Text("Ваши заметки могут пропасть"),
            actions=[
                ft.TextButton("Да", on_click=confirm_change),
                ft.TextButton("Нет", on_click=cancel_change)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True
        )
        self.page.dialog = dialog
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
        logging.info("Group change confirmation dialog opened")

    def report_issue(self, e):
        """Обработчик для отправки отчета о проблеме"""
        def notify_callback(message):
            self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
            self.page.snack_bar.open = True
            self.page.update()

        self.manager.report_issue(self.page, notify_callback)

    def build(self):
        """Создаём интерфейс настроек"""
        schedule_notifications_switch = ft.Switch(
            label="Уведомления об изменениях расписания",
            value=self.manager.app.settings.get("schedule_notifications", True),
            on_change=lambda e: (
                self.manager.app.settings.update({"schedule_notifications": e.control.value}),
                self.manager.data.save_settings(self.manager.app)
            )
        )
        expiry_days_dropdown = ft.Dropdown(
            label="Уведомлять о сроке заметки",
            options=[
                ft.dropdown.Option("1", "За 1 день"),
                ft.dropdown.Option("3", "За 3 дня"),
                ft.dropdown.Option("7", "За 7 дней")
            ],
            value=str(self.manager.app.settings.get("expiry_days", 1)),
            on_change=lambda e: self.manager.update_expiry_days(e.control.value, lambda msg: (
                setattr(self.page, 'snack_bar', ft.SnackBar(ft.Text(msg), duration=3000)),
                setattr(self.page.snack_bar, 'open', True),
                self.page.update()
            )),
            width=200
        )
        change_group_button = ft.ElevatedButton(
            text="Сменить группу",
            on_click=self.change_group
        )
        report_issue_button = ft.ElevatedButton(
            text="Сообщить о проблеме",
            on_click=self.report_issue
        )
        theme_switch = ft.Switch(
            label="Темная тема",
            value=self.manager.app.settings.get("theme", "light") == "dark",
            on_change=lambda e: self.manager.toggle_theme(self.page)
        )

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=20),
            content=ft.Column([
                # Группа: Уведомления
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Уведомления", weight="bold", size=16),
                            schedule_notifications_switch,
                            expiry_days_dropdown
                        ], spacing=10),
                        padding=10
                    )
                ),
                ft.Divider(),
                # Группа: Тема
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Тема", weight="bold", size=16),
                            theme_switch
                        ], spacing=10),
                        padding=10
                    )
                ),
                ft.Divider(),
                # Группа: Действия
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Действия", weight="bold", size=16),
                            change_group_button,
                            report_issue_button
                        ], spacing=10),
                        padding=10
                    )
                )
            ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
        )