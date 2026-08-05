"""SQLite DAO layer for OTA gateway and server services."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Iterator, Sequence


DEFAULT_SERVER_DB = Path("code/data/center_db.db")
DEFAULT_GATEWAY_DB = Path("database/gateway_db.db")


@dataclass(frozen=True)
class FirmwareRecord:
    fw_id: int
    version: int
    file_path: str | None
    file_size: int | None
    checksum_sha256: str | None
    is_force: int
    sync_status: int


@dataclass(frozen=True)
class PeerRecord:
    device_id: int
    fw_id: int
    version: int
    ip_address: str
    last_verified: int


class StorageManager:
    """Thin DAO wrapper around SQLite with explicit transaction handling."""

    def __init__(self, db_path: str | os.PathLike[str]):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def ensure_schema(self) -> None:
        schema_path = Path("code/data/init_center_db.sql")
        if not schema_path.exists():
            raise FileNotFoundError(f"schema file not found: {schema_path}")
        schema_sql = schema_path.read_text(encoding="utf-8")
        if "-- Sample data:" in schema_sql:
            schema_sql = schema_sql.split("-- Sample data:", 1)[0]
        with self.transaction() as connection:
            connection.executescript(schema_sql)

    def get_latest_firmware(self, device_id: int) -> list[FirmwareRecord]:
        query = """
            SELECT f.fw_id, f.version, f.file_path, f.file_size, f.checksum_sha256, f.is_force, f.sync_status
            FROM dev_join_fw AS j
            JOIN firmwares AS f ON f.fw_id = j.fw_id
            WHERE j.device_id = ?
            ORDER BY j.is_force DESC, j.version DESC, j.fw_id ASC
        """
        with self.connect() as connection:
            rows = connection.execute(query, (device_id,)).fetchall()
        return [
            FirmwareRecord(
                fw_id=int(row["fw_id"]),
                version=int(row["version"]),
                file_path=row["file_path"],
                file_size=row["file_size"],
                checksum_sha256=row["checksum_sha256"],
                is_force=int(row["is_force"]),
                sync_status=int(row["sync_status"]),
            )
            for row in rows
        ]

    def get_pending_manifest(self) -> list[tuple[int, int, int, int]]:
        query = """
            SELECT fw_id, version, COALESCE(file_size, 0) AS file_size, COALESCE(is_force, 0) AS is_force
            FROM firmwares
            WHERE sync_status = 1
            ORDER BY is_force DESC, version DESC, fw_id ASC
        """
        with self.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [tuple(int(row[column]) for column in ("fw_id", "version", "file_size", "is_force")) for row in rows]

    def update_peer_location(self, device_id: int, ip_address: str, fw_id: int, version: int) -> None:
        statement = """
            INSERT INTO peers_map (device_id, fw_id, version, ip_address, last_verified)
            VALUES (?, ?, ?, ?, strftime('%s','now'))
            ON CONFLICT(device_id, fw_id) DO UPDATE SET
                version = excluded.version,
                ip_address = excluded.ip_address,
                last_verified = excluded.last_verified
        """
        with self.transaction() as connection:
            connection.execute(statement, (device_id, fw_id, version, ip_address))

    def update_firmware_metadata(
        self,
        fw_id: int,
        version: int,
        file_path: str,
        file_size: int,
        checksum_sha256: str,
        is_force: int = 0,
        sync_status: int = 1,
    ) -> None:
        statement = """
            INSERT INTO firmwares (fw_id, version, file_path, file_size, checksum_sha256, is_force, sync_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fw_id) DO UPDATE SET
                version = excluded.version,
                file_path = excluded.file_path,
                file_size = excluded.file_size,
                checksum_sha256 = excluded.checksum_sha256,
                is_force = excluded.is_force,
                sync_status = excluded.sync_status
        """
        with self.transaction() as connection:
            connection.execute(statement, (fw_id, version, file_path, file_size, checksum_sha256, is_force, sync_status))

    def get_device_last_version(self, device_id: int) -> int | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT current_version FROM devices WHERE device_id = ? LIMIT 1",
                (device_id,),
            ).fetchone()
        return None if row is None else int(row[0])

    def update_device_sync(self, device_id: int, current_version: int, status: int = 1) -> None:
        with self.transaction() as connection:
            connection.execute(
                """
                INSERT INTO devices (device_id, current_version, last_update_timestamp, status)
                VALUES (?, ?, strftime('%s','now'), ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    current_version = excluded.current_version,
                    last_update_timestamp = excluded.last_update_timestamp,
                    status = excluded.status
                """,
                (device_id, current_version, status),
            )

    def update_system_sync(self, sync_key: str, server_status: str, timestamp: int) -> None:
        with self.transaction() as connection:
            connection.execute(
                """
                INSERT INTO system_sync (sync_key, last_sync_timestamp, server_status)
                VALUES (?, ?, ?)
                ON CONFLICT(sync_key) DO UPDATE SET
                    last_sync_timestamp = excluded.last_sync_timestamp,
                    server_status = excluded.server_status
                """,
                (sync_key, timestamp, server_status),
            )


class FileManifestManager:
    """Utility helper for server-side firmware ingestion and hashing."""

    @staticmethod
    def sha256_of_file(file_path: str | os.PathLike[str]) -> str:
        digest = hashlib.sha256()
        with open(file_path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
