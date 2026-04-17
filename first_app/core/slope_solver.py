import time
import threading
import math

# ИМПОРТИРУЕМ ТВОЙ НАСТОЯЩИЙ КОНТРОЛЛЕР!
from core.relay_controller import RelayController 

class RobotSimulator(threading.Thread):
    def __init__(self, profile_data, min_speed, pixel_to_meter, t1, t2, log_callback, led_callback, esp_ip="192.168.4.1"):
        super().__init__(daemon=True)
        self.profile = profile_data
        
        # Подключаем твой класс
        self.rc = RelayController(esp_ip)

        self.speed_kmh = float(min_speed) if float(min_speed) > 0 else 1.0
        self.speed_mps = self.speed_kmh / 3.6 
        self.pixel_to_meter = float(pixel_to_meter)
        self.t1 = float(t1) 
        self.t2 = float(t2)
        
        self.log_callback = log_callback # Пишет в консоль на экране
        self.led_callback = led_callback # Зажигает кружочки на экране
        
        self.running = True

    def calculate_slope_angle(self, dx_meters, dh_meters):
        if dx_meters == 0: return 0.0
        return math.degrees(math.atan(dh_meters / dx_meters))

    def run(self):
        self.log_callback("--- СТАРТ СИМУЛЯЦИИ ---")
        
        # --- НОВАЯ МАТЕМАТИКА: Ищем размах графика ---
        # Чтобы угол совпадал с картинкой, мы должны знать максимальные ширину и высоту
        dists = [p['dist'] for p in self.profile]
        heights = [p['h'] for p in self.profile]
        
        max_d, min_d = max(dists), min(dists)
        max_h, min_h = max(heights), min(heights)
        
        dist_range = max_d - min_d if max_d > min_d else 1
        height_range = max_h - min_h if max_h > min_h else 1

        for i in range(len(self.profile) - 1):
            if not self.running: break
                
            p1, p2 = self.profile[i], self.profile[i+1]
            
            # Сырые значения между двумя точками
            dx_raw = p2['dist'] - p1['dist']
            dh_raw = p2['h'] - p1['h']
            
            if dx_raw <= 0: continue
            
            # 1. Считаем РЕАЛЬНОЕ время (в метрах), чтобы скорость робота работала правильно
            dx_meters = dx_raw * self.pixel_to_meter
            time_to_travel = dx_meters / self.speed_mps
            
            # 2. Считаем ВИЗУАЛЬНЫЙ угол (как нарисовано на экране)
            # Переводим смещение в проценты (от 0 до 100) относительно всего графика
            dx_percent = (dx_raw / dist_range) * 100
            dh_percent = (dh_raw / height_range) * 100
            
            # math.atan2 сам разберется со знаками. Подъем = +, Спуск = -
            import math
            angle = math.degrees(math.atan2(dh_percent, dx_percent))
            
            # === ЛОГИКА РЕЛЕ ===
            # Первое реле (База) работает ВСЕГДА на протяжении всего маршрута
            r1 = 1 
            r2 = 0
            r3 = 0
            
            # Второе и Третье включаются ТОЛЬКО если это ПОДЪЕМ (angle > 0)
            # Если это спуск (например, angle = -45), условия не сработают!
            if angle >= self.t1: 
                r2 = 1
                
            if angle >= self.t2: 
                r3 = 1
            # ===================

            # Обновляем лампочки
            self.led_callback(r1, r2, r3)
            
            # Пишем лог с новым красивым углом
            log_text = f"Участок {i+1}: Угол {angle:.1f}° | R1={r1} R2={r2} R3={r3} | Ждем {time_to_travel:.1f}с"
            self.log_callback(log_text)

            # Отправляем на ESP32
            self.rc.set_relays(r1, r2, r3)
            
            # Ожидание
            wait_time = time_to_travel
            while wait_time > 0 and self.running:
                time.sleep(0.1)
                wait_time -= 0.1

        if self.running:
            self.rc.set_relays(0, 0, 0)
            self.led_callback(0, 0, 0)
            self.log_callback("--- ФИНИШ! МАРШРУТ ПРОЙДЕН ---")

    def stop(self):
        # Если нажали кнопку "СТОП"
        self.running = False
        self.rc.set_relays(0, 0, 0)
        self.led_callback(0, 0, 0)
        self.log_callback("--- СТОП! ПРЕРВАНО ПОЛЬЗОВАТЕЛЕМ ---")