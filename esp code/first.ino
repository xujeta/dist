#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_NeoPixel.h> // Подключаем библиотеку для RGB светодиода

const char* ssid = "Lobanov";
const char* password = "12345678";

WebServer server(80);

// --- ПИНЫ РЕЛЕ ---
const int RELAY1_PIN = 2; 
const int RELAY2_PIN = 4;
const int RELAY3_PIN = 5;

// --- НАСТРОЙКИ RGB СВЕТОДИОДА ---
const int RGB_PIN = 48; 
const int NUMPIXELS = 1;

Adafruit_NeoPixel pixels(NUMPIXELS, RGB_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(115200);
  
  // Инициализация RGB светодиода
  pixels.begin();
  pixels.setBrightness(50); // Яркость от 0 до 255 (50 - чтобы не слепило)
  pixels.clear();
  pixels.setPixelColor(0, pixels.Color(0, 0, 255)); // Синий цвет при включении (Ожидание)
  pixels.show();

  // Настройка пинов реле (изначально выключаем, чтобы не дергалось)
  digitalWrite(RELAY1_PIN, LOW); 
  digitalWrite(RELAY2_PIN, LOW);
  digitalWrite(RELAY3_PIN, LOW);
  
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  pinMode(RELAY3_PIN, OUTPUT);
  
  WiFi.softAP(ssid, password);
  
  // Эндпоинт для статуса
  server.on("/status", []() {
    String json = "{";
    json += "\"r1\":" + String(digitalRead(RELAY1_PIN)) + ",";
    json += "\"r2\":" + String(digitalRead(RELAY2_PIN)) + ",";
    json += "\"r3\":" + String(digitalRead(RELAY3_PIN));
    json += "}";
    server.send(200, "application/json", json);
  });

  // Универсальный сеттер с логикой цветов
  server.on("/set", []() {
    int active_relays = 0; // Считаем, сколько реле мы сейчас включим

    // Обрабатываем РЕЛЕ 1
    if (server.hasArg("r1")) {
      bool turn_on = server.arg("r1") == "1";
      digitalWrite(RELAY1_PIN, turn_on ? HIGH : LOW);
      if (turn_on) active_relays++;
    }
    
    // Обрабатываем РЕЛЕ 2
    if (server.hasArg("r2")) {
      bool turn_on = server.arg("r2") == "1";
      digitalWrite(RELAY2_PIN, turn_on ? HIGH : LOW);
      if (turn_on) active_relays++;
    }
    
    // Обрабатываем РЕЛЕ 3
    if (server.hasArg("r3")) {
      bool turn_on = server.arg("r3") == "1";
      digitalWrite(RELAY3_PIN, turn_on ? HIGH : LOW);
      if (turn_on) active_relays++;
    }

    // === ЛОГИКА ЦВЕТОВ RGB ===
    pixels.clear();
    if (active_relays == 0) {
      pixels.setPixelColor(0, pixels.Color(0, 0, 255));     // 0 реле: СИНИЙ (Ждет)
    } 
    else if (active_relays == 1) {
      pixels.setPixelColor(0, pixels.Color(0, 255, 0));     // 1 реле: ЗЕЛЕНЫЙ
    } 
    else if (active_relays == 2) {
      pixels.setPixelColor(0, pixels.Color(255, 150, 0));   // 2 реле: ЖЕЛТО-ОРАНЖЕВЫЙ
    } 
    else if (active_relays == 3) {
      pixels.setPixelColor(0, pixels.Color(255, 0, 0));     // 3 реле: КРАСНЫЙ
    }
    pixels.show(); // Применяем цвет
    // =========================

    server.send(200, "text/plain", "OK");
  });

  server.begin();
}

void loop() {
  server.handleClient();
}
