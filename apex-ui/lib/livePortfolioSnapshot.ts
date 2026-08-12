import type { PortfolioHoldingRow } from "@/types/portfolioApi";
import type { MonitorLiveTick } from "@/services/monitor/openPositions";
import type { ZerodhaPositionPnlRow } from "@/services/brokers/zerodha";

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

export function liveHoldingsSnapshotEqual(
  previous: PortfolioHoldingRow[],
  next: PortfolioHoldingRow[],
): boolean {
  if (previous.length !== next.length) {
    return false;
  }

  for (let index = 0; index < previous.length; index += 1) {
    const left = previous[index];
    const right = next[index];

    if (
      left.tradingsymbol !== right.tradingsymbol ||
      left.quantity !== right.quantity ||
      roundMoney(left.average_price) !== roundMoney(right.average_price) ||
      roundMoney(left.last_price) !== roundMoney(right.last_price) ||
      roundMoney(left.pnl) !== roundMoney(right.pnl) ||
      roundMoney(left.value) !== roundMoney(right.value) ||
      roundMoney(left.allocation_pct) !== roundMoney(right.allocation_pct)
    ) {
      return false;
    }
  }

  return true;
}

export function positionsBreakdownSnapshotEqual(
  previous: ZerodhaPositionPnlRow[],
  next: ZerodhaPositionPnlRow[],
): boolean {
  if (previous.length !== next.length) {
    return false;
  }

  for (let index = 0; index < previous.length; index += 1) {
    const left = previous[index];
    const right = next[index];

    if (
      left.symbol !== right.symbol ||
      left.quantity !== right.quantity ||
      roundMoney(left.average_price) !== roundMoney(right.average_price) ||
      roundMoney(left.last_price) !== roundMoney(right.last_price) ||
      roundMoney(left.pnl) !== roundMoney(right.pnl)
    ) {
      return false;
    }
  }

  return true;
}

export function positionTicksSnapshotEqual(
  previous: MonitorLiveTick[],
  next: MonitorLiveTick[],
): boolean {
  if (previous.length !== next.length) {
    return false;
  }

  for (let index = 0; index < previous.length; index += 1) {
    const left = previous[index];
    const right = next[index];

    if (
      left.id !== right.id ||
      roundMoney(left.currentPrice) !== roundMoney(right.currentPrice) ||
      roundMoney(left.unrealizedPnl) !== roundMoney(right.unrealizedPnl) ||
      roundMoney(left.pnlPct) !== roundMoney(right.pnlPct) ||
      roundMoney(left.positionDayPnl ?? 0) !== roundMoney(right.positionDayPnl ?? 0) ||
      left.stopStatus !== right.stopStatus
    ) {
      return false;
    }
  }

  return true;
}

export function runLivePortfolioSnapshotSelfCheck(): void {
  const base: PortfolioHoldingRow = {
    tradingsymbol: "RELIANCE",
    quantity: 10,
    average_price: 2500,
    last_price: 2550.12,
    pnl: 501.2,
    value: 25501.2,
    allocation_pct: 42.5,
  };

  if (!liveHoldingsSnapshotEqual([base], [{ ...base, last_price: 2550.124 }])) {
    throw new Error("live portfolio snapshot self-check failed: rounding tolerance");
  }

  if (liveHoldingsSnapshotEqual([base], [{ ...base, last_price: 2551 }])) {
    throw new Error("live portfolio snapshot self-check failed: price delta");
  }
}
