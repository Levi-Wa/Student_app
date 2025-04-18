import flet as ft

class SettingsTab(ft.Control):
    def _get_control_name(self):
        return "settingstab"
    
    def build(self):
        return ft.Text("Настройки (в разработке)")
    