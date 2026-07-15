"""Optional SQLite archive for evidence packets."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

from analyzer.evidence_engine.models import EvidencePacket
from analyzer.evidence_engine.serialization import evidence_packet_from_dict, evidence_packet_to_dict

_STORE_LOCK = threading.RLock()
_STORE_READY_PATH: Path | None = None


def evidence_store_path() -> Path:
    d = Path(__file__).resolve().parent.parent.parent / "data" / "evidence_engine"
    d.mkdir(parents=True, exist_ok=True)
    return d / "evidence.db"


def _connect_unlocked() -> sqlite3.Connection:
    conn = sqlite3.connect(evidence_store_path(), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS evidence_packets (
            packet_id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completeness_pct REAL NOT NULL DEFAULT 0,
            gap_count INTEGER NOT NULL DEFAULT 0,
            conflict_count INTEGER NOT NULL DEFAULT 0,
            payload_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_evidence_subject ON evidence_packets(subject);
        CREATE INDEX IF NOT EXISTS idx_evidence_created ON evidence_packets(created_at);
        """
    )


def _ensure_store() -> None:
    global _STORE_READY_PATH
    path = evidence_store_path()
    if _STORE_READY_PATH == path:
        return
    with _STORE_LOCK:
        if _STORE_READY_PATH == path:
            return
        with _connect_unlocked() as conn:
            _create_tables(conn)
        _STORE_READY_PATH = path


def save_evidence_packet(packet: EvidencePacket) -> str:
    """Persist packet JSON; returns packet_id."""
    _ensure_store()
    payload = json.dumps(evidence_packet_to_dict(packet), ensure_ascii=False)
    with _STORE_LOCK:
        with _connect_unlocked() as conn:
            conn.execute(
                """
                INSERT INTO evidence_packets (
                    packet_id, subject, subject_type, created_at,
                    completeness_pct, gap_count, conflict_count, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(packet_id) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    completeness_pct=excluded.completeness_pct,
                    gap_count=excluded.gap_count,
                    conflict_count=excluded.conflict_count
                """,
                (
                    packet.packet_id,
                    packet.subject,
                    packet.subject_type,
                    packet.created_at,
                    packet.completeness_pct,
                    packet.gap_count,
                    packet.conflict_count,
                    payload,
                ),
            )
            conn.commit()
    return packet.packet_id


def fetch_evidence_packet(packet_id: str) -> EvidencePacket | None:
    _ensure_store()
    with _STORE_LOCK:
        with _connect_unlocked() as conn:
            row = conn.execute(
                "SELECT payload_json FROM evidence_packets WHERE packet_id = ?",
                (packet_id,),
            ).fetchone()
    if not row:
        return None
    return evidence_packet_from_dict(json.loads(row["payload_json"]))


def init_evidence_store() -> None:
    _ensure_store()
