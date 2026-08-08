import type { Signals } from "@/types/decision";
import { STOP_LOSS_MULTIPLIER } from "@/services/risk/riskControl";

export const TAKE_PROFIT_MULTIPLIER = 1.05;
export const TAKE_PROFIT_SELL_FRACTION = 0.5;
export const SIGNAL_TREND_EXIT_THRESHOLD = 50;
export const SIGNAL_MOMENTUM_EXIT_THRESHOLD = 40;

export function checkTakeProfit(
  entryPrice: number,
  currentPrice: number,
): boolean {
  return currentPrice >= entryPrice * TAKE_PROFIT_MULTIPLIER;
}

export function computeTrailingStop(
  currentStopLoss: number,
  currentPrice: number,
): number {
  return Math.max(currentStopLoss, currentPrice * STOP_LOSS_MULTIPLIER);
}

export function shouldUpdateTrailingStop(
  currentStopLoss: number,
  currentPrice: number,
): boolean {
  return computeTrailingStop(currentStopLoss, currentPrice) > currentStopLoss;
}

export function checkSignalReversal(signals: Signals): boolean {
  return (
    signals.trend < SIGNAL_TREND_EXIT_THRESHOLD ||
    signals.momentum < SIGNAL_MOMENTUM_EXIT_THRESHOLD
  );
}

export function takeProfitSellQuantity(totalQuantity: number): number {
  if (totalQuantity < 2) {
    return 0;
  }

  return Math.max(1, Math.floor(totalQuantity * TAKE_PROFIT_SELL_FRACTION));
}
