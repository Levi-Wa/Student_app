import flet as ft
import httpx
import asyncio
from typing import List

class ScheduleTab(ft.Column):
    def __init__(self):
        super().__init__(expand=True)
        self.group_ids = []
        self.loading = False
        
        # Инициализация UI
        self.schedule_output = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        self.refresh_button = ft.ElevatedButton(
            "Обновить",
            icon=ft.icons.REFRESH,
            on_click=self.refresh_schedule
        )
        
        self.controls = [
            ft.Row([
                ft.Text("Расписание", size=20),
                self.refresh_button
            ]),
            self.schedule_output
        ]

    async def set_groups(self, group_ids: List[str]):
        """Устанавливает группы для отображения"""
        self.group_ids = group_ids
        await self.refresh_schedule()

    async def refresh_schedule(self, e=None):
        """Загружает расписание для выбранных групп"""
        if not self.group_ids:
            self.schedule_output.controls = [
                ft.Text("Группы не выбраны")
            ]
            await self.schedule_output.update_async()
            return

        self.loading = True
        self.schedule_output.controls = [
            ft.ProgressBar(),
            ft.Text("Загрузка расписания...")
        ]
        await self.schedule_output.update_async()
        
        try:
            schedules = await self.fetch_schedules()
            await self.display_schedules(schedules)
        except Exception as ex:
            self.schedule_output.controls = [
                ft.Text(f"Ошибка: {str(ex)}", color="red")
            ]
            await self.schedule_output.update_async()
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
        
        for group_id, schedule in zip(self.group_ids, schedules):
            if "error" in schedule:
                self.schedule_output.controls.append(
                    ft.Text(f"Ошибка для группы {group_id}: {schedule['error']}", color="red")
                )
                continue
            
            group_schedule = ft.Column()
            group_schedule.controls.append(
                ft.Text(f"Группа ID: {group_id}", size=16, weight="bold")
            )
            
            for month in schedule.get("Month", []):
                for day in month.get("Sched", []):
                    day_card = self.create_day_card(day)
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
        
        await self.schedule_output.update_async()

    def create_day_card(self, day):
        """Создает карточку дня"""
        date_str = day.get("datePair", "")
        day_week = day.get("dayWeek", "")
        
        lessons = ft.Column()
        for lesson in day.get("mainSchedule", []):
            lessons.controls.append(self.create_lesson_row(lesson))
        
        return ft.Container(
            content=ft.Column([
                ft.Text(f"📅 {date_str} ({day_week})", weight="bold"),
                lessons
            ]),
            padding=10,
            margin=5
        )

    def create_lesson_row(self, lesson):
        """Создает строку с информацией о занятии"""
        return ft.Row([
            ft.Text(lesson.get("TimeStart", ""), width=60),
            ft.Column([
                ft.Text(lesson.get("SubjName", ""), weight="bold"),
                ft.Text(lesson.get("LoadKindSN", ""), size=12, color="grey")
            ], expand=2),
            ft.Text(lesson.get("Aud", ""), width=60),
            ft.Text(lesson.get("FIO", ""), width=150, size=12)
        ], spacing=10)