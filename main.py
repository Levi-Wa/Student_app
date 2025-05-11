import flet as ft
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
from logic.logic_schedule.schedule_manager import ScheduleManager
from logic.logic_notes.notes_manager import NotesManager
from logic.logic_settings.settings_manager import SettingsManager
from logic.logic_selector_group.group_selection_manager import GroupSelectionManager
from ui.ui_schedule import ScheduleUI
from ui.ui_notes import NotesUI
from ui.ui_settings import SettingsUI
from ui.ui_group_selection import GroupSelectionUI

class App:
    """Класс приложения для управления настройками."""

    def __init__(self):
        self.settings = {}
        self.settings_file = Path(__file__).parent / "data" / "settings.json"
        self.load_settings()

    def load_settings(self):
        """Загружает настройки из файла."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
        # Установка значений по умолчанию
        self.settings.setdefault("schedule_notifications", True)
        self.settings.setdefault("expiry_days", 1)
        self.settings.setdefault("theme", "light")

    def save_settings(self):
        """Сохраняет настройки в файл."""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            import os
            os.chmod(self.settings_file, 0o600)  # Ограничение прав доступа
        except Exception as e:
            logging.error(f"Error saving settings: {e}")

def setup_logging():
    """Настраивает логирование с ротацией логов в папке data/log."""
    log_dir = Path(__file__).parent / "data" / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)
    logging.info(f"Logging initialized, logs will be saved to {log_dir / 'app.log'}")

def main(page: ft.Page):
    """Основная функция приложения."""
    setup_logging()
    logging.info("Starting Student App")

    # Инициализация приложения
    app = App()

    # Установка темы на основе настроек
    page.theme_mode = ft.ThemeMode.DARK if app.settings.get("theme") == "dark" else ft.ThemeMode.LIGHT

    # Инициализация менеджеров
    schedule_manager = ScheduleManager()
    group_selection_manager = GroupSelectionManager(schedule_manager, app)
    notes_manager = NotesManager(schedule_manager, app)
    settings_manager = SettingsManager(app, schedule_manager, group_selection_manager, notes_manager)

    # Инициализация UI
    schedule_ui = ScheduleUI(page, schedule_manager)
    notes_ui = NotesUI(page, notes_manager, schedule_manager)
    settings_ui = SettingsUI(page, settings_manager)

    # Определение функции on_selection_complete перед использованием
    async def on_selection_complete():
        """Переход к основному интерфейсу после выбора группы."""
        page.views.clear()
        page.views.append(
            ft.View(
                "/main",
                [
                    ft.Tabs(
                        tabs=[
                            ft.Tab(text="Расписание", content=schedule_ui.build()),
                            ft.Tab(text="Заметки", content=notes_ui.ui_content),
                            ft.Tab(text="Настройки", content=settings_ui.build())
                        ]
                    )
                ]
            )
        )
        try:
            notes_ui.update_disciplines()  # Убрали await
            logging.info("Disciplines updated in NotesUI")
        except Exception as e:
            logging.error(f"Error updating disciplines: {e}")
        page.update()
        logging.info("Main view displayed after group selection")

    # Инициализация GroupSelectionUI после определения on_selection_complete
    group_selection_ui = GroupSelectionUI(page, group_selection_manager, schedule_ui, on_selection_complete)

    # Проверка, есть ли сохранённый group_id
    if app.settings.get("group_id"):
        async def load_schedule():
            logging.info(f"Loading schedule for group_id: {app.settings['group_id']}")
            try:
                await schedule_manager.load_schedule_for_group(
                    group_id=app.settings["group_id"],
                    display_callback=schedule_ui.display_schedules,
                    notify_callback=lambda msg: (
                        setattr(page, 'snack_bar', ft.SnackBar(ft.Text(msg), duration=5000)),
                        setattr(page.snack_bar, 'open', True),
                        page.update()
                    )
                )
                await on_selection_complete()
            except Exception as e:
                logging.error(f"Error loading schedule: {e}")
                page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка загрузки расписания: {str(e)}"), duration=5000)
                page.snack_bar.open = True
                page.update()

        page.run_task(load_schedule)
    else:
        page.views.append(
            ft.View(
                "/group_selection",
                [group_selection_ui.build()]
            )
        )
        page.update()
        logging.info("Group selection view displayed")

if __name__ == "__main__":
    ft.app(target=main)