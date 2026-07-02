#!/usr/bin/env python3
"""CLI entry point — stock analysis, watchlist scan, and backtesting."""

from __future__ import annotations

import argparse
import sys

from analyzer.advisor import generate_advice, generate_portfolio_advice
from analyzer.combined import analyze_combined
from analyzer.backtest import run_backtest
from analyzer.data import fetch_benchmark, fetch_stock_data
from analyzer.indicators import add_indicators
from analyzer.india import search_indian_stocks
from analyzer.market_pulse import india_market_pulse
from analyzer.markets import MARKETS, format_price, normalize_ticker, parse_tickers
from analyzer.portfolio import analyze_portfolio
from analyzer.relative_strength import compute_relative_strength
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
)
from analyzer.signals import analyze
from analyzer.watchlist import scan_watchlist

DISCLAIMER = (
    "NOT FINANCIAL ADVICE. Technical analysis only. "
    "Do your own research before investing."
)


def _print_analysis(ticker: str, period: str, market: str) -> int:
    try:
        df, info = fetch_stock_data(ticker, period=period, market=market)
        df = add_indicators(df)
        combined = analyze_combined(df, info["symbol"], yf_info=info)
        result = combined.technical
        fund = combined.fundamental
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    sym = info["symbol"]
    print(f"\n{'=' * 50}")
    print(f"  {info['name']} ({result.ticker})")
    print(f"{'=' * 50}")
    print(f"  Price:              {format_price(result.current_price, sym)}")
    print(f"  Combined:           {combined.combined_recommendation} ({combined.combined_score:+.1f})")
    print(f"  Technical:          {result.recommendation} ({result.composite_score:+.1f})")
    print(f"  Fundamental:        {fund.recommendation} ({fund.composite_score:+.1f})")
    print(f"  Confidence:         {result.confidence}")
    sources = info.get("data_sources", ["Yahoo Finance"])
    print(f"  Data sources:       {', '.join(sources)}")
    if result.support:
        print(f"  Support:        {format_price(result.support, sym)}")
    if result.resistance:
        print(f"  Resistance:     {format_price(result.resistance, sym)}")
    if result.stop_loss:
        print(f"  Stop Loss:      {format_price(result.stop_loss, sym)}")
    if result.take_profit:
        print(f"  Take Profit:    {format_price(result.take_profit, sym)}")
    print(f"\n  Signal Breakdown (Technical):")
    print(f"  {'-' * 46}")
    for sig in result.signals:
        icon = {"bullish": "+", "bearish": "-", "neutral": "~"}[sig.signal]
        print(f"  [{icon}] {sig.name:20s}  {sig.detail}")
    print(f"\n  Fundamentals:")
    print(f"  {'-' * 46}")
    for m in fund.metrics:
        icon = {"bullish": "+", "bearish": "-", "neutral": "~"}[m.signal]
        print(f"  [{icon}] {m.name:18s}  {m.value:>10s}  {m.detail}")

    rs = None
    pulse = None
    if is_india := market in ("india", "nse", "bse"):
        try:
            pulse = india_market_pulse(period)
        except Exception:
            pass
    try:
        bench_df, bench_info = fetch_benchmark(market, period)
        rs = compute_relative_strength(df, bench_df, bench_info["symbol"], bench_info.get("benchmark_name", "Benchmark"))
    except Exception:
        pass

    advice = generate_advice(combined, info, rs, pulse, df)
    print(f"\n  {'=' * 46}")
    print(f"  INVESTMENT SUGGESTION: {advice.final_action} ({advice.conviction} conviction)")
    print(f"  {'=' * 46}")
    print(f"  {advice.summary.replace('**', '')}")
    print(f"\n  Position: {advice.position_hint.replace('**', '')}")
    print(f"  Entry: {advice.entry_zone} | Stop: {advice.stop_loss} | Target: {advice.target}")
    print(f"\n  Bullish:")
    for f in advice.bullish_factors[:5]:
        print(f"    + {f}")
    print(f"  Bearish:")
    for f in advice.bearish_factors[:5]:
        print(f"    - {f}")
    passed = sum(1 for _, ok, _ in advice.standards_checklist if ok)
    print(f"\n  Standards checklist: {passed}/{len(advice.standards_checklist)} passed")
    print(f"\n  {DISCLAIMER}\n")
    return 0


def _print_watchlist(tickers: list[str], period: str, market: str) -> int:
    print(f"\nScanning {len(tickers)} tickers...\n")
    rows = scan_watchlist(tickers, period=period, market=market)
    print(f"{'Ticker':<14} {'Combined':<12} {'Score':>7}  {'Tech':>6}  {'Fund':>6}  {'Price':>12}  Name")
    print("-" * 80)
    for row in rows:
        if row.error:
            print(f"{row.ticker:<14} {'ERROR':<12} {'—':>7}  {'—':>6}  {'—':>6}  {'—':>12}  {row.error[:40]}")
        else:
            print(
                f"{row.ticker:<14} {row.recommendation:<12} {row.score:>+7.1f}  "
                f"{row.technical_score:>+6.1f}  {row.fundamental_score:>+6.1f}  "
                f"{format_price(row.price, row.ticker):>12}  {row.name[:30]}"
            )
    print(f"\n  {DISCLAIMER}\n")
    return 0


def _print_backtest(ticker: str, period: str, market: str) -> int:
    try:
        df, info = fetch_stock_data(ticker, period=period, market=market)
        df = add_indicators(df)
        bt = run_backtest(df, info["symbol"])
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    sym = info["symbol"]
    print(f"\n{'=' * 50}")
    print(f"  Backtest: {info['name']} ({sym}) — {period}")
    print(f"{'=' * 50}")
    print(f"  Strategy Return:  {bt.strategy_return_pct:+.2f}%")
    print(f"  Buy & Hold:       {bt.buy_hold_return_pct:+.2f}%")
    print(f"  Alpha:            {bt.strategy_return_pct - bt.buy_hold_return_pct:+.2f}%")
    print(f"  Total Trades:     {bt.total_trades}")
    print(f"  Win Rate:         {bt.win_rate_pct:.1f}%")
    print(f"  Max Drawdown:     -{bt.max_drawdown_pct:.2f}%")
    if bt.trades:
        print(f"\n  Trades:")
        for t in bt.trades:
            ret = f"{t.return_pct:+.2f}%" if t.return_pct is not None else "—"
            print(
                f"    {t.entry_date.strftime('%Y-%m-%d')} → "
                f"{t.exit_date.strftime('%Y-%m-%d') if t.exit_date else '—'}  "
                f"{ret}  ({t.entry_signal} → {t.exit_signal})"
            )
    print(f"\n  {DISCLAIMER}\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Stock technical analysis CLI")
    parser.add_argument("ticker", nargs="?", help="Stock ticker (e.g. AAPL, RELIANCE)")
    parser.add_argument("--period", default="1y", choices=["3mo", "6mo", "1y", "2y", "5y"])
    parser.add_argument(
        "--market",
        default="india",
        choices=list(MARKETS.keys()),
        help="Market exchange (us, india, nse, bse)",
    )
    parser.add_argument(
        "--watchlist",
        metavar="TICKERS",
        help="Comma-separated tickers to scan (e.g. AAPL,MSFT,NVDA)",
    )
    parser.add_argument("--backtest", action="store_true", help="Run backtest on ticker")
    parser.add_argument(
        "--search",
        metavar="QUERY",
        help="Search Indian stocks by company name (e.g. 'Reliance', 'HDFC Bank')",
    )
    parser.add_argument(
        "--market-pulse",
        action="store_true",
        help="Show Indian index signals (Nifty, Sensex, Bank Nifty, IT)",
    )
    parser.add_argument(
        "--zerodha-login",
        metavar="REQUEST_TOKEN",
        help="Exchange Zerodha request_token for access_token (needs API key/secret in .env)",
    )
    parser.add_argument(
        "--zerodha-holdings",
        action="store_true",
        help="Fetch and analyze Zerodha holdings via Kite API",
    )
    parser.add_argument(
        "--zerodha-csv",
        metavar="FILE",
        help="Analyze holdings from Zerodha CSV export",
    )
    parser.add_argument(
        "--zerodha-symbols",
        metavar="SYMBOLS",
        help="Analyze pasted Kite symbols (e.g. 'NSE:RELIANCE-EQ,NSE:TCS-EQ')",
    )
    parser.add_argument(
        "--pulse-scan",
        action="store_true",
        help="Full market pulse: intraday + swing + long picks (Nifty 50)",
    )
    parser.add_argument(
        "--global-impact",
        action="store_true",
        help="Global markets spillover → Nifty bias",
    )
    parser.add_argument(
        "--daily-briefing",
        metavar="CSV",
        help="Daily advisor briefing from Zerodha holdings CSV",
    )
    parser.add_argument(
        "--telegram-test",
        action="store_true",
        help="Send test message via Telegram (.env tokens required)",
    )
    parser.add_argument(
        "--morning-briefing",
        action="store_true",
        help="Full morning briefing (global + pulse + holdings)",
    )
    parser.add_argument(
        "--send-morning-telegram",
        action="store_true",
        help="Build morning briefing and send to Telegram",
    )
    parser.add_argument(
        "--send-pulse-telegram",
        action="store_true",
        help="Run pulse scan and send summary to Telegram",
    )
    args = parser.parse_args()

    if args.telegram_test:
        from analyzer.telegram_notify import send_telegram_broadcast

        ok, msg = send_telegram_broadcast("Stock Analyzer test — Telegram alerts are working.")
        print(msg if ok else f"Failed: {msg}")
        return 0 if ok else 1

    if args.send_morning_telegram or args.morning_briefing:
        from analyzer.morning_briefing import build_morning_briefing, format_morning_markdown
        from analyzer.telegram_notify import format_morning_telegram, send_telegram_broadcast

        load_env_credentials()
        mb = build_morning_briefing(period=args.period, use_pulse_cache=not getattr(args, "no_cache", False))
        print(format_morning_markdown(mb))
        if args.send_morning_telegram:
            ok, msg = send_telegram_broadcast(format_morning_telegram(mb), alert_type="morning")
            print("Telegram:", msg)
            return 0 if ok else 1
        return 0

    if args.send_pulse_telegram:
        from analyzer.market_pulse_scan import run_market_pulse_scan
        from analyzer.telegram_notify import format_pulse_alert, send_telegram_broadcast

        r = run_market_pulse_scan(args.period, args.market, use_cache=False)
        ok, msg = send_telegram_broadcast(format_pulse_alert(r))
        print(msg if ok else f"Failed: {msg}")
        return 0 if ok else 1

    if args.global_impact:
        from analyzer.global_impact import build_india_impact_report

        r = build_india_impact_report()
        print(f"\nGlobal → India ({r.fetched_at})\n")
        print(f"  Bias: {r.predicted_nifty_bias}  Spillover: {r.spillover_score:+.0f}")
        print(f"  Predicted move: {r.predicted_move_pct:+.2f}%  ({r.confidence})")
        print(f"\n  {r.narrative.replace('**', '')}\n")
        return 0

    if args.pulse_scan:
        from analyzer.market_pulse_scan import run_market_pulse_scan

        print("\nRunning full market pulse scan (Nifty 50)...\n")
        r = run_market_pulse_scan(args.period, args.market, use_cache=False)
        if r.regime:
            print(f"  Regime: {r.regime.regime} (ADX {r.regime.adx})")
        print("\n  Intraday BUY:")
        for p in r.intraday_picks[:5]:
            print(f"    {p.nse_symbol:<12} {p.action:<12} {p.score:+.0f}")
        print("\n  Short-term BUY:")
        for p in r.short_term_picks[:5]:
            print(f"    {p.nse_symbol:<12} {p.action:<12} {p.score:+.0f}")
        print("\n  Long-term BUY:")
        for p in r.long_term_picks[:5]:
            print(f"    {p.nse_symbol:<12} {p.action:<12} {p.score:+.0f}")
        print(f"\n  {DISCLAIMER}\n")
        return 0

    if args.daily_briefing:
        try:
            content = open(args.daily_briefing, encoding="utf-8").read()
            imp = parse_holdings_csv(content)
            if imp.errors and not imp.holdings:
                print(imp.errors[0], file=sys.stderr)
                return 1
            from analyzer.daily_advisor import build_daily_briefing, save_briefing

            b = build_daily_briefing(imp, period=args.period)
            path = save_briefing(b)
            print(f"\nDaily briefing ({b.generated_at})\n")
            print(b.summary.replace("**", ""))
            for a in b.priority_actions[:6]:
                print(f"  - {a.replace('**', '')}")
            print(f"\n  Saved: {path}\n")
        except OSError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.market_pulse:
        from analyzer.market_pulse import india_market_pulse, overall_market_verdict

        pulses = india_market_pulse(args.period)
        print(f"\nIndian Market Pulse\n")
        for p in pulses:
            ch = f"{p.change_1m_pct:+.1f}% 1M" if p.change_1m_pct is not None else ""
            print(f"  {p.name:<14} {p.recommendation:<12} {p.score:>+6.0f}  {p.regime:<8}  {ch}")
        print(f"\n  {overall_market_verdict(pulses)}\n")
        return 0

    if args.zerodha_login:
        creds = load_env_credentials()
        if not creds["api_key"] or not creds["api_secret"]:
            print("Set ZERODHA_API_KEY and ZERODHA_API_SECRET in .env", file=sys.stderr)
            return 1
        try:
            token = exchange_request_token(
                creds["api_key"], creds["api_secret"], args.zerodha_login
            )
            save_access_token_to_env(token)
            print("\nAccess token saved to .env (valid until ~6 AM IST tomorrow).\n")
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.zerodha_holdings:
        imp = fetch_holdings_from_kite()
        if imp.errors and not imp.holdings:
            print(imp.errors[0], file=sys.stderr)
            return 1
        rows = analyze_portfolio(imp, period=args.period)
        print(f"\nZerodha Portfolio Analysis ({len(rows)} holdings)\n")
        print(f"{'Kite':<22} {'Signal':<12} {'Score':>7}  {'P&L':>10}  Name")
        print("-" * 75)
        for r in rows:
            pnl = f"₹{r.pnl:,.0f}" if r.pnl is not None else "—"
            if r.error:
                print(f"{r.kite_symbol:<22} {'ERROR':<12} {'—':>7}  {'—':>10}  {r.error[:30]}")
            else:
                print(
                    f"{r.kite_symbol:<22} {r.recommendation:<12} {r.score:>+7.1f}  "
                    f"{pnl:>10}  {r.name[:30]}"
                )
        print(f"\n  {DISCLAIMER}\n")
        return 0

    if args.zerodha_csv:
        try:
            content = open(args.zerodha_csv, encoding="utf-8").read()
            imp = parse_holdings_csv(content)
            if imp.errors and not imp.holdings:
                print(imp.errors[0], file=sys.stderr)
                return 1
            rows = analyze_portfolio(imp, period=args.period)
            print(f"\nCSV Portfolio Analysis ({len(rows)} holdings)\n")
            for r in rows:
                sig = r.recommendation if not r.error else "ERROR"
                print(f"  {r.kite_symbol:<22} {sig:<12} {r.score:+.1f}  {r.name[:35]}")
            print(f"\n  {DISCLAIMER}\n")
        except OSError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.zerodha_symbols:
        yahoo = parse_kite_symbol_list(args.zerodha_symbols)
        imp = ZerodhaImportResult(source="cli")
        for y in yahoo:
            base = y.replace(".NS", "").replace(".BO", "")
            imp.holdings.append(
                ZerodhaHolding(
                    kite_symbol=f"NSE:{base}-EQ",
                    tradingsymbol=base,
                    exchange="NSE",
                    quantity=1,
                    yahoo_symbol=y,
                )
            )
        rows = analyze_portfolio(imp, period=args.period)
        for r in rows:
            print(f"  {r.kite_symbol:<22} {r.recommendation:<12} {r.score:+.1f}  {r.name[:35]}")
        print(f"\n  {DISCLAIMER}\n")
        return 0

    if args.search:
        results = search_indian_stocks(args.search)
        if not results:
            print("No NSE/BSE results found.")
            return 1
        print(f"\nIndian stock search: '{args.search}'\n")
        for r in results:
            print(f"  {r['symbol']:<16} {r['exchange']:<4} {r['name']}")
        print()
        return 0

    if args.watchlist:
        tickers = parse_tickers(args.watchlist, args.market)
        return _print_watchlist(tickers, args.period, args.market)

    if not args.ticker:
        parser.error("ticker is required unless --watchlist is used")

    if args.backtest:
        return _print_backtest(args.ticker, args.period, args.market)

    return _print_analysis(args.ticker, args.period, args.market)


if __name__ == "__main__":
    raise SystemExit(main())
