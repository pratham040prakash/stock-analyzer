"""Zerodha Kite OAuth redirect handling."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import streamlit as st

from analyzer.zerodha import (
    exchange_request_token,
    load_env_credentials,
    save_access_token_to_env,
)
from ui.broker.bootstrap import reset_broker_bootstrap
from ui.broker.oauth_log import fn_trace, mask_oauth_url, oauth_log, oauth_log_exception, startup_trace
from ui.components.kite_connect import clear_kite_status_caches

_CHECKSUM_HELP = (
    "API Secret does not match your API Key. "
    "Open Settings → Broker → Advanced to reconfigure, then sign in again."
)


def _query_param(name: str) -> str:
    """Read a query param from st.query_params."""
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
    return ""


def _query_param_from_context_url(name: str) -> str:
    """Fallback: parse query string from st.context.url when query_params is empty."""
    try:
        url = str(getattr(st.context, "url", "") or "")
        if not url or "?" not in url:
            return ""
        values = parse_qs(urlparse(url).query).get(name) or []
        return str(values[0]).strip() if values else ""
    except Exception as exc:
        oauth_log("context.url parse error", f"{name}: {exc}")
    return ""


def _mask_token(token: str) -> str:
    token = token.strip()
    if not token:
        return ""
    if len(token) <= 8:
        return "(short)"
    return f"{token[:4]}…{token[-4:]}"


def get_request_token() -> str:
    """Resolve request_token from query_params or context URL."""
    qp_token = _query_param("request_token")
    ctx_token = _query_param_from_context_url("request_token")
    fn_trace(
        "get_request_token",
        "PROBE",
        f"query_params={_mask_token(qp_token) or 'empty'} "
        f"context.url={_mask_token(ctx_token) or 'empty'}",
    )
    if qp_token:
        oauth_log("Token source", "st.query_params")
        return qp_token
    if ctx_token:
        oauth_log("Token source", "st.context.url")
        return ctx_token
    return ""


def has_kite_oauth_callback() -> bool:
    """True when Zerodha redirected back with a request_token in the URL."""
    return bool(get_request_token())


def _checksum_error_message(exc: Exception) -> str:
    msg = str(exc).lower()
    if "checksum" in msg:
        return _CHECKSUM_HELP
    if "token" in msg and "expired" in msg:
        return "Login link expired. Click Sign In and complete login within 2 minutes."
    return "Unable to complete Zerodha sign in. Please try again."


def _clear_oauth_query_params() -> None:
    """Remove OAuth callback params so refresh does not reprocess."""
    startup_trace(8, "_clear_oauth_query_params")
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


def handle_kite_redirect(*, quiet: bool = False) -> bool:
    """
    Auto-exchange request_token when Zerodha redirects back to Streamlit.
    Returns True if a new token was saved this run.
    """
    print("HANDLE_KITE_REDIRECT ENTERED")
    fn_trace("handle_kite_redirect", "ENTER", f"quiet={quiet}")
    startup_trace(4, "handle_kite_redirect.enter")

    request_token = get_request_token()
    if not request_token:
        fn_trace("handle_kite_redirect", "EXIT", "return=False reason=no_request_token")
        startup_trace(4, "handle_kite_redirect.skip", "no request_token")
        return False

    oauth_log("Callback detected")
    oauth_log("Request token found", _mask_token(request_token))

    failed_key = f"kite_failed_token_{request_token}"
    if st.session_state.get("kite_token_exchanged") == request_token:
        oauth_log("Already exchanged", "skipping duplicate processing")
        _clear_oauth_query_params()
        fn_trace("handle_kite_redirect", "EXIT", "return=False reason=already_exchanged")
        startup_trace(4, "handle_kite_redirect.skip", "already exchanged")
        return False
    if st.session_state.get(failed_key):
        oauth_log("Skipped", "this request_token previously failed")
        _clear_oauth_query_params()
        fn_trace("handle_kite_redirect", "EXIT", "return=False reason=previously_failed")
        startup_trace(4, "handle_kite_redirect.skip", "previously failed")
        return False

    startup_trace(5, "load_env_credentials")
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
        fn_trace("handle_kite_redirect", "EXIT", "return=False reason=missing_credentials")
        startup_trace(4, "handle_kite_redirect.blocked", "missing API credentials")
        return False

    try:
        oauth_log("Exchanging request token")
        startup_trace(6, "exchange_request_token")
        access_token = exchange_request_token(
            creds["api_key"], creds["api_secret"], request_token
        )
        oauth_log("Access token received", _mask_token(access_token))

        startup_trace(7, "save_access_token_to_env")
        save_access_token_to_env(access_token)
        oauth_log("Token saved", "persisted to .env and process environment")

        st.session_state["kite_token_exchanged"] = request_token
        st.session_state["kite_access_token"] = access_token
        from analyzer.zerodha import hydrate_kite_access_token

        startup_trace(8, "hydrate_kite_access_token")
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
        fn_trace("handle_kite_redirect", "RETURN", "value=True")
        startup_trace(4, "handle_kite_redirect.done", "success")
        return True
    except Exception as exc:
        st.session_state[failed_key] = True
        fn_trace("handle_kite_redirect", "EXCEPTION", f"{type(exc).__name__}: {exc}")
        oauth_log_exception("Exchange failed", exc)
        detail = _checksum_error_message(exc)
        if quiet:
            st.session_state["_broker_toast"] = detail
        else:
            st.error(f"Login failed: {detail}")
        fn_trace("handle_kite_redirect", "RETURN", "value=False")
        startup_trace(4, "handle_kite_redirect.done", "failed")
        return False


def process_oauth_callback_if_present() -> None:
    """
    Section 9 gate — run before nav init, broker wizard, or startup skip flags.
    Exchanges request_token, bootstraps broker, strips URL, then reruns.
    """
    fn_trace("process_oauth_callback_if_present", "ENTER")
    startup_trace(2, "process_oauth_callback_if_present")

    try:
        context_url = str(getattr(st.context, "url", "") or "")
    except Exception:
        context_url = ""
    print("----------------------------")
    print("APP START")
    print("----------------------------")
    oauth_log(
        "Early OAuth probe",
        f"context.url={mask_oauth_url(context_url)}",
    )

    request_token = get_request_token()
    if not request_token:
        fn_trace("process_oauth_callback_if_present", "EXIT", "no callback")
        return

    print("CALLING HANDLE_KITE_REDIRECT")
    oauth_log("Early OAuth callback", _mask_token(request_token))
    oauth_ok = False
    try:
        oauth_ok = handle_kite_redirect(quiet=True)
    except Exception as exc:
        fn_trace("process_oauth_callback_if_present", "EXCEPTION", f"{type(exc).__name__}: {exc}")
        oauth_log_exception("Early OAuth handle_kite_redirect failed", exc)
        st.session_state["_broker_toast"] = "Unable to complete Zerodha sign in. Please try again."

    _clear_oauth_query_params()

    from analyzer.zerodha import hydrate_kite_access_token
    from ui.broker.bootstrap import broker_bootstrap

    hydrate_kite_access_token()
    if oauth_ok:
        reset_broker_bootstrap()
    try:
        broker_bootstrap(force_sync=True)
        oauth_log("Broker bootstrap completed", "after early OAuth callback")
    except Exception as exc:
        fn_trace("process_oauth_callback_if_present", "EXCEPTION", f"broker_bootstrap: {exc}")
        oauth_log_exception("broker_bootstrap failed", exc)

    return_tab = st.session_state.pop("_broker_return_tab", None) or "My Portfolio"
    if oauth_ok:
        st.session_state["nav_tab"] = return_tab

    st.session_state["_oauth_early_processed"] = True
    st.session_state["_broker_startup_done"] = True
    fn_trace(
        "process_oauth_callback_if_present",
        "EXIT",
        f"oauth_ok={oauth_ok} nav_tab={return_tab} → st.rerun()",
    )
    startup_trace(2, "process_oauth_callback_if_present.rerun", "strip OAuth params")
    st.rerun()
