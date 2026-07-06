"""Shared NSE India HTTP session (singleton, retry, circuit breaker, rate limit)."""

from __future__ import annotations

import json
import re
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.nseindia.com/",
    "Origin": "https://www.nseindia.com",
}

_WARM_URLS = (
    "https://www.nseindia.com/",
    "https://www.nseindia.com/market-data/live-equity-market",
    "https://www.nseindia.com/option-chain",
)

_SESSION: requests.Session | None = None
_SESSION_CREATED: float = 0.0
_SESSION_TTL = 300
_LAST_REQUEST: float = 0.0
_MIN_INTERVAL = 0.4
_CIRCUIT_OPEN_UNTIL: float = 0.0
_CIRCUIT_DURATION = 600  # 10 min pause after repeated failures
_RECENT_ERRORS: list[str] = []
_ERROR_SEEN: set[str] = set()


class NSEError(Exception):
    """NSE API request failed after retries."""


class NSECircuitOpen(NSEError):
    """NSE temporarily disabled after failures — use Yahoo fallback."""


def is_nse_available() -> bool:
    return time.time() >= _CIRCUIT_OPEN_UNTIL


def nse_status_message() -> str | None:
    if is_nse_available():
        return None
    remaining = max(0, int(_CIRCUIT_OPEN_UNTIL - time.time()))
    return (
        f"NSE data paused for {remaining // 60}m {remaining % 60}s "
        "(network/rate-limit). App uses Yahoo Finance until retry."
    )


def _trip_circuit(reason: str) -> None:
    global _CIRCUIT_OPEN_UNTIL
    _CIRCUIT_OPEN_UNTIL = time.time() + _CIRCUIT_DURATION
    _invalidate_session()
    record_nse_error(reason, trip=True)


def _invalidate_session() -> None:
    global _SESSION, _SESSION_CREATED
    _SESSION = None
    _SESSION_CREATED = 0.0


def _normalize_error(msg: str) -> str:
    """Collapse repetitive per-symbol errors into one line."""
    if "quote-equity" in msg and "HTTP 403" in msg:
        return "NSE equity quotes blocked (HTTP 403) — rate limit; using Yahoo"
    if "quote-equity" in msg and "RemoteDisconnected" in msg:
        return "NSE closed connection on equity quotes — using Yahoo"
    if "NameResolutionError" in msg or "nodename nor servname" in msg:
        return "Cannot reach nseindia.com (DNS/network) — check internet/VPN"
    if "cookie warm-up failed" in msg.lower():
        return "NSE cookie warm-up failed — site unreachable or blocked"
    if "Expecting value" in msg or "JSONDecodeError" in msg:
        return "NSE API returned unreadable response (encoding/block)"
    if "option-chain" in msg:
        return "NSE option chain unavailable — try again or check network"
    if "fiidii" in msg.lower():
        return "NSE FII/DII feed unavailable — macro uses other sources"
    if "delivery/volume" in msg or "historical-or-options" in msg:
        return ""  # deprecated path — fallback handles silently
    if "quote-equity" in msg and "HTTP 404" in msg:
        return "NSE equity quote unavailable — using Yahoo"
    m = re.search(r"NSE [^:]+: HTTP (\d+)", msg)
    if m:
        return f"NSE API HTTP {m.group(1)}"
    return msg[:120]


def record_nse_error(msg: str, trip: bool = False, silent: bool = False) -> None:
    key = _normalize_error(msg)
    if silent or not key:
        return
    if key in _ERROR_SEEN:
        return
    _ERROR_SEEN.add(key)
    _RECENT_ERRORS.append(key)
    if len(_RECENT_ERRORS) > 6:
        _RECENT_ERRORS.pop(0)
    if trip or "DNS" in key or "unreachable" in key or "network" in key:
        pass  # circuit set by caller


def get_recent_nse_errors() -> list[str]:
    status = nse_status_message()
    if status:
        return [status]
    return list(_RECENT_ERRORS)


def clear_nse_errors() -> None:
    _RECENT_ERRORS.clear()
    _ERROR_SEEN.clear()


def reset_nse_circuit() -> None:
    """Clear errors and reopen NSE after circuit-breaker pause."""
    global _CIRCUIT_OPEN_UNTIL
    _CIRCUIT_OPEN_UNTIL = 0.0
    clear_nse_errors()
    _invalidate_session()


def _throttle() -> None:
    global _LAST_REQUEST
    now = time.time()
    wait = _MIN_INTERVAL - (now - _LAST_REQUEST)
    if wait > 0:
        time.sleep(wait)
    _LAST_REQUEST = time.time()


def _new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(_NSE_HEADERS)
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def _warm_session(session: requests.Session) -> None:
    """Load NSE cookies; HTML pages may return 403 but still set cookies."""
    for url in _WARM_URLS:
        try:
            r = session.get(url, timeout=15)
            if r.status_code >= 500:
                raise requests.HTTPError(f"warm-up {url}: HTTP {r.status_code}")
        except requests.exceptions.RequestException:
            raise
        time.sleep(0.15)

    # Validate session with a lightweight API (works even when HTML pages 403).
    probe = session.get(
        "https://www.nseindia.com/api/marketStatus",
        timeout=15,
        headers={"Referer": "https://www.nseindia.com/"},
    )
    if probe.status_code >= 500:
        raise requests.HTTPError(f"warm-up probe: HTTP {probe.status_code}")


def nse_session(force_refresh: bool = False) -> requests.Session:
    """Return a warmed NSE session (reused for 5 minutes)."""
    if not is_nse_available():
        raise NSECircuitOpen(nse_status_message() or "NSE circuit open")

    global _SESSION, _SESSION_CREATED
    now = time.time()
    if _SESSION is not None and not force_refresh and now - _SESSION_CREATED < _SESSION_TTL:
        return _SESSION

    session = _new_session()
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            _warm_session(session)
            _SESSION = session
            _SESSION_CREATED = now
            return session
        except Exception as exc:
            last_exc = exc
            time.sleep(0.5 * (attempt + 1))

    msg = str(last_exc) if last_exc else "unknown"
    norm = _normalize_error(f"NSE cookie warm-up failed: {msg}")
    record_nse_error(f"NSE cookie warm-up failed: {msg}")
    if "DNS" in norm or "network" in norm or "unreachable" in norm:
        _trip_circuit(norm)
    raise NSEError("NSE session unavailable") from last_exc


def nse_get(
    session: requests.Session | None,
    path: str,
    timeout: int = 15,
) -> requests.Response:
    if not is_nse_available():
        raise NSECircuitOpen(nse_status_message() or "NSE circuit open")
    _throttle()
    url = path if path.startswith("http") else f"https://www.nseindia.com/api/{path.lstrip('/')}"
    sess = session or nse_session()
    return sess.get(url, timeout=timeout)


def _parse_json_response(resp: requests.Response, path: str) -> dict | list | None:
    """Parse NSE JSON; handle empty HTML or undecoded compressed bodies."""
    text = (resp.text or "").strip()
    if not text:
        record_nse_error(f"NSE {path}: empty response")
        return None
    if text[0] not in "{[":
        record_nse_error(f"NSE {path}: non-JSON body (HTTP {resp.status_code})")
        return None
    try:
        return resp.json()
    except json.JSONDecodeError as exc:
        record_nse_error(f"NSE {path}: {exc}")
        return None


def _optional_nse_path(path: str) -> bool:
    """Endpoints that may 404 when NSE deprecates them — no user-facing banner."""
    needles = (
        "historical-or-options",
        "historicalOR/delivery/volume",
        "historical/cm/equity",
        "historicalOR/foDerivatives",
    )
    return any(n in path for n in needles)


def nse_fetch_text(path: str, timeout: int = 20) -> str | None:
    """Fetch NSE CSV/text response (historical reports)."""
    if not is_nse_available():
        return None

    for attempt in range(2):
        try:
            sess = nse_session(force_refresh=attempt > 0)
            resp = nse_get(sess, path, timeout=timeout)
            if resp.status_code == 200 and (resp.text or "").strip():
                return resp.text
            if resp.status_code in (401, 403, 429):
                silent = "quote-equity" in path and resp.status_code == 403
                record_nse_error(f"NSE {path}: HTTP {resp.status_code}", silent=silent)
                if attempt == 0:
                    _invalidate_session()
                    continue
                return None
            if resp.status_code == 404:
                record_nse_error(
                    f"NSE {path}: HTTP 404",
                    silent=_optional_nse_path(path),
                )
                return None
            record_nse_error(f"NSE {path}: HTTP {resp.status_code}")
        except NSECircuitOpen:
            return None
        except NSEError:
            return None
        except Exception as exc:
            record_nse_error(f"NSE {path}: {exc}")
            if attempt > 0:
                return None
            _invalidate_session()
    return None


def nse_fetch_json(path: str, timeout: int = 20) -> dict | list | None:
    """Fetch NSE JSON with session reuse, throttle, and circuit breaker."""
    if not is_nse_available():
        return None

    for attempt in range(2):
        try:
            sess = nse_session(force_refresh=attempt > 0)
            resp = nse_get(sess, path, timeout=timeout)
            if resp.status_code == 200:
                payload = _parse_json_response(resp, path)
                if payload is not None:
                    return payload
                if attempt == 0:
                    _invalidate_session()
                    continue
                return None
            if resp.status_code in (401, 403, 429):
                silent = "quote-equity" in path and resp.status_code == 403
                record_nse_error(f"NSE {path}: HTTP {resp.status_code}", silent=silent)
                if attempt == 0:
                    _invalidate_session()
                    continue
                if "quote-equity" in path:
                    return None
                _trip_circuit(f"NSE API HTTP {resp.status_code}")
                return None
            if resp.status_code == 404:
                record_nse_error(
                    f"NSE {path}: HTTP 404",
                    silent=_optional_nse_path(path),
                )
                return None
            record_nse_error(f"NSE {path}: HTTP {resp.status_code}")
        except NSECircuitOpen:
            return None
        except NSEError:
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as exc:
            err = _normalize_error(str(exc))
            record_nse_error(str(exc))
            if "DNS" in err or "network" in err or "unreachable" in err:
                _trip_circuit(err)
            return None
        except Exception as exc:
            record_nse_error(f"NSE {path}: {exc}")
            if attempt > 0:
                return None
            _invalidate_session()
    return None
