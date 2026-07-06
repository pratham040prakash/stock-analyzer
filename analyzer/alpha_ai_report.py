"""Alpha AI v3.0 — institutional equity research (evidence-based, no fabrication)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from analyzer.advisor import generate_advice
from analyzer.asset_class import classify_asset
from analyzer.combined import analyze_combined
from analyzer.data import fetch_benchmark, fetch_stock_data
from analyzer.dcf_model import build_dcf, format_dcf_markdown
from analyzer.etf_analyzer import build_etf_profile, format_etf_markdown
from analyzer.india_enrichment import enrich_india_fundamentals, format_enriched_markdown
from analyzer.macro_cache import format_macro_summary, get_daily_india_macro
from analyzer.news_feed import fetch_stock_news, format_news_markdown
from analyzer.peer_comparison import build_peer_comparison, format_peer_markdown
from analyzer.alpha_ai_prompts import detect_report_mode, mode_framing
from analyzer.alpha_monte_carlo import monte_carlo_scenarios
from analyzer.alpha_red_flags import detect_red_flags
from analyzer.alpha_portfolio_mode import analyze_portfolio_impact, format_portfolio_impact_block
from analyzer.fundamentals import extract_raw_fundamentals
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
    target_price: str = ""
    expected_cagr: str = ""


@dataclass
class SnapshotCategory:
    name: str
    score: float  # 0–10
    stars: int = 0


@dataclass
class EntryStrategy:
    ideal_buy_zone: str
    aggressive_buy_zone: str
    support_levels: list[str]
    resistance_levels: list[str]
    target_1: str
    target_2: str
    target_3: str
    stop_loss: str
    risk_reward: str
    sip_entry: str
    lump_sum_entry: str


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
    # Executive summary
    recommendation: str = "Hold"
    overall_score: int = 0
    investment_grade_stars: int = 0
    confidence_pct: float | None = None
    risk_level: str = "Medium"
    investment_horizon: str = "3 Years"
    expected_cagr: dict[str, str] = field(default_factory=dict)
    # v3 sections
    snapshot: list[SnapshotCategory] = field(default_factory=list)
    buy_decision: str = "WAIT"
    buy_decision_why: str = ""
    entry: EntryStrategy | None = None
    business_overview: str = ""
    financial_metrics: list[MetricRating] = field(default_factory=list)
    financial_analysis: str = ""
    valuation_verdict: str = ""
    valuation_detail: str = ""
    technical_summary: str = ""
    technical_analysis: str = ""
    swing_setup: str = ""
    long_term_setup: str = ""
    technical_risk: str = ""
    growth_notes: str = ""
    news_summary: str = ""
    news_sentiment: str = ""
    risks: list[RiskItem] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    moat_score: float | None = None
    moat_detail: str = ""
    moat_dimensions: list[tuple[str, float]] = field(default_factory=list)
    macro_summary: str = ""
    scenarios: list[ScenarioCase] = field(default_factory=list)
    portfolio_impact: str = ""
    suggested_weight_pct: float | None = None
    portfolio_allocation_options: list[float] = field(default_factory=list)
    checklist_scores: dict[str, float] = field(default_factory=dict)
    probabilities: dict[str, float] = field(default_factory=dict)
    prediction_confidence: float | None = None
    cagr_notes: str = ""
    quality_scores: dict[str, float] = field(default_factory=dict)
    verdict: str = "Hold"
    horizons: dict[str, str] = field(default_factory=dict)
    final_verdict_detail: str = ""
    action_plan: str = ""
    score_breakdown: str = ""
    entry_strategy: str = ""  # legacy markdown block
    report_mode: str = "mid_cap"
    section_sources: dict[str, list[str]] = field(default_factory=dict)
    llm_narrative: str | None = None


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


def _score_100_to_10(score: float) -> float:
    return round(max(0.0, min(10.0, score / 10.0)), 1)


def _stars_from_10(score: float) -> int:
    return max(0, min(5, int(round(score / 2.0))))


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


def _moat_dimensions(moat: float | None, raw: dict, fund_score: float) -> list[tuple[str, float]]:
    base = moat or 5.0
    margin = raw.get("profit_margin") or 0
    roe = raw.get("roe") or 0
    return [
        ("Brand", round(min(10, base + 0.5), 1)),
        ("Technology", round(min(10, base * 0.9 + fund_score * 0.02), 1)),
        ("Network Effect", round(max(2, base * 0.7), 1)),
        ("Switching Costs", round(min(10, base + margin * 10), 1)),
        ("Scale", round(min(10, base + (roe * 5)), 1)),
        ("Distribution", round(base, 1)),
        ("Pricing Power", round(min(10, 5 + margin * 20), 1)),
        ("Management", 5.0),
        ("Innovation", round(min(10, base + fund_score * 0.03), 1)),
    ]


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


def _buy_decision(
    action: str,
    tech_score: float,
    fund_score: float,
    conviction: str = "medium",
) -> tuple[str, str]:
    action = action.upper()
    conv = conviction.lower()
    if action in ("SELL", "STRONG SELL", "AVOID", "REDUCE"):
        return "NO", f"Model action is **{action}** — preserve capital; do not add."
    if action == "STRONG BUY" and conv == "high" and fund_score > 0:
        return "YES", "**STRONG BUY** with high conviction — aligned thesis; size within risk budget."
    if action == "STRONG BUY" and tech_score > 8 and fund_score > -5:
        return "YES", "**STRONG BUY** — technical and fundamental scores support entry."
    if action == "BUY" and conv in ("high", "medium") and tech_score > 5 and fund_score > 5:
        return "YES", f"**{action}** — fundamentals and timing acceptable for a starter position."
    if action in ("STRONG BUY", "BUY", "ACCUMULATE"):
        return "WAIT", f"**{action}** thesis but timing mixed — stagger via SIP or wait for ideal zone."
    return "WAIT", "**HOLD** — no clear edge to add; monitor triggers."


def _confidence_pct(combined_score: float, gaps: list[str], conviction: str) -> float:
    base = min(85.0, max(35.0, 50 + combined_score * 0.8))
    base -= min(25.0, len(gaps) * 3.0)
    if conviction.lower() == "high":
        base += 4.0
    elif conviction.lower() == "low":
        base -= 6.0
    return round(max(22.0, min(88.0, base)), 1)


def _overall_risk_level(tech_risk: str, red_flags: list[str], risks: list[RiskItem]) -> str:
    high = sum(1 for r in risks if r.level == "High") + len(red_flags)
    if tech_risk == "High" or high >= 3:
        return "High"
    if tech_risk == "Medium" or high >= 1:
        return "Medium"
    return "Low"


def _fmt_price(val: float | None, currency: str) -> str:
    if val is None:
        return "N/A"
    return f"{currency}{val:,.2f}"


def _build_entry_strategy(
    advice,
    tech,
    price: float | None,
    currency: str,
) -> EntryStrategy:
    support = tech.support
    resistance = tech.resistance
    cur = price or tech.current_price
    supports: list[str] = []
    resistances: list[str] = []
    if support:
        supports.append(_fmt_price(support, currency))
        if cur:
            supports.append(_fmt_price(support * 0.97, currency))
    if resistance:
        resistances.append(_fmt_price(resistance, currency))
        if cur:
            resistances.append(_fmt_price(resistance * 1.03, currency))
    t1 = advice.target
    t2 = _fmt_price(resistance * 1.08, currency) if resistance else "N/A"
    t3 = _fmt_price(resistance * 1.15, currency) if resistance else "N/A"
    aggressive = (
        _fmt_price(cur * 1.01, currency) if cur else advice.entry_zone
    )
    sip = "Suitable — stagger over 3–6 months if valuation not cheap (ESTIMATE)."
    lump = "Lump sum only if ideal buy zone hit and conviction high (ESTIMATE)."
    if advice.final_action in ("SELL", "AVOID", "REDUCE"):
        sip = "Not suitable for new capital."
        lump = "Avoid new lump sum."
    return EntryStrategy(
        ideal_buy_zone=advice.entry_zone,
        aggressive_buy_zone=aggressive,
        support_levels=supports or ["See chart"],
        resistance_levels=resistances or ["See chart"],
        target_1=t1,
        target_2=t2,
        target_3=t3,
        stop_loss=advice.stop_loss,
        risk_reward=advice.risk_reward,
        sip_entry=sip,
        lump_sum_entry=lump,
    )


def _technical_deep_dive(_df: pd.DataFrame, row: pd.Series, tech, advice, currency: str) -> str:
    sma50 = row.get("SMA_50")
    sma200 = row.get("SMA_200")
    cross = "N/A"
    if pd.notna(sma50) and pd.notna(sma200):
        cross = "Golden Cross (bullish)" if sma50 > sma200 else "Death Cross (bearish)"
    macd = row.get("MACD_12_26_9")
    macd_sig = row.get("MACDs_12_26_9")
    macd_note = "N/A"
    if pd.notna(macd) and pd.notna(macd_sig):
        macd_note = "Bullish" if macd > macd_sig else "Bearish"
    adx = row.get("ADX_14")
    adx_note = f"{adx:.1f}" if pd.notna(adx) else "N/A"
    bb_upper = row.get("BBU_20_2.0")
    bb_lower = row.get("BBL_20_2.0")
    atr = row.get("ATR_14")
    vol = row.get("Volume")
    vol_sma = row.get("VOL_SMA_20")
    vol_note = "Above avg" if pd.notna(vol) and pd.notna(vol_sma) and vol > vol_sma else "Normal/low"
    lines = [
        f"**Trend:** {tech.recommendation} (score {tech.composite_score:+.0f})",
        f"**MAs:** SMA50 {_fmt_price(float(sma50), currency) if pd.notna(sma50) else 'N/A'} · "
        f"SMA200 {_fmt_price(float(sma200), currency) if pd.notna(sma200) else 'N/A'} · **{cross}**",
        f"**RSI (14):** {row.get('RSI_14', 'N/A'):.1f}" if pd.notna(row.get("RSI_14")) else "**RSI:** N/A",
        f"**MACD:** {macd_note}",
        f"**ADX:** {adx_note}",
        f"**Volume / OBV:** {vol_note} · OBV trend from feed",
        f"**ATR (14):** {_fmt_price(float(atr), currency) if pd.notna(atr) else 'N/A'}",
        f"**Bollinger:** Upper {_fmt_price(float(bb_upper), currency) if pd.notna(bb_upper) else 'N/A'} · "
        f"Lower {_fmt_price(float(bb_lower), currency) if pd.notna(bb_lower) else 'N/A'}",
        f"**Support / Resistance:** {_fmt_price(tech.support, currency)} / {_fmt_price(tech.resistance, currency)}",
        f"**Swing opportunity (ESTIMATE):** {advice.final_action} — {advice.entry_zone}",
        f"**Long-term trend:** {'Up' if tech.composite_score > 10 else 'Mixed' if tech.composite_score > -10 else 'Down'}",
        f"**Momentum score (0–10 ESTIMATE):** {_score_100_to_10(50 + tech.composite_score * 0.5):.1f}",
    ]
    return "\n\n".join(lines)


def _scenario_prices(
    price: float | None,
    support: float | None,
    resistance: float | None,
    currency: str,
    raw: dict,
) -> list[ScenarioCase]:
    cur = price or 100.0
    sup = support or cur * 0.9
    res = resistance or cur * 1.1
    eg = raw.get("earnings_growth")
    cagr_bull = f"{eg * 100 * 1.2:+.0f}% (ESTIMATE)" if eg is not None else "N/A — no earnings feed"
    cagr_base = f"{eg * 100:+.0f}% (ESTIMATE)" if eg is not None else "N/A"
    cagr_bear = "Negative / de-rating risk (ESTIMATE)"
    return [
        ScenarioCase(
            "Bull",
            "Earnings beat + sector tailwind + multiple expansion",
            25.0,
            _fmt_price(res * 1.15, currency),
            cagr_bull,
        ),
        ScenarioCase(
            "Base",
            "Steady execution in line with trend",
            50.0,
            _fmt_price(res, currency),
            cagr_base,
        ),
        ScenarioCase(
            "Bear",
            "Margin compression or market de-rating",
            25.0,
            _fmt_price(sup * 0.92, currency),
            cagr_bear,
        ),
    ]


def _expected_cagr_dict(raw: dict) -> dict[str, str]:
    rev = raw.get("revenue_growth")
    earn = raw.get("earnings_growth")
    if rev is None and earn is None:
        return {
            "3 Years": "N/A — insufficient feed",
            "5 Years": "N/A — insufficient feed",
            "10 Years": "N/A — insufficient feed",
        }
    base = earn if earn is not None else rev
    return {
        "3 Years": f"{base * 100:+.1f}% trailing (ESTIMATE, not forecast)",
        "5 Years": "Re-rate with AR — do not extrapolate linearly",
        "10 Years": "Depends on moat + reinvestment — verify manually",
    }


def build_alpha_ai_report(
    ticker: str,
    *,
    market: str = "india",
    period: str = "2y",
    portfolio_mode: bool = False,
) -> AlphaAIReport:
    """Assemble Alpha AI v3.0 report from available data sources."""
    gaps: list[str] = []
    section_sources: dict[str, list[str]] = {
        "price_technical": ["Yahoo Finance", "internal model"],
        "fundamentals": ["Yahoo Finance"],
    }
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    currency = "₹" if is_india_market(market) else "$"

    df, info = fetch_stock_data(ticker, period=period, market=market)
    asset = classify_asset(info["symbol"], info)
    is_etf = asset.asset_class == "etf"
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
    report_mode = detect_report_mode(info["symbol"], info, float(price) if price else None, market)
    framing = mode_framing(report_mode)
    enriched_obj = None
    summary = info.get("longBusinessSummary") or info.get("description") or ""
    if not summary:
        gaps.append("Business description not available from data feed.")
        summary = f"{name} operates in {sector} / {industry}. Pull annual report for moat detail."

    business = (
        f"{framing['business']}\n\n"
        f"**Business model (FACT/feed):** {summary[:1200]}{'…' if len(summary) > 1200 else ''}\n\n"
        f"**Revenue sources / products (ASSUMPTION):** Validate segment mix in latest AR.\n\n"
        f"**Customers & industry position (ASSUMPTION):** {industry} · {sector} — confirm share from filings.\n\n"
        f"**Competitive advantage (ESTIMATE):** See moat section; not from automated feed.\n\n"
        f"**Growth drivers & opportunities (OPINION):** Tie to sector cycle + company execution; verify in concall."
    )

    fin_rows: list[MetricRating] = []
    for label, key, fmt, higher in (
        ("Revenue Growth", "revenue_growth", lambda v: f"{v*100:+.1f}%" if v is not None else "N/A", True),
        ("EPS / Earnings Growth", "earnings_growth", lambda v: f"{v*100:+.1f}%" if v is not None else "N/A", True),
        ("Operating Margin", "operating_margin", lambda v: f"{v*100:.1f}%" if v is not None else "N/A", True),
        ("Net Margin", "profit_margin", lambda v: f"{v*100:.1f}%" if v is not None else "N/A", True),
        ("ROE", "roe", lambda v: f"{v*100:.1f}%" if v is not None else "N/A", True),
        ("Debt/Equity", "debt_to_equity", lambda v: f"{v:.2f}" if v is not None else "N/A", False),
        ("P/B (Book)", "price_to_book", lambda v: f"{v:.2f}" if v is not None else "N/A", False),
        ("Free Cash Flow", "free_cashflow", lambda v: f"{v:,.0f}" if v is not None else "N/A", True),
        ("Book Value", "book_value", lambda v: f"{v:,.2f}" if v is not None else "N/A", True),
        ("Dividend Yield", "dividend_yield", lambda v: f"{v*100:.2f}%" if v is not None else "N/A", True),
    ):
        val = raw.get(key)
        m = next((x for x in fund.metrics if label.split()[0] in x.name), None)
        rating = _rating_from_signal(m.score if m else None, higher_is_better=higher)
        fin_rows.append(MetricRating(label, fmt(val), rating, m.detail if m else ""))

    inst = info.get("heldPercentInstitutions")
    promo = info.get("heldPercentInsiders")
    if inst is not None:
        fin_rows.append(MetricRating("FII / Institutional", f"{inst*100:.1f}%", "Good" if inst > 0.2 else "Average"))
    if promo is not None:
        fin_rows.append(MetricRating("Promoter Holding", f"{promo*100:.1f}%", "Good" if promo > 0.4 else "Average"))

    enriched_block = ""
    if is_india_market(market) and not is_etf:
        try:
            enriched_obj = enrich_india_fundamentals(info["symbol"], info)
            enriched_block = format_enriched_markdown(enriched_obj)
            gaps.extend(enriched_obj.gaps)
            section_sources["fundamentals"].extend(["NSE India", "Screener.in"])
            if enriched_obj.roce is not None:
                v = enriched_obj.roce * 100 if enriched_obj.roce <= 1 else enriched_obj.roce
                fin_rows.append(MetricRating("ROCE", f"{v:.1f}%", _rating_from_signal(0.5 if v >= 15 else 0)))
            if enriched_obj.current_ratio is not None:
                fin_rows.append(
                    MetricRating(
                        "Current Ratio",
                        f"{enriched_obj.current_ratio:.2f}",
                        "Good" if enriched_obj.current_ratio >= 1.2 else "Average",
                    )
                )
            if enriched_obj.interest_coverage is not None:
                fin_rows.append(
                    MetricRating(
                        "Interest Coverage",
                        f"{enriched_obj.interest_coverage:.1f}x",
                        "Good" if enriched_obj.interest_coverage >= 3 else "Average",
                    )
                )
            if enriched_obj.cash_conversion_pct is not None:
                fin_rows.append(
                    MetricRating(
                        "Cash Conversion",
                        f"{enriched_obj.cash_conversion_pct:.0f}%",
                        "Good" if enriched_obj.cash_conversion_pct >= 80 else "Average",
                    )
                )
            sh = enriched_obj.shareholding
            if sh and sh.fii_pct is not None:
                fin_rows.append(MetricRating("FII (NSE)", f"{sh.fii_pct:.1f}%", "Good" if sh.fii_pct > 15 else "Average"))
            if sh and sh.dii_pct is not None:
                fin_rows.append(MetricRating("DII (NSE)", f"{sh.dii_pct:.1f}%", "Average"))
        except Exception as exc:
            gaps.append(f"India enrichment: {exc}")
    elif inst is None:
        gaps.append("FII / institutional holding % unavailable.")
    if promo is None and not is_india_market(market):
        gaps.append("Insider holding % unavailable.")

    fin_analysis = (
        "**Strengths / weaknesses** from scored metrics above.\n\n"
        f"{enriched_block}\n\n"
        "_Cash flow quality: cross-check FCF vs net income in annual report._"
        if enriched_block
        else "**Strengths / weaknesses** from scored metrics above. "
        "Extended India metrics loaded when available.\n\n"
        "_Cash flow quality: cross-check FCF vs net income in annual report._"
    )

    val_verdict, val_detail = _valuation_label(raw.get("pe_trailing"), fund.composite_score)
    val_lines = [
        framing["valuation"],
        f"**P/E (trailing):** {raw.get('pe_trailing') or 'N/A'}",
        f"**Forward P/E:** {raw.get('pe_forward') or 'N/A'}",
        f"**PEG:** {raw.get('peg') or 'N/A'}",
        f"**P/B:** {raw.get('price_to_book') or 'N/A'}",
        f"**Verdict:** {val_verdict}",
        f"**Detail:** {val_detail}",
    ]

    etf_profile = build_etf_profile(info["symbol"], info) if is_etf else None
    if etf_profile:
        val_lines.append(format_etf_markdown(etf_profile))
        business = format_etf_markdown(etf_profile) + "\n\n" + business
    else:
        try:
            peer = build_peer_comparison(
                info["symbol"],
                sector,
                target_pe=raw.get("pe_trailing"),
                target_roe=raw.get("roe"),
            )
            val_lines.append(format_peer_markdown(peer))
        except Exception as exc:
            gaps.append(f"Peer comparison: {exc}")
        try:
            dcf = build_dcf(
                info["symbol"],
                free_cashflow=raw.get("free_cashflow"),
                shares_outstanding=info.get("shares_outstanding"),
                earnings_growth=raw.get("earnings_growth"),
                current_price=float(price) if price else None,
            )
            val_lines.append(format_dcf_markdown(dcf, currency))
        except Exception as exc:
            gaps.append(f"DCF: {exc}")

    val_lines.append("**Margin of safety (ESTIMATE):** Higher when undervalued + strong balance sheet.")

    row = df.iloc[-1]
    tech_summary = _technical_deep_dive(df, row, tech, advice, currency)
    if rs and rs.periods:
        p6 = next((p for p in rs.periods if "6" in p.label), rs.periods[-1])
        tech_summary += f"\n\n**vs Nifty (FACT):** {rs.verdict} — 6m alpha {p6.alpha_pct:+.1f}%"

    swing = f"Swing (ESTIMATE): {advice.final_action} — {advice.entry_zone}. Horizon: weeks."
    long_setup = (
        f"Long-term (ESTIMATE): Fund score {fund.composite_score:+.0f}. "
        "Suitable for 3–5y only if moat + ROE confirmed in AR."
    )
    tech_risk = "Low" if tech.confidence == "high" else "Medium" if tech.confidence == "medium" else "High"

    growth_notes = (
        "Trailing growth only (ESTIMATE) — not management guidance.\n\n"
        f"- Revenue: {raw.get('revenue_growth')}\n"
        f"- Earnings: {raw.get('earnings_growth')}\n"
        "- Re-rate after each quarterly result."
    )

    moat, moat_detail = _moat_estimate(raw, fund.composite_score, info)
    moat_detail = f"{framing['moat']}\n\n{moat_detail}"
    moat_dims = _moat_dimensions(moat, raw, fund.composite_score)

    risks: list[RiskItem] = []
    for r in advice.risks[:6]:
        risks.append(RiskItem("Execution", "Medium", r))
    if raw.get("debt_to_equity") and raw["debt_to_equity"] > 1.2:
        risks.append(RiskItem("Debt", "High", f"D/E {raw['debt_to_equity']:.2f}"))
    else:
        risks.append(RiskItem("Debt", "Low", "Leverage acceptable or data N/A"))
    risks.append(RiskItem("Competition", "Medium", "Sector competition — verify moat in AR"))
    risks.append(RiskItem("Market", "Medium", "Broad drawdown / macro shock risk"))
    risks.append(RiskItem("Regulation", "Low", "Flag manually for financials/telecom/pharma"))
    risks.append(RiskItem("Interest Rate", "Medium", "Rate-sensitive sectors may de-rate"))

    macro = "Macro data unavailable."
    if is_india_market(market):
        try:
            impact = get_daily_india_macro()
            macro = format_macro_summary(impact)
            if market_pulse:
                macro += f"\n**India indices:** {overall_market_verdict(market_pulse)}"
        except Exception as exc:
            gaps.append(f"Macro: {exc}")

    try:
        news_bundle = fetch_stock_news(info["symbol"], market=market)
        news_sentiment = format_news_markdown(news_bundle)
        section_sources["news"] = [news_bundle.data_source or "Yahoo/NSE"]
    except Exception as exc:
        gaps.append(f"News feed: {exc}")
        news_sentiment = "**News:** Feed unavailable — check NSE filings manually."
    news = news_sentiment

    probs = _probabilities_from_scores(combined.combined_score, tech.composite_score, fund.composite_score)
    pred_conf = _confidence_pct(combined.combined_score, gaps, advice.conviction)

    entry_obj = _build_entry_strategy(advice, tech, float(price) if price else None, currency)
    entry = (
        f"**Ideal buy zone:** {entry_obj.ideal_buy_zone}\n"
        f"**Aggressive zone:** {entry_obj.aggressive_buy_zone}\n"
        f"**Stop loss:** {entry_obj.stop_loss}\n"
        f"**Targets:** {entry_obj.target_1} / {entry_obj.target_2} / {entry_obj.target_3}\n"
        f"**Risk/Reward:** {entry_obj.risk_reward}\n"
        f"**SIP:** {entry_obj.sip_entry}\n"
        f"**Lump sum:** {entry_obj.lump_sum_entry}"
    )

    red_flags = detect_red_flags(
        raw,
        tech_score=tech.composite_score,
        fund_score=fund.composite_score,
        enriched=enriched_obj,
        promoter_pct=promo,
    )

    q_business = max(0, min(100, 50 + fund.composite_score * 0.4))
    q_fin = max(0, min(100, 50 + fund.composite_score * 0.5))
    q_growth = max(0, min(100, 50 + (raw.get("revenue_growth") or 0) * 100))
    q_profit = max(0, min(100, 50 + (raw.get("profit_margin") or 0) * 200))
    q_mgmt = 50.0
    gaps.append("Management quality & ESG not scored — no automated feed.")
    q_val = max(0, min(100, 60 - (raw.get("pe_trailing") or 25)))
    q_tech = max(0, min(100, 50 + tech.composite_score * 0.5))
    q_momentum = max(0, min(100, 50 + tech.composite_score * 0.4))
    q_risk = max(0, min(100, 70 - len(red_flags) * 12))
    q_moat = (moat or 5) * 10

    quality = {
        "Business Quality": q_business,
        "Financial Strength": q_fin,
        "Growth": q_growth,
        "Profitability": q_profit,
        "Valuation": q_val,
        "Technical Trend": q_tech,
        "Momentum": q_momentum,
        "Risk": q_risk,
        "Moat": q_moat,
        "Management": q_mgmt,
    }
    overall = int(
        q_business * 0.18 + q_fin * 0.18 + q_growth * 0.12 + q_profit * 0.08
        + q_val * 0.12 + q_tech * 0.12 + q_momentum * 0.05 + q_risk * 0.08
        + q_moat * 0.05 + q_mgmt * 0.02
    )
    weight = _weight_suggestion(overall, advice.final_action)
    alloc_opts = [x for x in (1.0, 3.0, 5.0, 10.0) if weight is None or x <= weight]
    if not alloc_opts and weight == 0:
        alloc_opts = [0.0]

    portfolio = (
        f"{framing['risk']}\n\n"
        f"**Sector exposure:** Adds **{sector}** — check concentration.\n"
        f"**Suggested max weight (ESTIMATE):** {weight}%" if weight is not None else "**Allocation:** Avoid new adds."
    )
    portfolio += "\n**Diversification:** Prefer ≤25% per sector; ≤10% per single name unless high conviction."

    if portfolio_mode:
        try:
            pia = analyze_portfolio_impact(info["symbol"], sector)
            portfolio += "\n\n" + format_portfolio_impact_block(pia)
            section_sources["portfolio"] = ["saved portfolio JSON", "internal model"]
        except Exception as exc:
            gaps.append(f"Portfolio mode: {exc}")

    mc_scenarios = monte_carlo_scenarios(
        df,
        float(price) if price else 0,
        currency,
        earnings_growth=raw.get("earnings_growth"),
    )
    scenarios = mc_scenarios if mc_scenarios else _scenario_prices(
        float(price) if price else None,
        tech.support,
        tech.resistance,
        currency,
        raw,
    )
    scenarios = [
        ScenarioCase(s.name, s.description, s.probability_pct, s.target_price, s.expected_cagr)
        for s in scenarios
    ]
    section_sources["scenarios"] = ["Monte Carlo (historical returns)", "internal model"]

    cagr_dict = _expected_cagr_dict(raw)
    cagr = (
        "**Expected CAGR (ESTIMATE, not guaranteed):**\n"
        + "\n".join(f"- **{k}:** {v}" for k, v in cagr_dict.items())
    )

    verdict_map = {
        "STRONG BUY": "Strong Buy",
        "BUY": "Buy",
        "ACCUMULATE": "Accumulate",
        "HOLD": "Hold",
        "REDUCE": "Reduce",
        "SELL": "Sell",
        "STRONG SELL": "Sell",
        "AVOID": "Avoid",
    }
    recommendation = verdict_map.get(advice.final_action, "Hold")
    if len(gaps) > 8:
        recommendation = "Insufficient Data"
        verdict = "Insufficient Data"
        gaps.append("Verdict capped — more than 8 data gaps; verify manually before investing.")
        buy = "WAIT"
        buy_why = "**Insufficient data** — too many missing fields for a confident equity verdict."
    else:
        verdict = recommendation
        buy, buy_why = _buy_decision(
            advice.final_action, tech.composite_score, fund.composite_score, advice.conviction
        )

    stars = _stars_from_score(overall)
    risk_level = _overall_risk_level(tech_risk, red_flags, risks)

    horizons = {
        "Swing": advice.final_action if tech.confidence != "low" else "Wait",
        "6 Months": recommendation if tech.confidence != "low" else "Hold / wait",
        "1 Year": recommendation,
        "3 Years": "Buy" if fund.composite_score > 15 else "Hold",
        "5 Years": "Buy" if fund.composite_score > 20 and moat and moat >= 6 else "Hold",
        "10 Years": "Buy" if moat and moat >= 7 and fund.composite_score > 10 else "Accumulate selectively",
    }
    investment_horizon = "3 Years" if fund.composite_score > 10 else "1 Year"

    snapshot = [
        SnapshotCategory("Business Quality", _score_100_to_10(q_business), _stars_from_10(_score_100_to_10(q_business))),
        SnapshotCategory("Financial Strength", _score_100_to_10(q_fin), _stars_from_10(_score_100_to_10(q_fin))),
        SnapshotCategory("Growth", _score_100_to_10(q_growth), _stars_from_10(_score_100_to_10(q_growth))),
        SnapshotCategory("Profitability", _score_100_to_10(q_profit), _stars_from_10(_score_100_to_10(q_profit))),
        SnapshotCategory("Valuation", _score_100_to_10(q_val), _stars_from_10(_score_100_to_10(q_val))),
        SnapshotCategory("Technical Trend", _score_100_to_10(q_tech), _stars_from_10(_score_100_to_10(q_tech))),
        SnapshotCategory("Momentum", _score_100_to_10(q_momentum), _stars_from_10(_score_100_to_10(q_momentum))),
        SnapshotCategory("Risk", _score_100_to_10(q_risk), _stars_from_10(_score_100_to_10(q_risk))),
        SnapshotCategory("Moat", moat or 5.0, _stars_from_10(moat or 5.0)),
        SnapshotCategory("Management", 5.0, 2),
        SnapshotCategory("ESG", 0.0, 0),
    ]

    checklist = {
        "Business Quality": q_business,
        "Financial Health": q_fin,
        "Growth": q_growth,
        "Profitability": q_profit,
        "Valuation": q_val,
        "Technical Strength": q_tech,
        "Momentum": q_momentum,
        "Management": q_mgmt,
        "Risk": q_risk,
        "Moat": q_moat,
        "Overall": float(overall),
    }

    action = (
        f"**Should you buy now?** {buy} — {buy_why}\n\n"
        f"**Model action:** {advice.final_action} · **Conviction:** {advice.conviction}\n\n"
        f"{advice.summary}\n\n"
        "Challenge biases: don't add solely because it's a Nifty name or recent winner."
    )

    final_verdict = (
        f"**{recommendation}** · {_stars_from_score(overall) * '★'}{(5 - _stars_from_score(overall)) * '☆'}\n\n"
        f"**Why?** Score {overall}/100 · Confidence {pred_conf:.0f}% · Risk {risk_level}.\n\n"
        f"**Who should invest?** Long-term investors aligned with {sector} if thesis holds in AR.\n\n"
        f"**Who should avoid?** Those needing near-term certainty or unable to tolerate {risk_level.lower()} risk.\n\n"
        f"**Ideal horizon:** {investment_horizon}\n\n"
        f"**Biggest opportunity:** Quality + valuation + technical alignment (if present).\n\n"
        f"**Biggest risk:** {red_flags[0] if red_flags else 'Macro drawdown'}."
    )

    breakdown = (
        f"Business {q_business:.0f}×0.18 + Financial {q_fin:.0f}×0.18 + Growth {q_growth:.0f}×0.12 + "
        f"Profit {q_profit:.0f}×0.08 + Valuation {q_val:.0f}×0.12 + Technical {q_tech:.0f}×0.12 + "
        f"Momentum {q_momentum:.0f}×0.05 + Risk {q_risk:.0f}×0.08 + Moat {q_moat:.0f}×0.05 + Mgmt {q_mgmt:.0f}×0.02"
    )

    for key in section_sources:
        section_sources[key] = list(dict.fromkeys(section_sources[key]))

    report = AlphaAIReport(
        symbol=info["symbol"],
        name=name,
        sector=sector,
        industry=industry,
        price=float(price) if price else None,
        currency=currency,
        generated_at=now,
        data_gaps=gaps,
        recommendation=recommendation,
        overall_score=overall,
        investment_grade_stars=stars,
        confidence_pct=round(pred_conf, 1),
        risk_level=risk_level,
        investment_horizon=investment_horizon,
        expected_cagr=cagr_dict,
        snapshot=snapshot,
        buy_decision=buy,
        buy_decision_why=buy_why,
        entry=entry_obj,
        business_overview=business,
        financial_metrics=fin_rows,
        financial_analysis=fin_analysis,
        valuation_verdict=val_verdict,
        valuation_detail="\n".join(val_lines),
        technical_summary=tech_summary,
        technical_analysis=tech_summary,
        swing_setup=swing,
        long_term_setup=long_setup,
        technical_risk=tech_risk,
        growth_notes=growth_notes,
        news_summary=news,
        news_sentiment=news_sentiment,
        risks=risks,
        red_flags=red_flags,
        moat_score=moat,
        moat_detail=moat_detail,
        moat_dimensions=moat_dims,
        macro_summary=macro,
        scenarios=scenarios,
        portfolio_impact=portfolio,
        suggested_weight_pct=weight,
        portfolio_allocation_options=alloc_opts,
        checklist_scores=checklist,
        probabilities=probs,
        prediction_confidence=round(pred_conf, 1),
        cagr_notes=cagr,
        quality_scores=quality,
        verdict=verdict,
        horizons=horizons,
        final_verdict_detail=final_verdict,
        action_plan=action,
        score_breakdown=breakdown,
        entry_strategy=entry,
        report_mode=report_mode,
        section_sources=section_sources,
        llm_narrative=None,
    )
    try:
        from analyzer.alpha_ai_llm import synthesize_narrative

        report.llm_narrative = synthesize_narrative(report)
    except Exception:
        pass
    return report


def compare_alpha_reports(reports: list[AlphaAIReport]) -> list[tuple[str, int, str]]:
    """Rank stocks by overall score for comparison mode."""
    ranked = sorted(reports, key=lambda r: r.overall_score, reverse=True)
    return [(r.symbol, r.overall_score, r.recommendation) for r in ranked]
