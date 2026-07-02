"""Custom stock screener — filter universe by technical, fundamental, and India signals."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import pandas as pd

from analyzer.chart_horizon import analyze_long_term_chart, analyze_short_term_chart
from analyzer.combined import analyze_combined
from analyzer.data import fetch_stock_data
from analyzer.indicators import add_indicators
from analyzer.markets import is_india_market

SCAN_WORKERS = 8

BUY_COMBINED = ("STRONG BUY", "BUY")
SHORT_BUY = ("STRONG BUY", "BUY")
LONG_BUY = ("CORE BUY", "ACCUMULATE")


@dataclass
class ScreenerCriteria:
    """All fields optional — None means no filter on that dimension."""

    name: str = "Custom"
    min_combined_score: float | None = None
    max_combined_score: float | None = None
    combined_recommendations: tuple[str, ...] | None = None
    min_short_score: float | None = None
    min_long_score: float | None = None
    short_actions: tuple[str, ...] | None = None
    long_actions: tuple[str, ...] | None = None
    min_rsi: float | None = None
    max_rsi: float | None = None
    above_sma20: bool | None = None
    above_sma50: bool | None = None
    above_sma200: bool | None = None
    min_volume_ratio: float | None = None
    min_delivery_pct: float | None = None
    exclude_speculative_delivery: bool = False
    exclude_earnings_within_days: int | None = None
    min_roe: float | None = None
    max_pe: float | None = None
    max_debt_equity: float | None = None
    min_revenue_growth: float | None = None
    sector_contains: str | None = None

    def needs_india_extras(self) -> bool:
        return any([
            self.min_delivery_pct is not None,
            self.exclude_speculative_delivery,
            self.exclude_earnings_within_days is not None,
        ])


@dataclass
class ScreenerRow:
    ticker: str
    nse_symbol: str
    name: str
    price: float
    sector: str
    combined_score: float
    combined_rec: str
    technical_score: float
    fundamental_score: float
    short_action: str
    short_score: float
    long_action: str
    long_score: float
    rsi: float | None = None
    above_sma20: bool | None = None
    above_sma50: bool | None = None
    above_sma200: bool | None = None
    volume_ratio: float | None = None
    pe: float | None = None
    roe: float | None = None
    debt_equity: float | None = None
    revenue_growth: float | None = None
    delivery_pct: float | None = None
    delivery_quality: str = ""
    earnings_days_until: int | None = None
    error: str | None = None


def _safe_float(val) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _bool_above(price: float, sma) -> bool | None:
    s = _safe_float(sma)
    if s is None or price <= 0:
        return None
    return price > s


def _volume_ratio_from_df(df: pd.DataFrame) -> float | None:
    if len(df) < 2:
        return None
    row = df.iloc[-1]
    vol_sma = row.get("VOL_SMA_20")
    if vol_sma is None or pd.isna(vol_sma) or float(vol_sma) <= 0:
        return None
    return round(float(row["Volume"]) / float(vol_sma), 2)


PRESET_SCREENS: dict[str, ScreenerCriteria] = {
    "Strong buys": ScreenerCriteria(
        name="Strong buys",
        combined_recommendations=BUY_COMBINED,
        min_combined_score=15.0,
    ),
    "Quality compounders": ScreenerCriteria(
        name="Quality compounders",
        min_long_score=28.0,
        long_actions=LONG_BUY,
        min_roe=0.12,
        max_debt_equity=1.0,
    ),
    "Swing momentum": ScreenerCriteria(
        name="Swing momentum",
        min_short_score=22.0,
        short_actions=SHORT_BUY,
        above_sma20=True,
        min_volume_ratio=1.1,
        min_delivery_pct=25.0,
        exclude_speculative_delivery=True,
    ),
    "Oversold bounce": ScreenerCriteria(
        name="Oversold bounce",
        max_rsi=35.0,
        min_combined_score=0.0,
    ),
    "Breakout watch": ScreenerCriteria(
        name="Breakout watch",
        min_volume_ratio=1.5,
        above_sma20=True,
        min_short_score=15.0,
    ),
    "Earnings-safe swing": ScreenerCriteria(
        name="Earnings-safe swing",
        min_short_score=22.0,
        short_actions=SHORT_BUY,
        exclude_earnings_within_days=5,
        exclude_speculative_delivery=True,
    ),
    "Value hunters": ScreenerCriteria(
        name="Value hunters",
        max_pe=15.0,
        min_roe=0.10,
        min_combined_score=0.0,
    ),
    "Long-term accumulators": ScreenerCriteria(
        name="Long-term accumulators",
        min_long_score=28.0,
        long_actions=LONG_BUY,
        above_sma200=True,
        min_roe=0.10,
    ),
    "Penny momentum (risky)": ScreenerCriteria(
        name="Penny momentum (risky)",
        min_short_score=12.0,
        short_actions=SHORT_BUY,
        min_volume_ratio=1.0,
        exclude_speculative_delivery=True,
        exclude_earnings_within_days=3,
    ),
}


def _scan_one(
    ticker: str,
    period: str,
    market: str,
    *,
    fetch_india_extras: bool,
) -> ScreenerRow:
    nse = ticker.replace(".NS", "").replace(".BO", "").upper()
    try:
        df, info = fetch_stock_data(ticker, period=period, market=market, enrich_nse=True)
        df = add_indicators(df)
        combined = analyze_combined(df, info["symbol"], yf_info=info)
        short_h = analyze_short_term_chart(df)
        long_h = analyze_long_term_chart(df, yf_info=info)

        row = df.iloc[-1]
        price = float(info.get("nse_last_price") or combined.technical.current_price)
        rsi = _safe_float(row.get("RSI_14"))

        raw = combined.fundamental.raw
        pe = _safe_float(raw.get("pe_trailing"))
        roe = _safe_float(raw.get("roe"))
        de = _safe_float(raw.get("debt_to_equity"))
        if de is not None and de > 10:
            de = de / 100.0
        rev_g = _safe_float(raw.get("revenue_growth"))

        delivery_pct = None
        delivery_quality = ""
        earnings_days = None

        if fetch_india_extras and is_india_market(market) and ticker.endswith(".NS"):
            try:
                from analyzer.delivery_quality import build_delivery_snapshot

                snap = build_delivery_snapshot(info["symbol"], df=df, fetch_history=False)
                if snap:
                    delivery_pct = snap.delivery_pct
                    delivery_quality = snap.quality
            except Exception:
                pass
            try:
                from analyzer.earnings_calendar import fetch_corporate_event

                ev = fetch_corporate_event(info["symbol"], market=market)
                if ev:
                    earnings_days = ev.days_until
            except Exception:
                pass

        return ScreenerRow(
            ticker=info["symbol"],
            nse_symbol=nse,
            name=info.get("name", ticker),
            price=price,
            sector=str(info.get("sector") or ""),
            combined_score=combined.combined_score,
            combined_rec=combined.combined_recommendation,
            technical_score=combined.technical.composite_score,
            fundamental_score=combined.fundamental.composite_score,
            short_action=short_h.action,
            short_score=short_h.score,
            long_action=long_h.action,
            long_score=long_h.score,
            rsi=rsi,
            above_sma20=_bool_above(price, row.get("SMA_20")),
            above_sma50=_bool_above(price, row.get("SMA_50")),
            above_sma200=_bool_above(price, row.get("SMA_200")),
            volume_ratio=_volume_ratio_from_df(df),
            pe=pe,
            roe=roe,
            debt_equity=de,
            revenue_growth=rev_g,
            delivery_pct=delivery_pct,
            delivery_quality=delivery_quality,
            earnings_days_until=earnings_days,
        )
    except Exception as exc:
        return ScreenerRow(
            ticker=ticker,
            nse_symbol=nse,
            name=ticker,
            price=0.0,
            sector="",
            combined_score=0.0,
            combined_rec="ERROR",
            technical_score=0.0,
            fundamental_score=0.0,
            short_action="—",
            short_score=0.0,
            long_action="—",
            long_score=0.0,
            error=str(exc),
        )


def apply_criteria(rows: list[ScreenerRow], criteria: ScreenerCriteria) -> list[ScreenerRow]:
    """Filter scanned rows in-memory."""
    out: list[ScreenerRow] = []
    for row in rows:
        if row.error:
            continue
        if not _row_matches(row, criteria):
            continue
        out.append(row)
    out.sort(key=lambda r: (-r.combined_score, -r.short_score))
    return out


def _row_matches(row: ScreenerRow, c: ScreenerCriteria) -> bool:
    if c.min_combined_score is not None and row.combined_score < c.min_combined_score:
        return False
    if c.max_combined_score is not None and row.combined_score > c.max_combined_score:
        return False
    if c.combined_recommendations and row.combined_rec not in c.combined_recommendations:
        return False
    if c.min_short_score is not None and row.short_score < c.min_short_score:
        return False
    if c.min_long_score is not None and row.long_score < c.min_long_score:
        return False
    if c.short_actions and row.short_action not in c.short_actions:
        return False
    if c.long_actions and row.long_action not in c.long_actions:
        return False
    if c.min_rsi is not None and (row.rsi is None or row.rsi < c.min_rsi):
        return False
    if c.max_rsi is not None and (row.rsi is None or row.rsi > c.max_rsi):
        return False
    for flag, attr in (
        (c.above_sma20, "above_sma20"),
        (c.above_sma50, "above_sma50"),
        (c.above_sma200, "above_sma200"),
    ):
        if flag is not None:
            val = getattr(row, attr)
            if val is None or val != flag:
                return False
    if c.min_volume_ratio is not None:
        if row.volume_ratio is None or row.volume_ratio < c.min_volume_ratio:
            return False
    if c.min_delivery_pct is not None:
        if row.delivery_pct is None or row.delivery_pct < c.min_delivery_pct:
            return False
    if c.exclude_speculative_delivery and row.delivery_quality == "speculative":
        return False
    if c.exclude_earnings_within_days is not None:
        if row.earnings_days_until is not None and row.earnings_days_until <= c.exclude_earnings_within_days:
            return False
    if c.min_roe is not None:
        if row.roe is None or row.roe < c.min_roe:
            return False
    if c.max_pe is not None:
        if row.pe is None or row.pe <= 0 or row.pe > c.max_pe:
            return False
    if c.max_debt_equity is not None:
        if row.debt_equity is None or row.debt_equity > c.max_debt_equity:
            return False
    if c.min_revenue_growth is not None:
        if row.revenue_growth is None or row.revenue_growth < c.min_revenue_growth:
            return False
    if c.sector_contains:
        needle = c.sector_contains.lower()
        if needle not in (row.sector or "").lower():
            return False
    return True


def run_screener(
    tickers: list[str],
    criteria: ScreenerCriteria,
    *,
    period: str = "1y",
    market: str = "india",
    max_workers: int = SCAN_WORKERS,
) -> list[ScreenerRow]:
    """Scan universe then apply criteria."""
    if not tickers:
        return []
    extras = criteria.needs_india_extras() and is_india_market(market)
    rows: list[ScreenerRow] = []
    workers = min(max_workers, max(1, len(tickers)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {
            pool.submit(_scan_one, t, period, market, fetch_india_extras=extras): t
            for t in tickers
        }
        for fut in as_completed(futs):
            rows.append(fut.result())
    return apply_criteria(rows, criteria)


def merge_criteria(base: ScreenerCriteria, overrides: ScreenerCriteria) -> ScreenerCriteria:
    """Overlay user tweaks onto a preset."""
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    for f in overrides.__dataclass_fields__:
        val = getattr(overrides, f)
        if val is None or val is False or val == () or val == "":
            if f in ("exclude_speculative_delivery",) and not val:
                continue
            if f == "name":
                continue
        if val is not None and val != "" and val != ():
            data[f] = val
    return ScreenerCriteria(**data)


def criteria_summary(c: ScreenerCriteria) -> str:
    """Human-readable filter summary for UI."""
    parts: list[str] = []
    if c.combined_recommendations:
        parts.append(f"Combined ∈ {', '.join(c.combined_recommendations)}")
    if c.min_combined_score is not None:
        parts.append(f"Combined ≥ {c.min_combined_score:.0f}")
    if c.min_short_score is not None:
        parts.append(f"Swing ≥ {c.min_short_score:.0f}")
    if c.min_long_score is not None:
        parts.append(f"Long ≥ {c.min_long_score:.0f}")
    if c.max_rsi is not None:
        parts.append(f"RSI ≤ {c.max_rsi:.0f}")
    if c.min_rsi is not None:
        parts.append(f"RSI ≥ {c.min_rsi:.0f}")
    if c.above_sma20:
        parts.append("Above SMA-20")
    if c.above_sma200:
        parts.append("Above SMA-200")
    if c.min_volume_ratio is not None:
        parts.append(f"Vol ≥ {c.min_volume_ratio:.1f}× avg")
    if c.min_delivery_pct is not None:
        parts.append(f"Delivery ≥ {c.min_delivery_pct:.0f}%")
    if c.exclude_speculative_delivery:
        parts.append("No speculative delivery")
    if c.exclude_earnings_within_days is not None:
        parts.append(f"Earnings > {c.exclude_earnings_within_days}d away")
    if c.max_pe is not None:
        parts.append(f"P/E ≤ {c.max_pe:.0f}")
    if c.min_roe is not None:
        parts.append(f"ROE ≥ {c.min_roe * 100:.0f}%")
    if c.max_debt_equity is not None:
        parts.append(f"D/E ≤ {c.max_debt_equity:.1f}")
    return " · ".join(parts) if parts else "No filters (shows all scanned stocks)"
