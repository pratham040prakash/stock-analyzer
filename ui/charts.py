"""Plotly chart builders shared across pages."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from analyzer.global_markets import fetch_daily_history


def price_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.55, 0.22, 0.23],
        subplot_titles=("Price & Moving Averages", "MACD", "RSI"),
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    for col, name, color in [
        ("SMA_20", "SMA 20", "#42a5f5"),
        ("SMA_50", "SMA 50", "#ff7043"),
        ("SMA_200", "SMA 200", "#ab47bc"),
    ]:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df[col], name=name, line=dict(width=1.2, color=color)),
                row=1,
                col=1,
            )

    macd_col, signal_col, hist_col = "MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9"
    if hist_col in df.columns:
        colors = ["#00c853" if v >= 0 else "#d50000" for v in df[hist_col].fillna(0)]
        fig.add_trace(
            go.Bar(x=df.index, y=df[hist_col], name="MACD Hist", marker_color=colors, opacity=0.6),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df[macd_col], name="MACD", line=dict(color="#42a5f5")),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df[signal_col], name="Signal", line=dict(color="#ff7043")),
            row=2,
            col=1,
        )

    if "RSI_14" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["RSI_14"], name="RSI", line=dict(color="#7e57c2")),
            row=3,
            col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="#d50000", opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00c853", opacity=0.5, row=3, col=1)

    fig.update_layout(
        height=720,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        margin=dict(l=40, r=20, t=40, b=20),
        legend=dict(orientation="h", y=1.02),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    return fig


def equity_chart(equity: pd.Series, buy_hold_pct: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity.index,
            y=(equity - 1) * 100,
            name="Strategy",
            line=dict(color="#42a5f5", width=2),
        )
    )
    fig.add_hline(
        y=buy_hold_pct,
        line_dash="dash",
        line_color="#ff7043",
        annotation_text=f"Buy & Hold {buy_hold_pct:+.1f}%",
    )
    fig.update_layout(
        title="Strategy vs Buy & Hold",
        template="plotly_dark",
        height=400,
        yaxis_title="Return (%)",
        xaxis_title="Date",
    )
    return fig


def global_normalized_chart(symbols: list[str], labels: dict[str, str], period: str = "1mo") -> go.Figure:
    fig = go.Figure()
    for sym in symbols:
        df = fetch_daily_history(sym, period)
        if df.empty:
            continue
        norm = df["Close"] / float(df["Close"].iloc[0]) * 100
        fig.add_trace(go.Scatter(
            x=norm.index, y=norm.values,
            name=labels.get(sym, sym), mode="lines",
        ))
    fig.update_layout(
        height=400, template="plotly_dark",
        title="Global markets — normalized (100 = start)",
        yaxis_title="Indexed",
        legend=dict(orientation="h", y=1.1),
    )
    return fig
