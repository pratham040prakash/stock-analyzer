"""Penny / low-priced NSE stock scanner — high-risk swing ideas only."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from analyzer.markets import is_india_market
from analyzer.screener import ScreenerCriteria, ScreenerRow, _scan_one

# NSE names often in the ₹5–₹50 band (prices change — runtime filter applies).
PENNY_CANDIDATE_SYMBOLS: list[str] = [
    "IDBI", "SUZLON", "RPOWER", "YESBANK", "IDEA", "DISHTV",
    "JPPOWER", "RTNPOWER", "GTLINFRA", "PCJEWELLER", "DHANI",
    "MANAKSIA", "HCC", "UCOBANK", "CENTRALBK", "IOB", "J&KBANK",
    "NHPC", "SJVN", "GSFC", "GNFC", "RAIN", "MOREPENLAB", "TRIDENT",
    "SAIL", "NMDC", "BANKINDIA", "MAHABANK", "PNB", "ZEEL",
    "NETWORK18", "MRPL", "CHENNPETRO", "GMDCLTD", "RVNL", "IRCON",
    "RAILTEL", "ALOKINDS", "WOCKPHARMA", "SUNTV", "TATAPOWER",
    "IFCI", "RELCAPITAL", "JPASSOCIAT", "GAYAPROJ", "HLVLTD",
    "FILATEX", "TITAGARH", "JISLJALEQS", "SOUTHBANK", "FEDERALBNK",
]

DEFAULT_MAX_PRICE_INR = 20.0
MAX_PRICE_OPTIONS = (10.0, 20.0, 50.0)

BUY_ACTIONS = frozenset({"STRONG BUY", "BUY", "ACCUMULATE"})


@dataclass
class PennyStockPick:
    ticker: str
    nse_symbol: str
    name: str
    price: float
    combined_rec: str
    combined_score: float
    short_action: str
    short_score: float
    long_action: str
    long_score: float
    rsi: float | None
    volume_ratio: float | None
    delivery_pct: float | None
    delivery_quality: str
    penny_score: float
    rank: int
    thesis: str
    risk_flags: list[str] = field(default_factory=list)


@dataclass
class PennyStockReport:
    max_price_inr: float
    scanned: int
    matched_price: int
    picks: list[PennyStockPick] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    disclaimer: str = ""


PENNY_SCAN_CRITERIA = ScreenerCriteria(
    name="Penny momentum",
    min_short_score=12.0,
    short_actions=("STRONG BUY", "BUY"),
    min_volume_ratio=1.0,
    exclude_speculative_delivery=True,
    exclude_earnings_within_days=3,
)


def penny_universe_yahoo() -> list[str]:
    return [f"{s}.NS" for s in dict.fromkeys(PENNY_CANDIDATE_SYMBOLS)]


def _risk_flags(row: ScreenerRow) -> list[str]:
    flags: list[str] = []
    if row.price < 10:
        flags.append("Ultra-low price — manipulation / circuit risk")
    if row.delivery_quality == "speculative":
        flags.append("Low delivery — mostly intraday churn")
    elif row.delivery_pct is not None and row.delivery_pct < 25:
        flags.append("Weak delivery %")
    if row.volume_ratio is not None and row.volume_ratio < 1.1:
        flags.append("Thin volume vs average")
    if row.pe is not None and row.pe < 0:
        flags.append("Negative earnings (P/E)")
    if row.debt_equity is not None and row.debt_equity > 2:
        flags.append("High debt/equity")
    if row.rsi is not None and row.rsi > 70:
        flags.append("RSI stretched — chase risk")
    return flags


def _penny_score(row: ScreenerRow) -> float:
    score = row.combined_score * 0.35 + row.short_score * 0.45 + row.long_score * 0.1
    if row.short_action in ("STRONG BUY", "BUY"):
        score += 6
    if row.volume_ratio is not None:
        score += min(8, (row.volume_ratio - 1.0) * 10)
    if row.delivery_pct is not None:
        if row.delivery_pct >= 40:
            score += 5
        elif row.delivery_pct >= 25:
            score += 2
    if row.delivery_quality == "speculative":
        score -= 20
    if row.rsi is not None and 40 <= row.rsi <= 60:
        score += 2
    return round(score, 1)


def _thesis(row: ScreenerRow) -> str:
    parts = [f"Swing **{row.short_action}** ({row.short_score:+.0f})"]
    if row.volume_ratio is not None:
        parts.append(f"volume {row.volume_ratio:.1f}× avg")
    if row.delivery_pct is not None:
        parts.append(f"delivery {row.delivery_pct:.0f}%")
    if row.combined_rec in BUY_ACTIONS:
        parts.append(f"combined {row.combined_rec} ({row.combined_score:+.0f})")
    return " · ".join(parts)


def _row_to_pick(row: ScreenerRow, rank: int) -> PennyStockPick:
    flags = _risk_flags(row)
    return PennyStockPick(
        ticker=row.ticker,
        nse_symbol=row.nse_symbol,
        name=row.name,
        price=row.price,
        combined_rec=row.combined_rec,
        combined_score=row.combined_score,
        short_action=row.short_action,
        short_score=row.short_score,
        long_action=row.long_action,
        long_score=row.long_score,
        rsi=row.rsi,
        volume_ratio=row.volume_ratio,
        delivery_pct=row.delivery_pct,
        delivery_quality=row.delivery_quality,
        penny_score=_penny_score(row),
        rank=rank,
        thesis=_thesis(row),
        risk_flags=flags,
    )


def scan_penny_stocks(
    *,
    max_price_inr: float = DEFAULT_MAX_PRICE_INR,
    period: str = "6mo",
    market: str = "india",
    limit: int = 8,
    max_workers: int = 8,
) -> PennyStockReport:
    """Find best low-priced NSE setups under max_price_inr with liquidity filters."""
    if not is_india_market(market):
        return PennyStockReport(
            max_price_inr=max_price_inr,
            scanned=0,
            matched_price=0,
            disclaimer="Penny scan is India (NSE) only.",
        )

    tickers = penny_universe_yahoo()
    rows: list[ScreenerRow] = []
    workers = min(max_workers, len(tickers))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {
            pool.submit(_scan_one, t, period, market, fetch_india_extras=True): t
            for t in tickers
        }
        for fut in as_completed(futs):
            rows.append(fut.result())

    priced = [r for r in rows if not r.error and 0 < r.price <= max_price_inr]
    candidates: list[ScreenerRow] = []
    avoid: list[str] = []

    for row in priced:
        flags = _risk_flags(row)
        if row.delivery_quality == "speculative" and row.short_score < 25:
            avoid.append(f"{row.nse_symbol} — speculative churn")
            continue
        if row.short_action not in ("STRONG BUY", "BUY", "ACCUMULATE") and row.short_score < 15:
            continue
        if row.volume_ratio is not None and row.volume_ratio < 0.8:
            avoid.append(f"{row.nse_symbol} — very thin volume")
            continue
        candidates.append(row)

    candidates.sort(key=lambda r: _penny_score(r), reverse=True)
    picks = [_row_to_pick(r, i + 1) for i, r in enumerate(candidates[:limit])]

    return PennyStockReport(
        max_price_inr=max_price_inr,
        scanned=len(rows),
        matched_price=len(priced),
        picks=picks,
        avoid=avoid[:6],
        disclaimer=(
            "**Penny stocks are extremely risky.** Many are illiquid, manipulated, or near bankruptcy. "
            "Use only **risk capital** you can afford to lose entirely. Prefer **delivery** over MIS; "
            "avoid averaging down. This is **not** a buy list — verify on NSE/Kite before any trade."
        ),
    )


def format_penny_tips() -> str:
    return (
        "**How to use penny picks**\n"
        "- Treat as a **watchlist**, not automatic buys — confirm trend on **Single Stock**.\n"
        "- Size small: **≤2–3%** of portfolio per name; max **2 penny positions** at once.\n"
        "- Prefer names with **delivery ≥25%** and volume above average.\n"
        "- Set a **hard stop** (8–10% below entry); penny stocks gap down fast.\n"
        "- For long-term wealth, **Nifty quality names** (Screener / Compare) beat penny hunting."
    )
