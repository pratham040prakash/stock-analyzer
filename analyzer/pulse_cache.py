"""Disk cache for Market Pulse — JSON-safe across Streamlit hot-reloads."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from analyzer.cache_utils import CACHE_DIR, CACHE_VERSION
from analyzer.chart_horizon import HorizonAnalysis
from analyzer.india_macro import FiiDiiFlow, IndiaMacroSnapshot, MacroQuote
from analyzer.market_pulse import IndexPulse
from analyzer.market_pulse_scan import (
    ChartStockPick,
    IndexOptionsPulse,
    MarketPulseReport,
    StockPulseEntry,
)
from analyzer.earnings_calendar import event_from_dict, event_to_dict
from analyzer.market_regime import MarketRegime

PULSE_CACHE_VER = "pulse_v1"


def _pulse_cache_path(key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{CACHE_VERSION}_{safe}.pulse.json"


def _horizon(d: dict | None) -> HorizonAnalysis | None:
    return HorizonAnalysis(**d) if d else None


def _index_pulse(d: dict) -> IndexPulse:
    return IndexPulse(**d)


def _macro_quote(d: dict | None) -> MacroQuote | None:
    return MacroQuote(**d) if d else None


def _fii_dii(d: dict | None) -> FiiDiiFlow | None:
    return FiiDiiFlow(**d) if d else None


def _macro(d: dict | None) -> IndiaMacroSnapshot | None:
    if not d:
        return None
    return IndiaMacroSnapshot(
        fetched_at=d["fetched_at"],
        india_vix=_macro_quote(d.get("india_vix")),
        gift_nifty_proxy=_macro_quote(d.get("gift_nifty_proxy")),
        sectors=[MacroQuote(**s) for s in d.get("sectors", [])],
        fii_dii=_fii_dii(d.get("fii_dii")),
        vix_regime=d.get("vix_regime", ""),
        sector_leader=d.get("sector_leader", ""),
        sector_laggard=d.get("sector_laggard", ""),
        premarket_note=d.get("premarket_note", ""),
        errors=list(d.get("errors", [])),
    )


def _regime(d: dict | None) -> MarketRegime | None:
    return MarketRegime(**d) if d else None


def _chart_pick(d: dict) -> ChartStockPick:
    return ChartStockPick(**d)


def _stock_entry(d: dict) -> StockPulseEntry:
    return StockPulseEntry(
        symbol=d["symbol"],
        nse_symbol=d["nse_symbol"],
        name=d["name"],
        price=d["price"],
        combined_rec=d["combined_rec"],
        combined_score=d["combined_score"],
        intraday=_horizon(d.get("intraday")),
        short_term=_horizon(d.get("short_term")),
        long_term=_horizon(d.get("long_term")),
        intraday_verdict=None,
        intraday_df=None,
        short_chart_df=None,
        long_chart_df=None,
        what_to_do=d.get("what_to_do", ""),
        ltp_source=d.get("ltp_source", "Yahoo"),
        error=d.get("error"),
    )


def _index_options(d: dict) -> IndexOptionsPulse:
    return IndexOptionsPulse(
        fno_symbol=d["fno_symbol"],
        name=d["name"],
        index_pulse=_index_pulse(d["index_pulse"]) if d.get("index_pulse") else None,
        options_action=d["options_action"],
        chain=None,
        picks=[],
        error=d.get("error"),
    )


def serialize_pulse_report(report: MarketPulseReport) -> dict:
    """Strip charts / pickle-unsafe objects for JSON disk cache."""
    return {
        "pulse_ver": PULSE_CACHE_VER,
        "indices": [asdict(p) for p in report.indices],
        "market_verdict": report.market_verdict,
        "index_options": [
            {
                "fno_symbol": io.fno_symbol,
                "name": io.name,
                "index_pulse": asdict(io.index_pulse) if io.index_pulse else None,
                "options_action": io.options_action,
                "error": io.error,
            }
            for io in report.index_options
        ],
        "top_stocks": [_stock_to_dict(s) for s in report.top_stocks],
        "stock_map": {k: _stock_to_dict(v) for k, v in report.stock_map.items()},
        "intraday_picks": [asdict(p) for p in report.intraday_picks],
        "short_term_picks": [asdict(p) for p in report.short_term_picks],
        "long_term_picks": [asdict(p) for p in report.long_term_picks],
        "regime": asdict(report.regime) if report.regime else None,
        "macro": asdict(report.macro) if report.macro else None,
        "strongest_ce": list(report.strongest_ce),
        "strongest_pe": list(report.strongest_pe),
        "strongest_equity": list(report.strongest_equity),
        "index_options_deferred": getattr(report, "_index_options_deferred", False),
        "earnings_events": [event_to_dict(e) for e in getattr(report, "earnings_events", [])],
    }


def _stock_to_dict(s: StockPulseEntry) -> dict:
    return {
        "symbol": s.symbol,
        "nse_symbol": s.nse_symbol,
        "name": s.name,
        "price": s.price,
        "combined_rec": s.combined_rec,
        "combined_score": s.combined_score,
        "intraday": asdict(s.intraday) if s.intraday else None,
        "short_term": asdict(s.short_term) if s.short_term else None,
        "long_term": asdict(s.long_term) if s.long_term else None,
        "what_to_do": s.what_to_do,
        "ltp_source": s.ltp_source,
        "error": s.error,
    }


def deserialize_pulse_report(d: dict) -> MarketPulseReport:
    earnings_raw = [event_from_dict(x) for x in d.get("earnings_events", [])]
    report = MarketPulseReport(
        indices=[_index_pulse(x) for x in d.get("indices", [])],
        market_verdict=d.get("market_verdict", ""),
        index_options=[_index_options(x) for x in d.get("index_options", [])],
        top_stocks=[_stock_entry(x) for x in d.get("top_stocks", [])],
        stock_map={k: _stock_entry(v) for k, v in d.get("stock_map", {}).items()},
        intraday_picks=[_chart_pick(x) for x in d.get("intraday_picks", [])],
        short_term_picks=[_chart_pick(x) for x in d.get("short_term_picks", [])],
        long_term_picks=[_chart_pick(x) for x in d.get("long_term_picks", [])],
        regime=_regime(d.get("regime")),
        macro=_macro(d.get("macro")),
        from_cache=True,
        strongest_ce=list(d.get("strongest_ce", [])),
        strongest_pe=list(d.get("strongest_pe", [])),
        strongest_equity=list(d.get("strongest_equity", [])),
        earnings_events=earnings_raw,
        earnings_by_nse={e.nse_symbol.upper(): e for e in earnings_raw},
    )
    report._index_options_deferred = bool(d.get("index_options_deferred", False))  # type: ignore[attr-defined]
    return report


def save_pulse_cache(key: str, report: MarketPulseReport) -> None:
    path = _pulse_cache_path(key)
    try:
        payload = {
            "ts": time.time(),
            "ver": CACHE_VERSION,
            "data": serialize_pulse_report(report),
        }
        path.write_text(json.dumps(payload, default=str), encoding="utf-8")
    except (TypeError, ValueError):
        pass


def load_pulse_cache_with_stale(key: str, ttl_seconds: int) -> tuple[MarketPulseReport | None, bool]:
    path = _pulse_cache_path(key)
    if not path.exists():
        return None, False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("ver") != CACHE_VERSION:
            return None, False
        data = payload.get("data") or {}
        if data.get("pulse_ver") != PULSE_CACHE_VER:
            return None, False
        report = deserialize_pulse_report(data)
        fresh = time.time() - float(payload.get("ts", 0)) <= ttl_seconds
        return report, fresh
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return None, False


def _json_default(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Not JSON serializable: {type(obj)}")
