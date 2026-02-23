from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.properties import StringProperty, NumericProperty
from kivy.logger import Logger
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.label import MDLabel
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

    def get_platform(self):
        try:
            from kivy.utils import platform
            return platform
        except:
            return 'unknown'

    def open_camera(self):
        platform = self.get_platform()

        if platform == "android":
            self.open_camera_android()
        elif platform == "ios":
            self.open_camera_ios()
        else:
            self.open_camera_desktop()

    def open_camera_android(self):
        try:
            from android.permissions import request_permissions, Permission
            # Запрашиваем разрешение на камеру
            request_permissions([Permission.CAMERA], self._on_camera_permission)
        except ImportError:
            # Если модуль android не найден (например, при тестировании не на устройстве)
            self._actually_open_camera_android()
    
    def _on_camera_permission(self, permissions, results):
        if results and results[0]:
            # Разрешение получено
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
    
    def open_camera_ios(self):
        try:
            from plyer import camera

            filename = os.path.join(
                os.path.expanduser('~'),
                'Documents',
                f"photo_{int(time.time())}.jpg"
            )

            camera.take_picture(
                filename=filename,
                on_complete=self.img_ready
            )

        except Exception as e:
            Logger.error(f"Camera: Ошибка iOS камеры: {e}")
            self.show_snackbar(f"Ошибка камеры: {e}")


    def open_camera_desktop(self):
        self.show_snackbar("На ПК камера недоступна. Используй галерею.")


    def img_ready(self, filename):
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


    def pick_from_gallery(self):
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


if __name__ == "__main__":
    MainApp().run()
