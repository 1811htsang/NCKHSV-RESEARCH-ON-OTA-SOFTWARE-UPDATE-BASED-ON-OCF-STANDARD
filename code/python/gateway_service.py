"""Gateway smart-coordinator service for OTA orchestration."""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from protocol_provider import BinaryPacket, FirmwareOption, TftpBootstrap, bytes_to_hex, calculate_manifest_firmware_options
from storage_manager import StorageManager


class GatewayService:
    def __init__(self, db_path: str | os.PathLike[str]):
        self.storage = StorageManager(db_path)

    def build_gateway_request(self) -> bytes:
        return BinaryPacket.encode_request(int(time.time()))

    def build_device_response(self, device_id: int) -> bytes:
        records = self.storage.get_latest_firmware(device_id)
        options = [
            FirmwareOption(
                fw_id=record.fw_id,
                version=record.version,
                size=record.file_size or 0,
                force=record.is_force,
            )
            for record in records
        ]
        return BinaryPacket.encode_response(0x01 if options else 0x00, options)

    def resolve_source_node(self, device_id: int, fw_id: int) -> str | None:
        with self.storage.connect() as connection:
            row = connection.execute(
                """
                SELECT ip_address
                FROM peers_map
                WHERE device_id = ? AND fw_id = ?
                ORDER BY last_verified DESC
                LIMIT 1
                """,
                (device_id, fw_id),
            ).fetchone()
        return None if row is None else str(row[0])

    def build_tftp_bootstrap(self, device_id: int, fw_id: int, gateway_ip: str, filename: str) -> bytes:
        source_ip = self.resolve_source_node(device_id, fw_id) or gateway_ip
        return BinaryPacket.encode_tftp(
            TftpBootstrap(
                server_ip=source_ip,
                port=69,
                mode=1,
                filename=filename,
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gateway-service")
    subparsers = parser.add_subparsers(dest="command", required=True)

    response_parser = subparsers.add_parser("response", help="build device response packet")
    response_parser.add_argument("--db", default="database/gateway_db.db")
    response_parser.add_argument("--device-id", type=int, required=True)

    tftp_parser = subparsers.add_parser("tftp", help="build TFTP bootstrap packet")
    tftp_parser.add_argument("--db", default="database/gateway_db.db")
    tftp_parser.add_argument("--device-id", type=int, required=True)
    tftp_parser.add_argument("--fw-id", type=int, required=True)
    tftp_parser.add_argument("--gateway-ip", required=True)
    tftp_parser.add_argument("--filename", required=True)

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "response":
        service = GatewayService(args.db)
        print(bytes_to_hex(service.build_device_response(args.device_id)))
        return 0

    if args.command == "tftp":
        service = GatewayService(args.db)
        print(bytes_to_hex(service.build_tftp_bootstrap(args.device_id, args.fw_id, args.gateway_ip, args.filename)))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
