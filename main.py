import flet as ft
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
import os
from platform import system
from plyer import storagepath
from logic.logic_schedule.schedule_manager import ScheduleManager
from logic.logic_notes.notes_manager import NotesManager
from logic.logic_settings.settings_manager import SettingsManager
from logic.logic_selector_group.group_selection_manager import GroupSelectionManager
from ui.ui_schedule import ScheduleUI
from ui.ui_notes import NotesUI
from ui.ui_settings import SettingsUI
from ui.ui_group_selection import GroupSelectionUI

class App:
    def __init__(self):
        self.settings = {}
        # Определяем путь в зависимости от платформы
        if system() == "Android":
            base_dir = Path(storagepath.get_files_dir())  # Внутреннее хранилище приложения
        else:
            base_dir = Path(__file__).parent
        self.settings_file = base_dir / "data" / "settings.json"
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
            logging.info(f"Saving settings to: {self.settings_file}")
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            os.chmod(self.settings_file, 0o600)
        except Exception as e:
            logging.error(f"Error saving settings to {self.settings_file}: {e}")

def setup_logging():
    """Настраивает логирование с ротацией логов в папке data/log."""
    if system() == "Android":
        log_dir = Path(storagepath.get_files_dir()) / "data" / "log"
    else:
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
    # Оптимизация для Android
    page.window_width = 400
    page.window_height = 800
    page.window_resizable = False
    page.padding = 0
    page.theme = ft.Theme(
        color_scheme_seed=ft.colors.BLUE,
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary=ft.colors.BLUE,
            on_primary=ft.colors.WHITE,
            primary_container=ft.colors.BLUE_100,
            on_primary_container=ft.colors.BLUE_900,
            secondary=ft.colors.BLUE_GREY,
            on_secondary=ft.colors.WHITE,
            secondary_container=ft.colors.BLUE_GREY_100,
            on_secondary_container=ft.colors.BLUE_GREY_900,
            surface=ft.colors.SURFACE,
            on_surface=ft.colors.ON_SURFACE,
            surface_variant=ft.colors.SURFACE_VARIANT,
            on_surface_variant=ft.colors.ON_SURFACE_VARIANT,
            background=ft.colors.BACKGROUND,
            on_background=ft.colors.ON_BACKGROUND,
        )
    )
    
    # Асинхронная инициализация логирования
    async def async_setup():
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

    # Инициализация UI компонентов
    schedule_ui = ScheduleUI(page, schedule_manager)
    notes_ui = NotesUI(page, notes_manager, schedule_manager)
    settings_ui = SettingsUI(page, settings_manager)

    # Определение функции on_selection_complete
    async def on_selection_complete():
        """Переход к основному интерфейсу после выбора группы."""
        page.views.clear()
        page.views.append(
            ft.View(
                "/main",
                [
                    content_container,
                    nav_bar
                ],
                vertical_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                padding=0
            )
        )
        try:
            notes_ui.update_disciplines()
            logging.info("Disciplines updated in NotesUI")
        except Exception as e:
            logging.error(f"Error updating disciplines: {e}")
        page.update()
        logging.info("Main view with navigation bar displayed")

    # Инициализация GroupSelectionUI
    group_selection_ui = GroupSelectionUI(page, group_selection_manager, schedule_ui, on_selection_complete)
    group_selection_manager.ui = group_selection_ui  # Сохраняем ссылку на UI

    # Создание контейнера для основного контента
    content_container = ft.Container(
        content=schedule_ui.build(),
        expand=True
    )

    # Создание нижней навигационной панели
    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.icons.NOTE_ALT_OUTLINED,
                selected_icon=ft.icons.NOTE_ALT,
                label="Заметки",
            ),
            ft.NavigationBarDestination(
                icon=ft.icons.CALENDAR_TODAY_OUTLINED,
                selected_icon=ft.icons.CALENDAR_TODAY,
                label="Расписание",
            ),
            ft.NavigationBarDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label="Настройки",
            ),
        ],
        on_change=lambda e: handle_navigation_change(e.control.selected_index),
    )

    def handle_navigation_change(index):
        """Обработчик изменения вкладки в навигационной панели"""
        if index == 0:  # Заметки
            content_container.content = notes_ui.build()
        elif index == 1:  # Расписание
            content_container.content = schedule_ui.build()
        else:  # Настройки
            content_container.content = settings_ui.build()
        page.update()

    # Проверяем сохраненный group_id
    saved_group_id = app.settings.get("group_id")
    if saved_group_id:
        schedule_manager.group_id = saved_group_id
        schedule_manager.data.group_id = saved_group_id
        schedule_manager.data.load_schedules()
        
        # Если есть валидные данные расписания, показываем главный интерфейс
        if schedule_manager.data.schedules and any(not "error" in sched for sched in schedule_manager.data.schedules):
            page.views.append(
                ft.View(
                    "/main",
                    [content_container, nav_bar],
                    vertical_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    padding=0
                )
            )
        else:
            # Если данные невалидны, показываем выбор группы
            page.views.append(
                ft.View(
                    "/group_selection",
                    [group_selection_ui.build()],
                    padding=10
                )
            )
    else:
        # Если group_id не сохранен, показываем выбор группы
        page.views.append(
            ft.View(
                "/group_selection",
                [group_selection_ui.build()],
                padding=10
            )
        )
    
    # Запускаем асинхронную инициализацию
    page.run_task(async_setup)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)