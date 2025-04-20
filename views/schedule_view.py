import flet as ft
import datetime
import asyncio
import httpx
import pytz

class ScheduleTab(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.group_ids = []
        self.selected_day = datetime.date.today()
        self.selected_period = "Неделя"
        self.loading = False
        self.content = self.build()

    async def did_mount(self):
        self.page.on_view_pop = self.on_tab_ready
        self.page.run_task(self.check_schedule_at_5pm)

    async def set_groups(self, group_ids, selected_day):
        self.group_ids = group_ids
        self.selected_day = selected_day
        await self.refresh_schedule()


    def build(self):
        # Инициализация интерфейса
        self.period_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Сегодня"),
                ft.dropdown.Option("Неделя"),
                ft.dropdown.Option("Месяц"),
                ft.dropdown.Option("Все")
            ],
            value=self.selected_period,
            on_change=lambda e: asyncio.create_task(self.on_period_change(e)),
            width=150,
            border_color="#2196F3",
            focused_border_color="#1976D2",
            filled=True,
            bgcolor="#E3F2FD"
        )

        self.refresh_button = ft.ElevatedButton(
            "Обновить",
            icon=ft.icons.REFRESH,
            on_click=lambda e: asyncio.create_task(self.refresh_schedule())
            # Используем create_task для асинхронного вызова
        )

        self.schedule_output = ft.Column(
            scroll=ft.ScrollMode.ALWAYS,
            expand=True
        )

        # Инициализация индикатора загрузки
        self.loading_indicator = ft.ProgressBar(visible=False)

        # Инициализация отображения ошибок
        self.error_display = ft.Text("", color="red", visible=False)

        # Возвращаем основной интерфейс
        return ft.Column([
            ft.Row([
                ft.Text("Расписание", size=20),
                self.period_dropdown,
                self.refresh_button
            ]),
            self.loading_indicator,  # Теперь индикатор загрузки добавлен в интерфейс
            self.error_display,
            self.schedule_output
        ], expand=True)

    async def on_tab_ready(self, e):
        await asyncio.sleep(0.1)  # Подождать, пока build() отработает
        await self.refresh_schedule()
        await self.check_schedule_at_5pm()

    def set_loading(self, loading: bool):
        self.loading = loading
        if not hasattr(self, "error_display") or not hasattr(self, "schedule_output"):# Проверка, если атрибут существует
            return
        self.loading_indicator.visible = loading
        self.error_display.visible = False
        self.schedule_output.visible = not loading
        self.page.update()  # Обновляем страницу после изменения состояния загрузки

    async def refresh_schedule(self):
        if hasattr(self, "error_display") and not self.group_ids:
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

    async def fetch_schedules(self):
        async with httpx.AsyncClient() as client:
            tasks = []
            for group_id in self.group_ids:
                url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
                tasks.append(self.fetch_group_schedule(client, url))
            return await asyncio.gather(*tasks)

    async def fetch_group_schedule(self, client, url):
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            if not data.get("Month"):  # Проверка на пустые данные
                return {"error": "Расписание пустое"}
            return data
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error: {e.response.status_code}"}
        except Exception as ex:
            return {"error": str(ex)}

    async def display_schedules(self, schedules):
        self.schedule_output.controls.clear()
        current_date = datetime.date.today()
        tomorrow_date = current_date + datetime.timedelta(days=1)

        for group_id, schedule in zip(self.group_ids, schedules):
            if "error" in schedule:
                self.schedule_output.controls.append(
                    ft.Text(f"Ошибка для группы {group_id}: {schedule['error']}", color="red")
                )
                continue

            group_container = self.create_group_container(group_id, schedule, current_date, tomorrow_date)
            self.schedule_output.controls.append(group_container)

        self.update()

    def create_group_container(self, group_id, schedule, current_date, tomorrow_date):
        group_column = ft.Column(expand=True)
        group_column.controls.append(
            ft.Text(f"Группа ID: {group_id}", size=16, weight="bold")
        )

        for month in schedule.get("Month", []):
            for day in month.get("Sched", []):
                date_str = day.get("datePair", "")
                if not date_str:
                    continue
                day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

                # Фильтрация по выбранному периоду
                if self.selected_period == "Сегодня" and day_date != current_date:
                    continue
                elif self.selected_period == "Неделя" and (day_date - current_date).days > 7:
                    continue
                elif self.selected_period == "Месяц" and not (current_date.month == day_date.month):
                    continue
                elif self.selected_period == "Все" and day_date < current_date:
                    continue

                day_card = self.create_day_card(day, current_date, tomorrow_date)
                if day_card:
                    group_column.controls.append(day_card)

        return ft.Container(
            content=group_column,
            padding=10,
            border=ft.border.all(1, "#e0e0e0"),
            border_radius=5,
            margin=5,
            expand=True
        )

    def create_day_card(self, day, current_date, tomorrow_date):
        try:
            date_str = day.get("datePair", "")
            if not date_str:
                return ft.Text("Дата не указана", color="red")
            day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            day_week = day.get("dayWeek", "")

            color = self.get_date_color(day_date, current_date, tomorrow_date)
            lessons = self.create_lessons(day.get("mainSchedule", []))

            return ft.Container(
                content=ft.Column([ft.Text(f"📅 {date_str} ({day_week})", weight="bold", color=color), lessons]),
                padding=10,
                margin=5,
                expand=True
            )
        except Exception as ex:
            return ft.Text(f"Ошибка обработки дня: {str(ex)}", color="red")

    def get_date_color(self, day_date, current_date, tomorrow_date):
        if day_date == current_date:
            return "green"
        if day_date == tomorrow_date:
            return "blue"
        if day_date < current_date:
            return "grey"
        return None

    def create_lessons(self, lessons_data):
        return ft.Column([self.create_lesson_row(lesson) for lesson in lessons_data])

    def create_lesson_row(self, lesson):
        return ft.Container(
            content=ft.Row([
                ft.Text(lesson.get("TimeStart", ""), width=80),
                ft.Column([
                    ft.Text(lesson.get("SubjName", ""), weight="bold"),
                    ft.Text(lesson.get("LoadKindSN", ""), size=12, color="grey")
                ], expand=2),
                ft.Text(lesson.get("Aud", ""), width=80),
                ft.Text(lesson.get("FIO", ""), width=200, size=12)
            ], spacing=10),
            padding=5,
            border=ft.border.all(0.5, "#e0e0e0"),
            margin=2
        )

    def show_error(self, message):
        if hasattr(self, "error_display"):
            self.error_display.value = message
            self.error_display.visible = True
        self.update()

    def show_message(self, message):
        self.schedule_output.controls = [ft.Text(message)]
        self.update()

    async def check_schedule_at_5pm(self):
        chelyabinsk_tz = pytz.timezone('Asia/Yekaterinburg')
        while True:
            now = datetime.datetime.now(chelyabinsk_tz)
            target_time = now.replace(hour=17, minute=0, second=0)

            if now > target_time:
                target_time += datetime.timedelta(days=1)

            await asyncio.sleep((target_time - now).total_seconds())
            if self.page:
                await self.refresh_schedule()
