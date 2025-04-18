import flet as ft

class SettingsTab(ft.Control):
    def __init__(self):
            self.view = ft.Column([ft.Text("Настройки (в разработке)")])
    
    def build(self):
        return ft.Text("Настройки (в разработке)")
    