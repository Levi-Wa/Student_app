import flet as ft
import datetime
import asyncio
import httpx
import pytz
import logging


class ScheduleTab(ft.Control):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.group_ids = []
        self.selected_day = datetime.date.today()
        self.selected_period = "Неделя"
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

        logging.basicConfig(filename="schedule.log", level=logging.DEBUG)
        logging.debug(f"Period changed to: {self.selected_period}")

    def build(self):
        return ft.Column([
            ft.Row([ft.Text("\ud83d\uddd5\ufe0f Расписание", size=20, weight="bold"), self.period_dropdown]),
            self.loading_indicator,
            self.error_display,
            ft.Container(content=self.schedule_output, expand=True, visible=True)  # Убедитесь, что visible=True
        ], expand=True)

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
        async with httpx.AsyncClient() as client:
            tasks = []
            for group_id in self.group_ids:
                url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
                tasks.append(self.fetch_group_schedule(client, url))
            results = await asyncio.gather(*tasks)
            print("API response dates:",
                  [day["datePair"] for schedule in results for month in schedule.get("Month", []) for day in
                   month.get("Sched", [])])  # Отладка
            return results

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

    async def on_period_change(self, e):
        """Обработчик изменения выбранного периода"""
        self.selected_period = e.control.value
        print(f"Period changed to: {self.selected_period}")  # Отладка
        await self.refresh_schedule()
        self.page.update()  # Обновляем всю страницу

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
                key=f"date_{date_str}",  # Уникальный ключ для карточки
                content=ft.Column(
                    [ft.Text(f"\ud83d\uddd5\ufe0f {date_str} ({day_week})", weight="bold", color=color), lessons]),
                padding=10,
                margin=5,
                bgcolor="#ffffff",
                border=ft.border.all(1, "#ddd"),
                border_radius=8
            )
        except Exception as ex:
            return ft.Text(f"Ошибка дня: {str(ex)}", color="red")

    async def display_schedules(self, schedules):
        """Отображение расписания на основе выбранного периода"""
        print(f"Clearing schedule_output, current controls: {len(self.schedule_output.controls)}")  # Отладка
        self.schedule_output.controls.clear()
        current_date = datetime.date.today()
        tomorrow = current_date + datetime.timedelta(days=1)
        all_day_cards = []

        print(f"Displaying schedules for period: {self.selected_period}")  # Отладка

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

            if not schedule.get("Month"):
                self.schedule_output.controls.append(
                    ft.Text(f"Нет данных для группы {group_id}", color="orange")
                )
                continue

            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    date_str = day.get("datePair", "")
                    if not date_str:
                        print(f"Skipping empty date for group {group_id}")  # Отладка
                        continue

                    try:
                        day_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                    except ValueError as ve:
                        print(f"Invalid date format: {date_str}, error: {ve}")  # Отладка
                        continue

                    # Фильтрация по периоду
                    if self.selected_period == "Сегодня" and day_date != current_date:
                        continue
                    elif self.selected_period == "Неделя" and not (0 <= (day_date - current_date).days < 7):
                        continue
                    elif self.selected_period == "Месяц" and (
                            day_date.month != current_date.month or day_date.year != current_date.year):
                        continue
                    elif self.selected_period == "Все":
                        pass

                    print(f"Adding day: {date_str} for period: {self.selected_period}")  # Отладка

                    highlight_current_pair = (self.selected_period == "Сегодня")
                    force_blue = (self.selected_period == "Неделя" and day_date == tomorrow)

                    day_card = self.create_day_card(day, current_date, tomorrow, highlight_current_pair, force_blue)
                    all_day_cards.append((day_card, date_str))  # Сохраняем карточку и дату
                    group_column.controls.append(day_card)

            if group_column.controls:
                self.schedule_output.controls.append(
                    ft.Container(content=group_column, padding=10, bgcolor="#f9f9f9", border_radius=10, margin=5)
                )
            else:
                self.schedule_output.controls.append(
                    ft.Text(f"Нет расписания для группы {group_id} в выбранном периоде", color="orange")
                )

        if not self.schedule_output.controls:
            self.schedule_output.controls.append(
                ft.Text("Нет расписания для выбранного периода", color="orange")
            )

        print(f"Total cards added: {len(all_day_cards)}")  # Отладка
        print(f"Schedule output controls after update: {len(self.schedule_output.controls)}")  # Отладка

        self.schedule_output.update()
        self.page.update()

        # Прокрутка к текущей дате
        print(f"Attempting to scroll to current date: {current_date.strftime('%d.%m.%Y')}")  # Отладка
        if all_day_cards:
            current_date_str = current_date.strftime("%d.%m.%Y")
            current_card_key = f"date_{current_date_str}"
            try:
                # Даём время на рендеринг
                await asyncio.sleep(0.5)
                self.page.update()
                # Прокручиваем к элементу по ключу
                print(f"Scrolling to card with key: {current_card_key}")  # Отладка
                self.page.scroll_to(key=current_card_key, duration=1000)
            except AttributeError as e:
                print(f"Error: scroll_to with key not supported, falling back to index-based scrolling: {e}")  # Отладка
                # Fallback: прокрутка по индексу карточки
                card_index = next((i for i, (_, date) in enumerate(all_day_cards) if date == current_date_str), -1)
                if card_index >= 0:
                    estimated_offset = card_index * 150 + 50  # Высота карточки 150 + 50 для заголовка/отступов
                    print(f"Scrolling to estimated offset: {estimated_offset}")  # Отладка
                    self.page.scroll_to(offset=estimated_offset, duration=1000)
                else:
                    print("Current date card not found, scrolling to top")  # Отладка
                    self.page.scroll_to(offset=0, duration=1000)
            except Exception as e:
                print(f"Error during scroll attempt: {e}")  # Отладка
                self.page.scroll_to(offset=0, duration=1000)
        else:
            print("No cards to scroll to, scrolling to top")  # Отладка
            self.page.scroll_to(offset=0, duration=1000)

    def get_date_color(self, day_date, current_date, tomorrow_date):
        if day_date == current_date:
            return "green"
        elif day_date == tomorrow_date:
            return "blue"
        elif day_date < current_date:
            return "grey"
        else:
            return "black"

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
        self.loading = loading
        self.loading_indicator.visible = loading
        self.error_display.visible = False
        self.schedule_output.visible = not loading
        print(f"Schedule output visible: {self.schedule_output.visible}")  # Отладка
        self.page.update()

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
