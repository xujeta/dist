#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_NeoPixel.h>

const char* ssid = "Lobanov";
const char* password = "12345678";

WebServer server(80);

const int RELAY1_PIN = 2;
const int RELAY2_PIN = 4;
const int RELAY3_PIN = 5;

const int RGB_PIN = 48;
const int NUMPIXELS = 1;

Adafruit_NeoPixel pixels(NUMPIXELS, RGB_PIN, NEO_GRB + NEO_KHZ800);

int currentLevel = 0;

void updateLedColor() {
  pixels.clear();

  // Используем currentLevel вместо чтения пинов, так надежнее
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
  Serial.println("LED updated to level: " + String(currentLevel));
}

void applyLevel(int level) {

  currentLevel = level;

  digitalWrite(RELAY1_PIN, level >= 1 ? HIGH : LOW);
  digitalWrite(RELAY2_PIN, level >= 2 ? HIGH : LOW);
  digitalWrite(RELAY3_PIN, level >= 3 ? HIGH : LOW);

  updateLedColor();
}

void setup() {

  Serial.begin(115200);

  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  pinMode(RELAY3_PIN, OUTPUT);

  digitalWrite(RELAY1_PIN, LOW);
  digitalWrite(RELAY2_PIN, LOW);
  digitalWrite(RELAY3_PIN, LOW);

  pixels.begin();
  pixels.setBrightness(50); // 3. Ставим яркость побольше
  updateLedColor();

  WiFi.softAP(ssid, password);

  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());

  // ---------- STATUS ----------

  server.on("/status", []() {

    String json = "{";
    json += "\"level\":" + String(currentLevel) + ",";
    json += "\"r1\":" + String(digitalRead(RELAY1_PIN)) + ",";
    json += "\"r2\":" + String(digitalRead(RELAY2_PIN)) + ",";
    json += "\"r3\":" + String(digitalRead(RELAY3_PIN));
    json += "}";

    server.send(200, "application/json", json);
  });

  // ---------- SET LEVEL ----------

  server.on("/set", []() {

    if (!server.hasArg("level")) {
      server.send(400, "text/plain", "Missing level");
      return;
    }

    int level = server.arg("level").toInt();

    if (level < 0) level = 0;
    if (level > 3) level = 3;

    applyLevel(level);

    server.send(200, "text/plain", "OK");
  });

  // ---------- OFF ----------

  server.on("/off", []() {

    applyLevel(0);

    server.send(200, "text/plain", "OFF");
  });

  server.begin();

  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
}
