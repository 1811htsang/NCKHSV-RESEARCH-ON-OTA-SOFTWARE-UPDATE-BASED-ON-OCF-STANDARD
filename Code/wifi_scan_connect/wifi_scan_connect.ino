#include <WiFi.h>
#include <ESPping.h>

// Bổ sung các tham số trước để thuận tiện theo dõi thực thi

// Captive Portal SSID sử dụng cho kết nối 
const char* target_ssid = "Wi-MESH 2.4G";

// Thông tin kết nối cho SSID được targeted
uint8_t* bssid = 0;
int32_t channel = 0;

// Thông tin ID sử dụng cho kiểm tra
const IPAddress target_ip(192, 168, 249, 72);

// Hỗ trợ reset nhanh
void reset() {
  // Reset lại tốc độ của Serial
  Serial.begin(115200);

  // Reset lại về STA mode và ngắt kết nối
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(); 

  delay(100);
}

// Dùng để quét mạng và trả về số lượng phát hiện
int scan_wifi() {
  return WiFi.scanNetworks();
}

// Thực hiện kết nối 
bool connect(
  const char* ssid,
  const char* password,
  int32_t channel,
  uint8_t* bssid
) {
  // Hàm kết nối 
  WiFi.begin(ssid, "23521341", channel, bssid);

  // Bổ sung vòng lặp chờ kết nối để đảm bảo không bị trượt kết nối do timeout quá sớm
  int attempt_count = 0;
  while (WiFi.status() != WL_CONNECTED && attempt_count < 40) {
    delay(500);
    Serial.print(".");
    attempt_count++;
  }

  // Trả về thông tin kết nối 
  if (WiFi.status() == WL_CONNECTED) {
    return true;
  } else {
    return false;
  }
}

void setup() {
  delay(500);

  // Trước hết reset mạng để đảm bảo khởi đầu không có sai sót lỗi
  reset();

  // Thực hiện kiểm tra số lượng mạng phát hiện
  // Nếu không có thì thoát setup()
  int total_scan = scan_wifi();
  if (total_scan == 0) {
    Serial.println("No network found!");
    return;
  }

  // Tìm AP mạnh nhất có SSID được targeted
  int best_network_index = -1;
  int max_rssi = -100; // RSSI là số âm, nên -100 là rất yếu

  for (int i = 0; i < total_scan; ++i) {
    if (strcmp(WiFi.SSID(i).c_str(), target_ssid) == 0) {
      if (WiFi.RSSI(i) > max_rssi) {
        max_rssi = WiFi.RSSI(i);
        best_network_index = i;
      }
    }
  }

  // Đoạn này đảm bảo nếu không tìm thấy SSID được targeted thì kết thúc
  if (best_network_index == -1) {
    Serial.printf("Could not find SSID: %s\n", target_ssid);
    return;
  }

  // Thực hiện gán giá trị cho thông tin kết nối
  bssid = WiFi.BSSID(best_network_index);
  channel = WiFi.channel(best_network_index);

  // Đoạn này dùng để debug thông tin trên Serial
  Serial.printf("Found best AP for '%s'. Connecting...\n", target_ssid);
  Serial.printf("BSSID: %s\n", WiFi.BSSIDstr(best_network_index).c_str());
  Serial.printf("Channel: %d\n", WiFi.channel(best_network_index));
  Serial.printf("RSSI: %d\n", max_rssi);

  // Thực hiện kết nối
  bool connect_status = connect(target_ssid, NULL, channel, bssid);

  if (connect_status) {
    Serial.println("WiFi connected using specific BSSID!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Failed to connect even with specific BSSID.");
    Serial.print("Last WiFi status: ");
    Serial.println(WiFi.status());
  }
}

void loop() {
  // Thực hiện ping IP để kiểm tra
  Serial.println(target_ip);
  if (Ping.ping(target_ip) > 0){
    Serial.printf("Average time : %.2f ms\n", Ping.averageTime());
  } else {
    Serial.println("Error on connection !");
  }

  delay(1000);
}