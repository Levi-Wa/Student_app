import flet as ft
import json
import os
import logging
import time
import shutil

class SettingsView:
    def __init__(self, page: ft.Page, app, schedule_tab, group_selection_view, notes_tab):
        self.page = page
        self.app = app
        self.schedule_tab = schedule_tab
        self.group_selection_view = group_selection_view
        self.notes_tab = notes_tab
        self.settings_file = "settings.json"
        self.load_settings()

    def load_settings(self):
        """Загрузка настроек из файла"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.app.settings = json.load(f)
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
        self.app.settings.setdefault("schedule_notifications", True)
        self.app.settings.setdefault("expiry_days", 1)
        self.app.settings.setdefault("theme", "light")

    def save_settings(self):
        """Сохранение настроек в файл"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.app.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")

    def change_group(self, e):
        """Показывает диалог подтверждения перед сменой группы"""
        def confirm_change(e):
            try:
                # Очищаем файл schedules.json перед сменой группы
                try:
                    with open("schedules.json", "w", encoding="utf-8") as f:
                        json.dump([], f)
                    logging.info("Cleared schedules.json before changing group")
                except Exception as err:
                    logging.error(f"Error clearing schedules.json: {err}")

                logging.info("Switching to group selection")
                self.app.settings.pop("group_id", None)
                self.app.save_settings()
                self.schedule_tab.schedules = []
                self.schedule_tab.group_id = None
                self.notes_tab.ui_content.controls.clear()
                self.page.views.clear()
                self.page.views.append(
                    ft.View(
                        "/group_selection",
                        [self.group_selection_view.build()]
                    )
                )
                self.page.dialog.open = False
                self.page.update()
                logging.info("Group selection view displayed")
            except Exception as e:
                logging.error(f"Error switching to group selection: {e}")
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Ошибка при смене группы"),
                    duration=3000
                )
                self.page.snack_bar.open = True
                self.page.update()

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
        """Скачивает лог-файл и открывает Google Форму"""
        try:
            log_file = "app.log"
            if os.path.exists(log_file):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_log = f"app_log_{timestamp}.log"
                shutil.copyfile(log_file, output_log)
                self.page.launch_url(f"file://{os.path.abspath(output_log)}")
                logging.info(f"Log file copied to {output_log} and download initiated")
            else:
                logging.warning("Log file not found")
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Лог-файл не найден"),
                    duration=3000
                )
                self.page.snack_bar.open = True

            form_url = "https://docs.google.com/forms/d/e/1FAIpQLSfxrzBgkLRYaj4Ntp2I4FOAJdmKttq5qyleUqK6LOJLdIi_IQ/viewform?usp=dialog"
            self.page.launch_url(form_url)
            logging.info(f"Opened Google Form: {form_url}")
        except Exception as e:
            logging.error(f"Error reporting issue: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Ошибка при отправке отчета"),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()

    def toggle_theme(self, e):
        """Переключение темы"""
        self.app.settings["theme"] = "dark" if self.app.settings["theme"] == "light" else "light"
        self.page.theme_mode = ft.ThemeMode.DARK if self.app.settings["theme"] == "dark" else ft.ThemeMode.LIGHT
        self.save_settings()
        self.page.update()

    def update_expiry_days(self, e):
        """Обновление количества дней для уведомления"""
        selected_days = self.expiry_days_dropdown.value
        try:
            self.app.settings["expiry_days"] = int(selected_days)
            self.save_settings()
        except ValueError:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Ошибка: выберите значение"),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()

    def build(self):
        """Создаём интерфейс настроек"""
        self.schedule_notifications_switch = ft.Switch(
            label="Уведомления об изменениях расписания",
            value=self.app.settings.get("schedule_notifications", True),
            on_change=lambda e: (
                self.app.settings.update({"schedule_notifications": e.control.value}),
                self.save_settings()
            )
        )
        self.expiry_days_dropdown = ft.Dropdown(
            label="Уведомлять о сроке заметки",
            options=[
                ft.dropdown.Option("1", "За 1 день"),
                ft.dropdown.Option("3", "За 3 дня"),
                ft.dropdown.Option("7", "За 7 дней")
            ],
            value=str(self.app.settings.get("expiry_days", 1)),
            on_change=self.update_expiry_days,
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
            value=self.app.settings.get("theme", "light") == "dark",
            on_change=self.toggle_theme
        )

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=20),
            content=ft.Column([
            self.schedule_notifications_switch,
            self.expiry_days_dropdown,
            change_group_button,
            report_issue_button,
            theme_switch
        ], alignment=ft.MainAxisAlignment.CENTER))