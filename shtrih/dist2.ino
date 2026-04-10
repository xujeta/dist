#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_NeoPixel.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

const char* ssid = "Lobanov";
const char* password = "12345678";

WebServer server(80);

const int RELAY1_PIN = 13;
const int RELAY2_PIN = 12;
const int RELAY3_PIN = 14;

const int RGB_PIN = 48; 
const int NUMPIXELS = 1;
Adafruit_NeoPixel pixels(NUMPIXELS, RGB_PIN, NEO_GRB + NEO_KHZ800);

#define I2C_SDA 21
#define I2C_SCL 20
LiquidCrystal_I2C lcd(0x27, 16, 2);

int currentLevel = 0;

void updateLCD() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Level: ");
  lcd.print(currentLevel);
  
  lcd.setCursor(0, 1);
  lcd.print("R1:");
  lcd.print(currentLevel >= 1 ? "ON " : "OFF");
  lcd.print(" R2:");
  lcd.print(currentLevel >= 2 ? "ON " : "OFF");
}

void updateLedColor() {
  pixels.clear();
  if (currentLevel == 0) {
    pixels.setPixelColor(0, pixels.Color(0, 0, 255));   // Синий
  }
  else if (currentLevel == 1) {
    pixels.setPixelColor(0, pixels.Color(0, 255, 0));   // Зелёный
  }
  else if (currentLevel == 2) {
    pixels.setPixelColor(0, pixels.Color(255, 100, 0)); // Оранжевый
  }
  else {
    pixels.setPixelColor(0, pixels.Color(255, 0, 0));   // Красный
  }
  pixels.show();
}

void applyLevel(int level) {
  currentLevel = level;

  digitalWrite(RELAY1_PIN, currentLevel >= 1 ? LOW : HIGH);
  digitalWrite(RELAY2_PIN, currentLevel >= 2 ? LOW : HIGH);
  digitalWrite(RELAY3_PIN, currentLevel >= 3 ? LOW : HIGH);

  updateLedColor();
  updateLCD();
}

void setup() {
  Serial.begin(115200);

  // Инициализация LCD
  Wire.begin(I2C_SDA, I2C_SCL);
  lcd.init();
  lcd.backlight();

  // Инициализация Реле
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  pinMode(RELAY3_PIN, OUTPUT);

  // Инициализация RGB
  pixels.begin();
  pixels.setBrightness(50);

  // Установка начального состояния (все выключено)
  applyLevel(0);

  WiFi.softAP(ssid, password);
  Serial.println("AP IP: " + WiFi.softAPIP().toString());

  // --- API ---

  server.on("/status", []() {
    String json = "{";
    json += "\"level\":" + String(currentLevel) + ",";
    json += "\"r1\":" + String(!digitalRead(RELAY1_PIN)) + ","; 
    json += "\"r2\":" + String(!digitalRead(RELAY2_PIN)) + ",";
    json += "\"r3\":" + String(!digitalRead(RELAY3_PIN));
    json += "}";
    server.send(200, "application/json", json);
  });

  server.on("/set", []() {
    if (server.hasArg("level")) {
      int level = server.arg("level").toInt();
      if (level < 0) level = 0;
      if (level > 3) level = 3;
      applyLevel(level);
      server.send(200, "text/plain", "OK. Level set to " + String(level));
    } else {
      server.send(400, "text/plain", "Missing level");
    }
  });

  server.on("/off", []() {
    applyLevel(0);
    server.send(200, "text/plain", "OFF");
  });

  server.begin();
}

void loop() {
  server.handleClient();
}
