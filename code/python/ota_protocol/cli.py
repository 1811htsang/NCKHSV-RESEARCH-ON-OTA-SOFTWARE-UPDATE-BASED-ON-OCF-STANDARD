"""Minimal command-line entrypoints for the Python migration stage."""

from __future__ import annotations

import argparse
import time

from .packet import FirmwareOption, TftpBootstrap, build_gateway_request, build_gateway_response, build_tftp_bootstrap, bytes_to_hex, hex_to_bytes, parse_gateway_request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ota-protocol")
    subparsers = parser.add_subparsers(dest="command", required=True)

    request_parser = subparsers.add_parser("build-request", help="build gateway request packet")
    request_parser.add_argument("--sync-token", type=int, default=None)

    response_parser = subparsers.add_parser("build-response", help="build gateway response packet")
    response_parser.add_argument("--status", type=int, required=True)
    response_parser.add_argument("--fw-id", type=int, required=True)
    response_parser.add_argument("--version", type=int, required=True)
    response_parser.add_argument("--size", type=int, required=True)
    response_parser.add_argument("--force", type=int, default=0)

    tftp_parser = subparsers.add_parser("build-tftp", help="build a TFTP bootstrap packet")
    tftp_parser.add_argument("--ip", required=True)
    tftp_parser.add_argument("--port", type=int, default=69)
    tftp_parser.add_argument("--mode", type=int, default=1)
    tftp_parser.add_argument("--filename", required=True)
    tftp_parser.add_argument("--token", default="")

    parse_parser = subparsers.add_parser("parse-request", help="validate a gateway request packet")
    parse_parser.add_argument("packet_hex")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "build-request":
        sync_token = int(time.time()) if args.sync_token is None else args.sync_token
        print(bytes_to_hex(build_gateway_request(sync_token)))
        return 0

    if args.command == "build-response":
        packet = build_gateway_response(
            args.status,
            [FirmwareOption(args.fw_id, args.version, args.size, args.force)],
        )
        print(bytes_to_hex(packet))
        return 0

    if args.command == "build-tftp":
        packet = build_tftp_bootstrap(
            TftpBootstrap(
                server_ip=args.ip,
                port=args.port,
                mode=args.mode,
                filename=args.filename,
                token=args.token.encode("utf-8"),
            )
        )
        print(bytes_to_hex(packet))
        return 0

    if args.command == "parse-request":
        print(parse_gateway_request(hex_to_bytes(args.packet_hex)))
        return 0

    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
