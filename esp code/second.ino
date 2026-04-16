#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_NeoPixel.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Константы для логики реле
#define RELAY_ON  LOW
#define RELAY_OFF HIGH

const char* ssid = "Lobanov";
const char* password = "12345678";

WebServer server(80);

// -------- РЕЛЕ --------
const int RELAY1_PIN = 12;
const int RELAY2_PIN = 13;
const int RELAY3_PIN = 14;
// -------- RGB --------
const int RGB_PIN = 48;
const int NUMPIXELS = 1;
Adafruit_NeoPixel pixels(NUMPIXELS, RGB_PIN, NEO_GRB + NEO_KHZ800);

int level = 0;

#define I2C_SDA 21
#define I2C_SCL 20
LiquidCrystal_I2C lcd(0x27, 16, 2);

void updateLedColor() {
  uint32_t color;
  if(level == 0)      color = pixels.Color(0,0,255);     // синий
  else if(level == 1) color = pixels.Color(0,255,0);     // зелёный
  else if(level == 2) color = pixels.Color(255,120,0);   // оранжевый
  else                color = pixels.Color(255,0,0);     // красный

  pixels.setPixelColor(0, color);
  pixels.show();
}

void updateLCD() {
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("R1:");
  lcd.print(level >= 1 ? "ON " : "OFF");
  lcd.print(" R2:");
  lcd.print(level >= 2 ? "ON" : "OFF");

  lcd.setCursor(0,1);
  lcd.print("R3:");
  lcd.print(level >= 3 ? "ON " : "OFF");
}

void applyLevel(int lvl) {
  level = constrain(lvl, 0, 3);

  // Прямое управление пинами
  digitalWrite(RELAY1_PIN, (level >= 1) ? RELAY_ON : RELAY_OFF);
  digitalWrite(RELAY2_PIN, (level >= 2) ? RELAY_ON : RELAY_OFF);
  digitalWrite(RELAY3_PIN, (level >= 3) ? RELAY_ON : RELAY_OFF);

  updateLedColor();
  updateLCD();
}

void handlePing() {
  server.send(200, "text/plain", "alive");
}

void handleStatus() {
  // Читаем текущее состояние пинов
  int r1 = digitalRead(RELAY1_PIN);
  int r2 = digitalRead(RELAY2_PIN);
  int r3 = digitalRead(RELAY3_PIN);

  String json = "{";
  json += "\"level\":" + String(level) + ",";
  json += "\"r1\":" + String(r1) + ",";
  json += "\"r2\":" + String(r2) + ",";
  json += "\"r3\":" + String(r3);
  json += "}";
  server.send(200, "application/json", json);
}

void handleSetLevel() {
  if(!server.hasArg("level")) {
    server.send(400, "text/plain", "missing level");
    return;
  }
  applyLevel(server.arg("level").toInt());
  handleStatus();
}

void handleSetRelays() {
  // Если передаем 1 — включит (HIGH), если 0 — выключит (LOW)
  if(server.hasArg("r1")) digitalWrite(RELAY1_PIN, server.arg("r1").toInt() == 1 ? RELAY_ON : RELAY_OFF);
  if(server.hasArg("r2")) digitalWrite(RELAY2_PIN, server.arg("r2").toInt() == 1 ? RELAY_ON : RELAY_OFF);
  if(server.hasArg("r3")) digitalWrite(RELAY3_PIN, server.arg("r3").toInt() == 1 ? RELAY_ON : RELAY_OFF);
  handleStatus();
}

void setup() {
  Serial.begin(115200);

  // Важно: сначала ставим HIGH (выключено), потом включаем как OUTPUT
  // Это предотвратит щелчок реле при каждой перезагрузке
  digitalWrite(RELAY1_PIN, RELAY_OFF);
  digitalWrite(RELAY2_PIN, RELAY_OFF);
  digitalWrite(RELAY3_PIN, RELAY_OFF);
  
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  pinMode(RELAY3_PIN, OUTPUT);

  pixels.begin();
  pixels.setBrightness(50);
  Wire.begin(I2C_SDA, I2C_SCL);
  lcd.init();
  lcd.backlight();
  
  delay(500); // Даем время железу "проснуться"
  applyLevel(0);

  WiFi.softAP(ssid, password);
  server.on("/ping", handlePing);
  server.on("/status", handleStatus);
  server.on("/set", handleSetLevel);
  server.on("/setRelays", handleSetRelays);
  server.begin();
}

void loop() {
  server.handleClient();
}
