#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Deklarasi Pin Hardware
#define PIN_PIR       13  // Sensor Keberadaan Manusia (Edge 1)
#define PIN_POT       34  // Sensor Aktivitas Kompor (Edge 2 - Analog RMS)
#define PIN_LED_ALERT 12  // Output Alarm Visual
#define PIN_BUZZER    14  // Output Alarm Suara

// Batas Konfigurasi Sistem
#define THRESHOLD_KOMPOR_ON 1500  // Nilai ADC potensiometer saat kompor dianggap aktif
#define TIMEOUT_IDLE_SEC    15    // Toleransi waktu kompor ditinggal (15 detik)

// Konfigurasi Network & MQTT Broker
const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* mqtt_server = "broker.hivemq.com";
const int   mqtt_port = 1883;

const char* topic_telemetry = "stovewatch/telemetry";
const char* topic_alert     = "stovewatch/alert";

WiFiClient espClient;
PubSubClient client(espClient);

// Variabel Waktu & Status Sistem
unsigned long lastPersonSeenTime = 0;
bool isStoveActive = false;
bool isPersonPresent = false;

void setup_wifi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" -> Connected!");
}

void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT Broker HiveMQ...");
    if (client.connect("StoveWatch_Wokwi_Node")) {
      Serial.println(" -> Connected!");
    } else {
      Serial.print(" Failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 2 seconds...");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_POT, INPUT);
  pinMode(PIN_LED_ALERT, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  digitalWrite(PIN_LED_ALERT, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  
  lastPersonSeenTime = millis();
}

void loop() {
  if (!client.connected()) {
    reconnect_mqtt();
  }
  client.loop();

  // 1. Baca data sensor fisik
  int potValue = analogRead(PIN_POT);
  int pirState = digitalRead(PIN_PIR);

  isStoveActive = (potValue >= THRESHOLD_KOMPOR_ON);
  isPersonPresent = (pirState == HIGH);

  unsigned long currentMillis = millis();

  // 2. Pemrosesan Data: Presence Time Decay
  if (isPersonPresent) {
    lastPersonSeenTime = currentMillis; // Reset idle timer jika orang terlihat
  }
  
  unsigned long idleTimeSec = (currentMillis - lastPersonSeenTime) / 1000;

  // 3. Logika Fusi Keputusan (StoveWatch Decision Matrix)
  String systemStatus = "NORMAL";

  if (!isStoveActive) {
    // Kondisi 1: Kompor Mati -> STANDBY/NORMAL
    systemStatus = "NORMAL (STANDBY)";
    digitalWrite(PIN_LED_ALERT, LOW);
    noTone(PIN_BUZZER);
  } else {
    if (isPersonPresent) {
      // Kondisi 2: Kompor Aktif + Orang Terdeteksi -> SAFE
      systemStatus = "SAFE (COOKING)";
      digitalWrite(PIN_LED_ALERT, LOW);
      noTone(PIN_BUZZER);
    } else if (idleTimeSec < TIMEOUT_IDLE_SEC) {
      // Kondisi 3: Kompor Aktif + Orang Tidak Terlihat (<15 detik) -> WARNING
      systemStatus = "WARNING (UNATTENDED)";
      digitalWrite(PIN_LED_ALERT, HIGH); // LED Menyala Peringatan
      noTone(PIN_BUZZER);
    } else {
      // Kondisi 4: Kompor Aktif + Orang Tidak Terlihat (>=15 detik) -> ALERT (DANGER)
      systemStatus = "ALERT (DANGER!)";
      digitalWrite(PIN_LED_ALERT, HIGH);
      tone(PIN_BUZZER, 1000); // Buzzer Berbunyi Nyaring
    }
  }

  // 4. Pengiriman Telemetri JSON via MQTT Broker
  JsonDocument doc;
  doc["stove_active"] = isStoveActive;
  doc["person_present"] = isPersonPresent;
  doc["idle_time_sec"] = idleTimeSec;
  doc["status"] = systemStatus;

  char payloadBuffer[256];
  serializeJson(doc, payloadBuffer);

  client.publish(topic_telemetry, payloadBuffer);

  // Jika kondisi bahaya, kirim notifikasi darurat khusus
  if (systemStatus == "ALERT (DANGER!)") {
    client.publish(topic_alert, "DANGER: Stove Left Unattended over 15s!");
  }

  // Debug Serial Monitor
  Serial.print("[StoveWatch Status] ");
  Serial.print(systemStatus);
  Serial.print(" | Idle: ");
  Serial.print(idleTimeSec);
  Serial.println("s");

  delay(1000); // Iterasi loop per detik
}