"""Daily Advisor tab — holdings briefing."""
# APEX-012-LIFECYCLE: QUARANTINED

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from analyzer.daily_advisor import (
    DailyBriefing,
    build_daily_briefing,
    load_today_briefing,
    save_briefing,
)
from analyzer.portfolio_live import load_tracked_portfolio
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key, save_portfolio
from analyzer.zerodha import (
    fetch_holdings_from_kite,
    load_env_credentials,
    parse_holdings_csv,
    zerodha_setup_help,
)
from ui.navigation import request_nav_tab


def run_and_show_briefing(import_result, period: str) -> None:
    tracked = load_tracked_portfolio(import_result, profile=portfolio_profile_key())
    with st.spinner("Building daily briefing (holdings + watchlist + short/long picks)..."):
        briefing = build_daily_briefing(tracked, period=period)
        save_briefing(briefing)
    display_daily_briefing(briefing)


@st.fragment(run_every=timedelta(hours=6))
def daily_briefing_auto(period: str) -> None:
    import_result = st.session_state.get("zd_import")
    tracked = load_tracked_portfolio(import_result, profile=portfolio_profile_key())
    if not tracked.holdings:
        return
    with st.spinner("Refreshing daily briefing..."):
        briefing = build_daily_briefing(tracked, period=period)
        save_briefing(briefing)
    display_daily_briefing(briefing)


def display_daily_briefing(briefing: DailyBriefing) -> None:
    st.caption(f"Generated: **{briefing.generated_at}**")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Holdings reviewed", briefing.holdings_count)
    m2.metric("Watchlist", briefing.watchlist_count)
    m3.metric("Market", briefing.market_verdict[:24])
    m4.metric("Global bias", briefing.global_bias)
    m5.metric("Short-term ideas", len(briefing.short_term_picks))

    st.markdown(briefing.summary)

    if briefing.priority_actions:
        st.subheader("Priority actions today")
        for action in briefing.priority_actions:
            st.markdown(f"- {action}")

    st.divider()
    held = [h for h in briefing.holdings if h.quantity > 0]
    watch = [h for h in briefing.holdings if h.quantity <= 0]

    st.subheader("Your holdings — what to do")
    if held:
        rows = []
        for holding in held:
            rows.append({
                "Stock": holding.name[:30],
                "Kite": holding.kite_symbol,
                "Qty": int(holding.quantity),
                "P&L %": f"{holding.pnl_pct:+.1f}" if holding.pnl_pct is not None else "—",
                "Weight %": f"{holding.portfolio_weight_pct:.1f}" if holding.portfolio_weight_pct else "—",
                "Today": holding.today_action,
                "Short-term": holding.short_term,
                "Long-term": holding.long_term,
                "Score": f"{holding.combined_score:+.0f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("No delivery holdings — see watchlist insights below.")

    if watch:
        st.subheader("Watchlist insights — what to watch today")
        wrows = []
        for holding in watch:
            wrows.append({
                "Stock": holding.name[:30],
                "Kite": holding.kite_symbol,
                "LTP": f"₹{holding.last_price:,.2f}" if holding.last_price else "—",
                "Today": holding.today_action,
                "Short-term": holding.short_term,
                "Long-term": holding.long_term,
                "Score": f"{holding.combined_score:+.0f}",
                "Reason": holding.today_reason[:60],
            })
        st.dataframe(pd.DataFrame(wrows), use_container_width=True, hide_index=True)

    with st.expander("Detailed reasons per holding"):
        for holding in briefing.holdings:
            if holding.error:
                st.error(f"**{holding.kite_symbol}**: {holding.error}")
                continue
            st.markdown(
                f"**{holding.name}** (`{holding.kite_symbol}`) — **{holding.today_action}**\n\n"
                f"- {holding.today_reason}\n"
                f"- Short-term: {holding.short_term}\n"
                f"- Long-term: {holding.long_term}\n"
                f"- Scores: combined {holding.combined_score:+.0f} · tech {holding.technical_score:+.0f} · "
                f"fund {holding.fundamental_score:+.0f}"
            )

    st.divider()
    col_s, col_l = st.columns(2)

    with col_s:
        st.subheader("Short-term picks (2–8 weeks)")
        st.caption("Momentum + intraday — stocks **not** in your portfolio")
        if briefing.short_term_picks:
            for pick in briefing.short_term_picks:
                st.markdown(
                    f"**{pick.name}** (`{pick.symbol}`) · ₹{pick.price:,.0f} · **{pick.action}** "
                    f"(score {pick.score:+.0f})\n\n{pick.reason}"
                )
        else:
            st.caption("No strong short-term setups outside your holdings today.")

    with col_l:
        st.subheader("Long-term picks (1–3 years)")
        st.caption("Quality fundamentals — accumulate on dips")
        if briefing.long_term_picks:
            for pick in briefing.long_term_picks:
                st.markdown(
                    f"**{pick.name}** (`{pick.symbol}`) · ₹{pick.price:,.0f} · **{pick.action}** "
                    f"(score {pick.score:+.0f})\n\n{pick.reason}"
                )
        else:
            st.caption("No new long-term ideas today — you may already hold quality names.")

    if briefing.errors:
        with st.expander("Warnings"):
            for err in briefing.errors:
                st.caption(err)

    st.caption(
        "Briefing saved to `data/daily_briefing_YYYY-MM-DD.json`. "
        "Re-run each morning before market open. Not financial advice."
    )


def render_daily_advisor(period: str) -> None:
    st.subheader("Daily Advisor — What to do today")
    st.markdown(
        "Reviews **your saved portfolio** every day: **today's action**, **short-term** swing view, "
        "**long-term** quality view, plus **new stock ideas** you don't already own."
    )

    if not st.session_state.get("zd_import"):
        saved = load_saved_portfolio(profile=portfolio_profile_key())
        if saved:
            st.session_state["zd_import"] = saved

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Fetch holdings from Kite", key="daily_kite_fetch"):
            creds = load_env_credentials()
            with st.spinner("Fetching from Zerodha..."):
                import_result = fetch_holdings_from_kite(creds["api_key"], creds["access_token"])
                if import_result.holdings:
                    st.session_state["zd_import"] = import_result
                    save_portfolio(import_result, profile=portfolio_profile_key())
                    st.success(f"Loaded {len(import_result.holdings)} holdings")
                else:
                    st.error(import_result.errors[0] if import_result.errors else "No holdings")

    with c2:
        uploaded = st.file_uploader("Or upload holdings CSV", type=["csv"], key="daily_csv")
        if uploaded and st.button("Load CSV", key="daily_csv_btn"):
            content = uploaded.read().decode("utf-8", errors="replace")
            import_result = parse_holdings_csv(content)
            if import_result.holdings:
                st.session_state["zd_import"] = import_result
                save_portfolio(import_result, profile=portfolio_profile_key())
                st.success(f"Loaded {len(import_result.holdings)} holdings")
            else:
                st.error(import_result.errors[0] if import_result.errors else "Parse failed")

    with c3:
        if st.button("Open My Portfolio", key="daily_go_portfolio"):
            request_nav_tab("My Portfolio")
        st.caption("Or add holdings in **My Portfolio** (manual entry — no broker needed)")

    import_result = st.session_state.get("zd_import")
    tracked = load_tracked_portfolio(import_result, profile=portfolio_profile_key())
    if not tracked.holdings:
        st.info(
            "Add holdings in **My Portfolio** (manual entry works without Zerodha), "
            "sync from **Kite**, or paste **watchlist symbols**. Then click **Generate today's briefing**."
        )
        with st.expander("Kite Connect setup"):
            st.markdown(zerodha_setup_help())
        return

    held_n = sum(1 for h in tracked.holdings if h.quantity > 0)
    watch_n = sum(1 for h in tracked.holdings if h.quantity <= 0)
    st.caption(
        f"**{held_n} holdings**"
        + (f" + **{watch_n} watchlist**" if watch_n else "")
        + f" · source: {import_result.source if import_result else 'watchlist'}"
    )

    auto = st.checkbox("Auto-refresh briefing (every 6 hours)", value=True, key="daily_auto")
    if st.button("Generate today's briefing", type="primary", key="daily_run"):
        run_and_show_briefing(import_result, period)
    elif auto:
        daily_briefing_auto(period)
    else:
        cached = load_today_briefing()
        if cached:
            st.caption(f"Cached briefing from {cached.get('generated_at', 'today')}")
            for line in cached.get("priority_actions", []):
                st.markdown(f"- {line}")
            if st.button("Regenerate full briefing", key="daily_regen"):
                run_and_show_briefing(import_result, period)
        else:
            st.info("Click **Generate today's briefing** to analyze holdings, watchlist, and market picks.")
