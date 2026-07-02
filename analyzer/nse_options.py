"""
NSE India options chain (official API) + CE/PE strike recommendations.

APIs (2026): option-chain-contract-info → option-chain-v3
Source: https://www.nseindia.com/
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from analyzer.nse_session import is_nse_available, nse_fetch_json, nse_get, nse_session

# Yahoo / display symbol → NSE F&O symbol
INDEX_SYMBOL_MAP = {
    "NIFTY": "NIFTY",
    "NIFTY50": "NIFTY",
    "NIFTY 50": "NIFTY",
    "^NSEI": "NIFTY",
    "BANKNIFTY": "BANKNIFTY",
    "NIFTY BANK": "BANKNIFTY",
    "BANK NIFTY": "BANKNIFTY",
    "^NSEBANK": "BANKNIFTY",
    "FINNIFTY": "FINNIFTY",
    "MIDCPNIFTY": "MIDCPNIFTY",
}

MIN_OI_STOCK = 500
MIN_OI_INDEX = 2000
MIN_VOLUME_STOCK = 50
MIN_VOLUME_INDEX = 500


@dataclass
class NSEOptionLeg:
    option_type: str  # CE | PE
    strike: float
    expiry: str
    ltp: float | None
    bid: float | None
    ask: float | None
    open_interest: int
    oi_change: int
    volume: int
    iv: float | None
    identifier: str = ""

    @property
    def spread_pct(self) -> float | None:
        if self.ltp and self.bid and self.ask and self.ltp > 0:
            return (self.ask - self.bid) / self.ltp * 100
        return None


@dataclass
class NSEOptionChain:
    symbol: str
    instrument_type: str  # index | equity
    spot: float
    expiry: str
    expiry_dates: list[str] = field(default_factory=list)
    strikes: list[float] = field(default_factory=list)
    legs: list[NSEOptionLeg] = field(default_factory=list)
    total_ce_oi: int = 0
    total_pe_oi: int = 0
    total_ce_volume: int = 0
    total_pe_volume: int = 0
    pcr_oi: float | None = None
    max_pain: float | None = None
    source: str = "NSE India"
    timestamp: str = ""

    @property
    def ce_legs(self) -> list[NSEOptionLeg]:
        return [l for l in self.legs if l.option_type == "CE"]

    @property
    def pe_legs(self) -> list[NSEOptionLeg]:
        return [l for l in self.legs if l.option_type == "PE"]


@dataclass
class NSEOptionPick:
    rank: int
    leg: NSEOptionLeg
    reason: str
    score: float


def normalize_fno_symbol(ticker: str) -> tuple[str, str]:
    """Return (nse_symbol, 'index' | 'equity')."""
    raw = ticker.upper().strip()
    raw = re.sub(r"\.(NS|BO)$", "", raw)
    raw = re.sub(r"^NSE:", "", raw)
    raw = re.sub(r"-EQ$", "", raw)
    if raw in INDEX_SYMBOL_MAP:
        return INDEX_SYMBOL_MAP[raw], "index"
    for k, v in INDEX_SYMBOL_MAP.items():
        if k in raw:
            return v, "index"
    return raw, "equity"


def _parse_leg(side: dict | None, option_type: str, strike: float) -> NSEOptionLeg | None:
    if not side or side.get("strikePrice") is None:
        return None
    return NSEOptionLeg(
        option_type=option_type,
        strike=float(side.get("strikePrice", strike)),
        expiry=side.get("expiryDate", ""),
        ltp=_f(side.get("lastPrice")),
        bid=_f(side.get("bidprice")),
        ask=_f(side.get("askPrice")),
        open_interest=int(side.get("openInterest") or 0),
        oi_change=int(side.get("changeinOpenInterest") or 0),
        volume=int(side.get("totalTradedVolume") or 0),
        iv=_f(side.get("impliedVolatility")),
        identifier=side.get("identifier", ""),
    )


def _f(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def fetch_contract_info(symbol: str) -> dict:
    """Available expiries and strikes from NSE."""
    if not is_nse_available():
        raise ValueError("NSE temporarily unavailable — check network or wait a few minutes")
    nse_sym, kind = normalize_fno_symbol(symbol)
    instrument = "OPTIDX" if kind == "index" else "OPTSTK"
    data = nse_fetch_json(f"option-chain-contract-info?symbol={nse_sym}&instrument={instrument}")
    if not data:
        raise ValueError(f"NSE contract info unavailable for {nse_sym}")
    return data


def compute_max_pain(chain: NSEOptionChain) -> float | None:
    """Strike where option writers have minimum payout at expiry."""
    strikes = sorted(chain.strikes or {l.strike for l in chain.legs})
    if not strikes:
        return None
    ce_map = {l.strike: l for l in chain.ce_legs}
    pe_map = {l.strike: l for l in chain.pe_legs}
    best_strike = strikes[0]
    best_pain = float("inf")
    for test in strikes:
        pain = 0.0
        for sp in strikes:
            ce = ce_map.get(sp)
            pe = pe_map.get(sp)
            if ce and test > sp:
                pain += (test - sp) * ce.open_interest
            if pe and test < sp:
                pain += (sp - test) * pe.open_interest
        if pain < best_pain:
            best_pain = pain
            best_strike = test
    return best_strike


def fetch_option_chain(symbol: str, expiry: str | None = None) -> NSEOptionChain:
    """
    Full option chain from NSE v3 API for nearest or chosen expiry.
    """
    nse_sym, kind = normalize_fno_symbol(symbol)
    chain_type = "Indices" if kind == "index" else "Equities"

    info = fetch_contract_info(symbol)
    expiries = info.get("expiryDates") or []
    if not expiries:
        raise ValueError(f"No F&O expiries for {nse_sym} on NSE (not in F&O list?).")

    use_expiry = expiry if expiry in expiries else expiries[0]
    path = f"option-chain-v3?type={chain_type}&symbol={nse_sym}&expiry={use_expiry}"
    payload = nse_fetch_json(path, timeout=25)
    if not payload:
        raise ValueError(f"NSE option chain unavailable for {nse_sym}")

    records = payload.get("records") or {}
    spot = float(records.get("underlyingValue") or 0)
    data = records.get("data") or []
    filtered = payload.get("filtered") or {}

    legs: list[NSEOptionLeg] = []
    strikes: list[float] = []
    for row in data:
        sp = float(row.get("strikePrice") or 0)
        strikes.append(sp)
        ce = _parse_leg(row.get("CE"), "CE", sp)
        pe = _parse_leg(row.get("PE"), "PE", sp)
        if ce:
            legs.append(ce)
        if pe:
            legs.append(pe)

    ce_f = filtered.get("CE") or {}
    pe_f = filtered.get("PE") or {}
    total_ce_oi = int(ce_f.get("totOI") or ce_f.get("openInterest") or 0)
    total_pe_oi = int(pe_f.get("totOI") or pe_f.get("openInterest") or 0)
    total_ce_vol = int(ce_f.get("totVol") or ce_f.get("totalTradedVolume") or 0)
    total_pe_vol = int(pe_f.get("totVol") or pe_f.get("totalTradedVolume") or 0)
    pcr = total_pe_oi / total_ce_oi if total_ce_oi else None

    ts = ""
    if data and data[0].get("CE"):
        ts = data[0]["CE"].get("lastUpdateTime", "")

    chain = NSEOptionChain(
        symbol=nse_sym,
        instrument_type=kind,
        spot=spot,
        expiry=use_expiry,
        expiry_dates=expiries,
        strikes=sorted(set(strikes)),
        legs=legs,
        total_ce_oi=total_ce_oi,
        total_pe_oi=total_pe_oi,
        total_ce_volume=total_ce_vol,
        total_pe_volume=total_pe_vol,
        pcr_oi=round(pcr, 2) if pcr else None,
        timestamp=ts,
    )
    chain.max_pain = compute_max_pain(chain)
    return chain


def fetch_market_status() -> dict:
    data = nse_fetch_json("marketStatus")
    if not data:
        raise ValueError("NSE market status unavailable")
    return data


def _atm_strike(strikes: list[float], spot: float) -> float:
    return min(strikes, key=lambda s: abs(s - spot))


def _liquidity_score(leg: NSEOptionLeg, is_index: bool) -> float:
    min_oi = MIN_OI_INDEX if is_index else MIN_OI_STOCK
    min_vol = MIN_VOLUME_INDEX if is_index else MIN_VOLUME_STOCK
    if leg.open_interest < min_oi or leg.volume < min_vol:
        return -1.0
    score = leg.volume + leg.open_interest * 0.1 + abs(leg.oi_change) * 0.05
    if leg.spread_pct and leg.spread_pct > 5:
        score *= 0.7
    return score


def recommend_nse_strikes(
    chain: NSEOptionChain,
    action: str,
    max_picks: int = 3,
) -> list[NSEOptionPick]:
    """
    Pick specific CE/PE contracts from NSE chain based on candle verdict action.
    action: STRONG CE | BUY CE | BUY PE | STRONG PE | NO TRADE | WAIT
    """
    if action in ("NO TRADE", "WAIT", "NEUTRAL"):
        return []

    is_index = chain.instrument_type == "index"
    strikes = chain.strikes or sorted({l.strike for l in chain.legs})
    if not strikes:
        return []

    atm = _atm_strike(strikes, chain.spot)
    atm_idx = strikes.index(atm)

    if "CE" in action:
        otm_offset = 1 if "STRONG" in action else 0
        target_strikes = []
        for off in range(otm_offset, otm_offset + 3):
            idx = atm_idx + off
            if idx < len(strikes):
                target_strikes.append(strikes[idx])
        pool = chain.ce_legs
        opt = "CE"
    else:
        otm_offset = 1 if "STRONG" in action else 0
        target_strikes = []
        for off in range(otm_offset, otm_offset + 3):
            idx = atm_idx - off
            if idx >= 0:
                target_strikes.append(strikes[idx])
        pool = chain.pe_legs
        opt = "PE"

    candidates = [l for l in pool if l.strike in target_strikes]
    scored: list[tuple[float, NSEOptionLeg, str]] = []
    for leg in candidates:
        liq = _liquidity_score(leg, is_index)
        if liq < 0:
            continue
        dist = abs(leg.strike - chain.spot)
        dist_bonus = max(0, 1 - dist / (chain.spot * 0.02)) if chain.spot else 0
        total = liq + dist_bonus * 500
        moneyness = "ATM" if leg.strike == atm else ("OTM" if (opt == "CE" and leg.strike > chain.spot) or (opt == "PE" and leg.strike < chain.spot) else "ITM")
        reason = (
            f"{opt} {leg.strike:.0f} {moneyness} · LTP ₹{leg.ltp or 0:.2f} · "
            f"OI {leg.open_interest:,} · Vol {leg.volume:,}"
            + (f" · IV {leg.iv:.1f}%" if leg.iv else "")
        )
        scored.append((total, leg, reason))

    # fallback: best liquidity near ATM in full pool
    if not scored:
        near = sorted(pool, key=lambda l: abs(l.strike - chain.spot))[:8]
        for leg in near:
            liq = _liquidity_score(leg, is_index)
            if liq >= 0:
                reason = f"{opt} {leg.strike:.0f} (liquid) · LTP ₹{leg.ltp or 0:.2f} · OI {leg.open_interest:,}"
                scored.append((liq, leg, reason))

    scored.sort(key=lambda x: -x[0])
    picks: list[NSEOptionPick] = []
    for i, (sc, leg, reason) in enumerate(scored[:max_picks], start=1):
        picks.append(NSEOptionPick(rank=i, leg=leg, reason=reason, score=sc))
    return picks


def enrich_with_nse_chain(
    action: str,
    ticker: str,
    expiry: str | None = None,
) -> tuple[NSEOptionChain | None, list[NSEOptionPick], str | None]:
    """Fetch NSE chain and recommend strikes; returns (chain, picks, error)."""
    try:
        chain = fetch_option_chain(ticker, expiry=expiry)
        picks = recommend_nse_strikes(chain, action)
        return chain, picks, None
    except Exception as exc:
        return None, [], str(exc)


def chain_summary_markdown(chain: NSEOptionChain) -> str:
    pcr_note = ""
    if chain.pcr_oi:
        if chain.pcr_oi > 1.2:
            pcr_note = " (elevated PE OI — bearish hedging)"
        elif chain.pcr_oi < 0.8:
            pcr_note = " (low PCR — bullish positioning)"
    mp = ""
    if chain.max_pain:
        bias = "above" if chain.spot > chain.max_pain else "below"
        mp = f" · Max pain **{chain.max_pain:g}** (spot {bias} MP)"
    return (
        f"**{chain.symbol}** spot **₹{chain.spot:,.2f}** · Expiry **{chain.expiry}** · "
        f"CE OI {chain.total_ce_oi:,} · PE OI {chain.total_pe_oi:,} · "
        f"PCR **{chain.pcr_oi or '—'}**{pcr_note}{mp}"
    )
