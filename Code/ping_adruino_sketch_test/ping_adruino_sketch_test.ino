#include <WiFi.h>
#include <ESPping.h>
// Thông tin WiFi
const char* ssid = "SRedmi Note 11";
const char* password = "23521341";

// Địa chỉ IP muốn ping


void setup() {
  Serial.begin(115200);

  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");

  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());



  Serial.print("Redmi Note 11 Hotspot default gateway address: ");
  Serial.println(WiFi.gatewayIP());

  Serial.print("Redmi Note 11 Hotspot subnet mask: ");
  Serial.println(WiFi.subnetMask());

  IPAddress ip (192, 168, 174, 212);

  // Thực hiện lệnh ping
  bool pingResult = Ping.ping(ip);
  if (pingResult) {
    Serial.println("Ping successful");
  } else {
    Serial.println("Ping failed");
  }
}

void loop() {
  // Ping lại sau mỗi 10 giây
  delay(10000);
  IPAddress ip (192, 168, 174, 212);
  bool pingResult = Ping.ping(ip);
  Serial.println(pingResult);
  if (pingResult) {
    Serial.println("Ping successful");
  } else {
    Serial.println("Ping failed");
  }
}
