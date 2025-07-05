#include <WiFi.h>

void setup() {
  Serial.begin(115200);
  // WiFi.mode(WIFI_STA);
  WiFi.disconnect(); // Đảm bảo bắt đầu từ trạng thái sạch
  delay(100);

  const char* target_ssid = "Wi-MESH 2.4G";

  Serial.println("Scanning for networks...");
  int n = WiFi.scanNetworks();

  if (n == 0) {
    Serial.println("No networks found!");
    return;
  }

  // Tìm AP mạnh nhất có SSID chúng ta muốn
  int best_network_index = -1;
  int max_rssi = -100; // RSSI là số âm, nên -100 là rất yếu

  for (int i = 0; i < n; ++i) {
    if (strcmp(WiFi.SSID(i).c_str(), target_ssid) == 0) {
      if (WiFi.RSSI(i) > max_rssi) {
        max_rssi = WiFi.RSSI(i);
        best_network_index = i;
      }
    }
  }

  if (best_network_index == -1) {
    Serial.printf("Could not find SSID: %s\n", target_ssid);
    return;
  }

  Serial.printf("Found best AP for '%s'. Connecting...\n", target_ssid);
  Serial.printf("BSSID: %s\n", WiFi.BSSIDstr(best_network_index).c_str());
  Serial.printf("Channel: %d\n", WiFi.channel(best_network_index));
  Serial.printf("RSSI: %d\n", max_rssi);

  // Kết nối trực tiếp đến AP mạnh nhất bằng BSSID và channel của nó
  // Đây là phiên bản đầy đủ nhất của hàm WiFi.begin()
  uint8_t* bssid = WiFi.BSSID(best_network_index);
  int32_t channel = WiFi.channel(best_network_index);
  
  // Tham số mật khẩu vẫn là NULL cho mạng mở
  WiFi.begin(target_ssid, NULL, channel, bssid);

  // Vòng lặp chờ kết nối... (như ở giải pháp 1)
  int attempt_count = 0;
  while (WiFi.status() != WL_CONNECTED && attempt_count < 40) {
    delay(500);
    Serial.print(".");
    attempt_count++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected using specific BSSID!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect even with specific BSSID.");
    Serial.print("Last WiFi status: ");
    Serial.println(WiFi.status());
  }
}

void loop() {
  Serial.println("In loop");
  delay(500);
}