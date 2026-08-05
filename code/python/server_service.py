"""Server master service for manifest generation and sync handling."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from protocol_provider import BinaryPacket, bytes_to_hex, calculate_manifest_firmware_options
from storage_manager import DEFAULT_SERVER_DB, FileManifestManager, StorageManager


class ServerService:
    def __init__(self, db_path: str | os.PathLike[str]):
        self.storage = StorageManager(db_path)

    def build_manifest_packet(self, device_id: int) -> bytes:
        manifest_rows = self.storage.get_latest_firmware(device_id)
        options = calculate_manifest_firmware_options(
            [(row.fw_id, row.version, row.file_size or 0, row.is_force) for row in manifest_rows]
        )
        return BinaryPacket.encode_response(0x01 if options else 0x00, options)

    def build_manifest_packets_for_all_devices(self) -> dict[int, bytes]:
        with self.storage.connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT device_id
                FROM dev_join_fw
                ORDER BY device_id ASC
                """
            ).fetchall()
        return {int(row[0]): self.build_manifest_packet(int(row[0])) for row in rows}

    def handle_request_hex(self, request_hex: str) -> dict[int, str]:
        request_bytes = bytes.fromhex("".join(request_hex.split()))
        BinaryPacket.decode_request(request_bytes)
        return {device_id: bytes_to_hex(packet) for device_id, packet in self.build_manifest_packets_for_all_devices().items()}

    def ingest_firmware(self, fw_id: int, file_path: str, version: int, is_force: int = 0) -> dict[str, object]:
        checksum = FileManifestManager.sha256_of_file(file_path)
        size = Path(file_path).stat().st_size
        self.storage.update_firmware_metadata(
            fw_id=fw_id,
            version=version,
            file_path=str(file_path),
            file_size=size,
            checksum_sha256=checksum,
            is_force=is_force,
            sync_status=1,
        )
        self.storage.update_system_sync("last_manifest_sync", "OK", int(time.time()))
        return {"fw_id": fw_id, "version": version, "file_path": str(file_path), "size": size, "sha256": checksum}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="server-service")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("manifest", help="generate manifest packet for a device")
    sync_parser.add_argument("--db", default=str(DEFAULT_SERVER_DB))
    sync_parser.add_argument("--device-id", type=int, required=True)

    sync_all_parser = subparsers.add_parser("manifest-all", help="generate manifest packets for all registered devices")
    sync_all_parser.add_argument("--db", default=str(DEFAULT_SERVER_DB))

    ingest_parser = subparsers.add_parser("ingest", help="ingest a new firmware binary into the server DB")
    ingest_parser.add_argument("--db", default=str(DEFAULT_SERVER_DB))
    ingest_parser.add_argument("--fw-id", type=int, required=True)
    ingest_parser.add_argument("--version", type=int, required=True)
    ingest_parser.add_argument("--file-path", required=True)
    ingest_parser.add_argument("--force", type=int, default=0)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "manifest":
        service = ServerService(args.db)
        print(service.build_manifest_packet(args.device_id).hex().upper())
        return 0

    if args.command == "ingest":
        service = ServerService(args.db)
        print(json.dumps(service.ingest_firmware(args.fw_id, args.file_path, args.version, args.force), ensure_ascii=False))
        return 0

    if args.command == "manifest-all":
        service = ServerService(args.db)
        manifest_packets = {device_id: packet.hex().upper() for device_id, packet in service.build_manifest_packets_for_all_devices().items()}
        print(json.dumps(manifest_packets, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
