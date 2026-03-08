from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp


class StartScreen(MDScreen):

    def start(self):
        app = MDApp.get_running_app()

        text = self.ids.speed_input.text
        app.min_robot_speed = float(text) if text else 0

        app.go_next("camera")
