import requests
import threading
from kivy.logger import Logger

class RelayController:
    def __init__(self, esp_ip="192.168.4.1"):
        self.base_url = f"http://{esp_ip}"

    def set_relays(self, r1: bool, r2: bool, r3: bool):
        # Превращаем True/False в 1/0
        params = {
            "r1": 1 if r1 else 0,
            "r2": 1 if r2 else 0,
            "r3": 1 if r3 else 0
        }
        
        def _send():
            try:
                # Отправляем один запрос вместо трех!
                requests.get(f"{self.base_url}/setRelays", params=params, timeout=0.5)
            except Exception as e:
                print(f"Relay Error: {e}")

        threading.Thread(target=_send, daemon=True).start()