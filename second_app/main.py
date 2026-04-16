from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivy.utils import platform
import threading
import requests
from android.permissions import request_permissions, Permission

ESP_IP = "192.168.4.1"
ESP_PORT = 80
BASE_URL = f"http://{ESP_IP}:{ESP_PORT}"


class WiFiRelayApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_connected = False
        self.level = 0
        self.command_in_progress = False

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"

        request_permissions([
            Permission.INTERNET,
            Permission.ACCESS_NETWORK_STATE,
            Permission.ACCESS_WIFI_STATE,
            Permission.CHANGE_WIFI_STATE
        ])

        return Builder.load_file("app.kv")

    def on_start(self):
        Clock.schedule_interval(self.check_status, 2)

    def check_status(self, dt):

        if self.command_in_progress:
            return

        threading.Thread(
            target=self._fetch_status,
            daemon=True
        ).start()

    def _fetch_status(self):

        try:

            resp = requests.get(f"{BASE_URL}/status", timeout=2)

            if resp.status_code == 200:

                data = resp.json()

                self.level = data.get("level", 0)

                self.is_connected = True
                self.update_ui()

            else:

                self.is_connected = False
                self.update_status("Статус: Ошибка сервера", (1,0,0,1))

        except Exception:

            self.is_connected = False
            self.update_status("Статус: Нет связи с ESP", (1,0,0,1))

    @mainthread
    def update_ui(self):

        if self.is_connected:
            self.root.ids.status_label.text = "Статус: Подключено"
            self.root.ids.status_label.text_color = (0,1,0,1)
        else:
            self.root.ids.status_label.text = "Статус: Отключено"
            self.root.ids.status_label.text_color = (1,0,0,1)

        self._update_button_color("btn_relay1", self.level >= 1)
        self._update_button_color("btn_relay2", self.level >= 2)
        self._update_button_color("btn_relay3", self.level >= 3)

    def _update_button_color(self, btn_id, state):

        btn = self.root.ids[btn_id]

        if state:
            btn.md_bg_color = (0,0.8,0,1)
        else:
            btn.md_bg_color = (0.33, 0.33, 0.33, 1)  # OFF (#545454)

    def update_status(self, text, color):

        @mainthread
        def _update():
            self.root.ids.status_label.text = text
            self.root.ids.status_label.text_color = color

        Clock.schedule_once(lambda dt: _update())

    def set_level(self, level):

        # мгновенный отклик UI
        old_level = self.level
        self.level = level
        self.command_in_progress = True
        self.update_ui()

        threading.Thread(
            target=self._send_level,
            args=(level, old_level),
            daemon=True
        ).start()

    def _send_level(self, level, old_level):

        try:

            resp = requests.get(
                f"{BASE_URL}/set",
                params={"level": level},
                timeout=2
            )

            if resp.status_code == 200:
                self.command_in_progress = False
                self._fetch_status()

            else:
                self.rollback(old_level)

        except Exception:

            self.command_in_progress = False
            self.rollback(old_level)

    def rollback(self, level):

        self.level = level

        @mainthread
        def _update():
            self.update_ui()

        Clock.schedule_once(lambda dt: _update())

    # ---------- КНОПКИ ----------

    def toggle_relay1(self):

        if self.level >= 1:
            self.set_level(0)
        else:
            self.set_level(1)

    def toggle_relay2(self):

        if self.level >= 2:
            self.set_level(1)
        else:
            self.set_level(2)

    def toggle_relay3(self):

        if self.level >= 3:
            self.set_level(2)
        else:
            self.set_level(3)

    def off_all(self):

        self.set_level(0)


if __name__ == "__main__":
    WiFiRelayApp().run()
