from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.widget import Widget
from kivy.properties import ListProperty
from kivymd.app import MDApp
import requests
import threading

class ProfileChart(Widget):
    points_data = ListProperty([]) 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, points_data=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear() 
        
        if not self.points_data or len(self.points_data) < 2:
            return

        dists = [p[0] for p in self.points_data]
        heights = [p[1] for p in self.points_data]
        
        min_d, max_d = min(dists), max(dists)
        min_h, max_h = min(heights), max(heights)

        dist_range = max_d - min_d if max_d > min_d else 1
        height_range = max_h - min_h if max_h > min_h else 1

        pad_x, pad_y = 20, 20
        draw_w = self.width - 2 * pad_x
        draw_h = self.height - 2 * pad_y

        with self.canvas:
            Color(0.2, 0.8, 0.2, 1) # Зеленая линия графика
            
            line_pts = []
            for d, h in self.points_data:
                x = self.x + pad_x + ((d - min_d) / dist_range) * draw_w
                y = self.y + pad_y + ((h - min_h) / height_range) * draw_h
                line_pts.extend([x, y])
            
            Line(points=line_pts, width=2)


class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.simulator = None

    def display_result(self, profile_data):
        # 1. Сохраняем чистые (сырые) данные
        self.raw_profile_data = profile_data 
        
        # 2. Передаем координаты в график
        plot_points = [(p["dist"], p["h"]) for p in profile_data]
        self.ids.chart.points_data = plot_points
        self.ids.chart.update_canvas()
        
        # 3. Очищаем консоль для нового запуска
        self.clear_log()

    def start_simulation(self):
        app = MDApp.get_running_app()
        if not hasattr(self, 'raw_profile_data') or not self.raw_profile_data:
            app.show_snackbar("Ошибка: Нет данных профиля!")
            return

        if self.simulator and self.simulator.is_alive():
            app.show_snackbar("Робот уже едет!")
            return

        try:
            from core.slope_solver import RobotSimulator

            p_to_m = float(getattr(app, 'pixel_to_meter_ratio', 1.0))
            min_spd = float(getattr(app, 'min_robot_speed', 1.0))
            t1 = float(getattr(app, 'angle_t1', 30.0))
            t2 = float(getattr(app, 'angle_t2', 60.0))

            self.simulator = RobotSimulator(
                profile_data=self.raw_profile_data,
                min_speed=min_spd,
                pixel_to_meter=p_to_m,
                t1=t1,
                t2=t2,
                log_callback=self.add_log,
                led_callback=self.update_leds,
                esp_ip="192.168.4.1"
            )
            
            self.simulator.start()
            app.show_snackbar("Симуляция запущена!")
            
        except Exception as e:
            app.show_snackbar(f"ОШИБКА: {str(e)}")

    def stop_simulation(self):
        if self.simulator and self.simulator.is_alive():
            self.simulator.stop()
        else:
            MDApp.get_running_app().show_snackbar("Симуляция не запущена")

    def add_log(self, text):
        def _update_log(dt):
            current_text = self.ids.console_log.text
            self.ids.console_log.text = current_text + "\n" + text
            self.ids.scroll_view.scroll_y = 0 
        Clock.schedule_once(_update_log)

    def clear_log(self):
        self.ids.console_log.text = "Готов к запуску. Ожидание команд..."

    def update_leds(self, r1, r2, r3):
        def _update_ui(dt):
            states = [r1, r2, r3]
            for i in range(1, 4):
                led = self.ids[f"led{i}"]
                state = states[i-1]
                
                led.canvas.before.clear()
                with led.canvas.before:
                    if state == 1:
                        Color(0, 1, 0, 1) # Зеленый цвет
                    else:
                        Color(0.2, 0.2, 0.2, 1) # Темно-серый
                    Ellipse(pos=led.pos, size=led.size)
                led.canvas.ask_update()
        Clock.schedule_once(_update_ui)

    def on_leave(self):
        self.stop_simulation()
