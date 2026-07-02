"""NSE delivery % and volume-quality signals for swing / long-term entries."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from analyzer.cache_utils import cached_compute
from analyzer.nse_session import is_nse_available, nse_fetch_json

IST = ZoneInfo("Asia/Kolkata")
DELIVERY_CACHE_TTL = 21_600  # 6h — EOD delivery updates once daily


@dataclass
class DeliverySnapshot:
    nse_symbol: str
    delivery_pct: float | None
    delivery_quantity: int | None
    quantity_traded: int | None
    as_of_date: str = ""
    volume_ratio: float | None = None  # session vol vs 20d avg
    price_change_pct: float | None = None  # vs prior close
    avg_delivery_5d: float | None = None
    quality: str = "unknown"  # strong | moderate | weak | speculative | unknown
    signal: str = "neutral"  # bullish | bearish | neutral
    guidance: str = ""
    flags: list[str] = field(default_factory=list)


def _parse_nse_date(raw: str) -> str:
    if not raw:
        return ""
    return str(raw).replace(" EOD", "").strip()[:16]


def fetch_nse_delivery_trade_info(nse_symbol: str) -> dict | None:
    """Latest delivery stats from NSE quote-equity trade_info section."""
    if not is_nse_available():
        return None
    sym = nse_symbol.upper().replace(".NS", "").replace(".BO", "")
    if not sym or sym.startswith("^"):
        return None
    data = nse_fetch_json(f"quote-equity?symbol={sym}&section=trade_info")
    if not isinstance(data, dict):
        return None
    return data.get("securityWiseDP") or data


def fetch_delivery_history(nse_symbol: str, days: int = 15) -> list[dict]:
    """Historical delivery rows (best-effort)."""
    if not is_nse_available():
        return []
    sym = nse_symbol.upper().replace(".NS", "").replace(".BO", "")
    end = datetime.now(IST).date()
    start = end - timedelta(days=max(days, 5) + 10)
    path = (
        f"historicalOR/delivery/volume?symbol={sym}&series=EQ"
        f"&from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}"
    )
    payload = nse_fetch_json(path)
    if not payload:
        return []
    rows = payload if isinstance(payload, list) else payload.get("data", [])
    if not isinstance(rows, list):
        return []
    return rows[-days:]


def _avg_delivery_pct(history: list[dict]) -> float | None:
    pcts: list[float] = []
    for row in history:
        val = row.get("DELIV_PER") or row.get("deliveryToTradedQuantity")
        if val is not None:
            try:
                pcts.append(float(val))
            except (TypeError, ValueError):
                continue
    if not pcts:
        return None
    tail = pcts[-5:]
    return round(sum(tail) / len(tail), 1)


def _classify_quality(
    delivery_pct: float | None,
    volume_ratio: float | None,
    price_change_pct: float | None,
    avg_delivery_5d: float | None,
) -> tuple[str, str, str, list[str]]:
    flags: list[str] = []
    if delivery_pct is None:
        return "unknown", "neutral", "Delivery data unavailable — use price/volume on chart.", flags

    if delivery_pct >= 55:
        quality = "strong"
        signal = "bullish"
        flags.append(f"High delivery {delivery_pct:.1f}% — shares moving to demat (accumulation).")
    elif delivery_pct >= 40:
        quality = "moderate"
        signal = "bullish"
        flags.append(f"Healthy delivery {delivery_pct:.1f}% — decent participation.")
    elif delivery_pct >= 25:
        quality = "weak"
        signal = "neutral"
        flags.append(f"Moderate delivery {delivery_pct:.1f}% — mixed intraday + delivery.")
    else:
        quality = "speculative"
        signal = "bearish"
        flags.append(f"Low delivery {delivery_pct:.1f}% — mostly intraday churn.")

    if volume_ratio is not None:
        if volume_ratio >= 2.0 and delivery_pct < 30:
            quality = "speculative"
            signal = "bearish"
            flags.append(
                f"Volume {volume_ratio:.1f}× average with weak delivery — speculative move."
            )
        elif volume_ratio >= 1.3 and delivery_pct >= 45:
            signal = "bullish"
            flags.append(f"Volume spike {volume_ratio:.1f}× with solid delivery — conviction.")

    if price_change_pct is not None:
        if price_change_pct > 1.5 and delivery_pct < 28:
            flags.append("Price up on low delivery — rally may fade (swing caution).")
            signal = "bearish" if quality == "speculative" else signal
        elif price_change_pct < -1.5 and delivery_pct >= 45:
            flags.append("Fall with high delivery — possible accumulation on dips (long-term watch).")
            if signal != "bearish":
                signal = "bullish"

    if avg_delivery_5d is not None and delivery_pct is not None:
        if delivery_pct > avg_delivery_5d + 8:
            flags.append(f"Delivery above 5-day avg ({avg_delivery_5d:.1f}%) — improving quality.")
        elif delivery_pct < avg_delivery_5d - 10:
            flags.append(f"Delivery below 5-day avg ({avg_delivery_5d:.1f}%) — weakening.")

    guidance = _guidance_for_quality(quality, signal)
    return quality, signal, guidance, flags


def _guidance_for_quality(quality: str, signal: str) -> str:
    if quality == "strong":
        return "Good for swing/long — move backed by delivery. Still use stop-loss."
    if quality == "moderate":
        return "Acceptable for swing with confirmation; fine for long-term adds in tranches."
    if quality == "speculative":
        return "Avoid new swing/MIS — low delivery suggests traders, not investors."
    if quality == "weak":
        return "Wait for higher delivery or breakout with volume before sizing up."
    return "Verify delivery on NSE before trading."


def build_delivery_snapshot(
    nse_symbol: str,
    df: pd.DataFrame | None = None,
    *,
    fetch_history: bool = True,
) -> DeliverySnapshot | None:
    sym = nse_symbol.upper().replace(".NS", "").replace(".BO", "")
    trade = fetch_nse_delivery_trade_info(sym)
    if not trade:
        return None

    try:
        delivery_pct = float(trade.get("deliveryToTradedQuantity"))
    except (TypeError, ValueError):
        delivery_pct = None

    dq = trade.get("deliveryQuantity")
    qt = trade.get("quantityTraded")
    as_of = _parse_nse_date(str(trade.get("secWiseDelPosDate", "")))

    volume_ratio = None
    price_change_pct = None
    if df is not None and len(df) >= 2:
        row = df.iloc[-1]
        prev = df.iloc[-2]
        vol = float(row.get("Volume", 0))
        vol_sma = float(row.get("VOL_SMA_20", 0)) if "VOL_SMA_20" in df.columns else 0
        if vol_sma > 0:
            volume_ratio = round(vol / vol_sma, 2)
        p0, p1 = float(prev["Close"]), float(row["Close"])
        if p0 > 0:
            price_change_pct = round((p1 / p0 - 1) * 100, 2)

    history = fetch_delivery_history(sym, days=12) if fetch_history else []
    avg5 = _avg_delivery_pct(history)

    quality, signal, guidance, flags = _classify_quality(
        delivery_pct, volume_ratio, price_change_pct, avg5,
    )

    return DeliverySnapshot(
        nse_symbol=sym,
        delivery_pct=round(delivery_pct, 1) if delivery_pct is not None else None,
        delivery_quantity=int(dq) if dq is not None else None,
        quantity_traded=int(qt) if qt is not None else None,
        as_of_date=as_of,
        volume_ratio=volume_ratio,
        price_change_pct=price_change_pct,
        avg_delivery_5d=avg5,
        quality=quality,
        signal=signal,
        guidance=guidance,
        flags=flags,
    )


def merge_volume_context(
    snap: DeliverySnapshot,
    volume_ratio: float | None,
    price_change_pct: float | None,
) -> DeliverySnapshot:
    quality, signal, guidance, flags = _classify_quality(
        snap.delivery_pct, volume_ratio, price_change_pct, snap.avg_delivery_5d,
    )
    return DeliverySnapshot(
        nse_symbol=snap.nse_symbol,
        delivery_pct=snap.delivery_pct,
        delivery_quantity=snap.delivery_quantity,
        quantity_traded=snap.quantity_traded,
        as_of_date=snap.as_of_date,
        volume_ratio=volume_ratio,
        price_change_pct=price_change_pct,
        avg_delivery_5d=snap.avg_delivery_5d,
        quality=quality,
        signal=signal,
        guidance=guidance,
        flags=flags,
    )


def enrich_delivery_with_stocks(
    snapshots: list[DeliverySnapshot],
    stocks: list,
) -> list[DeliverySnapshot]:
    vol_map = {
        s.nse_symbol.upper(): (getattr(s, "volume_ratio", None), getattr(s, "price_change_pct", None))
        for s in stocks
    }
    out: list[DeliverySnapshot] = []
    for snap in snapshots:
        vr, pc = vol_map.get(snap.nse_symbol.upper(), (None, None))
        if vr is not None or pc is not None:
            out.append(merge_volume_context(snap, vr, pc))
        else:
            out.append(snap)
    return out


def _fetch_one(sym: str) -> DeliverySnapshot | None:
    return build_delivery_snapshot(sym, fetch_history=True)


def fetch_delivery_batch(symbols: list[str]) -> list[DeliverySnapshot]:
    """Parallel delivery fetch with 6h cache per universe key."""
    uniq = list(dict.fromkeys(s.replace(".NS", "").upper() for s in symbols if s))
    if not uniq:
        return []

    def _factory() -> list[DeliverySnapshot]:
        out: list[DeliverySnapshot] = []
        with ThreadPoolExecutor(max_workers=6) as pool:
            futs = {pool.submit(_fetch_one, s): s for s in uniq[:50]}
            for fut in as_completed(futs):
                snap = fut.result()
                if snap:
                    out.append(snap)
        out.sort(key=lambda s: (-(s.delivery_pct or 0)))
        return out

    key = f"delivery_batch_{len(uniq)}_{uniq[0]}_{uniq[-1]}"
    return cached_compute(key, DELIVERY_CACHE_TTL, _factory)


def delivery_by_nse(snapshots: list[DeliverySnapshot]) -> dict[str, DeliverySnapshot]:
    return {s.nse_symbol.upper(): s for s in snapshots}


def delivery_note_for_horizon(snap: DeliverySnapshot | None, horizon: str) -> str:
    if not snap or snap.delivery_pct is None:
        return ""
    if horizon == "intraday" and snap.quality == "speculative":
        return f"Low delivery {snap.delivery_pct:.0f}% — MIS churn; tight stops."
    if horizon == "short" and snap.quality in ("speculative", "weak"):
        return f"Delivery {snap.delivery_pct:.0f}% — weak for swing; prefer stronger names."
    if horizon == "long" and snap.quality == "strong":
        return f"Delivery {snap.delivery_pct:.0f}% — supports long-term accumulation thesis."
    return ""


def should_downgrade_for_delivery(
    snap: DeliverySnapshot | None,
    horizon: str,
    *,
    filter_weak_delivery: bool,
) -> bool:
    if not filter_weak_delivery or not snap:
        return False
    if horizon == "intraday":
        return snap.quality == "speculative" and (snap.volume_ratio or 0) >= 1.8
    if horizon == "short":
        return snap.quality == "speculative"
    return False


def snapshot_to_dict(s: DeliverySnapshot) -> dict:
    return {
        "nse_symbol": s.nse_symbol,
        "delivery_pct": s.delivery_pct,
        "delivery_quantity": s.delivery_quantity,
        "quantity_traded": s.quantity_traded,
        "as_of_date": s.as_of_date,
        "volume_ratio": s.volume_ratio,
        "price_change_pct": s.price_change_pct,
        "avg_delivery_5d": s.avg_delivery_5d,
        "quality": s.quality,
        "signal": s.signal,
        "guidance": s.guidance,
        "flags": list(s.flags),
    }


def snapshot_from_dict(d: dict) -> DeliverySnapshot:
    return DeliverySnapshot(
        nse_symbol=d["nse_symbol"],
        delivery_pct=d.get("delivery_pct"),
        delivery_quantity=d.get("delivery_quantity"),
        quantity_traded=d.get("quantity_traded"),
        as_of_date=d.get("as_of_date", ""),
        volume_ratio=d.get("volume_ratio"),
        price_change_pct=d.get("price_change_pct"),
        avg_delivery_5d=d.get("avg_delivery_5d"),
        quality=d.get("quality", "unknown"),
        signal=d.get("signal", "neutral"),
        guidance=d.get("guidance", ""),
        flags=list(d.get("flags", [])),
    )
