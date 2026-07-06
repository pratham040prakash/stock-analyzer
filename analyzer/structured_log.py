"""JSON-line structured logging for scheduled jobs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def log_event(event: str, **fields) -> None:
    """Append one JSON log line to logs/autopilot.jsonl."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
        "event": event,
        **fields,
    }
    path = LOG_DIR / "autopilot.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def tail_log_lines(path: Path, n: int = 8) -> list[str]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return lines[-n:]
    except OSError:
        return []
