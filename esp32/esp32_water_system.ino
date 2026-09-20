/*
  ============================================================================
  🌹 BABY ROSE - CLOUD SMART WATERING SYSTEM (ESP32 FIRMWARE v2.2)
  ============================================================================
  
  LIVE RAILWAY BACKEND: https://kayal-production.up.railway.app
  
  INSTRUCTIONS FOR ARDUINO IDE:
  1. Select Board: "ESP32 Dev Module" (or your specific ESP32 board).
  2. Select Port: The COM / tty USB port connected to your ESP32.
  3. Click Upload (➡️ arrow button)!
  ============================================================================
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// ============================================================
// 1. Wi-Fi Configuration
// ============================================================
const char* ssid     = "Dialog 4G 435";
const char* password = "419474D3";

// ============================================================
// 2. Railway Server URL (Configured for your live deployment)
// ============================================================
const char* serverDomain = "https://kayal-production.up.railway.app";

// ============================================================
// 3. Hardware Configuration
// ============================================================
const int sensorPin = 32; // Soil Moisture Sensor Analog Pin
const int relayPin  = 25; // Water Pump Relay Control Pin

// Relay logic:
// LOW  = Pump OFF
// HIGH = Pump ON
const int PUMP_ON  = HIGH;
const int PUMP_OFF = LOW;

// ============================================================
// Helper Functions
// ============================================================
void pumpOff() {
  digitalWrite(relayPin, PUMP_OFF);
}

void pumpOn() {
  digitalWrite(relayPin, PUMP_ON);
}

// Dynamically construct full endpoint URLs
String getEndpointURL(const char* path) {
  String domain = String(serverDomain);
  if (domain.endsWith("/")) {
    domain = domain.substring(0, domain.length() - 1);
  }
  return domain + String(path);
}

// Send current soil moisture reading to Railway DB
void sendSensorData(int moisture) {
  HTTPClient http;
  WiFiClientSecure client;
  client.setInsecure(); // Bypass SSL verification for HTTPS cloud host

  String url = getEndpointURL("/sensor-data");

  if (url.startsWith("https")) {
    http.begin(client, url);
  } else {
    http.begin(url);
  }

  http.addHeader("Content-Type", "application/json");

  String sensorJson = "{\"moisture\":" + String(moisture) + "}";
  int httpResponseCode = http.POST(sensorJson);

  Serial.print("[HTTP POST /sensor-data] Status Code: ");
  Serial.println(httpResponseCode);

  http.end();
}

// Check if user clicked WATER NOW, WATER INFINITELY, or STOP
bool checkWaterCommand(int &outDuration, bool &outStopPump) {
  HTTPClient http;
  WiFiClientSecure client;
  client.setInsecure();

  String url = getEndpointURL("/pump-command");
  bool shouldWater = false;
  outDuration = 3;
  outStopPump = false;

  if (url.startsWith("https")) {
    http.begin(client, url);
  } else {
    http.begin(url);
  }

  int httpResponseCode = http.GET();

  if (httpResponseCode == 200) {
    String response = http.getString();
    Serial.print("[HTTP GET /pump-command] Response: ");
    Serial.println(response);

    if (response.indexOf("\"stop_pump\":true") >= 0) {
      outStopPump = true;
    }

    if (response.indexOf("\"water\":true") >= 0) {
      shouldWater = true;

      int durationIdx = response.indexOf("\"duration\":");
      if (durationIdx >= 0) {
        int parsedDuration = response.substring(durationIdx + 11).toInt();
        if (parsedDuration > 0 && parsedDuration <= 60) {
          outDuration = parsedDuration;
        }
      }
    }
  } else {
    Serial.print("[HTTP GET /pump-command] Failed with code: ");
    Serial.println(httpResponseCode);
  }

  http.end();
  return shouldWater;
}

// Report completed watering event to Railway DB
void reportWatering(int durationSeconds) {
  HTTPClient http;
  WiFiClientSecure client;
  client.setInsecure();

  String url = getEndpointURL("/watering");

  if (url.startsWith("https")) {
    http.begin(client, url);
  } else {
    http.begin(url);
  }

  http.addHeader("Content-Type", "application/json");

  String wateringJson = "{\"duration\":" + String(durationSeconds) + ", \"triggered_by\":\"esp32\"}";
  int httpResponseCode = http.POST(wateringJson);

  Serial.print("[HTTP POST /watering] Status Code: ");
  Serial.println(httpResponseCode);

  http.end();
}

// ============================================================
// Arduino Setup
// ============================================================
void setup() {
  Serial.begin(115200);

  pinMode(relayPin, OUTPUT);
  pumpOff(); // Safety check: Start with pump OFF

  Serial.println();
  Serial.println("=========================================");
  Serial.println("   Baby Rose Cloud Water System (ESP32)  ");
  Serial.println("=========================================");

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(ssid);

  while (WiFi.status() != WL_CONNECTED) {
    pumpOff(); // Keep pump OFF while connecting
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("✅ Wi-Fi Connected successfully!");
  Serial.print("ESP32 Local IP Address: ");
  Serial.println(WiFi.localIP());

  pumpOff();
  Serial.println("System initialized. Syncing with Railway Cloud...");
}

// ============================================================
// Main Loop
// ============================================================
void loop() {
  pumpOff(); // Safety lock

  // 0. Auto Reconnect Wi-Fi if lost
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ Wi-Fi disconnected! Reconnecting...");
    WiFi.disconnect();
    WiFi.reconnect();
    delay(2000);
    return;
  }

  // 1. Read Soil Moisture from Sensor
  int moisture = analogRead(sensorPin);
  Serial.print("🌱 Current Soil Moisture Reading: ");
  Serial.println(moisture);

  // 2. Send Moisture Reading to Railway Database
  sendSensorData(moisture);

  // 3. Check for Water Command or Stop Command
  int waterDuration = 3;
  bool stopRequested = false;
  bool waterNow = checkWaterCommand(waterDuration, stopRequested);

  if (stopRequested) {
    pumpOff();
    Serial.println("🛑 STOP command received! Pump locked OFF.");
  } 
  else if (waterNow) {
    Serial.println();
    Serial.print("💧 WATERING STARTED! Max duration: ");
    Serial.print(waterDuration);
    Serial.println(" seconds");

    // Turn Pump ON
    pumpOn();
    Serial.println("Pump ON ⚡");

    int elapsedSeconds = 0;

    // Run pump for waterDuration seconds while listening for STOP
    for (int i = 0; i < waterDuration; i++) {
      delay(1000);
      elapsedSeconds++;

      // Check if user clicked STOP button during active watering
      int dummyDur = 3;
      bool manualStop = false;
      checkWaterCommand(dummyDur, manualStop);

      if (manualStop) {
        Serial.println("🛑 MANUAL STOP BUTTON CLICKED DURING WATERING!");
        break;
      }
    }

    // Turn Pump OFF
    pumpOff();
    Serial.print("Pump OFF 🛑. Total watering duration: ");
    Serial.print(elapsedSeconds);
    Serial.println("s");

    // 4. Report completed watering to Railway Database
    reportWatering(elapsedSeconds);
  }

  // Poll server every 5 seconds
  delay(5000);
}
