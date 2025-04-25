#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "SRedmi Note 11";
const char* password = "23521341";

const char* mqtt_server = "192.168.174.92";
int mqtt_port = 1883; // Đối với broker công khai, thường là 1883


WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");

  client.setServer(mqtt_server, mqtt_port);
  if (!client.connect("ESP32_CLIENT", NULL, NULL)) {
    Serial.println("MQTT connection failed");
    return;
  }
  Serial.println("MQTT connected");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  Serial.println("Publish to a topic name: request");
  client.publish("request", "update request message from esp32");
  delay(100000);
  client.loop();
}

void reconnect() {
  while (!client.connect("ESP32_CLIENT", NULL, NULL)) {
    Serial.println("MQTT connection failed");
    delay(5000);
  }
  Serial.println("MQTT connected");
}