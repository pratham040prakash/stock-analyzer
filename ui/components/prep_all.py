"""One-click nightly prep + bedtime checklist."""

from __future__ import annotations

import streamlit as st

from analyzer.affordable_invest import DEFAULT_MAX_OPTION_LOT_COST_INR
from analyzer.intraday_pulse_source import DEFAULT_INTRADAY_PULSE_PERIOD
from analyzer.mis_checklist_store import is_checklist_complete
from analyzer.market_session import market_session_status
from analyzer.nightly_prep import run_nightly_prep
from analyzer.nightly_prep import NightlyPrepResult
from analyzer.prep_status import (
    is_nightly_prep_complete,
    mark_prep_step,
    prep_complete_count,
    prep_status_for,
    sync_selection_prep_step,
)
from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured
from analyzer.trade_selection import is_selection_complete, load_selected_symbols
from analyzer.watchlist_pins import load_pinned_plans
from analyzer.mis_printable_checklist import format_printable_mis_checklist
from analyzer.watchlist_telegram import format_combined_prep_telegram


def _checklist_done() -> bool:
    return is_checklist_complete()


def render_prep_checklist() -> None:
    """Bedtime prep status: equity · options · telegram · 2 trades · MIS checklist."""
    status = prep_status_for()
    sync_selection_prep_step(status["trade_date"])
    status = prep_status_for()
    checklist_ok = _checklist_done()
    done = prep_complete_count(status) + (1 if checklist_ok else 0)
    total = 5

    icons = {
        "equity": "✅" if status["equity"] else "⬜",
        "options": "✅" if status["options"] else "⬜",
        "telegram": "✅" if status["telegram"] else "⬜",
        "selection": "✅" if status["selection"] else "⬜",
        "checklist": "✅" if checklist_ok else "⬜",
    }
    st.caption(
        f"**Prep checklist** ({done}/{total}): "
        f"{icons['equity']} Equity · "
        f"{icons['options']} Options · "
        f"{icons['telegram']} Telegram · "
        f"{icons['selection']} 2 trades · "
        f"{icons['checklist']} MIS checklist"
    )
    if not status["selection"]:
        st.warning("Star **2** names in the watchlist below before bed.")
    elif is_nightly_prep_complete(status) and checklist_ok:
        st.success("You're set for tomorrow — rest well.")
    elif is_nightly_prep_complete(status):
        st.info("Picks saved & sent — tick **Daily MIS checklist** when done reviewing.")


def render_prep_all_bar(market: str, *, period: str = DEFAULT_INTRADAY_PULSE_PERIOD) -> None:
    """Prep all button at top of Intraday tab."""
    max_lot = float(
        st.session_state.get("options_lot_budget", DEFAULT_MAX_OPTION_LOT_COST_INR)
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("#### 🚀 Nightly prep")
        st.caption(
            "One click: **Quick scan** → top **5** equity → **Nifty/Bank Nifty CE/PE** "
            "→ **Telegram** (if subscribed). ~2 min total."
        )
    with c2:
        prep_all = st.button(
            "Prep all tonight",
            type="primary",
            key="prep_all_btn",
            use_container_width=True,
        )

    if prep_all:
        with st.spinner("Running full MIS prep… equity scan + options chains…"):
            result, report = run_nightly_prep(
                market,
                period=period,
                max_lot_cost=max_lot,
                send_telegram=True,
                use_cache=False,
            )
            if report is not None:
                st.session_state["market_pulse_full"] = report
            st.session_state["options_expiry_loaded"] = True
            st.session_state.pop("options_expiry_watchlist_cache", None)
            _show_prep_result(result)
            st.rerun()

    render_prep_checklist()
    render_printable_checklist_block()


def render_printable_checklist_block(*, market_bias: str = "") -> None:
    """Copy / download full MIS checklist auto-filled from last prep."""
    cache = st.session_state.get("options_expiry_watchlist_cache")
    options_picks = getattr(cache, "picks", None) if cache else None
    if not market_bias:
        pulse = st.session_state.get("market_pulse_full")
        market_bias = getattr(pulse, "market_bias", "") if pulse else ""

    text = format_printable_mis_checklist(
        options_picks=options_picks,
        market_bias=market_bias,
        include_live_cues=True,
    )
    trade_date = market_session_status().get("date", "checklist")

    with st.expander("📋 Copy tonight's checklist (phone)", expanded=False):
        st.caption(
            "Auto-filled from your last **Quick scan** / **Prep all** — "
            "paste into Notes, Telegram Saved Messages, or WhatsApp."
        )
        st.code(text, language=None)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download .txt",
                data=text.encode("utf-8"),
                file_name=f"mis-checklist-{trade_date}.txt",
                mime="text/plain",
                key="prep_checklist_download",
                use_container_width=True,
            )
        with c2:
            from analyzer.whatsapp_export import whatsapp_share_url

            st.link_button(
                "Share on WhatsApp",
                whatsapp_share_url(text),
                use_container_width=True,
            )


def _show_prep_result(result: NightlyPrepResult) -> None:
    if result.equity_count:
        st.success(f"Equity: **{result.equity_count}** picks saved.")
    if result.options_count:
        st.success(f"Options: **{result.options_count}** CE/PE rows saved.")
    if result.telegram_sent:
        st.success("Combined prep sent to Telegram.")
    elif result.telegram_error:
        st.warning(result.telegram_error)
    for err in result.errors:
        st.warning(err)


def send_combined_telegram_from_session(
    *,
    options_picks: list | None = None,
    market_bias: str = "",
) -> tuple[bool, str]:
    """Send equity + options in one Telegram message."""
    if not telegram_configured():
        return False, "Telegram not configured"
    prep_date = market_session_status().get("date", "")
    msg = format_combined_prep_telegram(
        load_pinned_plans(),
        options_picks or [],
        market_bias=market_bias,
        prep_date=prep_date,
    )
    ok, err = send_telegram_broadcast(msg, alert_type="pulse")
    if ok:
        mark_prep_step("telegram")
    return ok, err
