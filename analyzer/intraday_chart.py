"""Intraday chart builder."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def intraday_chart(df: pd.DataFrame, analysis) -> go.Figure:
    """Candlestick + VWAP + EMAs + volume for intraday session."""
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
