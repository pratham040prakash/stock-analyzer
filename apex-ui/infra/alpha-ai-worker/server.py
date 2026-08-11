#!/usr/bin/env python3
"""Minimal HTTP service exposing Alpha AI summary JSON for apex-ui."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from analyzer.alpha_ai_report import build_alpha_ai_report  # noqa: E402


def build_payload(symbol: str) -> dict:
    report = build_alpha_ai_report(symbol.strip().upper(), market="india")
    return {
        "symbol": report.symbol,
        "name": report.name,
        "recommendation": report.recommendation,
        "overall_score": report.overall_score,
        "investment_grade_stars": report.investment_grade_stars,
        "confidence_pct": report.confidence_pct,
        "risk_level": report.risk_level,
        "buy_decision": report.buy_decision,
        "buy_decision_why": report.buy_decision_why,
        "business_overview": report.business_overview,
        "valuation_verdict": report.valuation_verdict,
        "technical_summary": report.technical_summary,
        "red_flags": report.red_flags[:5],
        "data_gaps": report.data_gaps[:8],
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._json(200, {"status": "ok"})
            return

        if parsed.path != "/summary":
            self._json(404, {"error": "not found"})
            return

        symbol = (parse_qs(parsed.query).get("symbol") or [""])[0].strip().upper()

        if not symbol:
            self._json(400, {"error": "symbol required"})
            return

        try:
            payload = build_payload(symbol)
            self._json(200, payload)
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"error": str(exc)})

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Alpha AI worker listening on :{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
