import flet as ft
import json
import os
import logging
from typing import List, Dict

class NotesView:
    def __init__(self, page: ft.Page, schedule_tab, app):
        self.page = page
        self.schedule_tab = schedule_tab
        self.app = app
        self.notes_file = "notes.json"
        self.notes = self.load_notes()
        self.ui_content = ft.Column()
        self.notes_list = ft.ListView(expand=True)
        self.ui_content.controls = [self.build_note_form(), self.notes_list]
        self.update_notes_list()
        logging.info("NotesView initialized")

    def build_note_form(self):
        """Создаём форму для добавления заметки"""
        import logging
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
                ft.dropdown.Option("Лабораторная")
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

        return ft.Column([
            self.discipline_dropdown,
            self.mode_dropdown,
            self.note_text,
            add_button
        ], alignment=ft.MainAxisAlignment.CENTER)

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
            "text": self.note_text.value
        }
        self.notes.append(note)
        self.save_notes()
        self.note_text.value = ""
        self.update_notes_list()
        self.page.update()
        logging.info(f"Note added: {note}")

    def update_notes_list(self):
        """Обновление списка заметок"""
        self.notes_list.controls.clear()
        for note in self.notes:
            self.notes_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"{note['discipline']} ({note['mode']})", weight="bold"),
                            ft.Text(note['text'])
                        ]),
                        padding=10
                    )
                )
            )
        self.page.update()
        logging.info(f"Notes list updated, total notes: {len(self.notes)}")