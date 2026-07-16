"""Zerodha Kite OAuth redirect handling."""

from __future__ import annotations

import streamlit as st

from analyzer.zerodha import (
    exchange_request_token,
    load_env_credentials,
    save_access_token_to_env,
)
from ui.broker.bootstrap import reset_broker_bootstrap
from ui.broker.oauth_log import oauth_log, oauth_log_exception
from ui.components.kite_connect import clear_kite_status_caches

_CHECKSUM_HELP = (
    "API Secret does not match your API Key. "
    "Open Settings → Broker → Advanced to reconfigure, then sign in again."
)
_OAUTH_RERUN_COUNT_KEY = "_oauth_rerun_count"
_OAUTH_MAX_RERUNS = 3


def _query_param(name: str) -> str:
    """Read a query param — Streamlit may expose values as str or list."""
    try:
        qp = st.query_params
        if name in qp:
            val = qp[name]
        else:
            val = qp.get(name)
        if isinstance(val, list):
            val = val[0] if val else ""
        return str(val or "").strip()
    except Exception as exc:
        oauth_log("query_param error", f"{name}: {exc}")
    try:
        for key, val in dict(st.query_params).items():
            if key == name:
                if isinstance(val, list):
                    return str(val[0] if val else "").strip()
                return str(val or "").strip()
    except Exception:
        pass
    return ""


def has_kite_oauth_callback() -> bool:
    """True when Zerodha redirected back with a request_token in the URL."""
    return bool(_query_param("request_token"))


def _mask_token(token: str) -> str:
    token = token.strip()
    if len(token) <= 8:
        return "(short)"
    return f"{token[:4]}…{token[-4:]}"


def _checksum_error_message(exc: Exception) -> str:
    msg = str(exc).lower()
    if "checksum" in msg:
        return _CHECKSUM_HELP
    if "token" in msg and "expired" in msg:
        return "Login link expired. Click Sign In and complete login within 2 minutes."
    return "Unable to complete Zerodha sign in. Please try again."


def _clear_oauth_query_params() -> None:
    """Remove OAuth callback params so refresh does not reprocess."""
    try:
        for key in ("request_token", "action", "type", "status"):
            if key in st.query_params:
                del st.query_params[key]
        oauth_log("URL params cleared", "request_token action type status")
    except Exception as exc:
        oauth_log("URL cleanup partial", str(exc))
        try:
            st.query_params.clear()
            oauth_log("URL params cleared", "full clear fallback")
        except Exception as exc2:
            oauth_log("URL cleanup failed", str(exc2))


def process_oauth_callback_early() -> None:
    """
    Run at the top of main() immediately after set_page_config.
    Must execute before ensure_broker_configured() or any early return.
    Schedules st.rerun() so the browser URL drops OAuth query params.
    """
    request_token = _query_param("request_token")
    if not request_token:
        st.session_state.pop(_OAUTH_RERUN_COUNT_KEY, None)
        return

    rerun_count = int(st.session_state.get(_OAUTH_RERUN_COUNT_KEY, 0))
    oauth_log(
        "Early callback",
        f"main() entry rerun_count={rerun_count} token={_mask_token(request_token)}",
    )

    if rerun_count >= _OAUTH_MAX_RERUNS:
        oauth_log("Rerun guard", "max reruns reached — continuing render")
        return

    handle_kite_redirect(quiet=True)
    _clear_oauth_query_params()
    st.session_state[_OAUTH_RERUN_COUNT_KEY] = rerun_count + 1
    oauth_log("Rerun scheduled", f"attempt {rerun_count + 1} to sync browser URL")
    st.rerun()


def handle_kite_redirect(*, quiet: bool = False) -> bool:
    """
    Auto-exchange request_token when Zerodha redirects back to Streamlit.
    Call on every app run when request_token is present (including after startup).
    Returns True if a new token was saved this run.
    """
    if not has_kite_oauth_callback():
        return False

    oauth_log("Callback detected")
    request_token = _query_param("request_token")
    oauth_log("Request token found", _mask_token(request_token))

    failed_key = f"kite_failed_token_{request_token}"
    if st.session_state.get("kite_token_exchanged") == request_token:
        oauth_log("Already exchanged", "skipping duplicate processing")
        _clear_oauth_query_params()
        return False
    if st.session_state.get(failed_key):
        oauth_log("Skipped", "this request_token previously failed")
        _clear_oauth_query_params()
        return False

    creds = load_env_credentials()
    if not creds["api_key"] or not creds["api_secret"]:
        oauth_log("Blocked", "API key or secret missing from configuration")
        if not quiet:
            st.error(
                "Zerodha returned a login token, but broker setup is incomplete. "
                "Complete the one-time setup wizard first."
            )
        else:
            st.session_state["_broker_toast"] = (
                "Broker setup incomplete. Complete the one-time setup wizard first."
            )
        return False

    try:
        oauth_log("Exchanging request token")
        access_token = exchange_request_token(
            creds["api_key"], creds["api_secret"], request_token
        )
        oauth_log("Access token received", _mask_token(access_token))

        save_access_token_to_env(access_token)
        oauth_log("Token saved", "persisted to .env and process environment")

        st.session_state["kite_token_exchanged"] = request_token
        st.session_state["kite_access_token"] = access_token
        from analyzer.zerodha import hydrate_kite_access_token

        hydrate_kite_access_token()
        clear_kite_status_caches()
        reset_broker_bootstrap()

        oauth_log("Portfolio sync started", "post_kite_login_sync")
        from analyzer.portfolio_live import post_kite_login_sync
        from analyzer.portfolio_store import portfolio_profile_key

        sync = post_kite_login_sync(profile=portfolio_profile_key())
        if sync.get("holdings"):
            st.session_state["zd_import"] = sync["holdings"]
        oauth_log(
            "Portfolio sync completed",
            f"holdings={sync.get('holdings_count', 0)} user={sync.get('user_id') or sync.get('user_name') or 'unknown'}",
        )
        if sync.get("error"):
            oauth_log("Portfolio sync warning", str(sync.get("error")))

        name = sync.get("user_name") or sync.get("user_id") or "your account"
        n = sync.get("holdings_count", 0)
        if sync.get("error") and not n:
            message = (
                f"Signed in as {name}, but holdings could not be loaded. "
                "Your last synced portfolio is still available."
            )
            if quiet:
                st.session_state["_broker_toast"] = message
            else:
                st.warning(message)
        elif n:
            message = f"Zerodha connected · {n} holdings synced"
            if quiet:
                st.session_state["_broker_toast"] = message
            else:
                st.success(f"Zerodha connected as **{name}** — fetched **{n} holdings** from Kite.")
        else:
            message = f"Zerodha connected as {name}."
            if quiet:
                st.session_state["_broker_toast"] = message
            else:
                st.success(message)
        oauth_log("OAuth complete", "authentication succeeded")
        return True
    except Exception as exc:
        st.session_state[failed_key] = True
        oauth_log_exception("Exchange failed", exc)
        detail = _checksum_error_message(exc)
        if quiet:
            st.session_state["_broker_toast"] = detail
        else:
            st.error(f"Login failed: {detail}")
        return False
