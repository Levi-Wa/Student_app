import flet as ft
import datetime
import asyncio
import httpx
import pytz
import weakref  # Добавляем модуль для слабых ссылок

class ScheduleTab(ft.Column):
    def __init__(self, page):
        super().__init__(expand=True)
        self.page_ref = weakref.ref(page)  # Используем слабую ссылку на страницу
        self.group_ids = []
        self.selected_period = "Неделя"
        self.selected_day = None
        self.loading = False
        self.init_ui()

    @property
    def page(self):
        # Получаем страницу через слабую ссылку
        return self.page_ref() if self.page_ref else None

    def init_ui(self):
        # Убраны явные ссылки на self.page в дочерних элементах
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
            icon=ft.icons.REFRESH,
            on_click=self.refresh_schedule
        )

        self.schedule_output = ft.Column(
            scroll=ft.ScrollMode.ALWAYS,
            expand=True
        )

        self.loading_indicator = ft.ProgressBar(visible=False)
        self.error_display = ft.Text("", color="red", visible=False)

        self.controls = [
            ft.Row([
                ft.Text("Расписание", size=20),
                self.period_dropdown,
                self.refresh_button
            ]),
            self.loading_indicator,
            self.error_display,
            self.schedule_output
        ]


    async def on_period_change(self, e):
        """Обработчик изменения периода"""
        self.selected_period = e.control.value
        await self.refresh_schedule()

    async def refresh_schedule(self, e=None):
        """Обновление расписания"""
        if not self.group_ids:
            self.show_message("Выберите группы в настройках")
            return

        self.set_loading(True)
        
        try:
            schedules = await self.fetch_schedules()
            await self.display_schedules(schedules)
        except Exception as ex:
            self.show_error(f"Ошибка загрузки: {str(ex)}")
        finally:
            self.set_loading(False)

    def set_loading(self, loading: bool):
        """Управление состоянием загрузки"""
        self.loading = loading
        self.loading_indicator.visible = loading
        self.error_display.visible = False
        self.schedule_output.visible = not loading
        self.loading_indicator.update()

    async def fetch_schedules(self):
        """Получение данных с API"""
        async with httpx.AsyncClient() as client:
            tasks = []
            for group_id in self.group_ids:
                url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
                tasks.append(self.fetch_group_schedule(client, url))
            return await asyncio.gather(*tasks)

    async def fetch_group_schedule(self, client, url):
        """Получение расписания для одной группы"""
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as ex:
            return {"error": str(ex)}

    async def display_schedules(self, schedules):
        """Отображение расписания"""
        self.schedule_output.controls.clear()
        current_date = datetime.date.today()
        tomorrow_date = current_date + datetime.timedelta(days=1)
        scroll_target = None

        for group_id, schedule in zip(self.group_ids, schedules):
            if "error" in schedule:
                self.schedule_output.controls.append(
                    ft.Text(f"Ошибка для группы {group_id}: {schedule['error']}", color="red")
                )
                continue

            group_container = self.create_group_container(group_id, schedule, current_date, tomorrow_date)
            self.schedule_output.controls.append(group_container)

        await self.schedule_output.update_async()

        if scroll_target:
            await self.page.scroll_to_async(scroll_target, duration=500)

    def create_group_container(self, group_id, schedule, current_date, tomorrow_date):
        group_column = ft.Column(expand=True)  # Растягиваем колонку
        group_column.controls.append(
            ft.Text(f"Группа ID: {group_id}", size=16, weight="bold")
        )

        for month in schedule.get("Month", []):
            for day in month.get("Sched", []):
                day_card = self.create_day_card(day, current_date, tomorrow_date)
                if day_card:
                    group_column.controls.append(day_card)

        return ft.Container(
            content=group_column,
            padding=10,
            border=ft.border.all(1, "#e0e0e0"),
            border_radius=5,
            margin=5,
            expand=True  # Растягиваем контейнер
        )

    def create_day_card(self, day, current_date, tomorrow_date):
        try:
            date_str = day.get("datePair", "")
            day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            day_week = day.get("dayWeek", "")

            color = self.get_date_color(day_date, current_date, tomorrow_date)
            lessons = self.create_lessons(day.get("mainSchedule", []))

            return ft.Container(
                content=ft.Column([
                    ft.Text(f"📅 {date_str} ({day_week})", weight="bold", color=color),
                    lessons
                ]),
                padding=10,
                margin=5,
                expand=True  # Растягиваем карточку
            )
        except Exception as ex:
            return ft.Text(f"Ошибка обработки дня: {str(ex)}", color="red")

    def get_date_color(self, day_date, current_date, tomorrow_date):
        """Определение цвета даты"""
        if day_date == current_date:
            return "green"
        if day_date == tomorrow_date:
            return "blue"
        if day_date < current_date:
            return "grey"
        return None

    def create_lessons(self, lessons_data):
        """Создание списка занятий"""
        return ft.Column([
            self.create_lesson_row(lesson) for lesson in lessons_data
        ])

    def create_lesson_row(self, lesson):
        """Создание строки занятия"""
        return ft.Row([
            ft.Text(lesson.get("TimeStart", ""), width=60),
            ft.Column([
                ft.Text(lesson.get("SubjName", ""), weight="bold"),
                ft.Text(lesson.get("LoadKindSN", ""), size=12, color="grey")
            ], expand=2),
            ft.Text(lesson.get("Aud", ""), width=60),
            ft.Text(lesson.get("FIO", ""), width=150, size=12)
        ], spacing=10)

    def show_error(self, message):
        """Отображение ошибки"""
        self.error_display.value = message
        self.error_display.visible = True
        self.error_display.update()

    def show_message(self, message):
        """Отображение информационного сообщения"""
        self.schedule_output.controls = [ft.Text(message)]
        self.schedule_output.update()

    async def set_groups(self, group_ids, selected_day):
        """Установка выбранных групп"""
        self.group_ids = group_ids
        self.selected_day = selected_day
        await self.refresh_schedule()

    async def check_schedule_at_5pm(self):
        chelyabinsk_tz = pytz.timezone('Asia/Yekaterinburg')
        while True:
            now = datetime.datetime.now(chelyabinsk_tz)
            target_time = now.replace(hour=17, minute=0, second=0)
            
            if now > target_time:
                target_time += datetime.timedelta(days=1)
            
            await asyncio.sleep((target_time - now).total_seconds())
            if self.page:  # Проверяем существование страницы
                await self.refresh_schedule()