import flet as ft
import logging
import os
import webbrowser
from pathlib import Path
from platform import system
from plyer import storagepath
from logic.logic_settings.settings_manager import SettingsManager

class SettingsUI:
    def __init__(self, page: ft.Page, manager):
        self.page = page
        self.manager = manager
        self.setup_logging()
        self.settings_output = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )

    def setup_logging(self):
        """Настраивает логирование"""
        try:
            if system() == "Android":
                base_dir = Path(storagepath.get_files_dir())
            else:
                base_dir = Path(__file__).parent.parent

            log_dir = base_dir / "data" / "log"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / "app.log"
            
            # Создаем обработчик с ротацией
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8"
            )
            
            # Настраиваем формат логов
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            
            # Настраиваем корневой логгер
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            
            # Удаляем существующие обработчики
            for h in root_logger.handlers[:]:
                root_logger.removeHandler(h)
            
            # Добавляем новый обработчик
            root_logger.addHandler(handler)
            
            logging.info(f"Logging initialized, logs will be saved to {log_file}")
        except Exception as e:
            logging.error(f"Error setting up logging: {e}")

    def get_logs(self):
        """Получает содержимое лог-файла"""
        try:
            if system() == "Android":
                base_dir = Path(storagepath.get_files_dir())
            else:
                base_dir = Path(__file__).parent.parent

            log_file = base_dir / "data" / "log" / "app.log"
            
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    return f.read()
            return "Лог-файл не найден"
        except Exception as e:
            logging.error(f"Error reading log file: {e}")
            return f"Ошибка чтения лог-файла: {str(e)}"

    def save_logs(self):
        """Сохраняет логи в файл для отправки"""
        try:
            if system() == "Android":
                base_dir = Path(storagepath.get_files_dir())
            else:
                base_dir = Path(__file__).parent.parent

            export_dir = base_dir / "data" / "export"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            log_content = self.get_logs()
            export_file = export_dir / "app_log.txt"
            
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(log_content)
            
            logging.info(f"Logs exported to {export_file}")
            return str(export_file)
        except Exception as e:
            logging.error(f"Error saving logs: {e}")
            return None

    def create_setting_card(self, title: str, content: ft.Control):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        title,
                        weight=ft.FontWeight.BOLD,
                        size=16,
                        color=ft.Colors.ON_SURFACE
                    ),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    content
                ], spacing=10),
                padding=15
            ),
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=10),
            color=ft.Colors.SURFACE
        )

    async def change_group(self, e):
        """Показывает диалог подтверждения перед сменой группы"""
        async def confirm_change(e):
            def notify_callback(message):
                self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
                self.page.snack_bar.open = True
                self.page.update()

            try:
                if await self.manager.change_group(notify_callback):
                    self.page.dialog.open = False
                    self.page.update()
                    # Закрываем приложение
                    self.page.window_destroy()
                else:
                    notify_callback("Не удалось сменить группу")
            except Exception as ex:
                logging.error(f"Error changing group: {ex}")
                notify_callback(f"Ошибка при смене группы: {str(ex)}")

        def cancel_change(e):
            self.page.dialog.open = False
            self.page.update()
            logging.info("Group change cancelled")

        dialog = ft.AlertDialog(
            title=ft.Text("Вы уверены?"),
            content=ft.Text("Приложение будет закрыто для применения изменений"),
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
        """Обработчик нажатия кнопки 'Сообщить о проблеме'"""
        try:
            # Сохраняем логи
            log_file = self.save_logs()
            if log_file:
                # Открываем форму Google
                webbrowser.open("https://docs.google.com/forms/d/e/1FAIpQLSfxrzBgkLRYaj4Ntp2I4FOAJdmKttq5qyleUqK6LOJLdIi_IQ/viewform?usp=dialog")
                
                # Показываем сообщение с информацией о логах
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(
                            f"Логи сохранены в файл: {log_file}\n"
                            "Пожалуйста, прикрепите этот файл к форме."
                        ),
                        duration=10000
                    )
                )
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Ошибка при сохранении логов"),
                        bgcolor=ft.Colors.ERROR
                    )
                )
        except Exception as e:
            logging.error(f"Error in report_issue: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Ошибка: {str(e)}"),
                    bgcolor=ft.Colors.ERROR
                )
            )

    def build(self):
        """Создает интерфейс настроек"""
        try:
            logging.info("Building settings interface")
            
            # Theme settings
            theme_switch = ft.Switch(
                label="Тёмная тема",
                value=self.manager.app.settings.get("theme") == "dark",
                on_change=lambda e: self.manager.toggle_theme(self.page)
            )

            # Notifications settings
            notifications_switch = ft.Switch(
                label="Уведомления о расписании",
                value=self.manager.app.settings.get("schedule_notifications", True),
                on_change=lambda e: self.manager.toggle_notifications(e.control.value)
            )

            # Expiry settings
            expiry_dropdown = ft.Dropdown(
                label="Срок актуальности заметок",
                value=str(self.manager.app.settings.get("expiry_days", 1)),
                options=[
                    ft.dropdown.Option("1", "1 день"),
                    ft.dropdown.Option("3", "3 дня"),
                    ft.dropdown.Option("7", "7 дней"),
                    ft.dropdown.Option("14", "14 дней"),
                    ft.dropdown.Option("30", "30 дней")
                ],
                on_change=lambda e: self.manager.update_expiry_days(int(e.control.value))
            )

            # Group settings
            change_group_button = ft.ElevatedButton(
                "Сменить группу",
                icon=ft.Icons.SWAP_HORIZ,
                on_click=self.change_group,
                style=ft.ButtonStyle(
                    color=ft.Colors.ERROR,
                )
            )
            
            group_settings = ft.Column([
                ft.Text(
                    "Внимание: при смене группы все настройки будут сброшены, а заметки удалены!",
                    color=ft.Colors.ERROR,
                    size=12,
                    italic=True
                ),
                change_group_button
            ], spacing=10)

            # Создаем кнопку для сообщения о проблеме
            report_button = ft.ElevatedButton(
                text="Сообщить о проблеме",
                icon=ft.Icons.REPORT_PROBLEM,
                on_click=self.report_issue,
                style=ft.ButtonStyle(
                    color=ft.Colors.ON_PRIMARY,
                    bgcolor=ft.Colors.PRIMARY,
                )
            )

            # Build settings cards
            settings_content = ft.Column(
                controls=[
                    self.create_setting_card("Внешний вид", theme_switch),
                    self.create_setting_card("Уведомления", notifications_switch),
                    self.create_setting_card("Заметки", expiry_dropdown),
                    self.create_setting_card("Группа", group_settings),
                    report_button
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO
            )

            # Создаем контейнер с отступами
            container = ft.Container(
                content=settings_content,
                padding=20,
                expand=True
            )

            logging.info("Settings interface built successfully")
            return container

        except Exception as e:
            logging.error(f"Error building settings interface: {e}")
            return ft.Container(
                content=ft.Text(
                    f"Ошибка загрузки настроек: {str(e)}",
                    color=ft.Colors.ERROR,
                    size=16
                ),
                padding=20,
                expand=True
            )