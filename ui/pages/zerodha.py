"""Zerodha Portfolio tab."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.advisor import generate_portfolio_advice
from analyzer.earnings_calendar import fetch_corporate_events
from analyzer.kite_stream import start_kite_ticker_for_holdings
from analyzer.markets import format_price
from analyzer.portfolio import analyze_portfolio
from analyzer.portfolio_risk import compute_portfolio_risk
from analyzer.zerodha import (
    ZerodhaHolding,
    ZerodhaImportResult,
    exchange_request_token,
    fetch_holdings_from_kite,
    get_kite_login_url,
    kite_to_yahoo,
    load_env_credentials,
    parse_holdings_csv,
    parse_kite_symbol_list,
    save_access_token_to_env,
    zerodha_setup_help,
)
from ui.components.kite_auth import handle_kite_redirect


def render_zerodha(period: str) -> None:
    st.subheader("Zerodha Portfolio Analyzer")
    st.caption("Import holdings from Kite API or CSV — get buy/sell signals on your actual portfolio")

    handle_kite_redirect()

    mode = st.radio(
        "Import method",
        ["Paste Kite symbols", "Upload holdings CSV", "Kite Connect API"],
        horizontal=True,
    )

    if mode == "Paste Kite symbols":
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
                st.session_state["zd_import"] = import_result
                st.success(f"Imported {len(yahoo_syms)} symbols")

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
                st.session_state["zd_import"] = import_result
                st.success(f"Parsed {len(import_result.holdings)} holdings from CSV")

    else:
        with st.expander("How to set up Kite Connect API", expanded=False):
            st.markdown(zerodha_setup_help())

        creds = load_env_credentials()
        api_key = st.text_input("API Key", value=creds["api_key"], type="password")
        api_secret = st.text_input("API Secret", value=creds["api_secret"], type="password")

        if api_key:
            login_url = get_kite_login_url(api_key)
            st.markdown(
                f"**Step 1:** Keep this app running, then "
                f"[**Login to Zerodha**]({login_url}) — you'll be redirected back here automatically."
            )
            st.caption("Request tokens expire in ~2 minutes. The app auto-saves your access token on redirect.")

        request_token = st.text_input(
            "Or paste request_token manually (if redirect didn't work)",
            placeholder="From URL: request_token=...",
        )
        if request_token and st.button("Generate access token", key="zd_token"):
            try:
                token = exchange_request_token(api_key, api_secret, request_token.strip())
                save_access_token_to_env(token)
                st.session_state["kite_access_token"] = token
                st.success("Access token saved to `.env` (valid until ~6 AM IST tomorrow)")
            except Exception as exc:
                st.error(f"Token exchange failed: {exc}. Log in again — tokens are single-use.")

        access_token = st.text_input(
            "Access token",
            value=creds["access_token"],
            type="password",
            help="From .env or generated above",
        )
        if st.button("Fetch live holdings from Kite", type="primary", key="zd_fetch"):
            with st.spinner("Connecting to Zerodha Kite..."):
                import_result = fetch_holdings_from_kite(api_key, access_token)
                if import_result.errors and not import_result.holdings:
                    st.error(import_result.errors[0])
                else:
                    st.session_state["zd_import"] = import_result
                    st.success(f"Fetched {len(import_result.holdings)} holdings from Kite")

    import_result = st.session_state.get("zd_import")
    if not import_result or not import_result.holdings:
        st.info("Import your Zerodha holdings using one of the methods above.")
        return

    st.divider()
    st.write(f"**{len(import_result.holdings)} holdings** ready · source: {import_result.source}")

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
        with st.spinner("Analyzing your Zerodha holdings..."):
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
        st.metric("Total unrealized P&L (from Zerodha)", f"₹{total_pnl:,.0f}")

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
