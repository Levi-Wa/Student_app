import flet as ft
import datetime
import asyncio
import httpx
import pytz

class ScheduleTab(ft.Control):
    def __init__(self, page: ft.Page, selected_day: datetime.date = None):
        super().__init__()
        self.page = page
        self.group_ids = []
        self.selected_day = selected_day if selected_day is not None else datetime.date.today()
        self.selected_period = "Месяц"
        self.loading = False

        # Дропдаун для выбора периода
        self.period_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Сегодня"),
                ft.dropdown.Option("Неделя"),
                ft.dropdown.Option("Месяц"),
                ft.dropdown.Option("Все")
            ],
            value=self.selected_period,  # Устанавливаем начальное значение
            on_change=self.on_period_change,  # Обработчик изменения
            width=150,
            border_color="#2196F3",
            focused_border_color="#1976D2",
            filled=True,
            bgcolor="#E3F2FD"
        )

        self.schedule_output = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)

        self.loading_indicator = ft.ProgressBar(visible=False)
        self.error_display = ft.Text("", color="red", visible=False)

    def build(self):
        return ft.Column([
            ft.Row([
                ft.Text("📅 Расписание", size=20, weight="bold"),
                self.period_dropdown  # Добавляем дропдаун в интерфейс
            ]),
            self.loading_indicator,
            self.error_display,
            ft.Container(
                content=self.schedule_output,
                expand=True
            )
        ], expand=True)

    async def on_period_change(self, e):
        """Обработчик изменения значения в Dropdown"""
        self.selected_period = e.control.value  # Обновляем выбранный период
        print(f"Выбранный период изменён: {self.selected_period}")
        await self.refresh_schedule()  # Автоматическое обновление расписания
        print("Обновление расписания завершено.")
        self.update()

    async def refresh_schedule(self):
        """Обновляем расписание в зависимости от выбранного периода."""
        # Устанавливаем индикатор загрузки
        self.set_loading(True)

        try:
            # Получаем расписания для всех групп
            schedules = await self.fetch_schedules()

            # Проверяем, есть ли ошибки в полученных расписаниях
            if any("error" in schedule for schedule in schedules):
                self.show_error("Ошибка при получении расписания для одной или нескольких групп.")
                return

            # Отображаем расписание
            await self.display_schedules(schedules)

        except Exception as ex:
            # Обрабатываем любые исключения и показываем сообщение об ошибке
            self.show_error(f"Ошибка загрузки: {str(ex)}")

        finally:
            # Скрываем индикатор загрузки и обновляем интерфейс
            self.set_loading(False)
            self.update()

    async def fetch_group_schedule(self, client, url):
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            if not data.get("Month"):
                return {"error": "Расписание пустое"}
            return data
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error: {e.response.status_code}"}
        except Exception as ex:
            return {"error": str(ex)}

    async def set_groups(self, group_ids, selected_day):
        self.group_ids = group_ids
        self.selected_day = selected_day
        await self.refresh_schedule()

    def set_loading(self, loading: bool):
        self.loading = loading
        self.loading_indicator.visible = loading
        self.error_display.visible = False
        self.schedule_output.visible = not loading
        self.update()  # Перерисовываем компонент

    async def fetch_schedules(self):
        async with httpx.AsyncClient() as client:
            tasks = []
            for group_id in self.group_ids:
                url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
                tasks.append(self.fetch_group_schedule(client, url))
            return await asyncio.gather(*tasks)

    async def display_schedules(self, schedules):
        print(f"Полученные расписания для отображения: {schedules}")  # Отладочное сообщение
        self.schedule_output.controls.clear()
        current_date = self.selected_day  # Используем выбранную дату
        tomorrow = current_date + datetime.timedelta(days=1)

        for group_id, schedule in zip(self.group_ids, schedules):
            if "error" in schedule:
                self.schedule_output.controls.append(
                    ft.Text(f"Ошибка для группы {group_id}: {schedule['error']}", color="red")
                )
                continue

            group_column = ft.Column()
            group_column.controls.append(
                ft.Text(f"Группа ID: {group_id}", size=16, weight="bold")
            )

            # Фильтрация расписания в зависимости от выбранного периода
            if self.selected_period == "Все":
                # Логика для отображения всех данных
                for month in schedule.get("Month", []):
                    # Добавьте логику для отображения всех месяцев
                    pass
            else:
                # Логика для фильтрации по выбранному периоду
                for month in schedule.get("Month", []):
                    for day in month.get("Sched", []):
                        date_str = day.get("datePair", "")
                        if not date_str:
                            continue
                        day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

                        # Фильтрация по выбранному периоду
                        if self.selected_period == "Сегодня" and day_date != current_date:
                            continue
                        elif self.selected_period == "Неделя" and not (0 <= (day_date - current_date).days < 7):
                            continue
                        elif self.selected_period == "Месяц" and (
                                day_date.month != current_date.month or day_date.year != current_date.year):
                            continue

                        day_card = self.create_day_card(day, current_date, tomorrow)
                        group_column.controls.append(day_card)

            self.schedule_output.controls.append(
                ft.Container(content=group_column, padding=10, bgcolor="#f9f9f9", border_radius=10, margin=5)
            )

        self.update()

    def create_day_card(self, day, current_date, tomorrow_date):
        """Создаем карточку для дня"""
        try:
            date_str = day.get("datePair", "")
            if not date_str:
                return ft.Text("Дата не указана", color="red")
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
                bgcolor="#ffffff",
                border=ft.border.all(1, "#ddd"),
                border_radius=8
            )
        except Exception as ex:
            return ft.Text(f"Ошибка дня: {str(ex)}", color="red")

    def get_date_color(self, day_date, current_date, tomorrow_date):
        """Определяем цвет для даты"""
        if day_date == current_date:
            return "green"
        elif day_date == tomorrow_date:
            return "blue"
        elif day_date < current_date:
            return "grey"
        else:
            return None

    def create_lesson_row(self, lesson):
        """Создаем строку для одного урока"""
        return ft.Container(
            content=ft.Row([
                ft.Text(lesson.get("TimeStart", ""), width=80),
                ft.Column([
                    ft.Text(lesson.get("SubjName", ""), weight="bold"),
                    ft.Text(lesson.get("LoadKindSN", ""), size=12, color="grey")
                ], expand=True),
                ft.Text(lesson.get("Aud", ""), width=80),
                ft.Text(lesson.get("FIO", ""), width=180, size=12)
            ], spacing=10),
            padding=5,
            border=ft.border.all(0.5, "#ccc"),
            border_radius=5,
            margin=3
        )
    def create_lessons(self, lessons_data):
        """Создаем строки для уроков"""
        return ft.Column([self.create_lesson_row(lesson) for lesson in lessons_data])

    def show_error(self, message):
        """Показать ошибку"""
        self.error_display.value = message
        self.error_display.visible = True
        self.update()

    def show_message(self, message):
        """Показать сообщение"""
        self.schedule_output.controls = [ft.Text(message)]
        self.update()

    async def check_schedule_at_5pm(self):
        """Проверка расписания в 17:00 на изменения"""
        chelyabinsk_tz = pytz.timezone("Asia/Yekaterinburg")
        previous_schedules = None  # Храним предыдущее расписание

        while True:
            now = datetime.datetime.now(chelyabinsk_tz)
            target = now.replace(hour=17, minute=0, second=0, microsecond=0)
            if now >= target:
                target += datetime.timedelta(days=1)

            await asyncio.sleep((target - now).total_seconds())

            # Получаем текущее расписание
            current_schedules = await self.fetch_schedules()

            # Сравниваем с предыдущим расписанием
            if current_schedules != previous_schedules:
                await self.display_schedules(current_schedules)
                previous_schedules = current_schedules  # Обновляем предыдущее расписание
