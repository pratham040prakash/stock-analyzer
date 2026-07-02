"""In-app Telegram subscription — link user chat_id via bot /start deep link."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from analyzer.env_loader import load_app_env

IST = ZoneInfo("Asia/Kolkata")
TOKEN_PREFIX = "sa_"

load_app_env()


def _data_dir() -> Path:
    d = Path(__file__).resolve().parent.parent / "data" / "telegram"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return _data_dir() / "subscribers.db"


def bot_state_path() -> Path:
    return _data_dir() / "bot_state.json"


def bot_token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()


def bot_configured() -> bool:
    return bool(bot_token())


@dataclass
class TelegramSubscriber:
    subscribe_token: str
    chat_id: str
    username: str
    first_name: str
    subscribed_at: str
    alerts_morning: bool = True
    alerts_eod: bool = True
    alerts_pulse: bool = False
    alerts_sip: bool = False
    active: bool = True


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_subscriptions_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS telegram_subscribers (
                subscribe_token TEXT PRIMARY KEY,
                chat_id TEXT UNIQUE,
                username TEXT,
                first_name TEXT,
                subscribed_at TEXT,
                alerts_morning INTEGER DEFAULT 1,
                alerts_eod INTEGER DEFAULT 1,
                alerts_pulse INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tg_chat ON telegram_subscribers(chat_id)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_tokens (
                subscribe_token TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)
        _migrate_subscriptions(conn)


def _migrate_subscriptions(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(telegram_subscribers)")}
    if "alerts_sip" not in cols:
        conn.execute(
            "ALTER TABLE telegram_subscribers ADD COLUMN alerts_sip INTEGER DEFAULT 0"
        )


def _row_to_subscriber(row: sqlite3.Row) -> TelegramSubscriber:
    return TelegramSubscriber(
        subscribe_token=row["subscribe_token"],
        chat_id=row["chat_id"] or "",
        username=row["username"] or "",
        first_name=row["first_name"] or "",
        subscribed_at=row["subscribed_at"] or "",
        alerts_morning=bool(row["alerts_morning"]),
        alerts_eod=bool(row["alerts_eod"]),
        alerts_pulse=bool(row["alerts_pulse"]),
        alerts_sip=bool(row["alerts_sip"]) if "alerts_sip" in row.keys() else False,
        active=bool(row["active"]),
    )


def _client_token_path() -> Path:
    return _data_dir() / "client_subscribe_token.txt"


def get_or_create_subscribe_token(*, force_new: bool = False) -> str:
    """
    Stable subscribe token across page refreshes (same machine).
    Regenerate only when force_new=True or after successful subscribe.
    """
    init_subscriptions_db()
    path = _client_token_path()
    if not force_new and path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if token.startswith(TOKEN_PREFIX):
            return token

    if not force_new:
        with _connect() as conn:
            row = conn.execute(
                "SELECT subscribe_token FROM pending_tokens ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
        if row and str(row["subscribe_token"]).startswith(TOKEN_PREFIX):
            token = str(row["subscribe_token"])
            path.write_text(token, encoding="utf-8")
            return token

    token = create_subscribe_token()
    path.write_text(token, encoding="utf-8")
    return token


def clear_client_subscribe_token() -> None:
    path = _client_token_path()
    if path.exists():
        path.unlink()


def create_subscribe_token() -> str:
    """New deep-link token for this browser session."""
    init_subscriptions_db()
    token = f"{TOKEN_PREFIX}{secrets.token_urlsafe(12)}"
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO pending_tokens (subscribe_token, created_at) VALUES (?, ?)",
            (token, now),
        )
    return token


def get_subscriber_by_token(subscribe_token: str) -> TelegramSubscriber | None:
    init_subscriptions_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM telegram_subscribers WHERE subscribe_token = ? AND active = 1",
            (subscribe_token,),
        ).fetchone()
    return _row_to_subscriber(row) if row and row["chat_id"] else None


def list_active_subscribers(alert_type: str | None = None) -> list[TelegramSubscriber]:
    init_subscriptions_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM telegram_subscribers WHERE active = 1 AND chat_id IS NOT NULL"
        ).fetchall()
    subs = [_row_to_subscriber(r) for r in rows if r["chat_id"]]

    env_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if env_chat and not any(s.chat_id == env_chat for s in subs):
        subs.append(
            TelegramSubscriber(
                subscribe_token="env",
                chat_id=env_chat,
                username="env",
                first_name="Legacy .env",
                subscribed_at="",
                alerts_morning=True,
                alerts_eod=True,
                alerts_pulse=True,
                alerts_sip=True,
                active=True,
            )
        )

    if alert_type == "morning":
        return [s for s in subs if s.alerts_morning]
    if alert_type == "eod":
        return [s for s in subs if s.alerts_eod]
    if alert_type == "pulse":
        return [s for s in subs if s.alerts_pulse]
    if alert_type == "sip":
        return [s for s in subs if s.alerts_sip]
    return subs


def has_active_subscribers() -> bool:
    return bool(list_active_subscribers())


def update_alert_preferences(
    subscribe_token: str,
    *,
    alerts_morning: bool | None = None,
    alerts_eod: bool | None = None,
    alerts_pulse: bool | None = None,
    alerts_sip: bool | None = None,
) -> bool:
    init_subscriptions_db()
    fields: list[str] = []
    values: list[object] = []
    if alerts_morning is not None:
        fields.append("alerts_morning = ?")
        values.append(int(alerts_morning))
    if alerts_eod is not None:
        fields.append("alerts_eod = ?")
        values.append(int(alerts_eod))
    if alerts_pulse is not None:
        fields.append("alerts_pulse = ?")
        values.append(int(alerts_pulse))
    if alerts_sip is not None:
        fields.append("alerts_sip = ?")
        values.append(int(alerts_sip))
    if not fields:
        return False
    values.append(subscribe_token)
    with _connect() as conn:
        conn.execute(
            f"UPDATE telegram_subscribers SET {', '.join(fields)} WHERE subscribe_token = ?",
            values,
        )
        return conn.total_changes > 0


def unsubscribe_token(subscribe_token: str) -> bool:
    init_subscriptions_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE telegram_subscribers SET active = 0 WHERE subscribe_token = ?",
            (subscribe_token,),
        )
        return conn.total_changes > 0


def _load_offset() -> int:
    path = bot_state_path()
    if not path.exists():
        return 0
    try:
        return int(json.loads(path.read_text()).get("offset", 0))
    except Exception:
        return 0


def _save_offset(offset: int) -> None:
    bot_state_path().write_text(json.dumps({"offset": offset}), encoding="utf-8")


def get_bot_username() -> str | None:
    token = bot_token()
    if not token:
        return None
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if r.status_code == 200:
            return r.json().get("result", {}).get("username")
    except Exception:
        pass
    return None


def subscribe_deep_link(subscribe_token: str, bot_username: str | None = None) -> str:
    bot_username = bot_username or get_bot_username()
    if not bot_username:
        return ""
    return f"https://t.me/{bot_username}?start={subscribe_token}"


def _send_bot_message(chat_id: str | int, text: str) -> None:
    token = bot_token()
    if not token:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception:
        pass


def _handle_start(chat_id: int, username: str, first_name: str, payload: str) -> None:
    init_subscriptions_db()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    if not payload.startswith(TOKEN_PREFIX):
        _send_bot_message(
            chat_id,
            "Open Stock Analyzer in your browser and tap *Subscribe on Telegram* "
            "to get your personal link.",
        )
        return

    with _connect() as conn:
        existing = conn.execute(
            "SELECT subscribe_token FROM telegram_subscribers WHERE chat_id = ? AND active = 1",
            (str(chat_id),),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE telegram_subscribers SET
                    username = ?, first_name = ?, subscribed_at = ?, active = 1
                WHERE chat_id = ?
                """,
                (username, first_name, now, str(chat_id)),
            )
            _send_bot_message(chat_id, "You're already subscribed to Stock Analyzer alerts.")
            return

        conn.execute(
            """
            INSERT INTO telegram_subscribers (
                subscribe_token, chat_id, username, first_name, subscribed_at,
                alerts_morning, alerts_eod, alerts_pulse, active
            ) VALUES (?, ?, ?, ?, ?, 1, 1, 0, 1)
            ON CONFLICT(chat_id) DO UPDATE SET
                subscribe_token = excluded.subscribe_token,
                username = excluded.username,
                first_name = excluded.first_name,
                subscribed_at = excluded.subscribed_at,
                active = 1
            """,
            (payload, str(chat_id), username, first_name, now),
        )
        conn.execute("DELETE FROM pending_tokens WHERE subscribe_token = ?", (payload,))

    _send_bot_message(
        chat_id,
        "Subscribed to Stock Analyzer alerts.\n"
        "You'll receive morning briefing and EOD track-record scorecards "
        "(toggle types in the app sidebar). Enable SIP reminders under SIP & Goals.",
    )


def ensure_webhook_cleared() -> tuple[bool, str]:
    """Polling requires no webhook. Clears webhook if set."""
    token = bot_token()
    if not token:
        return False, "No bot token"
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook", timeout=10)
        if r.status_code == 200 and r.json().get("ok"):
            return True, "OK"
        return False, r.text[:120]
    except Exception as exc:
        return False, str(exc)


def process_bot_updates(*, retries: int = 1, pause_sec: float = 1.5) -> int:
    """
    Poll Telegram for new /start commands and bind chat_id to subscribe tokens.
    Returns number of new subscriptions processed.
    """
    import time

    token = bot_token()
    if not token:
        return 0

    ensure_webhook_cleared()
    total = 0
    for attempt in range(max(1, retries)):
        total += _poll_bot_updates_once()
        if attempt + 1 < retries:
            time.sleep(pause_sec)
    return total


def _poll_bot_updates_once() -> int:
    token = bot_token()
    if not token:
        return 0

    offset = _load_offset()
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={
                "offset": offset,
                "timeout": 0,
                "limit": 100,
                "allowed_updates": json.dumps(["message"]),
            },
            timeout=15,
        )
        if r.status_code != 200:
            return 0
        data = r.json()
        if not data.get("ok"):
            return 0
    except Exception:
        return 0

    processed = 0
    max_id = offset
    for upd in data.get("result", []):
        max_id = max(max_id, upd["update_id"] + 1)
        msg = upd.get("message") or {}
        text = (msg.get("text") or "").strip()
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if not chat_id or not text:
            continue

        if text.startswith("/start"):
            parts = text.split(maxsplit=1)
            payload = parts[1].strip() if len(parts) > 1 else ""
            _handle_start(
                chat_id,
                chat.get("username") or "",
                chat.get("first_name") or "",
                payload,
            )
            if payload.startswith(TOKEN_PREFIX):
                processed += 1
        elif text.lower() in ("/stop", "/unsubscribe"):
            init_subscriptions_db()
            with _connect() as conn:
                conn.execute(
                    "UPDATE telegram_subscribers SET active = 0 WHERE chat_id = ?",
                    (str(chat_id),),
                )
            _send_bot_message(chat_id, "Unsubscribed from Stock Analyzer alerts.")

    if max_id > offset:
        _save_offset(max_id)
    return processed


def verify_subscription(subscribe_token: str) -> tuple[bool, str]:
    """
    Poll Telegram a few times and check if subscribe_token is linked.
    """
    n = process_bot_updates(retries=4, pause_sec=2.0)
    sub = get_subscriber_by_token(subscribe_token)
    if sub and sub.chat_id:
        clear_client_subscribe_token()
        return True, "Subscribed"

    # Token mismatch after page refresh — attach if exactly one pending match in DB
    init_subscriptions_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM telegram_subscribers
            WHERE subscribe_token = ? AND active = 1 AND chat_id IS NOT NULL
            """,
            (subscribe_token,),
        ).fetchone()
        if row:
            clear_client_subscribe_token()
            return True, "Subscribed"

    if n > 0:
        return False, "Telegram received your message but token did not match — tap **Get new link** below."
    return False, (
        "No /start received yet. Use **Open in Telegram** (not the bot search), "
        "press **Start**, then verify again."
    )
