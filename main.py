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
import asyncio

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

    def update_nav_bar_style(self, nav_bar, theme_mode):
        """Обновляет стили NavigationBar в зависимости от темы."""
        if theme_mode == ft.ThemeMode.DARK:
            nav_bar.bgcolor = ft.Colors.BLACK
            nav_bar.indicator_color = ft.Colors.BLUE_400
        else:
            nav_bar.bgcolor = ft.Colors.WHITE
            nav_bar.indicator_color = ft.Colors.BLUE_400
        logging.info(f"Updated NavigationBar styles for {theme_mode}")
        return nav_bar

    def toggle_theme(self, page, nav_bar):
        """Переключает тему приложения между светлой и тёмной."""
        try:
            current_theme = self.settings.get("theme", "light")
            new_theme = "dark" if current_theme == "light" else "light"
            self.settings["theme"] = new_theme
            self.save_settings()
            page.theme_mode = ft.ThemeMode.DARK if new_theme == "dark" else ft.ThemeMode.LIGHT
            self.update_nav_bar_style(nav_bar, page.theme_mode)
            page.update()
            logging.info(f"Theme switched to {new_theme}")
        except Exception as e:
            logging.error(f"Error toggling theme: {e}")

def setup_logging():
    """Настраивает логирование с ротацией логов в папке data/log."""
    try:
        if system() == "Android":
            base_dir = Path(storagepath.get_files_dir())
        else:
            base_dir = Path(__file__).parent

        log_dir = base_dir / "data" / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "app.log"
        
        # Создаем обработчик с ротацией
        handler = RotatingFileHandler(
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
        print(f"Error setting up logging: {e}")
        # Настраиваем базовое логирование в консоль
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

async def check_notifications(notes_manager):
    """Периодическая проверка уведомлений"""
    while True:
        try:
            # Проверяем уведомления о заметках
            await notes_manager.check_notes_expiry(lambda msg: None)
            
            # Ждем 1 час перед следующей проверкой
            await asyncio.sleep(3600)
        except Exception as e:
            logging.error(f"Error checking notifications: {e}")
            await asyncio.sleep(300)  # В случае ошибки ждем 5 минут

async def start_notification_check(notes_manager):
    """Starts the notification check task"""
    while True:
        try:
            await check_notifications(notes_manager)
        except Exception as e:
            logging.error(f"Error in notification check loop: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying

def main(page: ft.Page):
    """Основная функция приложения."""
    # Оптимизация для Android
    if system() == "Android":
        page.window_width = None  # Автоматическая ширина на Android
        page.window_height = None  # Автоматическая высота на Android
        page.window_resizable = False
        page.padding = 0
        page.theme_mode = ft.ThemeMode.SYSTEM  # Используем системную тему
    else:
        page.window_width = 400
        page.window_height = 800
        page.window_resizable = False
        page.padding = 0

    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.BLUE,
            on_primary=ft.Colors.WHITE,
            primary_container=ft.Colors.BLUE_100,
            on_primary_container=ft.Colors.BLUE_900,
            secondary=ft.Colors.BLUE_GREY,
            on_secondary=ft.Colors.WHITE,
            secondary_container=ft.Colors.BLUE_GREY_100,
            on_secondary_container=ft.Colors.BLUE_GREY_900,
            surface=ft.Colors.WHITE,
            on_surface=ft.Colors.BLACK,
            surface_variant=ft.Colors.GREY_100,
            on_surface_variant=ft.Colors.BLACK,
            background=ft.Colors.WHITE,
            on_background=ft.Colors.BLACK,
        )
    )
    
    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.BLUE,
            on_primary=ft.Colors.WHITE,
            primary_container=ft.Colors.BLUE_900,
            on_primary_container=ft.Colors.BLUE_100,
            secondary=ft.Colors.BLUE_GREY,
            on_secondary=ft.Colors.WHITE,
            secondary_container=ft.Colors.BLUE_GREY_900,
            on_secondary_container=ft.Colors.BLUE_GREY_100,
            surface=ft.Colors.BLACK,
            on_surface=ft.Colors.WHITE,
            surface_variant=ft.Colors.GREY_900,
            on_surface_variant=ft.Colors.WHITE,
            background=ft.Colors.GREY_900,
            on_background=ft.Colors.WHITE,
        )
    )

    # Инициализация приложения
    app = App()

    # Установка темы на основе настроек
    page.theme_mode = ft.ThemeMode.DARK if app.settings.get("theme") == "dark" else ft.ThemeMode.LIGHT

    # Инициализация менеджеров
    schedule_manager = ScheduleManager()
    group_selection_manager = GroupSelectionManager(schedule_manager, app)
    notes_manager = NotesManager(schedule_manager, app)

    # Создание нижней навигационной панели
    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.NOTE_ALT_OUTLINED,
                selected_icon=ft.Icons.NOTE_ALT,
                label="Заметки"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.CALENDAR_TODAY_OUTLINED,
                selected_icon=ft.Icons.CALENDAR_TODAY,
                label="Расписание"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Настройки"
            ),
        ],
        on_change=lambda e: handle_navigation_change(e.control.selected_index),
        height=60 if system() == "Android" else 50,
        elevation=8,
        indicator_color=ft.Colors.BLUE_400,
        bgcolor=ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.WHITE,
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        selected_index=1,  # По умолчанию выбрано расписание
    )

    # Инициализация SettingsManager после создания nav_bar
    settings_manager = SettingsManager(app, schedule_manager, group_selection_manager, notes_manager, page, nav_bar)

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
            # Загружаем расписание для выбранной группы
            await schedule_manager.load_schedule_for_group(
                group_id=schedule_manager.group_id,
                display_callback=lambda: None,
                notify_callback=lambda msg: None
            )
            # Обновляем список дисциплин после загрузки расписания
            notes_ui.update_disciplines()
            logging.info("Disciplines updated in NotesUI")
        except Exception as e:
            logging.error(f"Error updating disciplines: {e}")
        page.update()
        logging.info("Main view with navigation bar displayed")

    # Инициализация GroupSelectionUI
    group_selection_ui = GroupSelectionUI(page, group_selection_manager, schedule_ui, on_selection_complete)
    group_selection_manager.ui = group_selection_ui  # Сохраняем ссылку на UI
    
    # Инициализация данных групп
    group_selection_manager.initialize()

    # Создание контейнера для основного контента
    content_container = ft.Container(
        content=schedule_ui.build(),
        expand=True
    )

    # Инициализация главного интерфейса
    page.content_container = content_container
    page.add(content_container)
    page.add(nav_bar)

    def handle_navigation_change(index):
        """Обработчик изменения вкладки"""
        logging.info(f"Navigation change requested to index: {index}")
        
        async def update_content():
            try:
                # Создаем контейнер для контента, если его нет
                if not hasattr(page, 'content_container'):
                    page.content_container = ft.Container(expand=True)
                    page.add(page.content_container)
                    page.add(nav_bar)

                if index == 0:  # Заметки
                    logging.info("Switching to Notes tab")
                    notes_ui.update_disciplines()  # Обновляем список дисциплин
                    page.content_container.content = notes_ui.build()
                elif index == 1:  # Расписание
                    logging.info("Switching to Schedule tab")
                    page.content_container.content = schedule_ui.build()
                elif index == 2:  # Настройки
                    logging.info("Switching to Settings tab")
                    page.content_container.content = settings_ui.build()
                
                page.update()
                logging.info(f"Navigation completed to index: {index}")
            except Exception as e:
                logging.error(f"Error in navigation change: {e}")
                page.snack_bar = ft.SnackBar(
                    ft.Text("Ошибка при переключении вкладки"),
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
        
        page.run_task(update_content)

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
    
    page.update()

    # Запускаем проверку уведомлений в фоновом режиме
    async def run_notification_check():
        await start_notification_check(notes_manager)
    
    page.run_task(run_notification_check)

if __name__ == "__main__":
    ft.app(target=main)