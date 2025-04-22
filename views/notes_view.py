import flet as ft
import datetime
import json
import os
from typing import List, Dict
from views.schedule_view import ScheduleTab
import asyncio
import pytz

class NotesView:
    def __init__(self, page: ft.Page, schedule_tab: ScheduleTab, app):
        self.page = page
        self.schedule_tab = schedule_tab
        self.app = app
        self.notes_file = "notes.json"
        self.notes = self.load_notes()
        self.disciplines = self.schedule_tab.get_unique_disciplines()
        self.notes_list = ft.Column()
        self.ui_content = self.setup_ui()
        self.page.run_task(self.schedule_expiry_notifications)

    def load_notes(self) -> List[Dict]:
        """Загрузка заметок из файла"""
        if os.path.exists(self.notes_file):
            with open(self.notes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_notes(self):
        """Сохранение заметок в файл"""
        with open(self.notes_file, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=4)

    async def check_expiry_notifications(self):
        """Проверка заметок на срок актуальности"""
        current_date = datetime.date.today()
        expiry_days = int(self.app.settings.get("expiry_notification_days", 3))  # Приводим к int
        for note in self.notes:
            try:
                expiry_date = datetime.datetime.strptime(note["expiry_date"], "%d.%m.%Y").date()
                days_until_expiry = (expiry_date - current_date).days
                if days_until_expiry == expiry_days:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Заметка по дисциплине {note['discipline']} истекает через {days_until_expiry} дня ({note['expiry_date']})!"),
                        duration=5000
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            except ValueError:
                continue

    async def schedule_expiry_notifications(self):
        """Планировщик уведомлений о сроке актуальности в 12:00"""
        local_tz = datetime.datetime.now().astimezone().tzinfo
        while True:
            now = datetime.datetime.now(local_tz)
            target_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
            if now > target_time:
                target_time += datetime.timedelta(days=1)

            seconds_until_notification = (target_time - now).total_seconds()
            print(f"Next expiry notification in {seconds_until_notification} seconds")
            await asyncio.sleep(seconds_until_notification)

            print("Checking for expiring notes...")
            await self.check_expiry_notifications()

    def get_next_lesson_date(self, discipline: str, mode: str) -> datetime.date:
        """Определение даты следующего занятия по дисциплине через ScheduleTab"""
        return self.schedule_tab.get_next_lesson_date(discipline, mode)

    def is_note_actual(self, note: Dict) -> bool:
        """Проверка актуальности заметки"""
        try:
            expiry_date = datetime.datetime.strptime(note["expiry_date"], "%d.%m.%Y").date()
            return expiry_date >= datetime.date.today()
        except ValueError:
            return False

    def create_note_card(self, note: Dict, index: int) -> ft.Container:
        """Создание карточки заметки"""
        is_actual = self.is_note_actual(note)
        indicator_color = "green" if is_actual else "red"

        note_text_field = ft.TextField(
            value=note["text"],
            multiline=True,
            on_change=lambda e, idx=index: self.update_note_text(idx, e.control.value)
        )

        extend_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Продлить актуальность",
            on_click=lambda e, idx=index: self.extend_note_validity(idx)
        )

        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            tooltip="Удалить заметку",
            on_click=lambda e, idx=index: self.delete_note(idx)
        )

        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(f"Дисциплина: {note['discipline']}", size=14, weight="bold"),
                    ft.Text(f"Актуально до: {note['expiry_date']}", size=12),
                    note_text_field
                ], expand=True),
                ft.Row([
                    extend_button,
                    delete_button,
                    ft.Container(
                        width=15,
                        height=15,
                        bgcolor=indicator_color,
                        border_radius=7.5
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10,
            margin=5,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#ddd"),
            border_radius=8
        )

    def setup_ui(self) -> ft.Column:
        """Настройка интерфейса, возвращаем содержимое"""
        discipline_dropdown = ft.Dropdown(
            label="Дисциплина",
            options=[ft.dropdown.Option(dis) for dis in self.disciplines],
            value=self.disciplines[0] if self.disciplines else None,
            width=300,
            text_size=14,
            content_padding=10,
        )

        mode_dropdown = ft.Dropdown(
            label="Режим актуальности",
            options=[
                ft.dropdown.Option("До следующего занятия"),
                ft.dropdown.Option("До следующей практики")
            ],
            value="До следующего занятия",
            width=300,
            text_size=14,
            content_padding=10,
        )

        note_text_field = ft.TextField(
            label="Текст заметки",
            multiline=True,
            width=300,
            text_size=14,
            content_padding=10,
        )

        create_button = ft.ElevatedButton(
            "Создать заметку",
            on_click=lambda e: self.create_note(
                discipline_dropdown.value,
                mode_dropdown.value,
                note_text_field.value
            )
        )

        create_form = ft.Column([
            ft.Text("Создать заметку", size=20, weight="bold"),
            discipline_dropdown,
            mode_dropdown,
            note_text_field,
            create_button
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.notes_list.controls = [self.create_note_card(note, i) for i, note in enumerate(self.notes)]
        return ft.Column([
            create_form,
            ft.Text("Список заметок", size=16, weight="bold"),
            self.notes_list
        ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def create_note(self, discipline: str, mode: str, text: str):
        """Создание новой заметки"""
        if not discipline or not text:
            self.page.snack_bar = ft.SnackBar(ft.Text("Заполните все поля!"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        next_lesson_date = self.get_next_lesson_date(discipline, mode)
        expiry_date = next_lesson_date.strftime("%d.%m.%Y")

        note = {
            "discipline": discipline,
            "mode": mode,
            "text": text,
            "expiry_date": expiry_date
        }

        self.notes.append(note)
        self.save_notes()
        self.notes_list.controls.append(self.create_note_card(note, len(self.notes) - 1))
        self.page.snack_bar = ft.SnackBar(ft.Text("Заметка создана!"))
        self.page.snack_bar.open = True
        self.page.update()

    def update_note_text(self, index: int, new_text: str):
        """Обновление текста заметки"""
        self.notes[index]["text"] = new_text
        self.save_notes()

    def extend_note_validity(self, index: int):
        """Продление актуальности заметки"""
        note = self.notes[index]
        new_expiry_date = self.get_next_lesson_date(note["discipline"], note["mode"])
        note["expiry_date"] = new_expiry_date.strftime("%d.%m.%Y")
        self.save_notes()
        self.notes_list.controls[index] = self.create_note_card(note, index)
        self.page.snack_bar = ft.SnackBar(ft.Text("Актуальность продлена!"))
        self.page.snack_bar.open = True
        self.page.update()

    def delete_note(self, index: int):
        """Удаление заметки"""
        self.notes.pop(index)
        self.save_notes()
        self.notes_list.controls.pop(index)
        self.notes_list.controls = [self.create_note_card(note, i) for i, note in enumerate(self.notes)]
        self.page.snack_bar = ft.SnackBar(ft.Text("Заметка удалена!"))
        self.page.snack_bar.open = True
        self.page.update()

    def build_note_form(self):
        """Создаём форму для добавления заметки"""
        disciplines = self.schedule_tab.get_unique_disciplines()
        if not disciplines:
            print("Warning: No disciplines available")
            discipline_options = [ft.dropdown.Option("Нет дисциплин")]
        else:
            discipline_options = [ft.dropdown.Option(d) for d in disciplines]

        self.discipline_dropdown = ft.Dropdown(
            label="Дисциплина",
            options=discipline_options,
            value=disciplines[0] if disciplines else "Нет дисциплин",
            width=300
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