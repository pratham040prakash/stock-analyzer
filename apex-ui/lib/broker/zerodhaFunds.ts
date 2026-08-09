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

/** Parses Kite `/user/margins` equity segment into deployable broker-truth funds. */
export function parseZerodhaEquityFunds(
  equity?: KiteEquityMargins,
): ZerodhaEquityFunds | null {
  const cash = equity?.available?.cash;

  if (typeof cash !== "number" || Number.isNaN(cash)) {
    return null;
  }

  const ledgerCash = roundFunds(cash);
  const collateral = roundFunds(equity?.available?.collateral ?? 0);
  const liveBalance = roundFunds(equity?.available?.live_balance ?? 0);
  const net = roundFunds(equity?.net ?? 0);

  const marginAvailable =
    net > 0 ? net : liveBalance > 0 ? liveBalance : roundFunds(ledgerCash + collateral);

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
  assert(computeTotalCapital(400_000, 50_000) === 450_000, "Total capital sums portfolio + ledger cash");
}
