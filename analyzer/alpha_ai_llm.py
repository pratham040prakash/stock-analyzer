"""Optional LLM narrative — facts from report only, no invented numbers."""

from __future__ import annotations

import json
import os

import requests

from analyzer.alpha_ai_report import AlphaAIReport


def llm_enabled() -> bool:
    flag = os.getenv("ALPHA_AI_LLM", "").strip().lower()
    return flag in ("1", "true", "yes", "on") and bool(os.getenv("OPENAI_API_KEY", "").strip())


def _facts_payload(report: AlphaAIReport) -> dict:
    return {
        "symbol": report.symbol,
        "name": report.name,
        "score": report.overall_score,
        "recommendation": report.recommendation,
        "buy_decision": report.buy_decision,
        "confidence_pct": report.confidence_pct,
        "risk_level": report.risk_level,
        "valuation_verdict": report.valuation_verdict,
        "red_flags": report.red_flags[:8],
        "data_gaps": report.data_gaps[:8],
        "sector": report.sector,
        "scenarios": [
            {"name": s.name, "target": s.target_price, "prob": s.probability_pct}
            for s in report.scenarios
        ],
    }


def synthesize_narrative(report: AlphaAIReport) -> str | None:
    """
    Optional OpenAI synthesis. Set ALPHA_AI_LLM=1 and OPENAI_API_KEY in .env.
  Returns None if disabled or on failure.
    """
    if not llm_enabled():
        return None

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("ALPHA_AI_LLM_MODEL", "gpt-4o-mini")
    facts = json.dumps(_facts_payload(report), indent=2)

    prompt = (
        "You are Alpha AI. Write a 150-word executive narrative using ONLY the JSON facts below. "
        "Cite no numbers not in the JSON. Label opinions as opinion. "
        "Mention data gaps if present. No hype.\n\n"
        f"FACTS:\n{facts}"
    )

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 300,
            },
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
