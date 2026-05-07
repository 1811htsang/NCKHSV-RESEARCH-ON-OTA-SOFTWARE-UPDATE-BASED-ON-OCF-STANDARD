# Binary Protocol Implementation Guide

## ESP32 Firmware Synchronization with Gateway/Server Scripts

**Date:** 2026-05-07  
**Version:** 1.0  
**Status:** Implemented

---

## 1. Overview

The ESP32 firmware has been refactored to use **binary hex protocol** instead of JSON, ensuring synchronized communication between:

- **ESP32 Firmware** (DFU target device)
- **Gateway Script** (Jetson Nano)
- **Server Script** (Central management)

This aligns with the protocol definitions in [message_encoder_rule.md](../code/script/message_encoder_rule.md).

---

## 2. Changes Summary

### 2.1 CRC-16 Calculation

**Location:** [firmware.ino](../code/arduino/firmware/firmware.ino) lines 25-58

```cpp
uint16_t calc_crc16(const uint8_t *data, size_t len)
```

- Algorithm: **CCITT-FALSE (0xFFFF)**
- Matches Python `crc_hqx()` in gateway/server scripts
- Used for packet integrity verification

### 2.2 Device-to-Gateway Request Format

**Function:** `func_send_request()`  
**Protocol Format:**

```code
Device_ID(1B) | Control_Code(1B) | FW_ID(2B) | Current_Version(2B) | CRC(2B)
```

**Example Hex String (with spaces):**

```code
05 01 03E8 0019 C4B2
```

**Field Breakdown:**

| Field | Bytes | Example | Notes |
| ------- | ------- | --------- | ------- |
| Device_ID | 1 | `05` | Last byte of MAC address |
| Control_Code | 1 | `01` | 0x01 = Check Update |
| FW_ID | 2 | `03E8` | Firmware ID (1000 decimal) |
| Current_Version | 2 | `0019` | Version 2.5 (25 decimal) |
| CRC-16 | 2 | `C4B2` | CCITT-FALSE checksum |

**MQTT Topic:** `nckhsv/{MAC_ADDRESS}/request`

### 2.3 Gateway-to-Device Response Format

**Function:** `func_mqtt_callback()`  
**Protocol Format:** `0xBB` Packet

```code
0xBB | Status(1B) | Count(1B) | FW_ID(2B) | Version(2B) | Size(4B) | Force(1B) | CRC(2B)
```

**Field Breakdown:**

| Field | Bytes | Value | Notes |
| ------- | ------- | --------- | ------- |
| Header | 1 | `0xBB` | Gateway response marker |
| Status | 1 | `00`/`01`/`02` | 0x00=No Update, 0x01=Update Available, 0x02=Error |
| Count | 1 | `01` | Number of firmware options |
| FW_ID | 2 | `03E8` | Firmware ID |
| Version | 2 | `001A` | Firmware version (26 = v2.6) |
| Size | 4 | `0004B250` | File size in bytes |
| Force | 1 | `01` | 0x01=Mandatory, 0x00=Optional |
| CRC-16 | 2 | `2B1A` | Checksum |

**Example Packet (hex):**

```code
BB 01 01 03E8 001A 0004B250 01 2B1A
```

**Parsing in firmware:**

```cpp
// Response received:
// Status = 0x01 (Update Available)
// FW_ID = 0x03E8 (1000)
// Version = 0x001A (26 → v2.6)
// Generated filename: fw_1000_v26.bin
```

**MQTT Topic:** `nckhsv/{MAC_ADDRESS}/response`

---

## 3. System Integration Checklist

### 3.1 MQTT Broker Configuration

- [ ] Mosquitto running on `192.168.0.51:1883`
- [ ] No authentication required, OR
- [ ] User: `nckhsv`, Password: set in script
- [ ] Topics allowed:
  - `nckhsv/+/request` (device → gateway)
  - `nckhsv/+/response` (gateway → device)
  - `server/request` (gateway → server)
  - `server/response` (server → gateway)

### 3.2 Device ID Mapping

**Critical:** Device ID in packets must match server database

**Mapping Logic:**

- Extract last byte of ESP32 MAC address
- Example: `AA:BB:CC:DD:EE:FF` → Device_ID = `0xFF`
- Database stores this mapped ID for firmware assignment

**Verification:**

```bash
# On ESP32 Serial Monitor, should output:
Sent UPDATE_REQUEST (hex format): 05 01 03E8 0019 XXXX
# First byte (05) is the Device ID
```

### 3.3 File Paths & Directories

**ESP32 SD Card:**

```code
/fw_1000_v26.bin  ← Downloaded from FTP
```

**Gateway (Jetson Nano):**

```code
./code/arduino/firmware/cache/fw_1000_v26.bin  ← Cached firmware file
./database/gateway_db.db                         ← Local firmware manifest
```

**Server:**

```code
./database/server_db.db  ← Device firmware assignments
```

### 3.4 FTP Server Setup

**On Jetson Nano:**

1. **Create cache directory:**

   ```bash
   mkdir -p ~/NCKH/code/arduino/firmware/cache/
   chmod 755 ~/NCKH/code/arduino/firmware/cache/
   ```

2. **FTP User Configuration:**
   - Username: `shanghuang-jetsonnano`
   - Password: `181105`
   - Home directory: Can access `{MAC}_firmware/` subdirectories

3. **FTP Connection from ESP32:**
   - Server: `192.168.0.51`
   - Port: `21`
   - Path structure: `/{MAC_ADDRESS}_firmware/fw_1000_v26.bin`

---

## 4. Protocol Flow Diagram

```code
┌─────────────────────────────────────────────────────────────┐
│                     SYSTEM STARTUP                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │ ESP32: WiFi + MQTT Connect  │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────────────────────────┐
        │ ESP32: func_send_request()                      │
        │ Sends: Device_ID|Code|FW_ID|Ver|CRC             │
        │ Topic: nckhsv/{MAC}/request                     │
        └──────────────┬──────────────────────────────────┘
                       │
        ┌──────────────▼──────────────────────────────────┐
        │ Gateway: rewrite_gateway_script.sh              │
        │ 1. Receives hex request                         │
        │ 2. Queries database for FW update               │
        │ 3. Publishes 0xBB response packet               │
        │ Topic: nckhsv/{MAC}/response                    │
        └──────────────┬──────────────────────────────────┘
                       │
        ┌──────────────▼──────────────────────────────────┐
        │ ESP32: func_mqtt_callback()                     │
        │ 1. Parses 0xBB packet                           │
        │ 2. Extracts FW metadata                         │
        │ 3. Generates filename: fw_ID_vVersion.bin       │
        │ 4. Sets mqtt_loopstop_flg_glb = true            │
        └──────────────┬──────────────────────────────────┘
                       │
        ┌──────────────▼──────────────────────────────────┐
        │ ESP32: Main Loop                                │
        │ 1. Ping FTP server                              │
        │ 2. Login to FTP                                 │
        │ 3. Download: fw_1000_v26.bin to SD card         │
        │ 4. Perform internal OTA update                  │
        │ 5. Reboot with new firmware                     │
        └──────────────┬──────────────────────────────────┘
                       │
        ┌──────────────▼──────────────────────────────────┐
        │ ESP32: Restart                                  │
        │ Now running new firmware version                │
        └─────────────────────────────────────────────────┘
```

---

## 5. Troubleshooting

### Issue: CRC Mismatch

**Symptom:** Gateway/Server report CRC errors in binary packets

**Solution:**

- Verify `calc_crc16()` implementation matches Python
- Test with known values from gateway script
- Check byte order (big-endian vs little-endian)

### Issue: Device ID Mismatch

**Symptom:** Gateway doesn't recognize device, returns error status

**Solution:**

```cpp
// In ESP32 Serial Monitor, check extracted Device ID:
// If MAC is AA:BB:CC:DD:EE:FF
// Device_ID should be 0xFF (last byte)

// Verify in gateway database:
SELECT device_id FROM devices WHERE mac_address = 'AABBCCDDEEFF';
```

### Issue: Firmware Not Found After Download

**Symptom:** SD card file doesn't match FTP expected path

**Solution:**

- Ensure FTP directory structure: `/{MAC}_firmware/fw_1000_v26.bin`
- Verify file permissions on Jetson Nano
- Check FTP user home directory settings

### Issue: 0xBB Packet Not Parsed

**Symptom:** firmware doesn't recognize gateway response

**Solution:**

```cpp
// Add debug in func_mqtt_callback:
Serial.println("Raw payload length: " + String(length));
Serial.println("Hex data: " + hexData);

// Verify packet starts with BB:
if (!hexData.startsWith("BB")) {
  Serial.println("ERROR: Not a 0xBB packet!");
}
```

---

## 6. Testing Guide

### 6.1 Unit Test: CRC-16 Calculation

```cpp
// Test in Arduino IDE Serial Monitor
void test_crc16() {
  uint8_t test_data[] = {0x05, 0x01, 0x03, 0xE8, 0x00, 0x19};
  uint16_t crc = calc_crc16(test_data, 6);
  Serial.printf("CRC: 0x%04X\n", crc);
  // Compare with Python: crc_hqx(bytes.fromhex("0501 03E8 0019"), 0xFFFF)
}
```

### 6.2 Integration Test: Full Request-Response Cycle

**Manual Test Steps:**

1. **ESP32 Side:**
   - Power on ESP32
   - Watch Serial Monitor for "Sent UPDATE_REQUEST (hex format): ..."
   - Copy the hex string

2. **Server Side:**

   ```bash
   # Simulate server/gateway
   mosquitto_pub -h 192.168.0.51 -t nckhsv/{MAC}/response \
     -m "BB0101 03E8 001A 0004B250 01 2B1A"
   ```

3. **ESP32 Side:**
   - Should output "Update available: fw_1000_v26.bin"
   - Should transition to FTP download phase

### 6.3 Load Testing: Rapid Requests

- Multiple ESP32 devices sending requests simultaneously
- Verify CRC integrity with each packet
- Monitor MQTT broker message queue

---

## 7. Future Enhancements

### 7.1 0xCC Selection Protocol

Current implementation uses JSON for selection (temporary).  
**Planned upgrade:**

```code
0xCC | Selected_FW_ID(2B) | Block_Size(2B) | Protocol(1B) | CRC(2B)
```

### 7.2 P2P Support

Enable device-to-device firmware transfer via P2P protocol (0x03)  
See `peers_map` table in [database_design.md](../code/data/database_design.md)

### 7.3 Compressed Firmware Transfer

Support for deflate/gzip compressed firmware binary  
Reduces bandwidth and improves deployment speed

---

## 8. References

- [message_encoder_rule.md](../code/script/message_encoder_rule.md) - Protocol Specification
- [database_design.md](../code/data/database_design.md) - Database Schema
- [rewrite_gateway_script.sh](../code/script/rewrite_gateway_script.sh) - Gateway Implementation
- [rewrite_server_script.sh](../code/script/rewrite_server_script.sh) - Server Implementation
- [firmware.ino](../code/arduino/firmware/firmware.ino) - ESP32 Implementation

---

## 9. Version History

| Version | Date | Changes |
| --------- | ------ | --------- |
| 1.0 | 2026-05-07 | Initial binary protocol implementation |
| | | - Added CRC-16 calculation |
| | | - Refactored func_send_request for hex format |
| | | - Updated func_mqtt_callback to parse 0xBB |
| | | - Maintained JSON compatibility for selection |

---

**Last Updated:** 2026-05-07  
**Maintained By:** Shang Huang
