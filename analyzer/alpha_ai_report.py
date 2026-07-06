"""Alpha AI — institutional-style equity research report (evidence-based, no fabrication)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from analyzer.advisor import generate_advice
from analyzer.combined import analyze_combined
from analyzer.data import fetch_benchmark, fetch_stock_data
from analyzer.earnings_calendar import fetch_corporate_event
from analyzer.fundamentals import extract_raw_fundamentals
from analyzer.global_impact import build_india_impact_report
from analyzer.indicators import add_indicators
from analyzer.market_pulse import india_market_pulse, overall_market_verdict
from analyzer.markets import is_india_market
from analyzer.relative_strength import compute_relative_strength

IST = ZoneInfo("Asia/Kolkata")

RATINGS = ("Excellent", "Good", "Average", "Poor", "N/A")


@dataclass
class MetricRating:
    name: str
    value: str
    rating: str
    note: str = ""


@dataclass
class RiskItem:
    category: str
    level: str  # Low | Medium | High
    detail: str


@dataclass
class ScenarioCase:
    name: str
    description: str
    probability_pct: float | None


@dataclass
class AlphaAIReport:
    symbol: str
    name: str
    sector: str
    industry: str
    price: float | None
    currency: str
    generated_at: str
    data_gaps: list[str] = field(default_factory=list)
    business_overview: str = ""
    financial_metrics: list[MetricRating] = field(default_factory=list)
    valuation_verdict: str = ""
    valuation_detail: str = ""
    technical_summary: str = ""
    swing_setup: str = ""
    long_term_setup: str = ""
    technical_risk: str = ""
    growth_notes: str = ""
    moat_score: float | None = None
    moat_detail: str = ""
    risks: list[RiskItem] = field(default_factory=list)
    macro_summary: str = ""
    news_summary: str = ""
    probabilities: dict[str, float] = field(default_factory=dict)
    prediction_confidence: float | None = None
    entry_strategy: str = ""
    portfolio_impact: str = ""
    suggested_weight_pct: float | None = None
    scenarios: list[ScenarioCase] = field(default_factory=list)
    cagr_notes: str = ""
    red_flags: list[str] = field(default_factory=list)
    quality_scores: dict[str, float] = field(default_factory=dict)
    overall_score: int = 0
    investment_grade_stars: int = 0
    verdict: str = "Hold"
    horizons: dict[str, str] = field(default_factory=dict)
    action_plan: str = ""
    score_breakdown: str = ""


def _rating_from_signal(score: float | None, *, higher_is_better: bool = True) -> str:
    if score is None:
        return "N/A"
    if higher_is_better:
        if score >= 0.6:
            return "Excellent"
        if score >= 0.25:
            return "Good"
        if score >= -0.1:
            return "Average"
        return "Poor"
    if score <= 0.3:
        return "Excellent"
    if score <= 0.8:
        return "Good"
    if score <= 1.5:
        return "Average"
    return "Poor"


def _valuation_label(pe: float | None, fund_score: float) -> tuple[str, str]:
    if pe is None:
        return "Fairly Valued", "Insufficient P/E — use peer comparison manually."
    if fund_score >= 25 and pe < 18:
        return "Undervalued", f"Strong fundamentals with P/E {pe:.1f} — potential quality at reasonable price."
    if fund_score <= -15 and pe > 30:
        return "Overvalued", f"Weak fundamentals vs P/E {pe:.1f} — premium not supported."
    if pe > 35:
        return "Overvalued", f"P/E {pe:.1f} — elevated; growth must deliver."
    if pe < 14 and fund_score > 0:
        return "Undervalued", f"P/E {pe:.1f} with positive quality scores."
    return "Fairly Valued", f"P/E {pe:.1f} — aligned with current quality/technical mix."


def _moat_estimate(raw: dict, fund_score: float, info: dict) -> tuple[float | None, str]:
    """Heuristic moat 0–10 — ESTIMATE only."""
    parts: list[str] = []
    score = 5.0
    roe = raw.get("roe")
    if roe is not None:
        if roe >= 0.18:
            score += 1.5
            parts.append("High ROE supports capital efficiency moat.")
        elif roe < 0.08:
            score -= 1.0
    margin = raw.get("profit_margin")
    if margin is not None:
        if margin >= 0.15:
            score += 1.0
            parts.append("Healthy margins suggest pricing power.")
        elif margin < 0.05:
            score -= 0.5
    de = raw.get("debt_to_equity")
    if de is not None and de > 1.5:
        score -= 1.0
        parts.append("High leverage weakens balance-sheet moat.")
    if fund_score >= 30:
        score += 1.0
    elif fund_score <= -20:
        score -= 1.5
    sector = (info.get("sector") or "").lower()
    if any(x in sector for x in ("software", "financial", "consumer", "pharma")):
        score += 0.5
    score = max(0.0, min(10.0, score))
    return round(score, 1), " ".join(parts) or "Heuristic moat from margins, ROE, leverage, sector."


def _probabilities_from_scores(combined: float, tech: float, fund: float) -> dict[str, float]:
    """Map scores to action probabilities — ESTIMATE."""
    base = {
        "Strong Buy": 5.0,
        "Buy": 15.0,
        "Hold": 45.0,
        "Reduce": 20.0,
        "Sell": 15.0,
    }
    shift = combined / 8.0
    base["Strong Buy"] = max(0, base["Strong Buy"] + shift * 2)
    base["Buy"] = max(0, base["Buy"] + shift * 3)
    base["Hold"] = max(10, base["Hold"] - shift * 2)
    base["Reduce"] = max(0, base["Reduce"] - shift)
    base["Sell"] = max(0, base["Sell"] - shift)
    if tech > 20 and fund < 0:
        base["Hold"] += 10
        base["Buy"] -= 5
    total = sum(base.values()) or 1
    return {k: round(v / total * 100, 1) for k, v in base.items()}


def _stars_from_score(score: int) -> int:
    if score >= 85:
        return 5
    if score >= 70:
        return 4
    if score >= 55:
        return 3
    if score >= 40:
        return 2
    if score >= 25:
        return 1
    return 0


def _weight_suggestion(overall: int, verdict: str) -> float | None:
    if "Sell" in verdict or verdict == "Avoid":
        return 0.0
    if overall >= 80:
        return 8.0
    if overall >= 65:
        return 5.0
    if overall >= 50:
        return 3.0
    if overall >= 40:
        return 1.0
    return None


def build_alpha_ai_report(
    ticker: str,
    *,
    market: str = "india",
    period: str = "2y",
) -> AlphaAIReport:
    """Assemble 18-step institutional report from available data sources."""
    gaps: list[str] = []
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    currency = "₹" if is_india_market(market) else "$"

    df, info = fetch_stock_data(ticker, period=period, market=market)
    df = add_indicators(df)
    combined = analyze_combined(df, info["symbol"], yf_info=info)
    tech = combined.technical
    fund = combined.fundamental
    raw = extract_raw_fundamentals(info)

    rs = None
    market_pulse = None
    if is_india_market(market) and not info["symbol"].startswith("^"):
        try:
            market_pulse = india_market_pulse(period)
        except Exception as exc:
            gaps.append(f"Market pulse: {exc}")
        try:
            bench_df, _ = fetch_benchmark(market, period)
            rs = compute_relative_strength(df, bench_df, info["symbol"])
        except Exception as exc:
            gaps.append(f"Relative strength: {exc}")

    advice = generate_advice(combined, info, rs=rs, market_pulse=market_pulse, df=df)

    name = info.get("name", ticker)
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    price = info.get("nse_last_price") or tech.current_price
    summary = info.get("longBusinessSummary") or info.get("description") or ""
    if not summary:
        gaps.append("Business description not available from data feed.")
        summary = f"**{name}** operates in **{sector}** / **{industry}**. Pull annual report for moat detail."

    business = (
        f"**Business model (FACT/feed):** {summary[:1200]}{'…' if len(summary) > 1200 else ''}\n\n"
        f"**Industry:** {industry} · **Sector:** {sector}\n\n"
        f"**Competitive view (ASSUMPTION):** Validate market share and advantages from latest AR/concall — "
        "not available in automated feed."
    )

    fin_rows: list[MetricRating] = []
    for label, key, fmt, higher in (
        ("Revenue Growth", "revenue_growth", lambda v: f"{v*100:+.1f}%" if v is not None else "N/A", True),
        ("Earnings Growth", "earnings_growth", lambda v: f"{v*100:+.1f}%" if v is not None else "N/A", True),
        ("Operating Margin", "operating_margin", lambda v: f"{v*100:.1f}%" if v is not None else "N/A", True),
        ("Net Margin", "profit_margin", lambda v: f"{v*100:.1f}%" if v is not None else "N/A", True),
        ("ROE", "roe", lambda v: f"{v*100:.1f}%" if v is not None else "N/A", True),
        ("Debt/Equity", "debt_to_equity", lambda v: f"{v:.2f}" if v is not None else "N/A", False),
    ):
        val = raw.get(key)
        m = next((x for x in fund.metrics if label.split()[0] in x.name), None)
        rating = _rating_from_signal(m.score if m else None, higher_is_better=higher)
        fin_rows.append(MetricRating(label, fmt(val), rating, m.detail if m else ""))

    inst = info.get("heldPercentInstitutions")
    promo = info.get("heldPercentInsiders")
    if inst is not None:
        fin_rows.append(MetricRating("Institutional Holding", f"{inst*100:.1f}%", "Good" if inst > 0.2 else "Average"))
    else:
        gaps.append("Institutional holding % unavailable.")
    if promo is not None:
        fin_rows.append(MetricRating("Promoter Holding", f"{promo*100:.1f}%", "Good" if promo > 0.4 else "Average"))
    else:
        gaps.append("Promoter holding % unavailable.")

    val_verdict, val_detail = _valuation_label(raw.get("pe_trailing"), fund.composite_score)
    val_lines = [
        f"**P/E:** {raw.get('pe_trailing') or 'N/A'}",
        f"**Forward P/E:** {raw.get('pe_forward') or 'N/A'}",
        f"**PEG:** {raw.get('peg') or 'N/A'}",
        f"**P/B:** {raw.get('price_to_book') or 'N/A'}",
        f"**Verdict:** {val_verdict} — {val_detail}",
        "_DCF/EV-EBITDA: not computed — insufficient line-item feed (ESTIMATE via multiples only)._",
    ]

    row = df.iloc[-1]
    tech_lines = [
        f"**Trend:** {tech.recommendation} (score {tech.composite_score:+.0f})",
        f"**Support / Resistance:** {tech.support:,.0f} / {tech.resistance:,.0f}" if tech.support else "",
        f"**RSI:** {row.get('RSI_14', 'N/A')}",
        f"**Stop / Target (model):** {advice.stop_loss} / {advice.target}",
        f"**R:R:** {advice.risk_reward}",
    ]
    if rs and rs.periods:
        p6 = next((p for p in rs.periods if "6" in p.label), rs.periods[-1])
        tech_lines.append(
            f"**vs Nifty:** {rs.verdict} — 6m alpha {p6.alpha_pct:+.1f}%"
        )

    swing = f"**Swing (ASSUMPTION):** {advice.final_action} — {advice.entry_zone}. Horizon: weeks."
    long_setup = (
        f"**Long-term (ASSUMPTION):** Fund score {fund.composite_score:+.0f}. "
        f"Suitable for 3–5y only if moat + ROE confirmed in AR."
    )
    tech_risk = "Low" if tech.confidence == "high" else "Medium" if tech.confidence == "medium" else "High"

    growth_notes = (
        "**3y/5y/10y growth (ESTIMATE):** Derived from trailing revenue/earnings growth feeds only — "
        "not a management guidance model.\n\n"
        f"- Trailing revenue growth: {raw.get('revenue_growth')}"
        f"\n- Trailing earnings growth: {raw.get('earnings_growth')}"
        "\n- Re-rate with quarterly results before sizing positions."
    )

    moat, moat_detail = _moat_estimate(raw, fund.composite_score, info)

    risks: list[RiskItem] = []
    for r in advice.risks[:6]:
        risks.append(RiskItem("Company", "Medium", r))
    if raw.get("debt_to_equity") and raw["debt_to_equity"] > 1.2:
        risks.append(RiskItem("Debt", "High", f"D/E {raw['debt_to_equity']:.2f}"))
    else:
        risks.append(RiskItem("Debt", "Low", "Leverage acceptable or data N/A"))
    risks.append(RiskItem("Market", "Medium", "Broad market drawdown risk always present"))

    macro = "Macro data unavailable."
    if is_india_market(market):
        try:
            impact = build_india_impact_report()
            macro = (
                f"**Nifty bias (model):** {impact.predicted_nifty_bias} · "
                f"**Global tone:** {impact.narrative[:200]}"
            )
            if market_pulse:
                macro += f"\n**India indices:** {overall_market_verdict(market_pulse)}"
        except Exception as exc:
            gaps.append(f"Macro: {exc}")

    news = "**Facts:** "
    try:
        nse_sym = info.get("nse_symbol") or ticker.replace(".NS", "")
        ev = fetch_corporate_event(nse_sym, market=market)
        if ev:
            news += f"{ev.event_type} — {ev.detail} ({ev.risk_band})."
        else:
            news += "No flagged corporate event in next 2 weeks."
    except Exception:
        news += "Earnings calendar unavailable."
    news += "\n\n**Noise:** Ignore social media tips; verify against exchange filings."

    probs = _probabilities_from_scores(combined.combined_score, tech.composite_score, fund.composite_score)
    pred_conf = min(85.0, max(35.0, 50 + combined.combined_score * 0.8))

    entry = (
        f"**Ideal buy range:** {advice.entry_zone}\n"
        f"**Stop loss:** {advice.stop_loss}\n"
        f"**Targets:** {advice.target}\n"
        f"**Risk/Reward:** {advice.risk_reward}\n"
        f"**Position hint:** {advice.position_hint}"
    )

    weight = _weight_suggestion(0, advice.final_action)  # placeholder, updated after overall
    portfolio = (
        f"**Diversification:** Adds **{sector}** exposure — check current sector concentration.\n"
        f"**Suggested max weight (ESTIMATE):** See overall score below."
    )

    scenarios = [
        ScenarioCase("Bull", "Earnings beat + sector tailwind + multiple expansion", 25.0),
        ScenarioCase("Base", "Steady execution in line with trend", 50.0),
        ScenarioCase("Bear", "Margin compression or market de-rating", 25.0),
    ]

    cagr = (
        "**CAGR (ESTIMATE):** Not forecast from DCF. Use your SIP goal model — "
        "stock CAGR depends on starting valuation and reinvestment. "
        "Do not extrapolate trailing growth linearly."
    )

    red_flags: list[str] = []
    if raw.get("profit_margin") is not None and raw["profit_margin"] < 0:
        red_flags.append("Negative profit margin — loss-making operations.")
    if raw.get("debt_to_equity") and raw["debt_to_equity"] > 2:
        red_flags.append("Very high debt/equity.")
    if tech.composite_score < -25 and fund.composite_score < -15:
        red_flags.append("Both technical and fundamental scores weak.")
    if not red_flags:
        red_flags.append("No automated red flags — review governance manually.")

    q_business = max(0, min(100, 50 + fund.composite_score * 0.4))
    q_fin = max(0, min(100, 50 + fund.composite_score * 0.5))
    q_growth = max(0, min(100, 50 + (raw.get("revenue_growth") or 0) * 100))
    q_mgmt = 50.0  # no feed
    gaps.append("Management quality not scored — no automated feed.")
    q_val = max(0, min(100, 60 - (raw.get("pe_trailing") or 25)))
    q_tech = max(0, min(100, 50 + tech.composite_score * 0.5))
    q_risk = max(0, min(100, 70 - len(red_flags) * 15))

    quality = {
        "Business Quality": q_business,
        "Financial Strength": q_fin,
        "Growth": q_growth,
        "Management": q_mgmt,
        "Valuation": q_val,
        "Technical Setup": q_tech,
        "Risk": q_risk,
    }
    overall = int(
        q_business * 0.2 + q_fin * 0.2 + q_growth * 0.15 + q_val * 0.15
        + q_tech * 0.15 + q_risk * 0.1 + q_mgmt * 0.05
    )
    weight = _weight_suggestion(overall, advice.final_action)
    portfolio += f"\n**Suggested allocation cap:** {weight}%" if weight is not None else "\n**Allocation:** Avoid new adds."

    verdict_map = {
        "STRONG BUY": "Strong Buy",
        "BUY": "Buy",
        "ACCUMULATE": "Buy",
        "HOLD": "Hold",
        "REDUCE": "Reduce",
        "SELL": "Sell",
        "STRONG SELL": "Sell",
        "AVOID": "Avoid",
    }
    verdict = verdict_map.get(advice.final_action, "Hold")
    stars = _stars_from_score(overall)

    horizons = {
        "6 Months": advice.final_action if tech.confidence != "low" else "Hold / wait",
        "1 Year": verdict,
        "3 Years": "Buy" if fund.composite_score > 15 else "Hold",
        "5 Years": "Buy" if fund.composite_score > 20 and moat and moat >= 6 else "Hold",
        "10 Years": "Buy" if moat and moat >= 7 and fund.composite_score > 10 else "Accumulate selectively",
    }

    action = (
        f"**Should you buy now?** {advice.final_action} — {advice.summary}\n\n"
        f"**Conviction:** {advice.conviction} · **Horizon:** {advice.time_horizon}\n\n"
        "Challenge biases: don't add solely because it's a Nifty name or recent winner."
    )

    breakdown = (
        f"Business {q_business:.0f}×0.20 + Financial {q_fin:.0f}×0.20 + Growth {q_growth:.0f}×0.15 + "
        f"Valuation {q_val:.0f}×0.15 + Technical {q_tech:.0f}×0.15 + Risk {q_risk:.0f}×0.10 + "
        f"Mgmt {q_mgmt:.0f}×0.05"
    )

    return AlphaAIReport(
        symbol=info["symbol"],
        name=name,
        sector=sector,
        industry=industry,
        price=float(price) if price else None,
        currency=currency,
        generated_at=now,
        data_gaps=gaps,
        business_overview=business,
        financial_metrics=fin_rows,
        valuation_verdict=val_verdict,
        valuation_detail="\n".join(val_lines),
        technical_summary="\n".join(x for x in tech_lines if x),
        swing_setup=swing,
        long_term_setup=long_setup,
        technical_risk=tech_risk,
        growth_notes=growth_notes,
        moat_score=moat,
        moat_detail=moat_detail,
        risks=risks,
        macro_summary=macro,
        news_summary=news,
        probabilities=probs,
        prediction_confidence=round(pred_conf, 1),
        entry_strategy=entry,
        portfolio_impact=portfolio,
        suggested_weight_pct=weight,
        scenarios=scenarios,
        cagr_notes=cagr,
        red_flags=red_flags,
        quality_scores=quality,
        overall_score=overall,
        investment_grade_stars=stars,
        verdict=verdict,
        horizons=horizons,
        action_plan=action,
        score_breakdown=breakdown,
    )
