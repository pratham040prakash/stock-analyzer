#!/usr/bin/env python3
"""Emit Alpha AI executive summary as JSON for apex-ui bridge."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from analyzer.alpha_ai_report import build_alpha_ai_report  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "symbol required"}))
        sys.exit(1)

    symbol = sys.argv[1].strip().upper()
    report = build_alpha_ai_report(symbol, market="india")

    payload = {
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

    print(json.dumps(payload))


if __name__ == "__main__":
    main()
