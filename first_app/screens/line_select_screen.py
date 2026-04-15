import json
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse, Line, Triangle
from kivy.metrics import dp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

class LineSelectScreen(Screen):
    image_path = StringProperty("")
    
    # Сюда сохраним данные для отправки
    h_a = NumericProperty(150.0)
    h_b = NumericProperty(140.0)
    step = NumericProperty(10.0)
    extrema = ListProperty([]) # Список словарей:[{'x': px, 'y': px, 'h': h, 'type': 'hill'/'depression'}, ...]

    def set_image(self, path):
        self.image_path = path
        self.ids.line_widget.source = path
        self.ids.line_widget.reload()
        # Сбрасываем состояния
        self.ids.line_widget.reset_state()
        self.extrema =[]

class LineImageWidget(Image):
    point_a = ListProperty([])
    point_b = ListProperty([])
    
    # Состояния: "WAIT_A", "WAIT_B", "WAIT_EXTREMA"
    current_state = StringProperty("WAIT_A")
    temp_point = ListProperty([]) # Временная точка для диалога
    active_point_drag = StringProperty("") # "A" или "B" для перетаскивания
    
    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True
        self.bind(point_a=self.update_canvas, point_b=self.update_canvas, pos=self.update_canvas, size=self.update_canvas)

    def reset_state(self):
        self.point_a = []
        self.point_b =[]
        self.current_state = "WAIT_A"
        self.update_canvas()

    def _is_near(self, p1, p2, radius=50): 
        # Радиус 50, чтобы пальцем было легко попасть для перетаскивания
        if not p1 or not p2: return False
        return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 < radius**2

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        # 1. Проверяем, не хотим ли мы ПЕРЕТАЩИТЬ уже созданную точку
        if self.point_a and self._is_near(touch.pos, self.point_a):
            self.active_point_drag = "A"
            return True
        if self.point_b and self._is_near(touch.pos, self.point_b):
            self.active_point_drag = "B"
            return True

        # 2. Если клик в пустое место — ставим новую точку или экстремум
        self.temp_point = touch.pos

        if self.current_state == "WAIT_A":
            self.show_input_dialog("Точка А", "Введите высоту Точки А:")
            return True
        elif self.current_state == "WAIT_B":
            self.show_input_dialog("Точка B", "Введите высоту Точки B:")
            return True
        elif self.current_state == "WAIT_EXTREMA":
            self.show_extrema_dialog()
            return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        # Перетаскивание точек
        if self.active_point_drag == "A":
            self.point_a = touch.pos
            return True
        elif self.active_point_drag == "B":
            self.point_b = touch.pos
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        # Отпускаем точку
        if self.active_point_drag:
            self.active_point_drag = ""
            return True
        return super().on_touch_up(touch)

    def show_input_dialog(self, title, hint):
        self.text_field = MDTextField(hint_text=hint, input_filter="float")
        self.dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=self.text_field,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="OK", on_release=self.on_dialog_ok)
            ],
        )
        self.dialog.open()

    def on_dialog_ok(self, *args):
        input_text = self.text_field.text.strip()
        screen = self.parent_screen
        app = MDApp.get_running_app()

        try:
            val = float(input_text) if input_text else 0.0
        except ValueError:
            val = 0.0

        if self.current_state == "WAIT_A":
            self.point_a = self.temp_point
            screen.h_a = val
            self.current_state = "WAIT_B"
            self.dialog.dismiss()
            app.show_snackbar(f"Точка А = {val}м. Выберите Точку В.")
            
        elif self.current_state == "WAIT_B":
            self.point_b = self.temp_point
            screen.h_b = val
            self.current_state = "WAIT_DISTANCE" # ПЕРЕХОДИМ К МАСШТАБУ
            self.dialog.dismiss()
            # Сразу запрашиваем реальное расстояние между ними
            self.show_input_dialog("Масштаб", "Реальное расстояние между А и В (в метрах):")

        elif self.current_state == "WAIT_DISTANCE":
            # Вычисляем коэффициент пиксель/метр
            p_a = self.point_a
            p_b = self.point_b
            pixel_dist = ((p_b[0] - p_a[0])**2 + (p_b[1] - p_a[1])**2)**0.5
            
            real_dist = val if val > 0 else 1.0
            # Сохраняем в App, чтобы slope_solver его увидел
            app.pixel_to_meter_ratio = real_dist / pixel_dist
            
            self.current_state = "WAIT_STEP"
            self.dialog.dismiss()
            app.show_snackbar(f"Масштаб задан. Введите шаг изолиний:")
            self.show_input_dialog("Шаг изолиний", "Введите шаг (по умолчанию 10м):")

        elif self.current_state == "WAIT_STEP":
            screen.step = val
            self.current_state = "WAIT_EXTREMA"
            self.dialog.dismiss()
            app.show_snackbar(f"Шаг = {val}м. Кликайте для экстремумов.")

        self.update_canvas()

    def show_extrema_dialog(self):
        self.extrema_h_field = MDTextField(hint_text="Высота", input_filter="float")
        self.extrema_type_field = MDTextField(hint_text="Тип (х - холм, о - овраг)")
        
        from kivy.uix.boxlayout import BoxLayout
        box = BoxLayout(orientation="vertical", spacing="10dp", size_hint_y=None, height="120dp")
        box.add_widget(self.extrema_h_field)
        box.add_widget(self.extrema_type_field)

        self.dialog = MDDialog(
            title="Добавить экстремум",
            type="custom",
            content_cls=box,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="ДОБАВИТЬ", on_release=self.on_extrema_ok)
            ],
        )
        self.dialog.open()

    def on_extrema_ok(self, *args):
        try:
            h_val = float(self.extrema_h_field.text)
        except:
            h_val = 150.0
            
        # Умное распознавание: если ввели "х", "h" или "холм" - это холм, иначе низина
        user_input = self.extrema_type_field.text.strip().lower()
        if user_input in ['х', 'h', 'холм']:
            internal_type = 'hill'
            display_type = 'Холм'
        else:
            internal_type = 'depression'
            display_type = 'Овраг'
        
        screen = self.parent_screen
        
        # Переводим экранные координаты в пиксели картинки
        real_coords = self.get_image_coordinates(self.temp_point)
        if real_coords:
            screen.extrema.append({
                'x': real_coords[0],
                'y': real_coords[1],
                'h': h_val,
                'type': internal_type, # На сервер летит правильное английское слово
                'screen_pos': self.temp_point # Экранные координаты для отрисовки
            })
            MDApp.get_running_app().show_snackbar(f"Добавлен {display_type} ({h_val}м)")

        self.dialog.dismiss()
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.after.clear()
        with self.canvas.after:
            r = dp(4)
            if self.point_a:
                Color(0, 1, 0, 1) # Зеленая А
                Ellipse(pos=(self.point_a[0]-r, self.point_a[1]-r), size=(r*2, r*2))
            if self.point_b:
                Color(1, 0, 0, 1) # Красная В
                Ellipse(pos=(self.point_b[0]-r, self.point_b[1]-r), size=(r*2, r*2))
            if self.point_a and self.point_b:
                Color(0.2, 0.8, 1, 1)
                Line(points=[*self.point_a, *self.point_b], width=1.5)
            
            # Рисуем экстремумы
            if hasattr(self, 'parent_screen'):
                for ext in self.parent_screen.extrema:
                    sx, sy = ext['screen_pos']
                    if ext['type'] == 'hill':
                        Color(1, 0, 0, 1) # Красный холм (треугольник вверх)
                        Triangle(points=[sx, sy+r, sx-r, sy-r, sx+r, sy-r])
                    else:
                        Color(0, 0, 1, 1) # Синий овраг (треугольник вниз)
                        Triangle(points=[sx, sy-r, sx-r, sy+r, sx+r, sy+r])

    def get_image_coordinates(self, touch_pos):

        if not self.texture or not touch_pos: return None
        orig_w, orig_h = self.texture.size
        norm_w, norm_h = self.norm_image_size
        img_x = self.center_x - norm_w / 2
        img_y = self.center_y - norm_h / 2
        touch_x_rel = touch_pos[0] - img_x
        touch_y_rel = touch_pos[1] - img_y
        if touch_x_rel < 0 or touch_y_rel < 0 or touch_x_rel > norm_w or touch_y_rel > norm_h:
            return None
        scale_x = orig_w / norm_w
        scale_y = orig_h / norm_h
        real_x = int(touch_x_rel * scale_x)
        real_y = int(orig_h - (touch_y_rel * scale_y))
        return (real_x, real_y)

    def get_full_data_package(self):
        widget = self.ids.line_widget
        
        # Переводим точки А и В из координат экрана в координаты картинки
        real_a = widget.get_image_coordinates(widget.point_a)
        real_b = widget.get_image_coordinates(widget.point_b)
        
        if not real_a or not real_b:
            return None
    
        # Формируем пакет данных
        package = {
            "point_a": {"x": real_a[0], "y": real_a[1], "h": self.h_a},
            "point_b": {"x": real_b[0], "y": real_b[1], "h": self.h_b},
            "step": self.step,
            "extrema": self.extrema, # Там уже лежат 'x', 'y', 'h', 'type'
            "image_path": self.image_path
        }
        return package
