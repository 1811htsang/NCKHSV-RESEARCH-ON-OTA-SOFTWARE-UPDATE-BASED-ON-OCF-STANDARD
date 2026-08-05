# Kế hoạch chuyển đổi hệ thống OTA

Tài liệu này mô tả lộ trình chuyển đổi theo đúng hướng của thiết kế hiện tại:

- Chuyển các bash script sang Python.
- Giữ lớp điều phối bằng MQTT, nhưng thay đường truyền binary giữa gateway và ESP32 từ FTP sang TFTP.
- Lên kế hoạch port firmware từ Arduino sang ESP-IDF theo từng giai đoạn để giảm rủi ro.

## 1. Mục tiêu kiến trúc

### Giữ lại

- Luồng manifest, validation, và handshake giữa gateway với server.
- Bộ quy tắc packet đang mô tả trong [message_encoder_rule.md](../code/script/message_encoder_rule.md).
- Cấu trúc dữ liệu device / firmware / mapping trong SQLite.

### Thay đổi

- Thay shell script bằng Python để dễ test, tái sử dụng và mở rộng.
- Thay FTP bằng TFTP cho bước tải binary giữa gateway và ESP32.
- Chuyển firmware ESP32 từ Arduino sang ESP-IDF để đồng bộ với phần partition, OTA và networking.

## 2. Chuyển bash script sang Python

### Phạm vi cần chuyển

- `encode_gateway_script.sh`
- `encode_server_script.sh`
- `json_gateway_script.sh`
- `json_server_script.sh`
- `clear.sh`
- `wifi_host_ap_setup.sh` nếu script này còn được dùng trong luồng hiện tại

### Cấu trúc Python đề xuất

- `protocol/packet.py`: encode/decode packet, CRC-16, byte order, validate frame.
- `protocol/mqtt_topics.py`: chuẩn hóa topic names.
- `storage/gateway_db.py`: truy cập SQLite cho gateway.
- `storage/server_db.py`: truy cập SQLite cho server.
- `services/gateway_service.py`: logic gateway điều phối request/response.
- `services/server_service.py`: logic server xử lý manifest/validation.
- `cli/gateway.py`, `cli/server.py`: entrypoint chạy script.

### Quy tắc chuyển đổi

- Không đổi format packet trong cùng một phase nếu chưa cần.
- Mỗi script bash hiện tại nên được map sang một command Python duy nhất.
- CRC và packing/unpacking phải được gom vào một module dùng chung để tránh lệch logic giữa gateway và server.
- Input/output nên chuyển sang cấu trúc rõ ràng: JSON nội bộ, packet nhị phân ở biên giao tiếp.

### Kiểm thử tối thiểu

- Unit test CRC.
- Unit test encode/decode của packet `0xFF`, `0xBB`, `0xCC`.
- Test integration mô phỏng gateway publish/subscribe với MQTT broker local.

## 3. Thay FTP bằng TFTP giữa gateway và ESP32

### Phần không đổi

- MQTT vẫn dùng làm control plane.
- ESP32 vẫn hỏi gateway xem có update hay không.
- Gateway vẫn quyết định firmware nào được phép tải.

### Phần thay đổi

- `FTP IP`, `FTP Port`, user/pass và path kiểu FTP sẽ không còn là payload chính.
- Sau khi ESP32 chọn firmware, gateway trả về thông tin bootstrap TFTP thay cho thông tin FTP.

### Payload đề xuất cho bước tải

Giữ một gói control riêng, ví dụ kế thừa từ `0xDD`, nhưng nội dung sẽ là thông tin TFTP:

- Header: `0xDD`
- Server IP: 4 byte
- Port TFTP: 2 byte
- Mode: 1 byte, ví dụ `0x01` = download only
- Filename length + filename
- Optional token / nonce để tránh tải nhầm file
- CRC-16

### Hướng vận hành TFTP

- Gateway đóng vai trò TFTP server hoặc TFTP relay cục bộ.
- ESP32 đóng vai trò TFTP client, pull file binary từ gateway.
- Binary nên được đặt theo cấu trúc tên thống nhất, ví dụ `fw_<id>_v<ver>.bin`.

### Lưu ý thiết kế

- TFTP không có xác thực mạnh như FTP, nên nếu cần an toàn hơn phải bổ sung token ngắn hạn, whitelist IP, hoặc nonce theo session.
- Nếu firmware lớn, cần chốt block size và timeout rõ ràng ngay từ đầu.
- Nếu môi trường có NAT hoặc nhiều node, nên để gateway cấp port/session riêng cho mỗi lượt tải.

## 4. Lộ trình port Arduino sang ESP-IDF

### Pha 1: Tách phần lõi khỏi firmware Arduino

- Rà lại các hàm liên quan đến Wi-Fi, MQTT, packet parse, storage, và OTA.
- Tách các khối logic thành module độc lập trước khi port.
- Loại bỏ phụ thuộc vào `ArduinoJson`, `FTP32`, và các helper chỉ có trong Arduino nếu không còn cần.

### Pha 2: Tạo project ESP-IDF mới

- Tạo skeleton ESP-IDF theo cấu trúc chuẩn: `main/`, `components/`, `partitions.csv`, `sdkconfig.defaults`.
- Chuyển cấu hình Wi-Fi, MQTT, NVS, partition table và OTA sang ESP-IDF.
- Đối chiếu lại partition table trong [docs/esp32/parition_table_configuration_guideline.md](esp32/parition_table_configuration_guideline.md).

### Pha 3: Port networking và control flow

- Port Wi-Fi connect / reconnect.
- Port MQTT client, subscribe topic, publish request/response.
- Port parser cho packet binary và trạng thái update.
- Port TFTP client và luồng download firmware.

### Pha 4: Port OTA nội bộ

- Dùng API OTA của ESP-IDF để ghi firmware xuống partition đang được chọn.
- Thay toàn bộ luồng `Update.h` / Arduino OTA bằng `esp_ota_begin`, `esp_ota_write`, `esp_ota_end`, `esp_ota_set_boot_partition`.
- Kiểm tra lại logic versioning, checksum, và rollback.

### Pha 5: Kiểm thử tích hợp

- Test kết nối Wi-Fi / MQTT.
- Test request update từ ESP32.
- Test nhận packet response từ gateway.
- Test tải file qua TFTP.
- Test flash OTA và reboot sang firmware mới.

## 5. Thứ tự thực thi khuyến nghị

1. Chuẩn hóa lại packet và database schema đang dùng chung.
2. Port script sang Python trước, giữ nguyên hành vi đầu cuối.
3. Chuyển bước tải binary sang TFTP trên gateway và ESP32.
4. Port firmware Arduino sang ESP-IDF sau khi giao thức đã ổn định.
5. Dọn lại tài liệu, sơ đồ luồng, và script test.

## 6. Rủi ro chính

- Lệch CRC hoặc byte order giữa Python và firmware.
- TFTP không có cơ chế xác thực sẵn, cần kiểm soát session và IP chặt.
- Port sớm sang ESP-IDF khi packet chưa ổn định sẽ làm tăng số lần sửa.
- Nếu đổi đồng thời script, protocol, và firmware cùng lúc thì rất khó debug.

## 7. Đầu việc tiếp theo

- Chốt lại format TFTP bootstrap packet.
- Viết lớp Python chung cho encode/decode packet.
- Tạo project ESP-IDF mới và port từng module một.
- Cập nhật lại `docs/to-do.md` khi bước nào đã hoàn thành.