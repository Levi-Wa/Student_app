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
        self.ui_content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.notes_list = ft.ListView(expand=True)
        self.discipline_dropdown = None
        self.mode_dropdown = None
        self.note_text = None
        self.add_button = None
        self.build_note_form()
        self.ui_content.controls = [self.build_note_form_container(), self.notes_list]
        self.update_notes_list()
        logging.info("NotesUI initialized")

    def build_note_form(self):
        """Создаёт форму для добавления заметки."""
        disciplines = self.schedule_manager.utils.get_unique_disciplines(self.schedule_manager.data.schedules)
        logging.info(f"Disciplines in build_note_form: {disciplines}")
        if not disciplines:
            logging.warning("No disciplines available")
            discipline_options = [ft.dropdown.Option("Нет дисциплин")]
            discipline_value = "Нет дисциплин"
        else:
            discipline_options = [ft.dropdown.Option(d) for d in disciplines]
            discipline_value = disciplines[0] if disciplines else None

        self.discipline_dropdown = ft.Dropdown(
            label="Дисциплина",
            options=discipline_options,
            value=discipline_value,
            width=300,
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
        self.build_note_form()
        self.ui_content.controls[0] = self.build_note_form_container()
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

    def edit_note(self, index: int):
        """Открывает диалоговое окно для редактирования заметки"""
        try:
            note = self.manager.notes[index]
            logging.info(f"Editing note at index {index}: {note}")
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

                if self.manager.edit_note(index, edit_text.value, edit_mode.value, notify_callback):
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

    def delete_note(self, index: int):
        """Удаляет заметку через UI"""
        self.manager.delete_note(index)
        self.update_notes_list()
        self.page.update()

    def update_notes_list(self):
        """Обновление списка заметок"""
        self.notes_list.controls.clear()
        today = datetime.datetime.now().date()
        tomorrow = today + datetime.timedelta(days=1)
        seven_days_ago = today - datetime.timedelta(days=7)

        for index, note in enumerate(self.manager.notes):
            valid_until = note.get("valid_until", "Неизвестно")
            indicator_color = ft.colors.GREEN
            if valid_until == "Неизвестно":
                indicator_color = ft.colors.GREEN
            else:
                try:
                    valid_date = datetime.datetime.strptime(valid_until, "%d.%m.%Y").date()
                    if valid_date < seven_days_ago:
                        indicator_color = ft.colors.GREY
                    elif valid_date < today:
                        indicator_color = ft.colors.RED
                    elif valid_date == today or valid_date == tomorrow:
                        indicator_color = ft.colors.YELLOW
                    else:
                        indicator_color = ft.colors.GREEN
                except ValueError:
                    indicator_color = ft.colors.GREEN
                    logging.error(f"Invalid valid_until format: {valid_until}")

            self.notes_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{note['discipline']} ({note['mode']})", weight="bold"),
                                ft.Text(note['text']),
                                ft.Text(f"Актуально до: {valid_until}"),
                                ft.Row([
                                    ft.IconButton(
                                        ft.icons.EDIT,
                                        on_click=lambda e, idx=index: self.edit_note(idx),
                                        tooltip="Редактировать"
                                    ),
                                    ft.IconButton(
                                        ft.icons.TODAY,
                                        on_click=lambda e, idx=index: self.extend_validity(idx),
                                        tooltip="Продлить актуальность"
                                    ),
                                    ft.IconButton(
                                        ft.icons.DELETE,
                                        on_click=lambda e, idx=index: self.delete_note(idx),
                                        tooltip="Удалить"
                                    )
                                ])
                            ], expand=True),
                            ft.Container(
                                content=ft.CircleAvatar(bgcolor=indicator_color, radius=10),
                                alignment=ft.alignment.center,
                                margin=ft.margin.only(right=10)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10
                    )
                )
            )
        self.page.update()
        logging.info(f"Notes list updated, total notes: {len(self.manager.notes)}")