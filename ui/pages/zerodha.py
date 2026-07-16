"""My Portfolio tab — manual entry, CSV, or Zerodha Kite."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from analyzer.advisor import generate_portfolio_advice
from analyzer.earnings_calendar import fetch_corporate_events
from analyzer.portfolio_live import (
    ensure_kite_stream_for_tracked,
    load_tracked_portfolio,
    refresh_holdings_ltp,
    sync_holdings_from_kite,
    sync_watchlist_from_kite_activity,
)
from analyzer.kite_watchlist_store import (
    load_kite_watchlist,
    parse_watchlist_text,
    save_kite_watchlist,
)
from analyzer.providers.router import is_kite_live
from analyzer.market_session import market_session_status
from analyzer.markets import format_price
from analyzer.portfolio import analyze_portfolio
from analyzer.portfolio_risk import compute_portfolio_risk
from analyzer.portfolio_store import (
    clear_saved_portfolio,
    load_saved_portfolio,
    make_manual_holding,
    portfolio_profile_key,
    save_portfolio,
)
from analyzer.zerodha import (
    ZerodhaHolding,
    ZerodhaImportResult,
    kite_to_yahoo,
    load_env_credentials,
    parse_holdings_csv,
    parse_kite_symbol_list,
)
from ui.components.broker_connect import render_portfolio_broker_gate
from ui.components.portfolio_broker_header import render_portfolio_broker_header
from ui.components.empty_states import empty_portfolio
from ui.navigation import request_nav_tab


def _persist_import(import_result: ZerodhaImportResult) -> None:
    st.session_state["zd_import"] = import_result
    if import_result.holdings:
        save_portfolio(import_result, profile=portfolio_profile_key())
    ensure_kite_stream_for_tracked(import_result, profile=portfolio_profile_key())


@st.fragment(run_every=timedelta(seconds=15))
def _render_live_portfolio_panel(profile: str) -> None:
    """Refresh Kite LTP every 15s during market hours."""
    session = market_session_status()
    if not session.get("is_open"):
        st.caption("Market closed — live prices resume at 9:15 AM IST.")
        return
    if not is_kite_live():
        st.caption("Live Kite quotes unavailable — using last synced prices.")
        return

    imp = st.session_state.get("zd_import")
    tracked = load_tracked_portfolio(imp, profile=profile, refresh_ltp=True)
    if not tracked.holdings:
        return

    st.session_state["zd_import"] = refresh_holdings_ltp(
        ZerodhaImportResult(
            holdings=[h for h in tracked.holdings if h.quantity > 0],
            errors=tracked.errors,
            source=tracked.source,
        )
    )

    rows = []
    for h in tracked.holdings:
        kind = "Holding" if h.quantity > 0 else "Watchlist"
        pnl = h.pnl
        pnl_pct = None
        if pnl is not None and h.average_price and h.quantity:
            cost = h.average_price * h.quantity
            pnl_pct = (pnl / cost * 100) if cost else None
        rows.append({
            "Type": kind,
            "Symbol": h.tradingsymbol,
            "Qty": int(h.quantity) if h.quantity else "—",
            "Avg": f"₹{h.average_price:,.2f}" if h.average_price else "—",
            "LTP": f"₹{h.last_price:,.2f}" if h.last_price else "—",
            "P&L": f"₹{pnl:,.0f}" if pnl is not None else "—",
            "P&L %": f"{pnl_pct:+.1f}%" if pnl_pct is not None else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(f"Live refresh · {session.get('time_ist', '')} · Kite WebSocket + REST")


def _render_kite_watchlist_panel(profile: str) -> None:
    st.markdown("#### Kite watchlist mirror")
    st.caption(
        "Kite **marketwatch has no API**. We auto-sync symbols from your **open positions "
        "and recent orders** after login. Paste any extra symbols from Kite marketwatch below."
    )
    existing = load_kite_watchlist(profile)
    creds = load_env_credentials()
    if creds.get("access_token"):
        if st.button("Sync watchlist from Kite activity", key="kite_wl_sync", use_container_width=True):
            with st.spinner("Reading positions & orders from Kite…"):
                added, total, errs = sync_watchlist_from_kite_activity(profile=profile)
                ensure_kite_stream_for_tracked(st.session_state.get("zd_import"), profile=profile)
                if added:
                    st.success(f"Added **{added}** symbols — **{total}** total in watchlist")
                elif total:
                    st.info(f"Watchlist up to date — **{total}** symbols")
                else:
                    st.warning("No symbols from Kite positions/orders yet.")
                for err in errs:
                    st.caption(err)
                st.rerun()
    if existing:
        st.caption(f"**{len(existing)}** watchlist symbols saved: {', '.join(s.replace('NSE:', '').replace('-EQ', '') for s in existing[:8])}"
                   + ("…" if len(existing) > 8 else ""))

    text = st.text_area(
        "Paste from Kite marketwatch",
        value="\n".join(existing) if existing else "",
        placeholder="NSE:RELIANCE-EQ\nNSE:TCS-EQ\nSBIN",
        height=100,
        key="kite_watchlist_paste",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save watchlist", key="kite_wl_save", use_container_width=True):
            syms = parse_watchlist_text(text)
            if not syms:
                st.error("No symbols found.")
            else:
                save_kite_watchlist(syms, profile=profile)
                ensure_kite_stream_for_tracked(st.session_state.get("zd_import"), profile=profile)
                st.success(f"Saved {len(syms)} watchlist symbols")
                st.rerun()
    with c2:
        if st.button("Clear watchlist", key="kite_wl_clear", use_container_width=True):
            save_kite_watchlist([], profile=profile)
            st.rerun()


def render_zerodha(period: str) -> None:
    st.subheader("My Portfolio")
    st.caption(
        "Track holdings with **qty & avg price** — works without Zerodha. "
        "Saved portfolio powers **Daily Advisor**, **Suggestions** intraday strip, and morning briefing. "
        "**Connect Zerodha** for live sync + real-time LTP."
    )

    if msg := st.session_state.pop("_portfolio_auto_sync_msg", None):
        st.success(msg)

    prof = portfolio_profile_key()
    saved = load_saved_portfolio(profile=prof)
    if saved and not st.session_state.get("zd_import"):
        st.session_state["zd_import"] = saved

    snapshot = st.session_state.get("broker_snapshot")
    render_portfolio_broker_header(snapshot)
    if render_portfolio_broker_gate(snapshot):
        return

    mode = st.radio(
        "How to add holdings",
        ["Manual entry", "Upload holdings CSV", "Paste Kite symbols"],
        horizontal=True,
    )

    if mode == "Manual entry":
        st.markdown(
            "Enter symbols like **RELIANCE**, **TCS**, or **INFY.NS** with quantity and average buy price. "
            "Click **Save portfolio** — persists across browser sessions."
        )
        existing = st.session_state.get("zd_import")
        default_rows = [
            {
                "Symbol": h.tradingsymbol,
                "Qty": int(h.quantity),
                "Avg price": h.average_price or 0.0,
            }
            for h in (existing.holdings if existing else [])
        ]
        if not default_rows:
            default_rows = [{"Symbol": "RELIANCE", "Qty": 10, "Avg price": 0.0}]

        edited = st.data_editor(
            pd.DataFrame(default_rows),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Symbol": st.column_config.TextColumn("Symbol", width="medium"),
                "Qty": st.column_config.NumberColumn("Qty", min_value=0, step=1),
                "Avg price": st.column_config.NumberColumn("Avg price (₹)", min_value=0.0, format="%.2f"),
            },
            key="portfolio_manual_editor",
        )

        if st.button("Save portfolio", type="primary", key="zd_manual_save"):
            holdings: list[ZerodhaHolding] = []
            for _, row in edited.iterrows():
                sym = str(row.get("Symbol", "")).strip()
                if not sym:
                    continue
                qty = float(row.get("Qty", 0) or 0)
                avg_raw = row.get("Avg price", 0)
                avg = float(avg_raw) if avg_raw and float(avg_raw) > 0 else None
                h = make_manual_holding(sym, qty, avg)
                if h:
                    holdings.append(h)
            if not holdings:
                st.error("Add at least one symbol with quantity > 0.")
            else:
                imp = ZerodhaImportResult(holdings=holdings, source="manual")
                _persist_import(imp)
                st.success(f"Saved {len(holdings)} holdings")

    elif mode == "Upload holdings CSV":
        st.markdown(
            "Export from **Kite** → Holdings → Download, or **Console** → Reports → Equity holdings"
        )
        uploaded = st.file_uploader("Holdings CSV", type=["csv"])
        if uploaded and st.button("Parse CSV", key="zd_csv"):
            content = uploaded.read().decode("utf-8", errors="replace")
            import_result = parse_holdings_csv(content)
            if import_result.errors and not import_result.holdings:
                st.error(import_result.errors[0])
            else:
                _persist_import(import_result)
                st.success(f"Parsed {len(import_result.holdings)} holdings from CSV")

    elif mode == "Paste Kite symbols":
        st.markdown(
            "Paste symbols from Kite (comma or newline). Examples: `NSE:RELIANCE-EQ`, `NSE:TCS-EQ`, `SBIN`"
        )
        st.info(
            "Tip: for **watchlist-only** names (not owned), use **Kite watchlist mirror** below — "
            "keeps qty at 0 instead of fake holdings."
        )
        symbols_text = st.text_area(
            "Kite symbols",
            placeholder="NSE:RELIANCE-EQ, NSE:TCS-EQ, NSE:INFY-EQ",
            height=80,
        )
        if st.button("Import symbols", key="zd_paste"):
            yahoo_syms = parse_kite_symbol_list(symbols_text)
            if not yahoo_syms:
                st.error("No symbols found.")
            else:
                import_result = ZerodhaImportResult(source="paste")
                for y in yahoo_syms:
                    base = y.replace(".NS", "").replace(".BO", "")
                    import_result.holdings.append(
                        ZerodhaHolding(
                            kite_symbol=f"NSE:{base}-EQ",
                            tradingsymbol=base,
                            exchange="NSE",
                            quantity=1,
                            yahoo_symbol=y,
                        )
                    )
                _persist_import(import_result)
                st.success(f"Imported {len(yahoo_syms)} symbols")

    import_result = st.session_state.get("zd_import")
    _render_kite_watchlist_panel(prof)

    tracked = load_tracked_portfolio(import_result, profile=prof, refresh_ltp=is_kite_live())
    if not tracked.holdings:
        empty_portfolio(key="zd_empty_portfolio")
        return

    st.divider()
    held_n = sum(1 for h in tracked.holdings if h.quantity > 0)
    watch_n = sum(1 for h in tracked.holdings if h.quantity <= 0)
    st.write(
        f"**{held_n} holdings**"
        + (f" + **{watch_n} watchlist**" if watch_n else "")
        + f" · source: {import_result.source if import_result else 'watchlist'}"
    )

    creds = load_env_credentials()
    sync_col, live_col = st.columns([1, 2])
    with sync_col:
        if creds.get("access_token"):
            if st.button("Sync from Kite now", type="primary", key="zd_sync_kite", use_container_width=True):
                with st.spinner("Synchronizing Portfolio…"):
                    synced, err = sync_holdings_from_kite()
                    if err:
                        st.warning("Unable to sync holdings right now. Try again shortly.")
                    elif synced:
                        _persist_import(synced)
                        from ui.broker.bootstrap import reset_broker_bootstrap

                        reset_broker_bootstrap()
                        st.success(f"Synced {len(synced.holdings)} holdings with live prices")
                        st.rerun()
        else:
            st.caption("Holdings sync automatically after you sign in to Zerodha.")
    with live_col:
        if is_kite_live():
            ensure_kite_stream_for_tracked(import_result, profile=prof)

    with st.expander("📡 Live prices (15s refresh)", expanded=is_kite_live() and market_session_status().get("is_open")):
        _render_live_portfolio_panel(prof)

    save_col, clear_col, advisor_col = st.columns(3)
    with save_col:
        if import_result and st.button("Re-save portfolio", key="zd_resave"):
            held = ZerodhaImportResult(
                holdings=[h for h in import_result.holdings if h.quantity > 0],
                errors=import_result.errors,
                source=import_result.source,
            )
            save_portfolio(held, profile=prof)
            st.success("Saved")
    with clear_col:
        if st.button("Clear portfolio", key="zd_clear"):
            st.session_state.pop("zd_import", None)
            st.session_state.pop("zd_analysis", None)
            clear_saved_portfolio(profile=prof)
            st.rerun()
    with advisor_col:
        if st.button("Open Daily Advisor", key="zd_daily"):
            request_nav_tab("Daily Advisor")

    preview = pd.DataFrame([
        {
            "Type": "Holding" if h.quantity > 0 else "Watchlist",
            "Kite": h.kite_symbol,
            "Yahoo": h.yahoo_symbol or kite_to_yahoo(h.kite_symbol),
            "Qty": int(h.quantity) if h.quantity else "—",
            "Avg": f"₹{h.average_price:,.2f}" if h.average_price else "—",
            "LTP": f"₹{h.last_price:,.2f}" if h.last_price else "—",
        }
        for h in tracked.holdings
    ])
    st.dataframe(preview, use_container_width=True, hide_index=True)

    if st.button("Analyze my portfolio", type="primary", key="zd_analyze"):
        ensure_kite_stream_for_tracked(import_result, profile=prof)
        if is_kite_live():
            st.caption("Kite live LTP active for holdings + watchlist")
        with st.spinner("Analyzing your holdings + watchlist…"):
            rows = analyze_portfolio(tracked, period=period)
            st.session_state["zd_analysis"] = rows

    rows = st.session_state.get("zd_analysis")
    if not rows:
        return

    st.subheader("Portfolio signals")
    table = []
    for row in rows:
        if row.error:
            table.append({
                "Kite": row.kite_symbol,
                "Stock": row.name,
                "Qty": row.quantity,
                "Signal": "ERROR",
                "Score": "—",
                "P&L": "—",
                "Note": row.error[:50],
            })
        else:
            pnl_str = f"₹{row.pnl:,.0f}" if row.pnl is not None else "—"
            qty_label = int(row.quantity) if row.quantity else "Watch"
            table.append({
                "Kite": row.kite_symbol,
                "Stock": row.name[:28],
                "Qty": qty_label,
                "Combined": row.recommendation,
                "Score": f"{row.score:+.1f}",
                "Technical": f"{row.technical_score:+.1f}",
                "Fundamental": f"{row.fundamental_score:+.1f}",
                "LTP": format_price(row.last_price, row.yahoo_symbol),
                "P&L": pnl_str,
            })

    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    total_pnl = sum(r.pnl for r in rows if r.pnl is not None)
    if any(r.pnl is not None for r in rows):
        st.metric("Total unrealized P&L", f"₹{total_pnl:,.0f}")

    buys = [r for r in rows if not r.error and r.recommendation in ("STRONG BUY", "BUY")]
    sells = [r for r in rows if not r.error and r.recommendation in ("STRONG SELL", "SELL")]
    holds = [r for r in rows if not r.error and r.recommendation == "HOLD"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Buy signals", len(buys))
    c2.metric("Hold", len(holds))
    c3.metric("Sell signals", len(sells))

    if sells:
        st.warning(
            "**Consider reviewing (bearish signals):** "
            + ", ".join(f"{r.kite_symbol} ({r.score:+.0f})" for r in sells)
        )
    if buys:
        st.success(
            "**Strongest in portfolio:** "
            + ", ".join(f"{r.kite_symbol} ({r.score:+.0f})" for r in buys[:5])
        )

    try:
        risk = compute_portfolio_risk(rows, period=period)
        st.divider()
        st.subheader("Portfolio risk")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Portfolio value", f"₹{risk.total_value:,.0f}")
        r2.metric("Top-5 concentration", f"{risk.top5_concentration_pct:.0f}%")
        r3.metric("Largest holding", risk.largest_holding)
        r4.metric("Portfolio β vs Nifty", f"{risk.portfolio_beta:.2f}" if risk.portfolio_beta else "—")
        st.caption(risk.beta_note)
        if risk.sector_weights:
            sector_df = pd.DataFrame(
                [{"Sector": k, "Weight %": f"{v:.1f}"} for k, v in risk.sector_weights.items()]
            )
            st.dataframe(sector_df, use_container_width=True, hide_index=True)
        for warning in risk.warnings:
            st.warning(warning)

        symbols = [r.yahoo_symbol for r in rows if not r.error]
        events = fetch_corporate_events(symbols[:15], market="india")
        if events:
            st.subheader("Upcoming events (earnings / ex-div)")
            ev_df = pd.DataFrame([
                {"Symbol": e.symbol, "Event": e.event_type, "Date": e.date, "Detail": e.detail}
                for e in events[:12]
            ])
            st.dataframe(ev_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.caption(f"Risk summary unavailable: {exc}")

    st.divider()
    st.subheader("Portfolio Suggestions")
    st.markdown(generate_portfolio_advice(rows))
    st.caption("For **today's action** on each holding, open the **Daily Advisor** tab.")
