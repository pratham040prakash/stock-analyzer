"""Unified Home tab — default landing for daily + wealth workflow."""

from __future__ import annotations

import streamlit as st

from analyzer.intraday_beginner_tips import DEFAULT_MAX_CONCURRENT_TRADES
from analyzer.intraday_prefs import load_intraday_prefs
from ui.components.unified_hub import render_unified_hub


def render_unified_home(market: str, *, period: str = "1y") -> None:
    prefs = load_intraday_prefs()
    max_trades = 1 if prefs.beginner_mode else prefs.max_trades
    max_trades = max(1, min(max_trades, DEFAULT_MAX_CONCURRENT_TRADES))
    render_unified_hub(market, period=period, max_trades=max_trades)
