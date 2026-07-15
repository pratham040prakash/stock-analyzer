"""Decision history — immutable SQLite archive."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

from analyzer.decision_engine.models import DecisionArtifact
from analyzer.decision_engine.serialization import decision_artifact_from_dict, decision_artifact_to_dict

_STORE_LOCK = threading.RLock()
_STORE_READY_PATH: Path | None = None


class ImmutableDecisionError(RuntimeError):
    """Raised when attempting to overwrite an existing decision."""


def decision_store_path() -> Path:
    d = Path(__file__).resolve().parent.parent.parent / "data" / "decision_engine"
    d.mkdir(parents=True, exist_ok=True)
    return d / "decisions.db"


def _connect_unlocked() -> sqlite3.Connection:
    conn = sqlite3.connect(decision_store_path(), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS decision_artifacts (
            decision_id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            verdict TEXT NOT NULL,
            evidence_packet_id TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_decision_subject ON decision_artifacts(subject);
        CREATE INDEX IF NOT EXISTS idx_decision_evidence ON decision_artifacts(evidence_packet_id);
        CREATE INDEX IF NOT EXISTS idx_decision_created ON decision_artifacts(created_at);
        """
    )


def _ensure_store() -> None:
    global _STORE_READY_PATH
    path = decision_store_path()
    if _STORE_READY_PATH == path:
        return
    with _STORE_LOCK:
        if _STORE_READY_PATH == path:
            return
        with _connect_unlocked() as conn:
            _create_tables(conn)
        _STORE_READY_PATH = path


def save_decision(artifact: DecisionArtifact) -> str:
    """Persist decision — insert-only; never overwrite."""
    _ensure_store()
    payload = json.dumps(decision_artifact_to_dict(artifact), ensure_ascii=False)
    with _STORE_LOCK:
        with _connect_unlocked() as conn:
            existing = conn.execute(
                "SELECT decision_id FROM decision_artifacts WHERE decision_id = ?",
                (artifact.decision_id,),
            ).fetchone()
            if existing:
                raise ImmutableDecisionError(
                    f"Decision {artifact.decision_id} already exists — history is immutable"
                )
            conn.execute(
                """
                INSERT INTO decision_artifacts (
                    decision_id, subject, subject_type, verdict,
                    evidence_packet_id, confidence, created_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.decision_id,
                    artifact.subject,
                    artifact.subject_type,
                    artifact.verdict.value,
                    artifact.evidence_packet_id,
                    artifact.confidence,
                    artifact.timestamp,
                    payload,
                ),
            )
            conn.commit()
    return artifact.decision_id


def fetch_decision(decision_id: str) -> DecisionArtifact | None:
    _ensure_store()
    with _STORE_LOCK:
        with _connect_unlocked() as conn:
            row = conn.execute(
                "SELECT payload_json FROM decision_artifacts WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
    if not row:
        return None
    return decision_artifact_from_dict(json.loads(row["payload_json"]))


def fetch_decisions_for_subject(subject: str, *, limit: int = 20) -> list[DecisionArtifact]:
    _ensure_store()
    with _STORE_LOCK:
        with _connect_unlocked() as conn:
            rows = conn.execute(
                """
                SELECT payload_json FROM decision_artifacts
                WHERE subject = ? ORDER BY created_at DESC LIMIT ?
                """,
                (subject, limit),
            ).fetchall()
    return [decision_artifact_from_dict(json.loads(r["payload_json"])) for r in rows]


def init_decision_store() -> None:
    _ensure_store()
