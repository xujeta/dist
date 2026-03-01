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

from kivy.clock import Clock


class MainApp(MDApp):
    title_text = StringProperty("Камера")
    captured_image_path = StringProperty("")
    min_robot_speed = NumericProperty(0)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"

        Builder.load_file("app.kv")

        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.CAMERA,
            Permission.READ_MEDIA_IMAGES
        ])
        
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
        from kivy.clock import Clock
    
        def _show(dt):
            snackbar = Factory.StyledSnackbar()
            snackbar.ids.label.text = text
            snackbar.open()
    
        Clock.schedule_once(_show)

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
            from android import activity
            import os

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')
            File = autoclass('java.io.File')
            FileProvider = autoclass('androidx.core.content.FileProvider')

            activity_instance = PythonActivity.mActivity

            # создаём файл
            app_dir = activity_instance.getExternalFilesDir(None).getAbsolutePath()
            image_path = os.path.join(app_dir, "camera_photo.jpg")
            self._camera_image_path = image_path

            image_file = File(image_path)

            # authority = package + ".provider"
            authority = activity_instance.getPackageName() + ".provider"

            uri = FileProvider.getUriForFile(
                activity_instance,
                authority,
                image_file
            )

            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)

            activity.bind(on_activity_result=self._on_camera_result)
            activity_instance.startActivityForResult(intent, 2001)

        except Exception as e:
            self.show_snackbar(f"Ошибка запуска камеры: {e}")

    def _on_camera_result(self, request_code, result_code, intent):
        from android import activity
        activity.unbind(on_activity_result=self._on_camera_result)

        if request_code != 2001:
            return

        print("CAMERA RESULT:", result_code)

        if result_code == -1:
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.img_ready(self._camera_image_path))

            print("CAMERA RESULT CODE:", result_code)
            print("CAMERA INTENT:", intent)

            if result_code == -1 and intent:
                uri = intent.getData()
                print("CAMERA URI:", uri)

                if uri:
                    real_path = self._copy_uri_to_internal(uri)
                    print("CAMERA PATH:", real_path)

                    if real_path:
                        self.img_ready(real_path)

    def pick_from_gallery(self):
        try:
            from android.permissions import request_permissions, Permission
            
            request_permissions(
                [Permission.READ_MEDIA_IMAGES],
                self._on_gallery_permission
            )
        except ImportError:
            self.show_snackbar("Только Android")
        
    def _on_gallery_permission(self, permissions, results):
        if results and results[0]:
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self._on_gallery_select,
                filters=["*.jpg", "*.jpeg", "*.png"]
            )
        else:
            self.show_snackbar("Нет доступа к галерее")
    
    def _on_gallery_select(self, selection):
        print("SELECTION:", selection)
        if not selection:
            return

        uri = selection[0]

        if uri.startswith("/"):
            Clock.schedule_once(lambda dt: self.img_ready(uri))
            return

        if uri.startswith("content://"):
            from jnius import autoclass
            Uri = autoclass('android.net.Uri')
            parsed = Uri.parse(uri)

            real_path = self._copy_uri_to_internal(parsed)
            if real_path:
                Clock.schedule_once(lambda dt: self.img_ready(real_path))

    def _copy_uri_to_internal(self, uri):
        try:
            from jnius import autoclass
            import os

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            input_stream = resolver.openInputStream(uri)

            app_dir = activity.getFilesDir().getAbsolutePath()
            file_path = os.path.join(app_dir, "selected_image.jpg")

            output_stream = autoclass(
                'java.io.FileOutputStream'
            )(file_path)

            buffer = autoclass('java.nio.ByteBuffer').allocate(4096)
            byte_array = buffer.array()

            while True:
                length = input_stream.read(byte_array)
                if length == -1:
                    break
                output_stream.write(byte_array, 0, length)

            input_stream.close()
            output_stream.close()

            return file_path

        except Exception as e:
            print("COPY ERROR:", e)
            return None
    
    def img_ready(self, filename):
        self.captured_image_path = filename

        line_screen = self.sm.get_screen("line")
        line_screen.set_image(filename)

        self.go_next("line")


if __name__ == "__main__":
    MainApp().run()
