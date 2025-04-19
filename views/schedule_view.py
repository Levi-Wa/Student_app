import flet as ft
import datetime
import asyncio
import httpx
import pytz

class ScheduleTab(ft.Column):
    def __init__(self, page):
        super().__init__(expand=True)  # Растягиваем колонку
        self.page = page
        self.group_ids = []  # ID выбранных групп
        self.selected_period = "Неделя"  # По умолчанию выбран "Сегодня"
        self.selected_day = None  # Дата выбранного дня

        # Инициализация UI
        self.schedule_output = ft.Column(
            scroll=ft.ScrollMode.ALWAYS,  # Включаем прокрутку
            expand=True # Колонка будет расширяться в зависимости от контента 
        )

        self.period_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Сегодня"),
                ft.dropdown.Option("Неделя"),
                ft.dropdown.Option("Месяц"),
                ft.dropdown.Option("Все")
            ],
            value=self.selected_period,
            on_change=self.on_period_change,
            width=150
        )

        self.refresh_button = ft.ElevatedButton(
            "Обновить",
            icon=ft.Icons.REFRESH,
            on_click=self.refresh_schedule
        )

        # Добавляем элементы в UI
        self.controls = [
            ft.Row([ft.Text("Расписание", size=20), self.period_dropdown, self.refresh_button]),
            self.schedule_output
        ]
        self.page.add(self)
        self.page.update()  # Обновляем страницу, добавляем элементы

    def on_period_change(self, e):
        """Обработчик изменения периода"""
        self.selected_period = e.control.value
        self.page.run_task(self.refresh_schedule)  # Без скобок!

    async def refresh_schedule(self, e=None):
        if not self.group_ids:
            self.schedule_output.controls = [ft.Text("Группы не выбраны")]
            self.page.update()  # Обновляем страницу
            return

        try:
            schedules = await self.fetch_schedules()
            await self.display_schedules(schedules)
        except Exception as ex:
            self.schedule_output.controls = [ft.Text(f"Ошибка: {str(ex)}", color="red")]
        finally:
            self.page.update()

    async def fetch_schedules(self):
        """Получает расписание с API"""
        async with httpx.AsyncClient() as client:
            tasks = [
                self.fetch_group_schedule(client, f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}")
                for group_id in self.group_ids
            ]
            return await asyncio.gather(*tasks)

    async def fetch_group_schedule(self, client, url):
        """Получает расписание для одной группы"""
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as ex:
            return {"error": str(ex)}

    async def display_schedules(self, schedules):
        self.schedule_output.controls = []
        current_date = datetime.date.today()
        tomorrow_date = current_date + datetime.timedelta(days=1)
        scroll_target = None  # Контейнер с ближайшей датой

        for group_id, schedule in zip(self.group_ids, schedules):
            if "error" in schedule:
                self.schedule_output.controls.append(
                    ft.Text(f"Ошибка для группы {group_id}: {schedule['error']}", color="red"))
                continue

            group_schedule = ft.Column([ft.Text(f"Группа ID: {group_id}", size=16, weight="bold")])

            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    day_card = self.create_day_card(day, current_date, tomorrow_date)

                    # Найти первую дату сегодня или позже — запомнить для скролла
                    try:
                        date_str = day.get("datePair", "")
                        day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                        if day_date >= current_date and scroll_target is None:
                            scroll_target = day_card
                    except:
                        pass

                    group_schedule.controls.append(day_card)

            self.schedule_output.controls.append(
                ft.Container(
                    content=group_schedule,
                    padding=10,
                    border=ft.border.all(1, "#e0e0e0"),
                    border_radius=5,
                    margin=5
                )
            )

        self.page.update()

        # Прокрутка к ближайшей дате
        if scroll_target:
            self.page.scroll_to(scroll_target, duration=500)

    def create_day_card(self, day, current_date, tomorrow_date):
        """Создает карточку дня"""
        try:
            date_str = day.get("datePair", "")
            day_week = day.get("dayWeek", "")
            day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

            color = "grey"
            if day_date == current_date:
                color = "green"
            elif day_date == tomorrow_date:
                color = "blue"

            lessons = ft.Column([self.create_lesson_row(lesson) for lesson in day.get("mainSchedule", [])])

            return ft.Container(
                content=ft.Column([ft.Text(f"📅 {date_str} ({day_week})", weight="bold", color=color), lessons]),
                padding=10,
                margin=5
            )
        except Exception as ex:
            return ft.Text(f"Ошибка обработки дня: {str(ex)}", color="red")

    def create_lesson_row(self, lesson):
        """Создает строку с информацией о занятии"""
        return ft.Row([ft.Text(lesson.get("TimeStart", ""), width=60),
                       ft.Column([ft.Text(lesson.get("SubjName", ""), weight="bold"),
                                  ft.Text(lesson.get("LoadKindSN", ""), size=12, color="grey")], expand=2),
                       ft.Text(lesson.get("Aud", ""), width=60),
                       ft.Text(lesson.get("FIO", ""), width=150, size=12)],
                      spacing=10)

    async def set_groups(self, group_ids, selected_day):
        """Устанавливает группы и выбранный день"""
        self.group_ids = group_ids
        self.selected_day = selected_day
        await self.refresh_schedule()

    async def check_schedule_at_5pm(self):
        """Проверка расписания каждый день в 5:00 по Челябинскому времени"""
        chelyabinsk_tz = pytz.timezone('Asia/Yekaterinburg')
        while True:
            now = datetime.datetime.now(chelyabinsk_tz)
            target_time = now.replace(hour=17, minute=0, second=0, microsecond=0)

            if now > target_time:
                target_time += datetime.timedelta(days=1)

            time_to_wait = (target_time - now).total_seconds()
            await asyncio.sleep(time_to_wait)
            await self.refresh_schedule()
