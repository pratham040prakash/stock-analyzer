"""My Portfolio tab — manual entry, CSV, or Zerodha Kite."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.advisor import generate_portfolio_advice
from analyzer.earnings_calendar import fetch_corporate_events
from analyzer.kite_stream import start_kite_ticker_for_holdings
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
    fetch_holdings_from_kite,
    kite_to_yahoo,
    load_env_credentials,
    parse_holdings_csv,
    parse_kite_symbol_list,
)
from ui.components.kite_auth import handle_kite_redirect
from ui.components.kite_connect import render_kite_connect
from ui.navigation import request_nav_tab


def _persist_import(import_result: ZerodhaImportResult) -> None:
    st.session_state["zd_import"] = import_result
    if import_result.holdings:
        save_portfolio(import_result, profile=portfolio_profile_key())


def render_zerodha(period: str) -> None:
    st.subheader("My Portfolio")
    st.caption(
        "Track holdings with **qty & avg price** — works without Zerodha. "
        "Saved portfolio powers **Daily Advisor** and morning briefing."
    )

    profile = st.text_input(
        "Your profile name (use your initials on shared app)",
        value=st.session_state.get("portfolio_profile", ""),
        placeholder="e.g. pratham",
        key="portfolio_profile_input",
    )
    if profile.strip():
        st.session_state["portfolio_profile"] = profile.strip()

    prof = portfolio_profile_key()
    saved = load_saved_portfolio(profile=prof)
    if saved and not st.session_state.get("zd_import"):
        st.session_state["zd_import"] = saved

    handle_kite_redirect()

    mode = st.radio(
        "How to add holdings",
        ["Manual entry", "Upload holdings CSV", "Paste Kite symbols", "Kite Connect API"],
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

    else:
        render_kite_connect(key_prefix="portfolio_kite")
        st.divider()

        creds = load_env_credentials()
        access_token = creds["access_token"]
        if st.button("Fetch live holdings from Kite", type="primary", key="zd_fetch"):
            with st.spinner("Connecting to Zerodha Kite..."):
                import_result = fetch_holdings_from_kite(creds["api_key"], access_token)
                if import_result.errors and not import_result.holdings:
                    st.error(import_result.errors[0])
                else:
                    _persist_import(import_result)
                    st.success(f"Fetched {len(import_result.holdings)} holdings from Kite")

    import_result = st.session_state.get("zd_import")
    if not import_result or not import_result.holdings:
        st.info("Add holdings using **Manual entry** (no broker needed) or import from CSV / Kite.")
        return

    st.divider()
    st.write(f"**{len(import_result.holdings)} holdings** ready · source: {import_result.source}")

    save_col, clear_col, advisor_col = st.columns(3)
    with save_col:
        if st.button("Re-save portfolio", key="zd_resave"):
            save_portfolio(import_result, profile=prof)
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
            "Kite": h.kite_symbol,
            "Yahoo": h.yahoo_symbol or kite_to_yahoo(h.kite_symbol),
            "Qty": h.quantity,
            "Avg": f"₹{h.average_price:,.2f}" if h.average_price else "—",
        }
        for h in import_result.holdings
    ])
    st.dataframe(preview, use_container_width=True, hide_index=True)

    if st.button("Analyze my portfolio", type="primary", key="zd_analyze"):
        syms = [h.kite_symbol for h in import_result.holdings]
        if start_kite_ticker_for_holdings(syms):
            st.caption("Kite WebSocket live LTP active for your holdings")
        with st.spinner("Analyzing your holdings..."):
            rows = analyze_portfolio(import_result, period=period)
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
            table.append({
                "Kite": row.kite_symbol,
                "Stock": row.name[:28],
                "Qty": int(row.quantity),
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
