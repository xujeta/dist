#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_NeoPixel.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

const char* ssid = "Lobanov";
const char* password = "12345678";

WebServer server(80);

// -------- РЕЛЕ --------
const int RELAY1_PIN = 2;
const int RELAY2_PIN = 4;
const int RELAY3_PIN = 5;

// -------- RGB --------
const int RGB_PIN = 48;
const int NUMPIXELS = 1;

Adafruit_NeoPixel pixels(NUMPIXELS, RGB_PIN, NEO_GRB + NEO_KHZ800);

int level = 0;

#define I2C_SDA 21
#define I2C_SCL 20

LiquidCrystal_I2C lcd(0x27, 16, 2);

// ОБНОВЛЕНИЕ ЦВЕТА LED

void updateLedColor() {

  uint32_t color;

  if(level == 0)
    color = pixels.Color(0,0,255);     // синий
  else if(level == 1)
    color = pixels.Color(0,255,0);     // зелёный
  else if(level == 2)
    color = pixels.Color(255,120,0);   // оранжевый
  else
    color = pixels.Color(255,0,0);     // красный

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

// ПРИМЕНЕНИЕ УРОВНЯ

void applyLevel(int lvl) {

  level = constrain(lvl, 0, 3);

  bool r1 = false;
  bool r2 = false;
  bool r3 = false;

  if(level >= 1) r1 = true;
  if(level >= 2) r2 = true;
  if(level >= 3) r3 = true;

  digitalWrite(RELAY1_PIN, r1);
  digitalWrite(RELAY2_PIN, r2);
  digitalWrite(RELAY3_PIN, r3);

  updateLedColor();
  updateLCD();
}


void handlePing() {
  server.send(200, "text/plain", "alive");
}


void handleStatus() {

  bool r1 = digitalRead(RELAY1_PIN);
  bool r2 = digitalRead(RELAY2_PIN);
  bool r3 = digitalRead(RELAY3_PIN);

  String json = "{";
  json += "\"level\":" + String(level) + ",";
  json += "\"r1\":" + String(r1) + ",";
  json += "\"r2\":" + String(r2) + ",";
  json += "\"r3\":" + String(r3);
  json += "}";

  server.send(200, "application/json", json);
}

// ------------------------------------------------

void handleSetLevel() {

  if(!server.hasArg("level")) {
    server.send(400, "text/plain", "missing level");
    return;
  }

  int newLevel = server.arg("level").toInt();

  applyLevel(newLevel);

  handleStatus();
}

// ------------------------------------------------

void handleSetRelays() {

  if(server.hasArg("r1"))
    digitalWrite(RELAY1_PIN, server.arg("r1").toInt());

  if(server.hasArg("r2"))
    digitalWrite(RELAY2_PIN, server.arg("r2").toInt());

  if(server.hasArg("r3"))
    digitalWrite(RELAY3_PIN, server.arg("r3").toInt());

  handleStatus();
}

// ------------------------------------------------

void setup() {

  Serial.begin(115200);

  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  pinMode(RELAY3_PIN, OUTPUT);

  // RGB init
  pixels.begin();
  pixels.setBrightness(50);

  Wire.begin(I2C_SDA, I2C_SCL);

  lcd.init();
  lcd.backlight();
  applyLevel(0);

  WiFi.softAP(ssid, password);

  Serial.println("AP started");
  Serial.println(WiFi.softAPIP());

  server.on("/ping", handlePing);
  server.on("/status", handleStatus);
  server.on("/set", handleSetLevel);
  server.on("/setRelays", handleSetRelays);

  server.begin();
}

// ------------------------------------------------

void loop() {
  server.handleClient();
}
