from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.properties import StringProperty, NumericProperty
from kivy.logger import Logger
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest

import os
import threading
import requests
import base64
import urllib.parse
import json
from PIL import Image
from android.runnable import run_on_ui_thread

from screens.start_screen import StartScreen
from screens.camera_screen import CameraScreen
from screens.line_select_screen import LineSelectScreen
from screens.profile_screen import ProfileScreen
from screens.result_screen import ResultScreen

class MainApp(MDApp):
    title_text = StringProperty("Камера")
    captured_image_path = StringProperty("")
    min_robot_speed = NumericProperty(1.0) # Скорость
    angle_t1 = NumericProperty(30.0)       # Угол для Реле 2
    angle_t2 = NumericProperty(60.0)       # Угол для Реле 3
    pixel_to_meter_ratio = NumericProperty(1.0)
    
    robot = None

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
        # Если мы на экране выбора линии и нажимаем "Вперед" (в profile)
        if self.sm.current == "line" and screen_name == "profile":
            line_screen = self.sm.get_screen("line")
            widget = line_screen.ids.line_widget
            
            img_pt_a = widget.get_image_coordinates(widget.point_a)
            img_pt_b = widget.get_image_coordinates(widget.point_b)
            
            if img_pt_a and img_pt_b:
                # ИСПРАВЛЕНИЕ: Берем шаг прямо из экрана выбора линии
                step_val = line_screen.step 
                
                self.sm.transition.direction = "left"
                self.sm.current = "profile"
                self.update_title("profile")

                profile_screen = self.sm.get_screen("profile")
                if hasattr(profile_screen, 'show_loading'):
                    profile_screen.show_loading(True)

                # Теперь step_val будет именно тем числом, которое ты ввела в диалоге
                threading.Thread(
                    target=self._send_to_server, 
                    args=(line_screen.image_path, img_pt_a, img_pt_b, 
                          line_screen.h_a, line_screen.h_b, step_val, line_screen.extrema),
                    daemon=True
                ).start()
            else:
                self.show_snackbar("Сначала поставьте две точки на карте!")
            return

        # Обычный переход для остальных экранов
        self.sm.transition.direction = "left"
        self.sm.current = screen_name
        self.update_title(screen_name)

    def _send_to_server(self, image_path, pt_a, pt_b, h_a, h_b, step, extrema):
        SERVER_URL = "http://192.168.4.2:5000/process_profile" 
        try:
            # ПЕРЕСЧИТЫВАЕМ КООРДИНАТЫ ПОД НОВЫЙ РАЗМЕР
            ax_s, ay_s = pt_a[0] * scale, pt_a[1] * scale
            bx_s, by_s = pt_b[0] * scale, pt_b[1] * scale

            # Пересчитываем экстремумы (x, y, h, type)
            extrema_scaled = []
            for e in extrema:
                extrema_scaled.append([e['x'] * scale, e['y'] * scale, e['h'], e['type']])

            with open(compressed_path, 'rb') as f:
                response = requests.post(
                    SERVER_URL, 
                    files={'image': f}, 
                    data={
                        'a_x': ax_s, 'a_y': ay_s, 'h_a': h_a,
                        'b_x': bx_s, 'b_y': by_s, 'h_b': h_b,
                        'step': step,
                        'extrema': json.dumps(extrema_scaled) 
                    }, 
                    timeout=60
                )
            
            # Удаляем временный сжатый файл после отправки
            if compressed_path != image_path and os.path.exists(compressed_path):
                os.remove(compressed_path)

            if response.status_code == 200:
                result = response.json()
                Clock.schedule_once(lambda dt: self._on_server_response(result))
            else:
                Clock.schedule_once(lambda dt: self._on_server_error(f"Ошибка: {response.status_code}"))
        except Exception as e:
            # Не забываем почистить файл и тут, если была ошибка
            if compressed_path != image_path and os.path.exists(compressed_path):
                os.remove(compressed_path)
            error_msg = str(e)
            Clock.schedule_once(lambda dt, msg=error_msg: self._on_server_error(msg))

    def _on_server_error(self, error_msg):
        profile_screen = self.sm.get_screen("profile")
        if hasattr(profile_screen, 'show_loading'):
            profile_screen.show_loading(False)
        self.show_snackbar(error_msg)

    def _on_server_response(self, result):
        # 1. Скрываем индикатор загрузки
        profile_screen = self.sm.get_screen("profile")
        if hasattr(profile_screen, 'show_loading'):
            profile_screen.show_loading(False)

        # 2. Проверяем, нет ли ошибки в ответе сервера
        if "error" in result:
            self.show_snackbar(f"Ошибка сервера: {result['error']}")
            self.go_back("line")
            return

        # 3. Получаем данные профиля (это список словарей [{'dist': ..., 'h': ...}])
        profile_data = result["profile_data"]

        # 4. Находим экран результатов и отдаем ему СЫРЫЕ данные
        res_screen = self.sm.get_screen("result")
        
        # Мы убрали создание переменной 'points'. 
        # Теперь передаем список словарей напрямую.
        res_screen.display_result(profile_data)

        # 5. Переключаем экран
        self.sm.transition.direction = "left"
        self.sm.current = "result"
        self.update_title("result")
        
    def go_back(self, screen_name):
        # Защита от вылета: проверяем, существует ли экран
        if self.sm.has_screen(screen_name):
            self.sm.transition.direction = "right"
            self.sm.current = screen_name
            self.update_title(screen_name)
        else:
            self.sm.current = "start"

    def update_title(self, screen_name):
        titles = {
            "start": "Старт", "camera": "Камера", 
            "line": "Выбор линии", "profile": "Профиль", "result": "Результат"}
        self.title_text = titles.get(screen_name, "")

    def show_snackbar(self, text):
        def _show(dt):
            snackbar = Factory.StyledSnackbar()
            snackbar.ids.label.text = text
            snackbar.open()
        Clock.schedule_once(_show)

    def open_camera(self):
        try:
            from android.permissions import request_permissions, check_permission, Permission
            if check_permission(Permission.CAMERA):
                self._actually_open_camera_android()
            else:
                request_permissions([Permission.CAMERA], self._on_camera_permission)
        except ImportError:
            self.show_snackbar("Не удалось запросить разрешение на камеру")

    def _on_camera_permission(self, permissions, results):
        if results and results[0]:
            Clock.schedule_once(lambda dt: self._actually_open_camera_android(), 0.5)
        else:
            self.show_snackbar("Необходимо разрешение на камеру")

    def _actually_open_camera_android(self):
        try:
            import os
            from jnius import autoclass
            from android import activity

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity_instance = PythonActivity.mActivity

            # 1. Формируем путь для сохранения файла
            app_dir = activity_instance.getExternalFilesDir(None).getAbsolutePath()
            image_path = os.path.join(app_dir, "camera_photo.jpg")
            self._camera_image_path = image_path

            if os.path.exists(image_path):
                os.remove(image_path)

            # 2. Привязываем обработчик возврата из камеры
            try:
                activity.unbind(on_activity_result=self._on_camera_result)
            except ValueError:
                pass
            activity.bind(on_activity_result=self._on_camera_result)

            # 3. ВЫЗЫВАЕМ ФУНКЦИЮ В ГЛАВНОМ ПОТОКЕ ANDROID
            self._dispatch_camera_intent(image_path)

        except Exception as e:
            self.show_snackbar(f"Ошибка подготовки камеры: {str(e)}")

    def _compress_image(self, input_path):
        try:
            img = Image.open(input_path)
            orig_w, orig_h = img.size
            max_size = 1600 # 1600px хватит для точности и это ускорит сервер в 5 раз

            if max(orig_w, orig_h) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            new_w, new_h = img.size
            scale = new_w / orig_w # Коэффициент масштабирования

            temp_path = input_path.replace(".jpg", "_compressed.jpg")
            img.save(temp_path, "JPEG", quality=80, optimize=True)
            return temp_path, scale
        except Exception as e:
            return input_path, 1.0

    @run_on_ui_thread
    def _dispatch_camera_intent(self, image_path):
        # Эта функция теперь гарантированно выполняется в UI-потоке Android!
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')
            File = autoclass('java.io.File')
            FileProvider = autoclass('androidx.core.content.FileProvider')

            activity_instance = PythonActivity.mActivity
            image_file = File(image_path)
            authority = "com.map2motion.map2motion.provider"

            uri = FileProvider.getUriForFile(activity_instance, authority, image_file)

            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            parcelable_uri = cast('android.os.Parcelable', uri)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, parcelable_uri)
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            activity_instance.startActivityForResult(intent, 2001)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _on_camera_result(self, request_code, result_code, intent):
        from android import activity
        activity.unbind(on_activity_result=self._on_camera_result)

        if request_code == 2001 and result_code == -1:
            Clock.schedule_once(lambda dt: self.img_ready(self._camera_image_path))

    def pick_from_gallery(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_MEDIA_IMAGES], self._on_gallery_permission)
        except ImportError:
            self.show_snackbar("Только Android")
    
    def _on_gallery_permission(self, permissions, results):
        if results and results[0]:
            from plyer import filechooser
            filechooser.open_file(on_selection=self._on_gallery_select, filters=["*.jpg", "*.jpeg", "*.png"])
        else:
            self.show_snackbar("Нет доступа к галерее")

    def _on_gallery_select(self, selection):
        if not selection: return
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
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()
            input_stream = resolver.openInputStream(uri)

            app_dir = activity.getFilesDir().getAbsolutePath()
            file_path = os.path.join(app_dir, "selected_image.jpg")

            output_stream = autoclass('java.io.FileOutputStream')(file_path)
            buffer = autoclass('java.nio.ByteBuffer').allocate(4096)
            byte_array = buffer.array()

            while True:
                length = input_stream.read(byte_array)
                if length == -1: break
                output_stream.write(byte_array, 0, length)

            input_stream.close()
            output_stream.close()
            return file_path
        except Exception as e:
            return None


    def img_ready(self, filename):
        self.captured_image_path = filename
        line_screen = self.sm.get_screen("line")
        line_screen.set_image(filename)
        self.go_next("line")

if __name__ == "__main__":
    MainApp().run()
