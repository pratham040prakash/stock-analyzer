"""Intraday option premium charts with T1/T2/T3 ladder levels."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analyzer.intraday_chart import _add_plan_hlines
from analyzer.providers.types import IntradayMeta
from analyzer.trade_ladder import OptionsLadder, TradeLadder

IST = ZoneInfo("Asia/Kolkata")

_INDEX_YAHOO = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
}

KITE_INTERVAL = {
    "1m": "minute",
    "5m": "5minute",
    "15m": "15minute",
}

# Long-option premium: buying CE/PE is always a long-premium position (not equity SHORT).
PREMIUM_LADDER_SIDE = "LONG"


def _ladder_as_trade(ladder: OptionsLadder) -> TradeLadder:
    """Map options premium ladder to TradeLadder for shared chart helpers."""
    return TradeLadder(
        side=PREMIUM_LADDER_SIDE,
        entry=ladder.entry,
        initial_stop=ladder.initial_stop,
        targets=ladder.targets,
        partials=ladder.partials,
        stops_after=ladder.stops_after,
    )


def options_premium_chart(
    df: pd.DataFrame,
    ladder: OptionsLadder,
    *,
    title: str = "Option premium",
    price_decimals: int = 2,
) -> go.Figure:
    """Premium candlestick with entry / stop / T1/T2/T3 lines."""
    fig = make_subplots(
        rows=2 if "Volume" in df.columns and df["Volume"].sum() > 0 else 1,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.78, 0.22] if "Volume" in df.columns and df["Volume"].sum() > 0 else [1.0],
        subplot_titles=(title, "Volume") if "Volume" in df.columns and df["Volume"].sum() > 0 else (title,),
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Premium",
        ),
        row=1,
        col=1,
    )

    trade_ladder = _ladder_as_trade(ladder)
    _add_plan_hlines(fig, trade_ladder, row=1, col=1, price_decimals=price_decimals)

    if "Volume" in df.columns and df["Volume"].sum() > 0:
        colors = ["#00c853" if c >= o else "#d50000" for o, c in zip(df["Open"], df["Close"])]
        fig.add_trace(
            go.Bar(x=df.index, y=df["Volume"], name="Vol", marker_color=colors, opacity=0.5),
            row=2,
            col=1,
        )

    fig.update_layout(
        height=480,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=40, r=20, t=40, b=20),
        legend=dict(orientation="h", y=1.02),
    )
    fig.update_yaxes(title_text="Premium (₹)", row=1, col=1, tickformat=f".{price_decimals}f")
    if "Volume" in df.columns and df["Volume"].sum() > 0:
        fig.update_yaxes(title_text="Vol", row=2, col=1)
    return fig


def index_context_chart(
    df: pd.DataFrame,
    *,
    strike: float,
    spot: float,
    title: str,
) -> go.Figure:
    """Index spot candles with strike line when premium history unavailable."""
    fig = make_subplots(rows=1, cols=1, subplot_titles=(title,))
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Index",
        ),
        row=1,
        col=1,
    )
    fig.add_hline(
        y=strike,
        line_dash="dot",
        line_color="#ffeb3b",
        annotation_text=f"Strike ₹{strike:,.0f}",
        row=1,
        col=1,
    )
    fig.add_hline(
        y=spot,
        line_dash="solid",
        line_color="#42a5f5",
        opacity=0.6,
        annotation_text=f"Spot ₹{spot:,.0f}",
        row=1,
        col=1,
    )
    fig.update_layout(
        height=360,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=40, r=20, t=40, b=20),
    )
    fig.update_yaxes(title_text="Index (₹)", row=1, col=1)
    return fig


def _kite_premium_bars(
    token: int,
    interval: str,
) -> pd.DataFrame | None:
    from analyzer.zerodha import get_kite_client

    if interval not in KITE_INTERVAL:
        return None
    kite = get_kite_client()
    if kite is None:
        return None

    now = datetime.now(IST)
    lookback = timedelta(days=5 if interval == "1m" else 30)
    from_dt = now - lookback
    try:
        raw = kite.historical_data(
            token,
            from_dt.replace(tzinfo=None),
            now.replace(tzinfo=None),
            KITE_INTERVAL[interval],
            continuous=False,
            oi=False,
        )
    except Exception:
        return None
    if not raw:
        return None

    df = pd.DataFrame(raw)
    df = df.rename(
        columns={
            "date": "Datetime",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    if "Datetime" not in df.columns and "date" in df.columns:
        df["Datetime"] = df["date"]
    df["Datetime"] = pd.to_datetime(df["Datetime"])
    if df["Datetime"].dt.tz is None:
        df["Datetime"] = df["Datetime"].dt.tz_localize(IST)
    else:
        df["Datetime"] = df["Datetime"].dt.tz_convert(IST)
    df = df.set_index("Datetime")[["Open", "High", "Low", "Close", "Volume"]]
    today = now.date()
    session = df[df.index.date == today]
    if session.empty:
        last_date = df.index.date[-1]
        session = df[df.index.date == last_date]
    session = session.between_time("09:15", "15:30")
    return session if not session.empty else None


def fetch_option_premium_intraday(
    *,
    fno_symbol: str,
    strike: float,
    expiry: str,
    option_type: str,
    interval: str = "5m",
) -> tuple[pd.DataFrame, IntradayMeta] | None:
    """Intraday premium OHLCV via Kite NFO (requires token + market data)."""
    from analyzer.options_watchlist_history import resolve_kite_nfo_option

    resolved = resolve_kite_nfo_option(fno_symbol, strike, expiry, option_type)
    if not resolved:
        return None
    tradingsymbol, token = resolved
    session = _kite_premium_bars(token, interval)
    if session is None or session.empty:
        return None

    today = session.index.date[-1]
    meta = IntradayMeta(
        symbol=f"NFO:{tradingsymbol}",
        interval=interval,
        session_date=str(today),
        bars=len(session),
        source="Kite NFO",
        market={},
        lag_note="Live option premium candles (Kite Connect + NFO data).",
    )
    return session, meta


def ladder_for_pick(pick) -> OptionsLadder:
    from analyzer.trade_ladder import build_options_ladder

    entry = float(pick.premium or 0)
    if entry <= 0:
        return build_options_ladder(0.0)
    t2 = getattr(pick, "target2_premium", None)
    t3 = getattr(pick, "target3_premium", None)
    stop = float(pick.stop_premium or 0)
    target = float(pick.target_premium or 0)
    if t2 and t3 and target:
        return build_options_ladder(
            entry,
            stop_mult=stop / entry if stop else 0.65,
            target_mults=(target / entry, t2 / entry, t3 / entry),
        )
    return build_options_ladder(entry, stop_mult=stop / entry if stop else 0.65)
