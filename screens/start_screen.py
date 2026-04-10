from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp

class StartScreen(MDScreen):
    def start(self):
        app = MDApp.get_running_app()
        
        try:
            app.min_robot_speed = float(self.ids.speed_input.text)
            app.angle_t1 = float(self.ids.t1_input.text)
            app.angle_t2 = float(self.ids.t2_input.text)
        except ValueError:
            app.min_robot_speed = 1.0
            app.angle_t1 = 30.0
            app.angle_t2 = 60.0

        app.root.current = "camera"
        app.update_title("camera")
