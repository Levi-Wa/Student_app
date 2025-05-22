import flet as ft
import datetime
import logging
from logic.logic_notes.notes_manager import NotesManager
from typing import List, Dict

class NotesUI:
    def __init__(self, page: ft.Page, manager, schedule_manager):
        self.page = page
        self.manager = manager
        self.schedule_manager = schedule_manager
        self.notes_output = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )
        self.discipline_dropdown = None
        self.mode_dropdown = None
        self.note_text = None
        self.add_button = None
        self.ui_content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.notes_list = ft.ListView(expand=True)
        
        # Инициализируем форму и список заметок
        self.build_note_form()
        self.update_notes_list()
        
        # Добавляем форму в контент
        self.ui_content.controls.append(self.build_note_form_container())
        
        logging.info("NotesUI initialized")

    def build_note_form(self):
        """Создаёт форму для добавления заметки."""
        disciplines = self.schedule_manager.utils.get_unique_disciplines(self.schedule_manager.data.schedules)
        logging.info(f"Disciplines in build_note_form: {disciplines}")
        
        # Сохраняем текущее значение, если оно есть
        current_value = self.discipline_dropdown.value if self.discipline_dropdown else None
        
        if not disciplines:
            logging.warning("No disciplines available")
            discipline_options = []
            discipline_value = None
        else:
            discipline_options = [ft.dropdown.Option(d) for d in disciplines]
            # Если текущее значение есть в списке дисциплин, оставляем его
            discipline_value = current_value if current_value in disciplines else disciplines[0] if disciplines else None

        self.discipline_dropdown = ft.Dropdown(
            label="Дисциплина",
            options=discipline_options,
            value=discipline_value,
            width=300,
            hint_text="Выберите дисциплину",
            on_change=lambda e: self.page.update()
        )
        self.mode_dropdown = ft.Dropdown(
            label="Режим",
            options=[
                ft.dropdown.Option("Лекция"),
                ft.dropdown.Option("Практика"),
                ft.dropdown.Option("Лабораторная"),
                ft.dropdown.Option("До следующей пары")
            ],
            value="Лекция",
            width=300
        )
        self.note_text = ft.TextField(
            label="Текст заметки",
            multiline=True,
            width=300
        )
        self.add_button = ft.ElevatedButton(
            text="Добавить",
            on_click=self.add_note
        )

    def build_note_form_container(self):
        """Возвращает контейнер с формой."""
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=20),
            content=ft.Column([
                self.discipline_dropdown,
                self.mode_dropdown,
                self.note_text,
                self.add_button
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

    def update_disciplines(self):
        """Обновляет список дисциплин после загрузки расписания."""
        logging.info("Updating disciplines in NotesUI")
        try:
            # Проверяем наличие расписания
            if not self.schedule_manager.data.schedules:
                logging.warning("No schedules available")
                self.discipline_dropdown.options = []
                self.discipline_dropdown.value = None
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Нет данных расписания. Пожалуйста, выберите группу в настройках."),
                    duration=5000
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            # Получаем актуальный список дисциплин
            disciplines = self.schedule_manager.utils.get_unique_disciplines(self.schedule_manager.data.schedules)
            logging.info(f"Retrieved disciplines: {disciplines}")
            
            if not disciplines:
                logging.warning("No disciplines available")
                self.discipline_dropdown.options = []
                self.discipline_dropdown.value = None
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("В расписании нет дисциплин. Пожалуйста, проверьте настройки группы."),
                    duration=5000
                )
                self.page.snack_bar.open = True
            else:
                # Создаем новые опции для выпадающего списка
                self.discipline_dropdown.options = [ft.dropdown.Option(d) for d in disciplines]
                # Если текущее значение есть в списке дисциплин, оставляем его
                if self.discipline_dropdown.value not in disciplines:
                    self.discipline_dropdown.value = disciplines[0]
            
            # Обновляем форму
            if self.ui_content.controls:
                self.ui_content.controls[0] = self.build_note_form_container()
            else:
                self.ui_content.controls.append(self.build_note_form_container())
            
            self.page.update()
            logging.info("Disciplines dropdown updated successfully")
        except Exception as e:
            logging.error(f"Error updating disciplines: {e}")
            # Показываем уведомление об ошибке
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Ошибка при обновлении списка дисциплин"),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()

    def add_note(self, e):
        """Добавление новой заметки через UI"""
        def notify_callback(message):
            self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
            self.page.snack_bar.open = True
            self.page.update()

        if self.manager.add_note(
            discipline=self.discipline_dropdown.value,
            mode=self.mode_dropdown.value,
            text=self.note_text.value,
            notify_callback=notify_callback
        ):
            self.note_text.value = ""
            self.update_notes_list()
            self.page.update()

    def edit_note(self, note: Dict):
        """Открывает диалоговое окно для редактирования заметки"""
        try:
            logging.info(f"Editing note: {note}")
            edit_text = ft.TextField(label="Текст заметки", value=note["text"], multiline=True, width=300)
            edit_mode = ft.Dropdown(
                label="Режим",
                options=[
                    ft.dropdown.Option("Лекция"),
                    ft.dropdown.Option("Практика"),
                    ft.dropdown.Option("Лабораторная"),
                    ft.dropdown.Option("До следующей пары")
                ],
                value=note["mode"],
                width=300
            )

            def save_changes(e):
                def notify_callback(message):
                    self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
                    self.page.snack_bar.open = True
                    self.page.update()

                if self.manager.edit_note(note["index"], edit_text.value, edit_mode.value, notify_callback):
                    self.update_notes_list()
                    self.page.dialog.open = False
                    self.page.update()

            def cancel_changes(e):
                self.page.dialog.open = False
                self.page.update()
                logging.info("Edit dialog cancelled")

            dialog = ft.AlertDialog(
                title=ft.Text("Редактировать заметку"),
                content=ft.Column([edit_text, edit_mode], tight=True),
                actions=[
                    ft.TextButton("Сохранить", on_click=save_changes),
                    ft.TextButton("Отмена", on_click=cancel_changes)
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                modal=True
            )
            self.page.dialog = dialog
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            logging.info("Edit dialog opened")
        except Exception as e:
            logging.error(f"Error opening edit dialog: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Ошибка при открытии редактирования"),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()

    def extend_validity(self, index: int):
        """Продлевает актуальность заметки через UI"""
        def notify_callback(message):
            self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
            self.page.snack_bar.open = True
            self.page.update()

        if self.manager.extend_validity(index, notify_callback):
            self.update_notes_list()
            self.page.update()

    def delete_note(self, note: Dict):
        """Удаляет заметку через UI"""
        self.manager.delete_note(note["index"])
        self.update_notes_list()
        self.page.update()

    def update_notes_list(self):
        """Обновление списка заметок"""
        self.notes_list.controls.clear()
        today = datetime.datetime.now().date()
        tomorrow = today + datetime.timedelta(days=1)
        seven_days_ago = today - datetime.timedelta(days=7)

        for index, note in enumerate(self.manager.notes):
            # Добавляем индекс в словарь заметки
            note_with_index = note.copy()
            note_with_index["index"] = index
            
            valid_until = note.get("valid_until", "Неизвестно")
            indicator_color = ft.Colors.GREEN
            if valid_until == "Неизвестно":
                indicator_color = ft.Colors.GREEN
            else:
                try:
                    valid_date = datetime.datetime.strptime(valid_until, "%d.%m.%Y").date()
                    if valid_date < seven_days_ago:
                        indicator_color = ft.Colors.GREY
                    elif valid_date < today:
                        indicator_color = ft.Colors.RED
                    elif valid_date == today or valid_date == tomorrow:
                        indicator_color = ft.Colors.YELLOW
                    else:
                        indicator_color = ft.Colors.GREEN
                except ValueError:
                    indicator_color = ft.Colors.GREEN
                    logging.error(f"Invalid valid_until format: {valid_until}")

            self.notes_list.controls.append(
                self.create_note_card(note_with_index)
            )
        self.page.update()
        logging.info(f"Notes list updated, total notes: {len(self.manager.notes)}")

    def create_note_card(self, note: Dict):
        # Определяем цвет индикатора актуальности
        today = datetime.datetime.now().date()
        valid_until = note.get("valid_until", "Неизвестно")
        indicator_color = ft.Colors.GREEN
        
        if valid_until != "Неизвестно":
            try:
                valid_date = datetime.datetime.strptime(valid_until, "%d.%m.%Y").date()
                if valid_date < today:
                    indicator_color = ft.Colors.RED
                elif valid_date == today:
                    indicator_color = ft.Colors.YELLOW
            except ValueError:
                logging.error(f"Invalid valid_until format: {valid_until}")

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            width=4,
                            height=40,
                            bgcolor=indicator_color,
                            border_radius=ft.border_radius.all(4)
                        ),
                        ft.Column([
                            ft.Text(
                                note.get("text", "").split("\n")[0][:50] + "..." if len(note.get("text", "").split("\n")[0]) > 50 else note.get("text", "").split("\n")[0],
                                weight=ft.FontWeight.BOLD,
                                size=16,
                                color=ft.Colors.ON_SURFACE
                            ),
                            ft.Text(
                                f"Дисциплина: {note.get('discipline', 'Не указана')}",
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT
                            ),
                            ft.Text(
                                f"Режим: {note.get('mode', 'Не указан')}",
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT
                            ),
                            ft.Text(
                                f"Актуально до: {valid_until}",
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT
                            ),
                        ], spacing=2)
                    ], spacing=10),
                    ft.Text(
                        note.get("text", ""),
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT
                    ),
                    ft.Row([
                        ft.TextButton(
                            "Следующая пара",
                            icon=ft.Icons.NEXT_PLAN,
                            on_click=lambda e, idx=note["index"]: self.extend_validity(idx)
                        ),
                        ft.TextButton(
                            "Редактировать",
                            icon=ft.Icons.EDIT,
                            on_click=lambda e, n=note: self.edit_note(n)
                        ),
                        ft.TextButton(
                            "Удалить",
                            icon=ft.Icons.DELETE,
                            on_click=lambda e, idx=note["index"]: self.delete_note({"index": idx})
                        )
                    ], alignment=ft.MainAxisAlignment.END)
                ], spacing=5),
                padding=15
            ),
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=10),
            color=ft.Colors.SURFACE
        )

    def build(self):
        """Создает основной интерфейс заметок"""
        return ft.Column([
            self.ui_content,
            self.notes_list
        ], expand=True)