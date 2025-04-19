import flet as ft
from datetime import datetime
import json
from pathlib import Path

# Конфигурационный файл
CONFIG_FILE = Path("config.json")

# Фиксированный список групп (редактируется в коде)
GROUPS = {
    "1": {"ИД-101": 26616},
    "2": {},
    "3": {},
    "4": {}
}

class StartupMenu(ft.Column):
    """Начальный экран выбора группы"""
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.selected_group_id = None
        
        # Элементы управления
        self.course_dropdown = ft.Dropdown(
            label="Выберите курс",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 5)],
            on_change=self.update_groups,
            width=200
        )
        
        self.group_dropdown = ft.Dropdown(
            label="Выберите группу",
            width=300
        )
        
        self.controls = [
            ft.Text("Настройки группы", size=24, weight="bold"),
            ft.Row([self.course_dropdown, self.group_dropdown]),
            ft.ElevatedButton(
                "Сохранить и продолжить",
                on_click=self.save_settings,
                icon=ft.icons.SAVE
            )
        ]
        
        # Загрузка начальных данных
        self.update_groups()

    def update_groups(self, e=None):
        course = self.course_dropdown.value or "1"
        groups = GROUPS.get(course, {})
        
        self.group_dropdown.options = [
            ft.dropdown.Option(
                text=f"{name} (ID: {id_})", 
                key=str(id_)
            for name, id_ in groups.items()
        ]
        self.group_dropdown.update()

    def save_settings(self, e):
        if not self.group_dropdown.value:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Выберите группу!"),
                open=True
            )
            self.page.update()
            return
            
        config = {
            "course": self.course_dropdown.value,
            "group_id": self.group_dropdown.value
        }
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
            
        self.page.views.clear()
        main_view = MainView(self.page)
        self.page.views.append(main_view)
        self.page.update()

class ScheduleTab(ft.Column):
    """Вкладка с расписанием (без выбора группы)"""
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.group_id = None
        self.schedule_output = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        self.controls = [
            ft.Text("📅 Расписание", size=24, weight="bold"),
            ft.ElevatedButton(
                "Обновить",
                icon=ft.icons.REFRESH,
                on_click=self.refresh_schedule
            ),
            self.schedule_output
        ]
        
    async def refresh_schedule(self, e=None):
        if not self.group_id:
            return
            
        self.schedule_output.controls = [
            ft.ProgressBar(),
            ft.Text("Загрузка расписания...")
        ]
        self.schedule_output.update()
        
        try:
            url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={self.group_id}"
            async with ft.HttpClient() as client:
                response = await client.get(url)
                data = response.json()
                self.display_schedule(data)
        except Exception as e:
            self.schedule_output.controls = [
                ft.Text(f"Ошибка загрузки: {str(e)}", color="red")
            ]
            self.schedule_output.update()

    def display_schedule(self, data):
        self.schedule_output.controls = []
        
        for month in data.get("Month", []):
            for day in month.get("Sched", []):
                day_schedule = ft.Column(spacing=5)
                date_str = day.get("datePair", "")
                day_week = day.get("dayWeek", "")
                
                day_title = f"📅 {date_str} ({day_week})"
                day_schedule.controls.append(ft.Text(day_title, weight="bold"))
                
                for lesson in day.get("mainSchedule", []):
                    lesson_text = [
                        f"🕒 {lesson.get('TimeStart', '')}",
                        f"📚 {lesson.get('SubjName', '')}",
                    ]
                    if classroom := lesson.get("Aud", ""):
                        lesson_text.append(f"🏫 {classroom}")
                    if teacher := lesson.get("FIO", ""):
                        lesson_text.append(f"👤 {teacher}")
                    
                    day_schedule.controls.append(
                        ft.Text(" | ".join(lesson_text))
                    )
                
                self.schedule_output.controls.append(
                    ft.Container(
                        content=day_schedule,
                        padding=10,
                        margin=5,
                        border=ft.border.all(1, "#e0e0e0"),
                        border_radius=5
                    )
                )
        

    

