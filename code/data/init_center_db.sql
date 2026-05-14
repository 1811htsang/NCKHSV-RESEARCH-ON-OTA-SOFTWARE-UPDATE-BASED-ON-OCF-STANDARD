PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- Table: devices
CREATE TABLE IF NOT EXISTS devices (
  device_id INTEGER PRIMARY KEY,
  mac_address TEXT UNIQUE,
  current_version INTEGER,
  last_update_timestamp INTEGER,
  status INTEGER DEFAULT 1
);

-- Table: firmwares
CREATE TABLE IF NOT EXISTS firmwares (
  fw_id INTEGER PRIMARY KEY,
  version INTEGER,
  file_path TEXT,
  file_size INTEGER,
  checksum_sha256 TEXT,
  is_force INTEGER DEFAULT 0,
  sync_status INTEGER DEFAULT 1
);

-- Table: peers_map
CREATE TABLE IF NOT EXISTS peers_map (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id INTEGER,
  fw_id INTEGER,
  version INTEGER,
  ip_address TEXT,
  last_verified INTEGER,
  FOREIGN KEY(device_id) REFERENCES devices(device_id)
);

-- Table: system_sync
CREATE TABLE IF NOT EXISTS system_sync (
  sync_key TEXT PRIMARY KEY,
  last_sync_timestamp INTEGER,
  server_status TEXT
);

-- Table: dev_join_fw
CREATE TABLE IF NOT EXISTS dev_join_fw (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id INTEGER,
  fw_id INTEGER,
  version INTEGER,
  is_force INTEGER DEFAULT 0,
  FOREIGN KEY(device_id) REFERENCES devices(device_id),
  FOREIGN KEY(fw_id) REFERENCES firmwares(fw_id)
);

-- Sample data: devices
INSERT OR REPLACE INTO devices (device_id, mac_address, current_version, last_update_timestamp, status) VALUES
  (5, 'AA:BB:CC:DD:EE:05', 25, strftime('%s','now'), 1),
  (10, 'AA:BB:CC:DD:EE:0A', 24, strftime('%s','now','-1 day'), 1),
  (100, 'AA:BB:CC:DD:EE:64', 26, strftime('%s','now','-7 days'), 0);

-- Sample data: firmwares
INSERT OR REPLACE INTO firmwares (fw_id, version, file_path, file_size, checksum_sha256, is_force, sync_status) VALUES
  (1000, 26, '/srv/firmwares/fw_1000_v26.bin', 524288, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 0, 1),
  (1001, 27, '/srv/firmwares/fw_1001_v27.bin', 1048576, 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 1, 1),
  (2000, 30, '/srv/firmwares/fw_2000_v30.bin', 2097152, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', 0, 0);

-- Sample data: peers_map (P2P sources)
INSERT INTO peers_map (device_id, fw_id, version, ip_address, last_verified) VALUES
  (5, 1000, 26, '192.168.1.50', strftime('%s','now','-10 minutes')),
  (100, 1001, 27, '192.168.1.51', strftime('%s','now','-2 hours'));

-- Sample data: system_sync
INSERT OR REPLACE INTO system_sync (sync_key, last_sync_timestamp, server_status) VALUES
  ('last_manifest_sync', strftime('%s','now'), 'OK');

-- Sample data: dev_join_fw
INSERT INTO dev_join_fw (device_id, fw_id, version, is_force) VALUES
  (5, 1000, 26, 0),
  (10, 1000, 26, 0),
  (100, 1001, 27, 1);

COMMIT;
