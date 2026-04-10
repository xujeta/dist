from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.metrics import dp

class ProfileGraph(Widget):
    def draw_graph(self, profile_data):
        self.canvas.clear()
        if not profile_data:
            return

        # Достаем дистанции и высоты
        dists = [p['dist'] for p in profile_data]
        heights = [p['h'] for p in profile_data]

        min_d, max_d = min(dists), max(dists)
        min_h, max_h = min(heights), max(heights)

        # Защита от деления на ноль, если линия слишком короткая
        range_d = max_d - min_d if max_d > min_d else 1
        range_h = max_h - min_h if max_h > min_h else 1

        # Переводим координаты в масштаб экрана
        points = []
        for d, h in zip(dists, heights):
            x = self.x + (d - min_d) / range_d * self.width
            # Отступаем немного снизу и сверху (умножаем на 0.8 и добавляем 0.1), чтобы график не прилипал к краям
            y = self.y + self.height * 0.1 + ((h - min_h) / range_h * (self.height * 0.8))
            points.extend([x, y])

        # Рисуем саму линию
        with self.canvas:
            Color(0.2, 0.8, 1, 1)  # Голубоватый цвет линии
            Line(points=points, width=dp(2))

    # Перерисовываем график при изменении размера окна
    def on_size(self, *args):
        if hasattr(self, 'last_data'):
            self.draw_graph(self.last_data)

class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout()
        self.add_widget(self.layout)

        # Вместо картинки создаем наш виджет графика
        self.graph_widget = ProfileGraph()
        self.layout.add_widget(self.graph_widget)

    def show_loading(self, value):
        print("Loading:", value)

    def display_result(self, profile_data):
        # Сохраняем данные, чтобы график мог перерисоваться при ресайзе
        self.graph_widget.last_data = profile_data
        self.graph_widget.draw_graph(profile_data)
