#!/usr/bin/env python3
"""Kite Connect login + full API health check.

Usage:
  python scripts/kite_auth.py login          # print login URL
  python scripts/kite_auth.py token <rt>     # exchange request_token → save .env
  python scripts/kite_auth.py check         # verify all Kite APIs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyzer.kite_health import check_kite_apis
from analyzer.zerodha import (
    exchange_request_token,
    get_kite_login_url,
    load_env_credentials,
    save_access_token_to_env,
)


def cmd_login() -> int:
    creds = load_env_credentials()
    if not creds["api_key"]:
        print("Set ZERODHA_API_KEY in .env first.", file=sys.stderr)
        return 1
    url = get_kite_login_url(creds["api_key"])
    print("\n1. Open this URL in your browser and log in with Zerodha:\n")
    print(f"   {url}\n")
    print("2. After redirect, copy request_token from the URL (?request_token=...)\n")
    print("3. Run:\n")
    print("   python scripts/kite_auth.py token YOUR_REQUEST_TOKEN\n")
    return 0


def cmd_token(request_token: str) -> int:
    creds = load_env_credentials()
    if not creds["api_key"] or not creds["api_secret"]:
        print("Set ZERODHA_API_KEY and ZERODHA_API_SECRET in .env", file=sys.stderr)
        return 1
    try:
        access = exchange_request_token(creds["api_key"], creds["api_secret"], request_token.strip())
        save_access_token_to_env(access)
        print("Access token saved to .env (valid until ~6 AM IST tomorrow).\n")
    except Exception as exc:
        print(f"Token exchange failed: {exc}", file=sys.stderr)
        return 1
    return cmd_check()


def cmd_check() -> int:
    result = check_kite_apis()
    print("\nKite API health check\n" + "=" * 40)
    for check in result["checks"]:
        mark = "OK" if check["ok"] else "FAIL"
        print(f"  [{mark}] {check['name']}: {check['detail']}")
    for err in result["errors"]:
        if not any(err.startswith(c["name"]) for c in result["checks"] if not c["ok"]):
            print(f"  [FAIL] {err}")
    print()
    if result["ok"]:
        print("All Kite APIs working. Restart Streamlit: streamlit run app.py\n")
        return 0
    print("Fix: python scripts/kite_auth.py login  (then token <request_token>)\n")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Kite Connect auth and API check")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("login", help="Print Zerodha login URL")
    p_token = sub.add_parser("token", help="Exchange request_token and save to .env")
    p_token.add_argument("request_token", help="From redirect URL after login")
    sub.add_parser("check", help="Verify profile, holdings, LTP, historical, instruments")

    args = parser.parse_args()
    if args.command == "login":
        return cmd_login()
    if args.command == "token":
        return cmd_token(args.request_token)
    if args.command == "check":
        return cmd_check()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
