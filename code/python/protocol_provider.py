"""Shared binary protocol provider for gateway, server, and emulator code."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from typing import Iterable, Sequence


def calculate_crc16(data: bytes) -> int:
    """Return CRC-16/CCITT-FALSE for *data* using init value 0xFFFF."""

    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode_u16(value: int) -> bytes:
    return value.to_bytes(2, "big")


def encode_u32(value: int) -> bytes:
    return value.to_bytes(4, "big")


def decode_u16(data: bytes) -> int:
    if len(data) != 2:
        raise ValueError("u16 requires exactly 2 bytes")
    return int.from_bytes(data, "big")


def decode_u32(data: bytes) -> int:
    if len(data) != 4:
        raise ValueError("u32 requires exactly 4 bytes")
    return int.from_bytes(data, "big")


def hex_to_bytes(value: str) -> bytes:
    cleaned = "".join(value.split())
    if len(cleaned) % 2:
        raise ValueError("hex string must contain an even number of digits")
    return bytes.fromhex(cleaned)


def bytes_to_hex(data: bytes) -> str:
    return data.hex().upper()


@dataclass(frozen=True)
class FirmwareOption:
    fw_id: int
    version: int
    size: int
    force: int


@dataclass(frozen=True)
class TftpBootstrap:
    server_ip: str
    port: int
    mode: int
    filename: str
    token: bytes = b""


class BinaryPacket:
    """Encoder/decoder for the OTA binary packet families."""

    HEADER_REQUEST = 0xFF
    HEADER_RESPONSE = 0xBB
    HEADER_SELECT = 0xCC
    HEADER_TFTP = 0xDD

    @staticmethod
    def encode_request(sync_token: int) -> bytes:
        payload = bytes([BinaryPacket.HEADER_REQUEST, 0xD1]) + encode_u32(sync_token)
        return payload + encode_u16(calculate_crc16(payload))

    @staticmethod
    def decode_request(packet: bytes) -> dict[str, int]:
        if len(packet) != 8:
            raise ValueError("request packet must be exactly 8 bytes")
        if packet[0] != BinaryPacket.HEADER_REQUEST or packet[1] != 0xD1:
            raise ValueError("invalid request packet header")
        if calculate_crc16(packet[:6]) != decode_u16(packet[6:]):
            raise ValueError("request packet CRC mismatch")
        return {"header": packet[0], "device_code": packet[1], "sync_token": decode_u32(packet[2:6])}

    @staticmethod
    def encode_response(status: int, options: Iterable[FirmwareOption]) -> bytes:
        option_list = list(options)
        payload = bytearray()
        payload.append(BinaryPacket.HEADER_RESPONSE)
        payload.append(status & 0xFF)
        payload.append(len(option_list) & 0xFF)
        for option in option_list:
            payload.extend(encode_u16(option.fw_id))
            payload.extend(encode_u16(option.version))
            payload.extend(encode_u32(option.size))
            payload.append(option.force & 0xFF)
        payload.extend(encode_u16(calculate_crc16(bytes(payload))))
        return bytes(payload)

    @staticmethod
    def decode_response(packet: bytes) -> dict[str, object]:
        if len(packet) < 5:
            raise ValueError("response packet is too short")
        if packet[0] != BinaryPacket.HEADER_RESPONSE:
            raise ValueError("invalid response packet header")
        if calculate_crc16(packet[:-2]) != decode_u16(packet[-2:]):
            raise ValueError("response packet CRC mismatch")

        status = packet[1]
        count = packet[2]
        offset = 3
        options: list[dict[str, int]] = []
        for _ in range(count):
            if offset + 9 > len(packet) - 2:
                raise ValueError("incomplete firmware option list")
            options.append(
                {
                    "fw_id": decode_u16(packet[offset : offset + 2]),
                    "version": decode_u16(packet[offset + 2 : offset + 4]),
                    "size": decode_u32(packet[offset + 4 : offset + 8]),
                    "force": packet[offset + 8],
                }
            )
            offset += 9
        return {"header": packet[0], "status": status, "count": count, "options": options}

    @staticmethod
    def encode_select(fw_id: int, preferred_block_size: int, protocol: int) -> bytes:
        payload = bytearray()
        payload.append(BinaryPacket.HEADER_SELECT)
        payload.extend(encode_u16(fw_id))
        payload.extend(encode_u16(preferred_block_size))
        payload.append(protocol & 0xFF)
        payload.extend(encode_u16(calculate_crc16(bytes(payload))))
        return bytes(payload)

    @staticmethod
    def decode_select(packet: bytes) -> dict[str, int]:
        if len(packet) != 8:
            raise ValueError("select packet must be exactly 8 bytes")
        if packet[0] != BinaryPacket.HEADER_SELECT:
            raise ValueError("invalid select packet header")
        if calculate_crc16(packet[:6]) != decode_u16(packet[6:]):
            raise ValueError("select packet CRC mismatch")
        return {
            "header": packet[0],
            "fw_id": decode_u16(packet[1:3]),
            "preferred_block_size": decode_u16(packet[3:5]),
            "protocol": packet[5],
        }

    @staticmethod
    def encode_tftp(bootstrap: TftpBootstrap) -> bytes:
        ip_bytes = ipaddress.IPv4Address(bootstrap.server_ip).packed
        filename_bytes = bootstrap.filename.encode("utf-8")
        token = bytes(bootstrap.token)
        if len(filename_bytes) > 255:
            raise ValueError("filename is too long for bootstrap packet")
        if len(token) > 255:
            raise ValueError("token is too long for bootstrap packet")
        payload = bytearray()
        payload.append(BinaryPacket.HEADER_TFTP)
        payload.extend(ip_bytes)
        payload.extend(encode_u16(bootstrap.port))
        payload.append(bootstrap.mode & 0xFF)
        payload.append(len(filename_bytes) & 0xFF)
        payload.extend(filename_bytes)
        payload.append(len(token) & 0xFF)
        payload.extend(token)
        payload.extend(encode_u16(calculate_crc16(bytes(payload))))
        return bytes(payload)

    @staticmethod
    def decode_tftp(packet: bytes) -> dict[str, object]:
        if len(packet) < 11:
            raise ValueError("tftp packet is too short")
        if packet[0] != BinaryPacket.HEADER_TFTP:
            raise ValueError("invalid tftp packet header")
        if calculate_crc16(packet[:-2]) != decode_u16(packet[-2:]):
            raise ValueError("tftp packet CRC mismatch")
        server_ip = str(ipaddress.IPv4Address(packet[1:5]))
        port = decode_u16(packet[5:7])
        mode = packet[7]
        filename_length = packet[8]
        filename_start = 9
        filename_end = filename_start + filename_length
        if filename_end + 1 > len(packet) - 2:
            raise ValueError("incomplete tftp filename section")
        filename = packet[filename_start:filename_end].decode("utf-8")
        token_length = packet[filename_end]
        token_start = filename_end + 1
        token_end = token_start + token_length
        if token_end > len(packet) - 2:
            raise ValueError("incomplete tftp token section")
        token = packet[token_start:token_end]
        return {
            "header": packet[0],
            "server_ip": server_ip,
            "port": port,
            "mode": mode,
            "filename": filename,
            "token": token,
        }


def calculate_manifest_firmware_options(rows: Sequence[Sequence[object]]) -> list[FirmwareOption]:
    """Convert database rows into firmware options for response packets."""

    options: list[FirmwareOption] = []
    for row in rows:
        fw_id, version, size, force = row
        options.append(
            FirmwareOption(
                fw_id=int(fw_id),
                version=int(version),
                size=int(size),
                force=int(force),
            )
        )
    return options
