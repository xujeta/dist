from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.properties import StringProperty, NumericProperty
from kivy.logger import Logger
from kivy.factory import Factory
from screens.start_screen import StartScreen
import os, time

from screens.camera_screen import CameraScreen
from screens.line_select_screen import LineSelectScreen
from screens.profile_screen import ProfileScreen
from screens.result_screen import ResultScreen


class MainApp(MDApp):
    title_text = StringProperty("Камера")
    captured_image_path = StringProperty("")
    min_robot_speed = NumericProperty(0)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"

        Builder.load_file("app.kv")

        self.sm = ScreenManager(transition=SlideTransition(direction="left"))
        self.sm.add_widget(StartScreen(name="start"))
        self.sm.add_widget(CameraScreen(name="camera"))
        self.sm.add_widget(LineSelectScreen(name="line"))
        self.sm.add_widget(ProfileScreen(name="profile"))
        self.sm.add_widget(ResultScreen(name="result"))
        self.sm.current = "start"

        return self.sm
    
    def go_next(self, screen_name):
        self.sm.transition.direction = "left"
        self.sm.current = screen_name
        self.update_title(screen_name)
        
    def go_back(self, screen_name):
        self.sm.transition.direction = "right"
        self.sm.current = screen_name
        self.update_title(screen_name)

    def update_title(self, screen_name):
        titles = {
            "start": "Старт",
            "camera": "Камера",
            "line": "Выбор линии",
            "profile": "Профиль",
            "result": "Результат"}
        self.title_text = titles.get(screen_name, "")

    def show_snackbar(self, text):
        snackbar = Factory.StyledSnackbar()
        snackbar.ids.label.text = text
        snackbar.open()

    # --- Android-only functions ---

    def open_camera(self):
        """Запуск камеры на Android с запросом разрешений"""
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA], self._on_camera_permission)
        except ImportError:
            self.show_snackbar("Не удалось запросить разрешение на камеру")

    def _on_camera_permission(self, permissions, results):
        if results and results[0]:
            self._actually_open_camera_android()
        else:
            self.show_snackbar("Необходимо разрешение на камеру")
    
    def _actually_open_camera_android(self):
        try:
            from jnius import autoclass

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')

            activity = PythonActivity.mActivity
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)

            activity.startActivity(intent)

            self.show_snackbar("Сделай фото, затем выбери его из галереи")

        except Exception as e:
            self.show_snackbar(f"Ошибка запуска камеры: {e}")

    def pick_from_gallery(self):
        """Выбор изображения из галереи Android"""
        try:
            from plyer import filechooser

            filechooser.open_file(
                on_selection=self._on_gallery_select,
                filters=[("Images", "*.png;*.jpg;*.jpeg")]
            )
        except Exception as e:
            self.show_snackbar(f"Не удалось открыть галерею: {e}")

    def _on_gallery_select(self, selection):
        if selection:
            self.img_ready(selection[0])

    def img_ready(self, filename):
        """Обработка выбранного или снятого изображения"""
        if not filename or not os.path.exists(filename):
            self.show_snackbar("Файл не найден")
            return

        self.captured_image_path = filename

        try:
            line_screen = self.sm.get_screen("line")
            if hasattr(line_screen, "set_image"):
                line_screen.set_image(filename)
        except Exception as e:
            self.show_snackbar(f"Ошибка обработки: {e}")
            return
        
        self.go_next("line")


if __name__ == "__main__":
    MainApp().run()
