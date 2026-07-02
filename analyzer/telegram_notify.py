"""Telegram notifications for pulse picks and daily briefing."""

from __future__ import annotations

import os

import requests

from analyzer.env_loader import load_app_env

load_app_env()

from analyzer.telegram_subscriptions import (
    bot_configured,
    bot_token,
    has_active_subscribers,
    list_active_subscribers,
    process_bot_updates,
)


def telegram_configured() -> bool:
    """Bot token plus at least one subscriber (in-app or legacy .env chat ID)."""
    if not bot_configured():
        return False
    if os.getenv("TELEGRAM_CHAT_ID", "").strip():
        return True
    return has_active_subscribers()


def send_telegram(
    message: str,
    parse_mode: str = "Markdown",
    *,
    chat_id: str | None = None,
) -> tuple[bool, str]:
    token = bot_token()
    if not token:
        return False, "Set TELEGRAM_BOT_TOKEN in .env (create bot via @BotFather)"

    text = message[:4000]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    target = (chat_id or os.getenv("TELEGRAM_CHAT_ID", "")).strip()
    if not target:
        return False, "Subscribe to Telegram in the app sidebar first"

    try:
        r = requests.post(
            url,
            json={"chat_id": target, "text": text, "parse_mode": parse_mode},
            timeout=15,
        )
        if r.status_code == 200:
            return True, "Sent"
        return False, r.text[:200]
    except Exception as exc:
        return False, str(exc)


def send_telegram_broadcast(
    message: str,
    parse_mode: str = "Markdown",
    *,
    alert_type: str | None = None,
) -> tuple[bool, str]:
    """
    Send to all subscribers for alert_type (morning | eod | pulse).
    Processes pending bot /start updates first.
    """
    if not bot_configured():
        return False, "Set TELEGRAM_BOT_TOKEN in .env"

    process_bot_updates()
    subs = list_active_subscribers(alert_type)
    if not subs:
        return False, "No Telegram subscribers — use sidebar to subscribe"

    sent = 0
    errors: list[str] = []
    for sub in subs:
        ok, err = send_telegram(message, parse_mode=parse_mode, chat_id=sub.chat_id)
        if ok:
            sent += 1
        else:
            errors.append(err)

    if sent:
        return True, f"Sent to {sent} subscriber(s)"
    return False, errors[0] if errors else "Send failed"


def format_pulse_alert(report) -> str:
    lines = ["*Market Pulse*"]
    if getattr(report, "regime", None):
        lines.append(f"Regime: {report.regime.regime}")
    lines.append(report.market_verdict.replace("**", "*"))

    for label, picks in (
        ("Intraday", getattr(report, "intraday_picks", [])[:3]),
        ("Swing", getattr(report, "short_term_picks", [])[:3]),
        ("Long", getattr(report, "long_term_picks", [])[:3]),
    ):
        if picks:
            syms = ", ".join(f"{p.nse_symbol} ({p.action})" for p in picks)
            lines.append(f"*{label}:* {syms}")

    lines.append("_Not financial advice._")
    return "\n".join(lines)


def format_morning_telegram(briefing) -> str:
    lines = [f"*Morning briefing* — {briefing.generated_at}"]
    lines.append(f"Session: {briefing.session_status} · {briefing.next_session}")
    lines.append(
        f"Global: *{briefing.global_bias}* spillover {briefing.spillover_score:+.0f} "
        f"({briefing.predicted_move_pct:+.2f}%)"
    )
    lines.append(f"VIX: {briefing.vix_regime}")
    if briefing.fii_dii_summary != "—":
        lines.append(briefing.fii_dii_summary.replace("**", "*")[:200])
    lines.append(f"Regime: {briefing.regime}")
    if briefing.swing_picks:
        lines.append(f"Swing: {', '.join(briefing.swing_picks[:4])}")
    if briefing.long_picks:
        lines.append(f"Long: {', '.join(briefing.long_picks[:4])}")
    if briefing.holdings_briefing and briefing.holdings_briefing.priority_actions:
        lines.append("*Holdings:*")
        for a in briefing.holdings_briefing.priority_actions[:4]:
            lines.append(f"• {a.replace('**', '*')}")
    lines.append("_Not financial advice._")
    return "\n".join(lines)


def format_briefing_alert(briefing) -> str:
    lines = [f"*Daily Briefing* — {briefing.generated_at}"]
    lines.append(briefing.summary.replace("**", "*")[:500])
    for a in briefing.priority_actions[:5]:
        lines.append(f"• {a.replace('**', '*')}")
    lines.append("_Not financial advice._")
    return "\n".join(lines)


def format_track_record_telegram(report, tuning, validation: dict | None = None) -> str:
    """EOD scorecard after suggestion validation."""
    validation = validation or {}
    lines = ["*Track Record — EOD scorecard*"]

    validated_run = validation.get("validated", 0)
    if validated_run:
        lines.append(f"Scored *{validated_run}* new picks this run.")

    lines.append(
        f"Total validated: *{report.validated_count}* · "
        f"Win rate: *{report.overall_win_rate_pct:.1f}%* · "
        f"Pending: {report.pending_count}"
    )

    if tuning and tuning.changes:
        lines.append("*Threshold updates:*")
        for ch in tuning.changes:
            lines.append(
                f"• {ch.horizon}: {ch.old_value} → {ch.new_value} "
                f"({ch.win_rate_pct:.0f}% over {ch.scored} picks)"
            )
    elif tuning:
        t = tuning.thresholds
        lines.append(
            f"Gates unchanged — intraday *{t['intraday']}* · "
            f"swing *{t['short']}* · long *{t['long']}*"
        )

    if report.insights:
        lines.append("*Insights:*")
        for insight in report.insights[:4]:
            lines.append(f"• {insight.replace('**', '*')}")

    hits, misses = [], []
    for r in report.recent_validated[:12]:
        if r.outcome_correct == 1:
            hits.append(r.symbol)
        elif r.outcome_correct == 0:
            misses.append(r.symbol)
    if hits:
        lines.append(f"Recent hits: {', '.join(hits[:6])}")
    if misses:
        lines.append(f"Recent misses: {', '.join(misses[:6])}")

    lines.append("_Not financial advice._")
    return "\n".join(lines)
