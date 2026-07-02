"""Backtest tab with optional walk-forward validation."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.backtest import ZERODHA_COST_PRESET, run_backtest, run_walk_forward
from analyzer.data import fetch_benchmark, fetch_stock_data
from analyzer.indicators import add_indicators
from analyzer.markets import format_price, is_india_market
from ui.charts import equity_chart


def render_backtest(market: str, period: str) -> None:
    default = "RELIANCE" if is_india_market(market) else "AAPL"
    if "bt_ticker" not in st.session_state:
        st.session_state["bt_ticker"] = default
    ticker = st.text_input("Ticker", key="bt_ticker").strip()
    bt_period = st.selectbox(
        "Backtest period",
        options=["1y", "2y", "5y"],
        index=1,
        help="Use 2y+ for reliable SMA-200 warm-up and walk-forward folds",
    )
    use_zerodha_costs = st.checkbox(
        "Use Zerodha cost preset (0.03% + 0.05% slippage/side)",
        value=True,
        key="bt_zerodha_costs",
    )
    compare_nifty = st.checkbox("Compare vs Nifty 50 benchmark", value=is_india_market(market), key="bt_nifty")
    walk_forward = st.checkbox(
        "Run walk-forward validation (out-of-sample folds)",
        value=False,
        key="bt_walk_forward",
        help="Splits history into train/test folds to reduce overfitting",
    )
    col1, col2 = st.columns(2)
    buy_threshold = col1.slider("Buy threshold (score)", 10, 50, 20)
    sell_threshold = col2.slider("Sell threshold (score)", -50, -10, -20)
    run_btn = st.button("Run Backtest", type="primary", key="backtest_run")

    if not run_btn:
        st.markdown(
            """
            Simulates a **long-only** strategy:
            - **Buy** when composite score ≥ buy threshold
            - **Sell** when score ≤ sell threshold
            - Compares against buy-and-hold
            - Optional **walk-forward** shows per-fold out-of-sample returns
            """
        )
        return

    with st.spinner(f"Backtesting {ticker} over {bt_period}..."):
        try:
            df, info = fetch_stock_data(ticker, period=bt_period, market=market)
            df = add_indicators(df)
            comm = ZERODHA_COST_PRESET["commission_pct"] if use_zerodha_costs else 0.0
            slip = ZERODHA_COST_PRESET["slippage_pct"] if use_zerodha_costs else 0.0
            bench_df = None
            if compare_nifty and is_india_market(market):
                bench_df, _ = fetch_benchmark(market, bt_period)
            bt = run_backtest(
                df, info["symbol"], buy_threshold, sell_threshold,
                commission_pct=comm, slippage_pct=slip, benchmark_df=bench_df,
            )
            wf = None
            if walk_forward:
                wf = run_walk_forward(
                    df, info["symbol"],
                    buy_threshold=buy_threshold,
                    sell_threshold=sell_threshold,
                    benchmark_df=bench_df,
                )
        except Exception as exc:
            st.error(f"Backtest failed: {exc}")
            return

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Strategy Return", f"{bt.strategy_return_pct:+.2f}%")
    m2.metric("Buy & Hold", f"{bt.buy_hold_return_pct:+.2f}%")
    if bt.benchmark_return_pct is not None:
        m3.metric("Nifty B&H", f"{bt.benchmark_return_pct:+.2f}%")
    else:
        m3.metric("Nifty B&H", "—")
    m4.metric("Win Rate", f"{bt.win_rate_pct:.1f}%", help=f"{bt.winning_trades}/{bt.total_trades} trades")
    m5.metric("Max Drawdown", f"-{bt.max_drawdown_pct:.2f}%")

    alpha = bt.strategy_return_pct - bt.buy_hold_return_pct
    if bt.alpha_vs_benchmark_pct is not None:
        if bt.alpha_vs_benchmark_pct > 0:
            st.success(
                f"Strategy beat Nifty by **{bt.alpha_vs_benchmark_pct:+.2f}%** "
                f"(vs stock buy-hold {alpha:+.2f}%)."
            )
        else:
            st.warning(f"Strategy lagged Nifty by **{bt.alpha_vs_benchmark_pct:.2f}%**.")
    elif alpha > 0:
        st.success(f"Strategy outperformed buy-and-hold by **{alpha:+.2f}%** over the period.")
    else:
        st.warning(f"Strategy underperformed buy-and-hold by **{alpha:.2f}%** over the period.")

    if wf:
        st.subheader("Walk-forward validation")
        w1, w2, w3 = st.columns(3)
        w1.metric("Avg OOS return", f"{wf.avg_test_return_pct:+.2f}%")
        if wf.avg_test_alpha_pct is not None:
            w2.metric("Avg OOS alpha vs Nifty", f"{wf.avg_test_alpha_pct:+.2f}%")
        else:
            w2.metric("Avg OOS alpha vs Nifty", "—")
        w3.metric("Profitable folds", f"{wf.profitable_folds}/{len(wf.folds)}")
        fold_rows = [
            {
                "Fold": fold.fold,
                "Train bars": fold.train_bars,
                "Test bars": fold.test_bars,
                "Train return": f"{fold.train_return_pct:+.2f}%",
                "OOS return": f"{fold.test_return_pct:+.2f}%",
                "OOS alpha": (
                    f"{fold.test_alpha_pct:+.2f}%" if fold.test_alpha_pct is not None else "—"
                ),
            }
            for fold in wf.folds
        ]
        st.dataframe(pd.DataFrame(fold_rows), use_container_width=True, hide_index=True)
        st.caption(
            "Walk-forward trains on earlier bars and tests on the next segment — "
            "stronger signal than a single in-sample backtest."
        )

    if not bt.equity_curve.empty:
        st.plotly_chart(equity_chart(bt.equity_curve, bt.buy_hold_return_pct), use_container_width=True)

    if bt.trades:
        st.subheader("Trade Log")
        trade_rows = [
            {
                "Entry": trade.entry_date.strftime("%Y-%m-%d"),
                "Exit": trade.exit_date.strftime("%Y-%m-%d") if trade.exit_date else "—",
                "Entry Price": format_price(trade.entry_price, info["symbol"]),
                "Exit Price": format_price(trade.exit_price, info["symbol"]) if trade.exit_price else "—",
                "Return": f"{trade.return_pct:+.2f}%" if trade.return_pct is not None else "—",
                "Entry Signal": trade.entry_signal,
                "Exit Signal": trade.exit_signal or "—",
            }
            for trade in bt.trades
        ]
        st.dataframe(pd.DataFrame(trade_rows), use_container_width=True, hide_index=True)
