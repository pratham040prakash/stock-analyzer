export type ZerodhaEquityFunds = {
  /** Raw cash in the equity ledger (`available.cash`). */
  ledgerCash: number;
  /** Margin from pledged holdings (`available.collateral`). */
  collateral: number;
  /** Free cash for CNC trading — Zerodha "Margin available" (`equity.net`). */
  marginAvailable: number;
  /** Live balance after utilisation (`available.live_balance`). */
  liveBalance: number;
};

type KiteEquityMargins = {
  net?: number;
  available?: {
    cash?: number;
    collateral?: number;
    live_balance?: number;
  };
};

function roundFunds(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.max(0, Math.round(value));
}

function coerceFundsNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
}

/** Parses Kite `/user/margins` equity segment into deployable broker-truth funds. */
export function parseZerodhaEquityFunds(
  equity?: KiteEquityMargins,
): ZerodhaEquityFunds | null {
  if (!equity) {
    return null;
  }

  const rawCash = coerceFundsNumber(equity.available?.cash);
  const rawNet = coerceFundsNumber(equity.net);
  const rawLive = coerceFundsNumber(equity.available?.live_balance);
  const rawCollateral = coerceFundsNumber(equity.available?.collateral);

  if (rawCash === null && rawNet === null && rawLive === null) {
    return null;
  }

  const collateral = roundFunds(rawCollateral ?? 0);
  const ledgerCash = roundFunds(rawCash ?? 0);
  const liveBalance = roundFunds(rawLive ?? 0);
  const net = roundFunds(rawNet ?? 0);

  const marginAvailable =
    net > 0
      ? net
      : rawLive !== null && rawLive > 0
        ? roundFunds(rawLive)
        : roundFunds((rawCash ?? 0) + (rawCollateral ?? 0));

  return {
    ledgerCash,
    collateral,
    marginAvailable,
    liveBalance,
  };
}

export function computeTotalCapital(
  portfolioValue: number,
  ledgerCash: number,
): number {
  return Math.max(0, Math.round(portfolioValue)) + Math.max(0, Math.round(ledgerCash));
}

export function runZerodhaFundsSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Zerodha funds self-check failed: ${message}`);
    }
  };

  const sample = parseZerodhaEquityFunds({
    net: 99_725,
    available: {
      cash: 245_431,
      collateral: 12_000,
      live_balance: 99_725,
    },
  });

  assert(sample !== null, "Sample margins must parse");
  if (!sample) {
    return;
  }

  assert(sample.marginAvailable === 99_725, "Margin available must prefer net");
  assert(sample.ledgerCash === 245_431, "Ledger cash must map available.cash");
  assert(sample.collateral === 12_000, "Collateral must map available.collateral");

  const fallback = parseZerodhaEquityFunds({
    available: {
      cash: 50_000,
      collateral: 10_000,
    },
  });

  assert(fallback?.marginAvailable === 60_000, "Fallback deployable is cash + collateral");

  const netOnly = parseZerodhaEquityFunds({
    net: 12_500,
    available: {},
  });
  assert(netOnly?.marginAvailable === 12_500, "Net-only margins must parse");

  assert(computeTotalCapital(400_000, 50_000) === 450_000, "Total capital sums portfolio + ledger cash");
}
