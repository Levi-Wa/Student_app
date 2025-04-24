import flet as ft
import json
import os
import logging
import datetime
from typing import List, Dict


class NotesView:
    def __init__(self, page: ft.Page, schedule_tab, app):
        self.page = page
        self.schedule_tab = schedule_tab
        self.app = app
        self.notes_file = "notes.json"
        self.notes = self.load_notes()
        self.ui_content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.notes_list = ft.ListView(expand=True)
        self.ui_content.controls = [self.build_note_form(), self.notes_list]
        self.update_notes_list()
        logging.info("NotesView initialized")

    def build_note_form(self):
        """Создаём форму для добавления заметки"""
        disciplines = self.schedule_tab.get_unique_disciplines()
        logging.info(f"Disciplines in build_note_form: {disciplines}")
        if not disciplines:
            logging.warning("No disciplines available")
            discipline_options = [ft.dropdown.Option("Нет дисциплин")]
            discipline_value = "Нет дисциплин"
        else:
            discipline_options = [ft.dropdown.Option(d) for d in disciplines]
            discipline_value = disciplines[0]

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
        add_button = ft.ElevatedButton(
            text="Добавить",
            on_click=self.add_note
        )

        return ft.Container(padding=ft.padding.symmetric(horizontal=20,vertical=20),
            content=ft.Column([
                self.discipline_dropdown,
                self.mode_dropdown,
                self.note_text,
                add_button
            ], alignment=ft.MainAxisAlignment.CENTER)
                            )

    def get_next_lesson_date(self, discipline: str, mode: str, current_valid_until: str = None) -> str:
        """Находим дату следующего занятия по дисциплине и режиму после текущей даты или valid_until"""
        today = datetime.datetime.now().date()
        reference_date = today
        if current_valid_until and current_valid_until != "Неизвестно":
            try:
                reference_date = datetime.datetime.strptime(current_valid_until, "%d.%m.%Y").date()
            except ValueError:
                logging.error(f"Invalid current_valid_until format: {current_valid_until}")

        next_date = None
        mode_mapping = {
            "Лекция": "Лекция",
            "Практика": "Практ зан",
            "Лабораторная": "Лабор",
            "До следующей пары": None  # Любой тип занятия
        }
        target_mode = mode_mapping.get(mode)

        for schedule in self.schedule_tab.schedules:
            if "error" in schedule:
                continue
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_pair = day.get("datePair", "")
                    try:
                        day_date = datetime.datetime.strptime(date_pair, "%d.%m.%Y").date()
                        if day_date <= reference_date:
                            continue
                        for lesson in day.get("mainSchedule", []):
                            if lesson.get("SubjName") == discipline:
                                if target_mode is None or lesson.get("LoadKindSN") == target_mode:
                                    if not next_date or day_date < next_date:
                                        next_date = day_date
                    except ValueError:
                        logging.error(f"Invalid date format: {date_pair}")

        if next_date is None:
            logging.warning(f"No upcoming lessons found for {discipline} ({mode}) after {reference_date}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Нет предстоящих занятий по {discipline} ({mode})"),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
            return "Неизвестно"
        return next_date.strftime("%d.%m.%Y")

    def load_notes(self) -> List[Dict]:
        """Загрузка заметок из файла"""
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading notes: {e}")
        return []

    def save_notes(self):
        """Сохранение заметок в файл"""
        try:
            with open(self.notes_file, "w", encoding="utf-8") as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Error saving notes: {e}")

    def add_note(self, e):
        """Добавление новой заметки"""
        if not self.note_text.value or self.discipline_dropdown.value == "Нет дисциплин":
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Заполните текст заметки и выберите дисциплину!"),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        note = {
            "discipline": self.discipline_dropdown.value,
            "mode": self.mode_dropdown.value,
            "text": self.note_text.value,
            "valid_until": self.get_next_lesson_date(self.discipline_dropdown.value, self.mode_dropdown.value)
        }
        self.notes.append(note)
        self.save_notes()
        self.note_text.value = ""
        self.update_notes_list()
        self.page.update()
        logging.info(f"Note added: {note}")

    def edit_note(self, index: int):
        """Открывает диалоговое окно для редактирования заметки"""
        try:
            note = self.notes[index]
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
                try:
                    note["text"] = edit_text.value
                    note["mode"] = edit_mode.value
                    note["valid_until"] = self.get_next_lesson_date(note["discipline"], edit_mode.value,
                                                                    note["valid_until"])
                    logging.info(
                        f"Updated validity for {note['discipline']} with mode {edit_mode.value}: {note['valid_until']}")
                    self.save_notes()
                    self.update_notes_list()
                    self.page.dialog.open = False
                    self.page.update()
                    logging.info(f"Note edited: {note}")
                except Exception as e:
                    logging.error(f"Error saving note changes: {e}")
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Ошибка при сохранении изменений"),
                        duration=3000
                    )
                    self.page.snack_bar.open = True
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
        """Продлевает актуальность заметки до следующей пары"""
        try:
            note = self.notes[index]
            logging.info(f"Extending validity for note at index {index}: {note}")
            if note["discipline"] != "Нет дисциплин":
                note["valid_until"] = self.get_next_lesson_date(note["discipline"], "До следующей пары",
                                                                note["valid_until"])
                logging.info(f"Extended validity for {note['discipline']} to next lesson: {note['valid_until']}")
                self.save_notes()
                self.update_notes_list()
                self.page.update()
            else:
                logging.warning("Cannot extend validity: No discipline selected")
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Невозможно продлить: дисциплина не выбрана"),
                    duration=3000
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            logging.error(f"Error extending validity: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Ошибка при продлении актуальности"),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()

    def delete_note(self, index: int):
        """Удаляет заметку по индексу"""
        note = self.notes.pop(index)
        self.save_notes()
        self.update_notes_list()
        self.page.update()
        logging.info(f"Note deleted: {note}")

    def update_notes_list(self):
        """Обновление списка заметок"""
        self.notes_list.controls.clear()
        today = datetime.datetime.now().date()
        tomorrow = today + datetime.timedelta(days=1)
        seven_days_ago = today - datetime.timedelta(days=7)

        for index, note in enumerate(self.notes):
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
        logging.info(f"Notes list updated, total notes: {len(self.notes)}")