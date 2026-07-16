"""Lightweight broker snapshot persisted locally for desktop startup UX."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
BROKER_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "broker"
SNAPSHOT_PATH = BROKER_DIR / "session_state.json"


@dataclass
class BrokerSnapshot:
    state: str = "disconnected"
    user_id: str = ""
    user_name: str = ""
    last_sync_at: str = ""
    last_sync_status: str = ""
    holdings_count: int = 0
    positions_count: int = 0
    portfolio_value_inr: float = 0.0
    today_unrealized_pnl_inr: float = 0.0
    today_realized_pnl_inr: float = 0.0
    available_cash_inr: float = 0.0
    error_message: str = ""
    broker_label: str = "Zerodha"

    def connected(self) -> bool:
        return self.state in ("connected", "limited")

    def needs_sign_in(self) -> bool:
        return self.state in ("disconnected", "expired", "no_token")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> BrokerSnapshot:
        if not data:
            return cls()
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


def _ensure_dir() -> None:
    BROKER_DIR.mkdir(parents=True, exist_ok=True)


def now_ist_label() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")


def save_broker_snapshot(snapshot: BrokerSnapshot) -> None:
    _ensure_dir()
    payload = {
        "version": 1,
        "updated_at": now_ist_label(),
        "snapshot": snapshot.to_dict(),
    }
    SNAPSHOT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_broker_snapshot() -> BrokerSnapshot:
    if not SNAPSHOT_PATH.exists():
        return BrokerSnapshot()
    try:
        raw = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        return BrokerSnapshot.from_dict(raw.get("snapshot"))
    except Exception:
        return BrokerSnapshot()
