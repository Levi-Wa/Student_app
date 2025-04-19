import flet as ft
import httpx
import asyncio
import datetime
from typing import List
import pytz  # Для работы с временными зонами


class ScheduleTab(ft.Column):
    def __init__(self):
        super().__init__(expand=True)
        self.group_ids = []
        self.loading = False
        self.selected_period = "Сегодня"  # По умолчанию выбран "Сегодня"
        self.previous_schedules = []  # Для хранения предыдущих расписаний
        self.selected_day = None  # Дата выбранного дня

        # Инициализация UI
        self.schedule_output = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        self.period_buttons = ft.RadioGroup(
            content=[
                ft.Radio(value="Сегодня", label="Сегодня"),
                ft.Radio(value="Неделя", label="Неделя"),
                ft.Radio(value="Месяц", label="Месяц"),
                ft.Radio(value="Все", label="Все")
            ],
            value=self.selected_period,
            on_change=self.on_period_change
        )

        self.refresh_button = ft.ElevatedButton(
            "Обновить",
            icon=ft.icons.REFRESH,
            on_click=self.refresh_schedule
        )

        self.controls = [
            ft.Row([ft.Text("Расписание", size=20), self.period_buttons, self.refresh_button]),
            self.schedule_output
        ]

    def on_period_change(self, e):
        """Обработчик изменения периода"""
        self.selected_period = e.control.value
        asyncio.create_task(self.refresh_schedule())

    async def refresh_schedule(self, e=None):
        """Загружает расписание для выбранных групп"""
        if not self.group_ids:
            self.schedule_output.controls = [ft.Text("Группы не выбраны")]
            await self.schedule_output.update()
            return

        self.loading = True
        self.schedule_output.controls = [ft.ProgressBar(), ft.Text("Загрузка расписания...")]
        await self.schedule_output.update()

        try:
            schedules = await self.fetch_schedules()
            if self.previous_schedules:
                changes = self.compare_schedules(self.previous_schedules, schedules)
                if changes:
                    await self.display_changes(changes)

            await self.display_schedules(schedules)
            self.previous_schedules = schedules  # Сохраняем новое расписание

        except Exception as ex:
            self.schedule_output.controls = [ft.Text(f"Ошибка: {str(ex)}", color="red")]
            await self.schedule_output.update()
        finally:
            self.loading = False

    async def fetch_schedules(self):
        """Получает расписание с API"""
        async with httpx.AsyncClient() as client:
            tasks = []
            for group_id in self.group_ids:
                url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
                tasks.append(self.fetch_group_schedule(client, url))
            return await asyncio.gather(*tasks)

    async def fetch_group_schedule(self, client, url):
        """Получает расписание для одной группы"""
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as ex:
            return {"error": str(ex)}

    async def display_schedules(self, schedules):
        """Отображает расписание в интерфейсе"""
        self.schedule_output.controls = []

        current_date = datetime.date.today()
        tomorrow_date = current_date + datetime.timedelta(days=1)

        # Если сегодня выходной, то сдвигаем на следующий рабочий день
        if current_date.weekday() >= 5:  # 5 - суббота, 6 - воскресенье
            current_date += datetime.timedelta(days=(7 - current_date.weekday()))  # Переводим на понедельник

        for group_id, schedule in zip(self.group_ids, schedules):
            if "error" in schedule:
                self.schedule_output.controls.append(ft.Text(f"Ошибка для группы {group_id}: {schedule['error']}", color="red"))
                continue

            group_schedule = ft.Column()
            group_schedule.controls.append(ft.Text(f"Группа ID: {group_id}", size=16, weight="bold"))

            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    day_card = self.create_day_card(day, current_date, tomorrow_date)
                    group_schedule.controls.append(day_card)

            self.schedule_output.controls.append(
                ft.Container(content=group_schedule, padding=10, border=ft.border.all(1, "#e0e0e0"), border_radius=5, margin=5)
            )

        await self.schedule_output.update()

    def create_day_card(self, day, current_date, tomorrow_date):
        """Создает карточку дня"""
        date_str = day.get("datePair", "")
        day_week = day.get("dayWeek", "")
        day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

        color = "grey"  # По умолчанию серый

        if day_date == current_date:
            color = "green"  # Сегодняшний день — зеленым
        elif day_date == tomorrow_date:
            color = "blue"  # Завтрашний день — синим
        elif day_date < current_date:
            color = "grey"  # Прошедший день — серым

        lessons = ft.Column()
        for lesson in day.get("mainSchedule", []):
            lessons.controls.append(self.create_lesson_row(lesson))

        return ft.Container(
            content=ft.Column([ft.Text(f"📅 {date_str} ({day_week})", weight="bold", color=color), lessons]),
            padding=10,
            margin=5
        )

    def create_lesson_row(self, lesson):
        """Создает строку с информацией о занятии"""
        return ft.Row([
            ft.Text(lesson.get("TimeStart", ""), width=60),
            ft.Column([ft.Text(lesson.get("SubjName", ""), weight="bold"), ft.Text(lesson.get("LoadKindSN", ""), size=12, color="grey")], expand=2),
            ft.Text(lesson.get("Aud", ""), width=60),
            ft.Text(lesson.get("FIO", ""), width=150, size=12)
        ], spacing=10)

    def compare_schedules(self, old_schedules, new_schedules):
        """Сравнивает старое и новое расписание и возвращает изменения"""
        changes = []
        for old, new in zip(old_schedules, new_schedules):
            if old != new:  # Если расписания изменились
                changes.append({"old": old, "new": new})
        return changes

    async def display_changes(self, changes):
        """Отображает изменения в расписании"""
        for change in changes:
            self.schedule_output.controls.append(
                ft.Text(f"Изменение расписания: {change}", color="red")
            )
        await self.schedule_output.update()

    async def check_schedule_at_3am(self):
        """Проверяет расписание каждый день в 3:00 по МСК"""
        # Настроим временную зону для Москвы
        moscow_tz = pytz.timezone('Europe/Moscow')
        
        while True:
            now = datetime.datetime.now(moscow_tz)
            target_time = now.replace(hour=3, minute=0, second=0, microsecond=0)
            
            if now > target_time:
                target_time += datetime.timedelta(days=1)  # Если 3:00 уже прошло, назначаем на завтра

            time_to_wait = (target_time - now).total_seconds()
            await asyncio.sleep(time_to_wait)  # Засыпаем до 3:00 по МСК

            # После того, как время наступило, проверяем расписание
            await self.refresh_schedule()
