import flet as ft
import datetime
import asyncio
import httpx
import pytz

class ScheduleTab(ft.Control):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.group_ids = []
        self.selected_day = datetime.date.today()
        self.selected_period = "Месяц"
        self.loading = False

        # Dropdown для выбора периода
        self.period_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Сегодня"),
                ft.dropdown.Option("Неделя"),
                ft.dropdown.Option("Месяц"),
                ft.dropdown.Option("Все")
            ],
            value=self.selected_period,
            on_change=self.on_period_change,  # Смена периода
            width=150,
            border_color="#2196F3",
            focused_border_color="#1976D2",
            filled=True,
            bgcolor="#E3F2FD"
        )

        # Основной контейнер для расписания
        self.schedule_output = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)
        self.loading_indicator = ft.ProgressBar(visible=False)
        self.error_display = ft.Text("", color="red", visible=False)

    def build(self):
        return ft.Column([
            ft.Row([ft.Text("\ud83d\uddd5\ufe0f Расписание", size=20, weight="bold"), self.period_dropdown]),
            self.loading_indicator,
            self.error_display,
            ft.Container(content=self.schedule_output, expand=True)
        ], expand=True)

    async def on_period_change(self, e):
        """Обработчик изменения выбранного периода"""
        self.selected_period = e.control.value
        await self.refresh_schedule()  # Обновление расписания после изменения периода
        self.update()

    async def refresh_schedule(self):
        """Метод для обновления расписания"""
        self.set_loading(True)
        try:
            schedules = await self.fetch_schedules()
            if any("error" in schedule for schedule in schedules):
                self.show_error("Ошибка при получении расписания.")
                return
            await self.display_schedules(schedules)  # Отображаем расписание
        except Exception as ex:
            self.show_error(f"Ошибка загрузки: {str(ex)}")
        finally:
            self.set_loading(False)
            self.update()

    async def set_groups(self, group_ids: object) -> None:
        """Устанавливаем ID групп и обновляем расписание"""
        self.group_ids = group_ids
        await self.refresh_schedule()

    async def fetch_schedules(self):
        """Получение расписания для всех групп"""
        async with httpx.AsyncClient() as client:
            tasks = []
            for group_id in self.group_ids:
                url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
                tasks.append(self.fetch_group_schedule(client, url))
            return await asyncio.gather(*tasks)

    async def fetch_group_schedule(self, client, url):
        """Загрузка расписания для конкретной группы"""
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

    async def display_schedules(self, schedules):
        """Отображение расписания на основе выбранного периода"""
        self.schedule_output.controls.clear()
        current_date = datetime.date.today()
        tomorrow = current_date + datetime.timedelta(days=1)

        all_day_cards = []

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

            # Фильтруем расписание в зависимости от выбранного периода
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    if not date_str:
                        continue

                    day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

                    # Фильтруем по выбранному периоду
                    if self.selected_period == "Сегодня" and day_date != current_date:
                        continue
                    elif self.selected_period == "Неделя" and not (0 <= (day_date - current_date).days < 7):
                        continue
                    elif self.selected_period == "Месяц" and (day_date.month != current_date.month or day_date.year != current_date.year):
                        continue
                    elif self.selected_period == "Все":
                        # Отображаем все расписания
                        pass

                    highlight_current_pair = (self.selected_period == "Сегодня")
                    force_blue = (self.selected_period == "Неделя" and day_date > current_date)

                    day_card = self.create_day_card(day, current_date, tomorrow, highlight_current_pair, force_blue)
                    all_day_cards.append(day_card)
                    group_column.controls.append(day_card)

            self.schedule_output.controls.append(
                ft.Container(content=group_column, padding=10, bgcolor="#f9f9f9", border_radius=10, margin=5)
            )

        self.update()

        # Прокрутка к текущей дате
        for card in all_day_cards:
            if isinstance(card.content.controls[0], ft.Text):
                text = card.content.controls[0].value
                if str(current_date.strftime("%d.%m.%Y")) in text:
                    await asyncio.sleep(0.2)
                    self.page.scroll_to(card.offset.y, duration=300)
                    break

    def create_day_card(self, day, current_date, tomorrow_date, highlight_current_pair=False, force_blue=False):
        try:
            date_str = day.get("datePair", "")
            if not date_str:
                return ft.Text("Дата не указана", color="red")

            day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            day_week = day.get("dayWeek", "")
            color = "blue" if force_blue else self.get_date_color(day_date, current_date, tomorrow_date)
            lessons = self.create_lessons(day.get("mainSchedule", []), day_date, highlight_current_pair)

            return ft.Container(
                content=ft.Column([ft.Text(f"\ud83d\uddd5\ufe0f {date_str} ({day_week})", weight="bold", color=color), lessons]),
                padding=10,
                margin=5,
                bgcolor="#ffffff",
                border=ft.border.all(1, "#ddd"),
                border_radius=8
            )
        except Exception as ex:
            return ft.Text(f"Ошибка дня: {str(ex)}", color="red")

    def get_date_color(self, day_date, current_date, tomorrow_date):
        if day_date == current_date:
            return "green"
        elif day_date == tomorrow_date:
            return "blue"
        elif day_date < current_date:
            return "grey"
        else:
            return None

    def create_lessons(self, lessons_data, lesson_date=None, highlight_current=False):
        rows = []
        now = datetime.datetime.now()

        for lesson in lessons_data:
            time_str = lesson.get("TimeStart", "")
            is_current = False

            if highlight_current and lesson_date == now.date() and time_str:
                try:
                    start_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                    start_dt = datetime.datetime.combine(now.date(), start_time)
                    end_dt = start_dt + datetime.timedelta(minutes=90)
                    if start_dt <= now <= end_dt:
                        is_current = True
                except Exception:
                    pass

            rows.append(self.create_lesson_row(lesson, is_current))

        return ft.Column(rows)

    def create_lesson_row(self, lesson, highlight=False):
        return ft.Container(
            content=ft.Row([ft.Text(lesson.get("TimeStart", ""), width=80),
                            ft.Column([ft.Text(lesson.get("SubjName", ""), weight="bold"),
                                      ft.Text(lesson.get("LoadKindSN", ""), size=12, color="grey")], expand=True),
                            ft.Text(lesson.get("Aud", ""), width=80),
                            ft.Text(lesson.get("FIO", ""), width=180, size=12)
                            ], spacing=10),
            padding=5,
            border=ft.border.all(1, "#4CAF50") if highlight else ft.border.all(0.5, "#ccc"),
            bgcolor="#f1fff1" if highlight else "#ffffff",
            border_radius=5,
            margin=3
        )

    def set_loading(self, loading: bool):
        """Метод отображения индикатора загрузки"""
        self.loading = loading
        self.loading_indicator.visible = loading
        self.error_display.visible = False
        self.schedule_output.visible = not loading
        self.update()

    def show_error(self, message):
        """Метод отображения ошибок"""
        self.error_display.value = message
        self.error_display.visible = True
        self.update()

    def show_message(self, message):
        """Метод отображения сообщений"""
        self.schedule_output.controls = [ft.Text(message)]
        self.update()

    async def check_schedule_at_5pm(self):
        """Проверка расписания ежедневно в 17:00"""
        chelyabinsk_tz = pytz.timezone("Asia/Yekaterinburg")
        previous_schedules = None

        while True:
            now = datetime.datetime.now(chelyabinsk_tz)
            target = now.replace(hour=17, minute=0, second=0, microsecond=0)
            if now >= target:
                target += datetime.timedelta(days=1)

            await asyncio.sleep((target - now).total_seconds())

            current_schedules = await self.fetch_schedules()
            if current_schedules != previous_schedules:
                await self.display_schedules(current_schedules)
                previous_schedules = current_schedules
