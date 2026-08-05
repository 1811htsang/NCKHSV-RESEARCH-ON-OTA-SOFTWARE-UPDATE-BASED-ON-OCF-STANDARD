"""ESP32 emulator for validating gateway packet flows before flashing firmware."""

from __future__ import annotations

import argparse
import json
import time

from protocol_provider import BinaryPacket, bytes_to_hex, hex_to_bytes


def build_request(device_id: int, firmware_id: int, current_version: int) -> bytes:
    sync_token = int(time.time())
    _ = device_id, firmware_id, current_version
    return BinaryPacket.encode_request(sync_token)


def parse_response(packet_hex: str) -> dict[str, object]:
    return BinaryPacket.decode_response(hex_to_bytes(packet_hex))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="emulator-esp32")
    subparsers = parser.add_subparsers(dest="command", required=True)

    request_parser = subparsers.add_parser("request", help="build an ESP32-style request packet")
    request_parser.add_argument("--device-id", type=int, required=True)
    request_parser.add_argument("--fw-id", type=int, required=True)
    request_parser.add_argument("--current-version", type=int, required=True)

    parse_parser = subparsers.add_parser("parse-response", help="decode a gateway response packet")
    parse_parser.add_argument("packet_hex")

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "request":
        print(bytes_to_hex(build_request(args.device_id, args.fw_id, args.current_version)))
        return 0

    if args.command == "parse-response":
        print(json.dumps(parse_response(args.packet_hex), ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
