"""Backtest the signal strategy against historical data."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer.signals import analyze_at_index


@dataclass
class Trade:
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp | None
    entry_price: float
    exit_price: float | None
    return_pct: float | None
    entry_signal: str
    exit_signal: str | None = None


@dataclass
class BacktestResult:
    ticker: str
    period: str
    strategy_return_pct: float
    buy_hold_return_pct: float
    total_trades: int
    winning_trades: int
    win_rate_pct: float
    max_drawdown_pct: float
    benchmark_return_pct: float | None = None
    alpha_vs_benchmark_pct: float | None = None
    trades: list[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)


# Zerodha equity delivery friction (simplified per side)
ZERODHA_COST_PRESET = {"commission_pct": 0.03, "slippage_pct": 0.05}


def _warmup_index(df: pd.DataFrame) -> int:
    """Skip rows until core indicators are available."""
    for col in ("SMA_50", "RSI_14"):
        if col not in df.columns:
            return 50
    valid = df["SMA_50"].first_valid_index()
    if valid is None:
        return 50
    return df.index.get_loc(valid)


def run_backtest(
    df: pd.DataFrame,
    ticker: str,
    buy_threshold: float = 20.0,
    sell_threshold: float = -20.0,
    commission_pct: float = ZERODHA_COST_PRESET["commission_pct"],
    slippage_pct: float = ZERODHA_COST_PRESET["slippage_pct"],
    benchmark_df: pd.DataFrame | None = None,
) -> BacktestResult:
    """
    Simulate a long-only strategy with Indian equity friction:
    - commission_pct: per side (~0.03% brokerage + taxes simplified)
    - slippage_pct: per side execution slippage
    """
    start = _warmup_index(df)
    if start >= len(df) - 1:
        raise ValueError("Not enough data for backtesting. Use a longer period (2y+).")

    initial_price = float(df["Close"].iloc[start])
    final_price = float(df["Close"].iloc[-1])

    in_position = False
    entry_price = 0.0
    entry_date: pd.Timestamp | None = None
    entry_signal = ""
    trades: list[Trade] = []
    equity = 1.0
    peak_equity = 1.0
    max_drawdown = 0.0
    equity_points: list[tuple[pd.Timestamp, float]] = []

    friction = (commission_pct + slippage_pct) / 100

    for i in range(start, len(df)):
        date = df.index[i]
        price = float(df["Close"].iloc[i])
        result = analyze_at_index(df, ticker, index=i)
        score = result.composite_score

        if not in_position and score >= buy_threshold:
            in_position = True
            entry_price = price * (1 + friction)
            entry_date = date
            entry_signal = result.recommendation
        elif in_position and score <= sell_threshold:
            exit_px = price * (1 - friction)
            ret = (exit_px - entry_price) / entry_price
            equity *= 1 + ret
            trades.append(
                Trade(
                    entry_date=entry_date,
                    exit_date=date,
                    entry_price=entry_price,
                    exit_price=exit_px,
                    return_pct=round(ret * 100, 2),
                    entry_signal=entry_signal,
                    exit_signal=result.recommendation,
                )
            )
            in_position = False

        mark_equity = equity
        if in_position:
            mark_equity = equity * (price / entry_price)
        equity_points.append((date, mark_equity))
        peak_equity = max(peak_equity, mark_equity)
        drawdown = (peak_equity - mark_equity) / peak_equity if peak_equity else 0
        max_drawdown = max(max_drawdown, drawdown)

    if in_position and entry_date is not None:
        exit_px = final_price * (1 - friction)
        ret = (exit_px - entry_price) / entry_price
        equity *= 1 + ret
        trades.append(
            Trade(
                entry_date=entry_date,
                exit_date=df.index[-1],
                entry_price=entry_price,
                exit_price=exit_px,
                return_pct=round(ret * 100, 2),
                entry_signal=entry_signal,
                exit_signal="OPEN",
            )
        )

    winning = sum(1 for t in trades if t.return_pct and t.return_pct > 0)
    strategy_return = (equity - 1) * 100
    buy_hold_return = (final_price - initial_price) / initial_price * 100

    benchmark_return: float | None = None
    alpha: float | None = None
    if benchmark_df is not None and len(benchmark_df) >= start + 1:
        b_start = float(benchmark_df["Close"].iloc[start])
        b_end = float(benchmark_df["Close"].iloc[-1])
        benchmark_return = round((b_end - b_start) / b_start * 100, 2)
        alpha = round(strategy_return - benchmark_return, 2)

    equity_series = pd.Series(
        [v for _, v in equity_points],
        index=[d for d, _ in equity_points],
        name="equity",
    )

    return BacktestResult(
        ticker=ticker,
        period=f"{len(df)} bars",
        strategy_return_pct=round(strategy_return, 2),
        buy_hold_return_pct=round(buy_hold_return, 2),
        benchmark_return_pct=benchmark_return,
        alpha_vs_benchmark_pct=alpha,
        total_trades=len(trades),
        winning_trades=winning,
        win_rate_pct=round(winning / len(trades) * 100, 1) if trades else 0.0,
        max_drawdown_pct=round(max_drawdown * 100, 2),
        trades=trades,
        equity_curve=equity_series,
    )


@dataclass
class WalkForwardFold:
    fold: int
    train_bars: int
    test_bars: int
    train_return_pct: float
    test_return_pct: float
    test_alpha_pct: float | None


@dataclass
class WalkForwardResult:
    ticker: str
    folds: list[WalkForwardFold] = field(default_factory=list)
    avg_test_return_pct: float = 0.0
    avg_test_alpha_pct: float | None = None
    profitable_folds: int = 0


def run_walk_forward(
    df: pd.DataFrame,
    ticker: str,
    n_folds: int = 4,
    train_ratio: float = 0.7,
    buy_threshold: float = 20.0,
    sell_threshold: float = -20.0,
    benchmark_df: pd.DataFrame | None = None,
) -> WalkForwardResult:
    """
    Walk-forward validation: train on earlier window, test on next out-of-sample segment.
    Production quant stacks use this to reduce overfitting.
    """
    warmup = _warmup_index(df)
    usable = len(df) - warmup
    if usable < n_folds * 40:
        raise ValueError("Not enough history for walk-forward. Use 2y+ daily data.")

    fold_size = usable // n_folds
    folds: list[WalkForwardFold] = []
    test_returns: list[float] = []
    test_alphas: list[float] = []

    for fold in range(n_folds):
        test_start = warmup + fold * fold_size
        test_end = min(test_start + fold_size, len(df))
        train_end = test_start
        train_start = max(warmup, int(train_end - fold_size * train_ratio))
        if test_end - test_start < 20 or train_end - train_start < 30:
            continue

        train_df = df.iloc[train_start:train_end]
        test_df = df.iloc[test_start:test_end]
        bench_test = None
        if benchmark_df is not None:
            bench_test = benchmark_df.iloc[test_start:test_end]

        train_bt = run_backtest(
            train_df, ticker, buy_threshold=buy_threshold, sell_threshold=sell_threshold,
        )
        test_bt = run_backtest(
            test_df, ticker, buy_threshold=buy_threshold, sell_threshold=sell_threshold,
            benchmark_df=bench_test,
        )
        folds.append(
            WalkForwardFold(
                fold=fold + 1,
                train_bars=len(train_df),
                test_bars=len(test_df),
                train_return_pct=train_bt.strategy_return_pct,
                test_return_pct=test_bt.strategy_return_pct,
                test_alpha_pct=test_bt.alpha_vs_benchmark_pct,
            )
        )
        test_returns.append(test_bt.strategy_return_pct)
        if test_bt.alpha_vs_benchmark_pct is not None:
            test_alphas.append(test_bt.alpha_vs_benchmark_pct)

    profitable = sum(1 for f in folds if f.test_return_pct > 0)
    return WalkForwardResult(
        ticker=ticker,
        folds=folds,
        avg_test_return_pct=round(sum(test_returns) / len(test_returns), 2) if test_returns else 0.0,
        avg_test_alpha_pct=(
            round(sum(test_alphas) / len(test_alphas), 2) if test_alphas else None
        ),
        profitable_folds=profitable,
    )
