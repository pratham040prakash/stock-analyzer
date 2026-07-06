"""Intraday chart builder."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

if TYPE_CHECKING:
    from analyzer.trade_ladder import TradeLadder


def _add_plan_hlines(
    fig: go.Figure,
    ladder: TradeLadder,
    *,
    row: int = 1,
    col: int = 1,
    price_decimals: int = 0,
) -> None:
    """Overlay entry, stop, and T1/T2/T3 from the MIS ladder."""
    fmt = f",.{price_decimals}f" if price_decimals else ",.0f"
    levels = [
        (ladder.initial_stop, "Stop", "#ff5252", "solid", 2),
        (ladder.entry, "Entry", "#ffeb3b", "solid", 2),
        (ladder.targets[0], "T1", "#00e676", "dash", 1.5),
        (ladder.targets[1], "T2", "#69f0ae", "dash", 1.5),
        (ladder.targets[2], "T3", "#b9f6ca", "dash", 1.5),
    ]
    for y, label, color, dash, width in levels:
        fig.add_hline(
            y=y,
            line_dash=dash,
            line_color=color,
            line_width=width,
            opacity=0.9,
            row=row,
            col=col,
            annotation_text=f"{label} ₹{y:{fmt}}",
            annotation_position="right",
            annotation_font_size=10,
            annotation_font_color=color,
        )


def intraday_chart(
    df: pd.DataFrame,
    analysis,
    *,
    ladder: TradeLadder | None = None,
) -> go.Figure:
    """Candlestick + VWAP + EMAs + volume; optional MIS plan levels."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.72, 0.28],
        subplot_titles=("Intraday Price", "Volume"),
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

    if "VWAP" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["VWAP"], name="VWAP",
                line=dict(color="#ffeb3b", width=2, dash="dot"),
            ),
            row=1, col=1,
        )

    for col, name, color in [("EMA_9", "EMA 9", "#42a5f5"), ("EMA_21", "EMA 21", "#ff7043")]:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df[col], name=name, line=dict(width=1.2, color=color)),
                row=1, col=1,
            )

    # Opening range box
    fig.add_hline(
        y=analysis.opening_range_high, line_dash="dash", line_color="#00c853",
        opacity=0.7, row=1, col=1,
        annotation_text="OR High",
    )
    fig.add_hline(
        y=analysis.opening_range_low, line_dash="dash", line_color="#d50000",
        opacity=0.7, row=1, col=1,
        annotation_text="OR Low",
    )

    if ladder is not None:
        _add_plan_hlines(fig, ladder, row=1, col=1)

    colors = ["#00c853" if c >= o else "#d50000" for o, c in zip(df["Open"], df["Close"])]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=colors, opacity=0.6),
        row=2, col=1,
    )

    fig.update_layout(
        height=560,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=40, r=20, t=40, b=20),
        legend=dict(orientation="h", y=1.02),
    )
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Vol", row=2, col=1)
    return fig
