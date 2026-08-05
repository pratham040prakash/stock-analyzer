"""Immutable Decision Snapshot store — flight recorder ledger (APEX-013 E0)."""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any

from analyzer.decision_engine.models import DECISION_VERSION
from analyzer.intelligence_lab.snapshot_schema import (
    build_decision_snapshot_payload,
    collect_forbidden_hindsight_keys,
    new_snapshot_id,
    utc_created_at,
)
from analyzer.use_cases.morning_brief import MorningBriefDomain
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from ui.broker.state import BrokerSnapshot

logger = logging.getLogger(__name__)

_STORE_LOCK = threading.RLock()
_STORE_READY_PATH: Path | None = None


class ImmutableSnapshotError(RuntimeError):
    """Raised when attempting to overwrite an existing snapshot."""


def snapshot_store_path() -> Path:
    d = Path(__file__).resolve().parent.parent.parent / "data" / "intelligence_lab"
    d.mkdir(parents=True, exist_ok=True)
    return d / "decision_snapshots.db"


def _connect_unlocked() -> sqlite3.Connection:
    conn = sqlite3.connect(snapshot_store_path(), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS decision_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            decision_id TEXT NOT NULL DEFAULT '',
            verdict_key TEXT NOT NULL DEFAULT '',
            market TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_snapshots_created ON decision_snapshots(created_at);
        CREATE INDEX IF NOT EXISTS idx_snapshots_decision ON decision_snapshots(decision_id);
        CREATE INDEX IF NOT EXISTS idx_snapshots_verdict ON decision_snapshots(verdict_key);
        """
    )


def _ensure_store() -> None:
    global _STORE_READY_PATH
    path = snapshot_store_path()
    if _STORE_READY_PATH == path:
        return
    with _STORE_LOCK:
        if _STORE_READY_PATH == path:
            return
        with _connect_unlocked() as conn:
            _create_tables(conn)
        _STORE_READY_PATH = path


def save_decision_snapshot(payload: dict[str, Any]) -> str:
    """Insert-only persist — never overwrite an existing snapshot."""
    forbidden = collect_forbidden_hindsight_keys(payload)
    if forbidden:
        raise ValueError(f"Snapshot contains hindsight fields: {forbidden}")

    snapshot_id = str(payload["snapshot_id"])
    schema_version = str(payload["schema_version"])
    created_at = str(payload["created_at"])
    decision = payload.get("decision") or {}
    decision_id = str(decision.get("decision_id") or "")
    verdict_key = str((decision.get("verdict_key") or ""))
    market = str((payload.get("market_session") or {}).get("market") or "")

    _ensure_store()
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    with _STORE_LOCK:
        with _connect_unlocked() as conn:
            existing = conn.execute(
                "SELECT snapshot_id FROM decision_snapshots WHERE snapshot_id = ?",
                (snapshot_id,),
            ).fetchone()
            if existing:
                raise ImmutableSnapshotError(
                    f"Snapshot {snapshot_id} already exists — ledger is immutable"
                )
            conn.execute(
                """
                INSERT INTO decision_snapshots (
                    snapshot_id, schema_version, created_at,
                    decision_id, verdict_key, market, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (snapshot_id, schema_version, created_at, decision_id, verdict_key, market, body),
            )
            conn.commit()
    return snapshot_id


def fetch_decision_snapshot(snapshot_id: str) -> dict[str, Any] | None:
    _ensure_store()
    with _STORE_LOCK:
        with _connect_unlocked() as conn:
            row = conn.execute(
                "SELECT payload_json FROM decision_snapshots WHERE snapshot_id = ?",
                (snapshot_id,),
            ).fetchone()
    if not row:
        return None
    return json.loads(row["payload_json"])


def persist_decision_snapshot_safe(
    brief: MorningBriefViewModel,
    *,
    domain: MorningBriefDomain,
    broker: BrokerSnapshot,
) -> str | None:
    """Persist flight recorder snapshot; never raise — Morning Brief must continue."""
    snapshot_id = new_snapshot_id()
    created_at = utc_created_at()
    try:
        payload = build_decision_snapshot_payload(
            brief,
            context=domain.context,
            decision_source=domain.decision_source,
            stale=domain.stale,
            stale_reason=domain.stale_reason,
            decision_engine_version=(
                domain.decision.decision_version if domain.decision else DECISION_VERSION
            ),
            snapshot_id=snapshot_id,
            created_at=created_at,
        )
        return save_decision_snapshot(payload)
    except Exception:
        logger.exception(
            "APEX-013 E0: decision snapshot persist failed (snapshot_id=%s)",
            snapshot_id,
        )
        return None
