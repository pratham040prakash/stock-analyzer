"""Sidebar UI — subscribe to Telegram alerts without editing .env chat ID."""

from __future__ import annotations

import streamlit as st

from analyzer.env_loader import save_env_key, validate_telegram_bot_token
from analyzer.telegram_notify import send_telegram
from analyzer.telegram_subscriptions import (
    bot_configured,
    bot_token,
    ensure_webhook_cleared,
    get_bot_username,
    get_or_create_subscribe_token,
    get_subscriber_by_token,
    list_active_subscribers,
    process_bot_updates,
    subscribe_deep_link,
    unsubscribe_token,
    update_alert_preferences,
    verify_subscription,
)


def _render_bot_setup() -> bool:
    """In-app BotFather token setup. Returns True when bot is configured."""
    st.info(
        "**Step 1 — Create a bot** (one-time)\n\n"
        "1. Open [@BotFather](https://t.me/BotFather) in Telegram\n"
        "2. Send `/newbot` and follow the prompts\n"
        "3. Copy the **HTTP API token** BotFather gives you"
    )

    with st.expander("Paste bot token here", expanded=True):
        token_input = st.text_input(
            "Bot token",
            type="password",
            placeholder="123456789:ABCdefGHI…",
            key="tg_bot_token_input",
            label_visibility="collapsed",
        )
        if st.button("Save & connect bot", type="primary", key="tg_save_bot", use_container_width=True):
            ok, msg, _username = validate_telegram_bot_token(token_input)
            if not ok:
                st.error(msg)
                return False
            save_env_key("TELEGRAM_BOT_TOKEN", token_input.strip())
            ensure_webhook_cleared()
            st.session_state.pop("tg_bot_token_input", None)
            st.success(f"{msg}. Scroll down to subscribe.")
            st.rerun()
    return bot_configured()


def render_telegram_subscribe_sidebar() -> None:
    st.subheader("Telegram alerts")

    if not bot_configured():
        _render_bot_setup()
        st.caption("After saving the token, subscribe buttons appear below on refresh.")
        return

    process_bot_updates()
    token = get_or_create_subscribe_token()
    sub = get_subscriber_by_token(token)
    bot_user = get_bot_username()

    if sub and sub.chat_id:
        label = f"@{sub.username}" if sub.username else sub.first_name or "Telegram"
        st.success(f"Subscribed as **{label}**")

        morning = st.checkbox(
            "Morning briefing (8:30 AM)",
            value=sub.alerts_morning,
            key="tg_pref_morning",
        )
        eod = st.checkbox(
            "EOD track record (after close)",
            value=sub.alerts_eod,
            key="tg_pref_eod",
        )
        pulse = st.checkbox(
            "Market pulse (manual send only)",
            value=sub.alerts_pulse,
            key="tg_pref_pulse",
        )
        sip = st.checkbox(
            "SIP reminders (monthly)",
            value=sub.alerts_sip,
            key="tg_pref_sip",
        )
        if (
            morning != sub.alerts_morning
            or eod != sub.alerts_eod
            or pulse != sub.alerts_pulse
            or sip != sub.alerts_sip
        ):
            update_alert_preferences(
                token,
                alerts_morning=morning,
                alerts_eod=eod,
                alerts_pulse=pulse,
                alerts_sip=sip,
            )

        if st.button("Send test message", key="tg_test"):
            ok, msg = send_telegram(
                "Stock Analyzer test — your Telegram subscription is working.",
                chat_id=sub.chat_id,
            )
            if ok:
                st.success("Test sent.")
            else:
                st.error(msg)

        if st.button("Unsubscribe", key="tg_unsubscribe"):
            unsubscribe_token(token)
            st.session_state.pop("tg_subscribe_token", None)
            _send_bot_unsub_notice(sub.chat_id)
            st.rerun()

        total = len(list_active_subscribers())
        if total > 1:
            st.caption(f"{total} active subscribers on this bot.")
        return

    st.markdown("**Step 2 — Subscribe your Telegram**")
    st.caption(
        "Important: use the button below — do **not** search for the bot manually, "
        "or the link code will not attach."
    )

    link = subscribe_deep_link(token, bot_user)
    if link:
        st.link_button("Open in Telegram", link, type="primary", use_container_width=True)
        with st.expander("Troubleshooting link"):
            st.code(link, language=None)
            st.caption("If the button fails on desktop, paste this URL in your browser.")
    elif bot_user is None:
        masked = f"{bot_token()[:8]}…" if bot_token() else ""
        st.warning(
            f"Could not reach Telegram API for token `{masked}`. "
            "Re-save the token in the expander above."
        )
        with st.expander("Update bot token"):
            _render_bot_setup()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Verify subscription", key="tg_verify", use_container_width=True):
            with st.spinner("Checking Telegram (up to ~8s)…"):
                ok, msg = verify_subscription(token)
            if ok:
                st.success("Subscribed!")
                st.rerun()
            else:
                st.warning(msg)
    with col_b:
        if st.button("Get new link", key="tg_new_link", use_container_width=True):
            from analyzer.telegram_subscriptions import clear_client_subscribe_token

            clear_client_subscribe_token()
            st.session_state.pop("tg_subscribe_token", None)
            get_or_create_subscribe_token(force_new=True)
            st.rerun()

    st.caption("Send /stop in the bot chat to unsubscribe anytime.")


def _send_bot_unsub_notice(chat_id: str) -> None:
    try:
        send_telegram("You unsubscribed from Stock Analyzer in the app.", chat_id=chat_id)
    except Exception:
        pass
