"""Broker bootstrap — verify session, sync holdings/positions/funds before UI render."""

from __future__ import annotations

from analyzer.kite_status import clear_kite_probe_cache, kite_connection_status
from analyzer.portfolio_live import hydrate_portfolio_from_kite, sync_holdings_from_kite
from analyzer.portfolio_store import portfolio_profile_key, save_portfolio
from analyzer.zerodha import (
    fetch_kite_margins,
    fetch_kite_profile,
    get_kite_client,
    hydrate_kite_access_token,
    load_env_credentials,
)
from ui.broker.state import BrokerSnapshot, load_broker_snapshot, now_ist_label, save_broker_snapshot


def is_broker_configured() -> bool:
    creds = load_env_credentials()
    return bool(creds.get("api_key") and creds.get("api_secret"))


def _is_network_error(message: str) -> bool:
    msg = message.lower()
    needles = (
        "connection",
        "network",
        "timeout",
        "unreachable",
        "name or service",
        "failed to establish",
        "temporarily unavailable",
    )
    return any(n in msg for n in needles)


def _open_positions_count() -> int:
    kite = get_kite_client()
    if kite is None:
        return 0
    try:
        positions = kite.positions()
        count = 0
        for bucket in ("net", "day"):
            for row in positions.get(bucket) or []:
                if float(row.get("quantity") or 0) != 0:
                    count += 1
        return count
    except Exception:
        return 0


def _portfolio_metrics_from_import(imp) -> tuple[float, float]:
    value = 0.0
    pnl = 0.0
    if not imp or not getattr(imp, "holdings", None):
        return value, pnl
    for h in imp.holdings:
        if h.quantity <= 0:
            continue
        ltp = h.last_price or h.average_price or 0.0
        value += float(ltp) * float(h.quantity)
        if h.pnl is not None:
            pnl += float(h.pnl)
    return value, pnl


def _map_connection_level(level: str) -> str:
    if level == "ok":
        return "connected"
    if level == "limited":
        return "limited"
    if level == "expired":
        return "expired"
    if level == "no_token":
        return "disconnected"
    if level == "missing":
        return "not_configured"
    return "disconnected"


def broker_bootstrap(*, force_sync: bool = False) -> BrokerSnapshot:
    """
    Verify Zerodha session and sync broker data once per app session.
    Returns a BrokerSnapshot; never raises to the UI layer.
    """
    from ui.broker.oauth_log import fn_trace

    fn_trace("broker_bootstrap", "ENTER", f"force_sync={force_sync}")
    try:
        import streamlit as st
    except Exception:
        st = None  # type: ignore

    session_key = "_broker_bootstrap_done"
    if st is not None and st.session_state.get(session_key) and not force_sync:
        cached = st.session_state.get("broker_snapshot")
        if cached:
            snap = BrokerSnapshot.from_dict(cached)
            fn_trace("broker_bootstrap", "RETURN", f"cached state={snap.state}")
            return snap

    try:
        hydrate_kite_access_token()
        prior = load_broker_snapshot()

        if not is_broker_configured():
            snap = BrokerSnapshot(state="not_configured")
            _persist_snapshot(snap, st)
            fn_trace("broker_bootstrap", "RETURN", "state=not_configured")
            return snap

        status = kite_connection_status(probe=True)
        level = status.get("level", "missing")
        market = status.get("market_data", "")
        state = _map_connection_level(level)

        snap = BrokerSnapshot(
            state=state,
            broker_label="Zerodha",
            user_id=prior.user_id,
            user_name=prior.user_name,
            last_sync_at=prior.last_sync_at,
            last_sync_status=prior.last_sync_status,
            holdings_count=prior.holdings_count,
            positions_count=prior.positions_count,
            portfolio_value_inr=prior.portfolio_value_inr,
            today_unrealized_pnl_inr=prior.today_unrealized_pnl_inr,
            available_cash_inr=prior.available_cash_inr,
        )

        if state in ("disconnected", "expired", "not_configured"):
            if status.get("detail"):
                snap.error_message = _user_friendly_detail(status)
            _persist_snapshot(snap, st)
            fn_trace("broker_bootstrap", "RETURN", f"state={snap.state}")
            return snap

        profile = fetch_kite_profile()
        if profile:
            snap.user_id = str(profile.get("user_id") or snap.user_id)
            snap.user_name = str(profile.get("user_name") or snap.user_name)

        prof = portfolio_profile_key()
        sync_error = ""
        imp = None

        try:
            imp, sync_error = sync_holdings_from_kite()
            if imp and imp.holdings:
                save_portfolio(imp, profile=prof)
                if st is not None:
                    st.session_state["zd_import"] = imp
            elif not imp and not sync_error:
                imp, sync_error = hydrate_portfolio_from_kite(profile=prof)
                if imp and imp.holdings and st is not None:
                    st.session_state["zd_import"] = imp
        except Exception as exc:
            sync_error = str(exc)

        if sync_error and not imp:
            if _is_network_error(sync_error):
                snap.state = "offline"
                snap.error_message = "Internet unavailable. Retry when connection is restored."
            else:
                snap.state = "error"
                snap.error_message = (
                    "Unable to connect to Zerodha. Your most recently synced portfolio is available."
                )
            _persist_snapshot(snap, st, mark_done=True)
            fn_trace("broker_bootstrap", "RETURN", f"state={snap.state} sync_error")
            return snap

        if imp:
            value, pnl = _portfolio_metrics_from_import(imp)
            snap.holdings_count = sum(1 for h in imp.holdings if h.quantity > 0)
            snap.portfolio_value_inr = value
            snap.today_unrealized_pnl_inr = pnl

        snap.positions_count = _open_positions_count()

        margins = fetch_kite_margins()
        if margins:
            try:
                equity = margins.get("equity") or margins
                available = equity.get("available") or {}
                cash = available.get("cash") or available.get("live_balance")
                if cash is not None:
                    snap.available_cash_inr = float(cash)
            except (TypeError, ValueError):
                pass

        snap.last_sync_at = now_ist_label()
        snap.last_sync_status = "ok"
        snap.error_message = ""
        if state == "limited":
            snap.error_message = _user_friendly_detail(status)

        _persist_snapshot(snap, st, mark_done=True)
        fn_trace(
            "broker_bootstrap",
            "RETURN",
            f"state={snap.state} holdings={snap.holdings_count}",
        )
        return snap
    except Exception as exc:
        fn_trace("broker_bootstrap", "EXCEPTION", f"{type(exc).__name__}: {exc}")
        snap = BrokerSnapshot(state="error", error_message=str(exc)[:200])
        _persist_snapshot(snap, st)
        return snap


def _user_friendly_detail(status: dict) -> str:
    level = status.get("level", "")
    if level == "expired":
        return "Session expired. Reconnect to Zerodha."
    if level == "no_token":
        return "Broker not connected."
    detail = str(status.get("detail") or "")
    if "sidebar" in detail.lower():
        return detail.replace("sidebar → **Login with Zerodha**.", "Sign in to Zerodha.").replace(
            "Sidebar → **Login with Zerodha** again (~10 sec).", "Sign in to Zerodha."
        )
    return detail


def _persist_snapshot(snap: BrokerSnapshot, st, *, mark_done: bool = False) -> None:
    save_broker_snapshot(snap)
    if st is not None:
        st.session_state["broker_snapshot"] = snap.to_dict()
        if mark_done:
            st.session_state["_broker_bootstrap_done"] = True


def reset_broker_bootstrap() -> None:
    """Clear session bootstrap flag after OAuth or manual retry."""
    try:
        import streamlit as st

        st.session_state.pop("_broker_bootstrap_done", None)
        st.session_state.pop("_broker_startup_done", None)
        clear_kite_probe_cache()
    except Exception:
        clear_kite_probe_cache()
