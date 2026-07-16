"""Reusable empty states with primary CTAs."""

from __future__ import annotations

import streamlit as st

from ui.navigation import request_nav_tab


def empty_state(
    title: str,
    body: str,
    *,
    cta_label: str | None = None,
    cta_tab: str | None = None,
    cta_kwargs: dict | None = None,
    key: str = "empty_cta",
) -> None:
    st.markdown(f"##### {title}")
    st.caption(body)
    if cta_label and cta_tab:
        if st.button(cta_label, type="primary", key=key):
            request_nav_tab(cta_tab, **(cta_kwargs or {}))


def empty_connect_kite(*, key: str = "empty_kite") -> None:
    empty_state(
        "Broker not connected",
        "Sign in to Zerodha to sync holdings and live prices.",
        cta_label="Open My Portfolio",
        cta_tab="My Portfolio",
        key=key,
    )


def empty_quick_scan(*, key: str = "empty_scan") -> None:
    empty_state(
        "No suggestions yet",
        "Run **Quick scan** after market close to save tomorrow's top 5 with Entry · Stop · Target.",
        cta_label="Go to Quick scan",
        cta_tab="Suggestions",
        cta_kwargs={"intraday_focus_watchlist": True},
        key=key,
    )


def empty_portfolio(*, key: str = "empty_portfolio") -> None:
    empty_state(
        "Portfolio empty",
        "Import holdings from Kite, CSV, or manual entry to power Daily Advisor and Alpha portfolio mode.",
        cta_label="Open My Portfolio",
        cta_tab="My Portfolio",
        key=key,
    )
