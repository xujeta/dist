from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp


class LineSelectScreen(Screen):
    image_path = StringProperty("")

    def set_image(self, path):
        self.image_path = path


class LineImageWidget(Image):
    point_a = ListProperty([])
    point_b = ListProperty([])
    active_point = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True

        self.bind(
            point_a=self.update_canvas,
            point_b=self.update_canvas,
            pos=self.update_canvas,
            size=self.update_canvas,
        )

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        # если A ещё нет
        if not self.point_a:
            self.point_a = touch.pos
            self.active_point = "A"
            return True

        # если B ещё нет
        if not self.point_b:
            self.point_b = touch.pos
            self.active_point = "B"
            return True

        # проверка попадания в A
        if self._is_near(touch.pos, self.point_a):
            self.active_point = "A"
            return True

        # проверка попадания в B
        if self._is_near(touch.pos, self.point_b):
            self.active_point = "B"
            return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.active_point == "A":
            self.point_a = touch.pos
            return True

        if self.active_point == "B":
            self.point_b = touch.pos
            return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        self.active_point = None
        return super().on_touch_up(touch)

    def _is_near(self, p1, p2, radius=20):
        return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 < radius**2

    def update_canvas(self, *args):
        self.canvas.after.clear()

        with self.canvas.after:
            Color(1, 0, 0, 1)

            r = dp(3)

            if self.point_a:
                Ellipse(pos=(self.point_a[0]-r, self.point_a[1]-r),
                        size=(r*2, r*2))

            if self.point_b:
                Ellipse(pos=(self.point_b[0]-r, self.point_b[1]-r),
                        size=(r*2, r*2))

            if self.point_a and self.point_b:
                Line(points=[*self.point_a, *self.point_b], width=1.5)
