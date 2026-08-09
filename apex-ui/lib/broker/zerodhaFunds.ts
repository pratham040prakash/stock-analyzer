export type ZerodhaEquityFunds = {
  /** Available cash in the equity ledger — Zerodha "Available cash" (`live_balance`). */
  ledgerCash: number;
  /** Margin from pledged holdings (`available.collateral`). */
  collateral: number;
  /** Deployable balance — Zerodha "Available margin (Cash + Collateral)". */
  marginAvailable: number;
  /** Live cash component before collateral (`available.live_balance`). */
  liveBalance: number;
};

type KiteEquityMargins = {
  net?: number;
  available?: {
    cash?: number;
    collateral?: number;
    live_balance?: number;
    opening_balance?: number;
    intraday_payin?: number;
    adhoc_margin?: number;
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

function resolveEffectiveCash(
  rawCash: number | null,
  rawOpening: number | null,
): number {
  if (rawCash !== null && rawCash > 0) {
    return roundFunds(rawCash);
  }

  if (rawOpening !== null && rawOpening > 0) {
    return roundFunds(rawOpening);
  }

  if (rawCash !== null) {
    return roundFunds(rawCash);
  }

  if (rawOpening !== null) {
    return roundFunds(rawOpening);
  }

  return 0;
}

/** Parses Kite `/user/margins` equity segment into deployable broker-truth funds. */
export function parseZerodhaEquityFunds(
  equity?: KiteEquityMargins,
): ZerodhaEquityFunds | null {
  if (!equity) {
    return null;
  }

  const rawCash = coerceFundsNumber(equity.available?.cash);
  const rawOpening = coerceFundsNumber(equity.available?.opening_balance);
  const rawNet = coerceFundsNumber(equity.net);
  const rawLive = coerceFundsNumber(equity.available?.live_balance);
  const rawCollateral = coerceFundsNumber(equity.available?.collateral);
  const rawIntraday = coerceFundsNumber(equity.available?.intraday_payin);
  const rawAdhoc = coerceFundsNumber(equity.available?.adhoc_margin);

  if (
    rawCash === null &&
    rawOpening === null &&
    rawNet === null &&
    rawLive === null &&
    rawCollateral === null &&
    rawIntraday === null &&
    rawAdhoc === null
  ) {
    return null;
  }

  const collateral = roundFunds(rawCollateral ?? 0);
  const intraday = roundFunds(rawIntraday ?? 0);
  const adhoc = roundFunds(rawAdhoc ?? 0);
  const effectiveCash = resolveEffectiveCash(rawCash, rawOpening);
  const liveBalance =
    rawLive !== null ? roundFunds(rawLive) : effectiveCash;
  const ledgerCash = liveBalance;

  const cashCollateralFallback = roundFunds(
    effectiveCash + collateral + intraday + adhoc,
  );

  let marginAvailable: number;
  if (rawLive !== null && rawLive > 0) {
    // Zerodha funds page: Available margin (Cash + Collateral) = available cash + collateral.
    marginAvailable = roundFunds(liveBalance + collateral);
  } else if (rawNet !== null && rawNet > 0) {
    marginAvailable = roundFunds(rawNet);
  } else {
    marginAvailable = cashCollateralFallback;
  }

  if (marginAvailable === 0 && cashCollateralFallback > 0) {
    marginAvailable = cashCollateralFallback;
  }

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

  assert(
    sample.marginAvailable === 111_725,
    "Margin available must be live_balance + collateral",
  );
  assert(sample.ledgerCash === 99_725, "Ledger cash must map live_balance");
  assert(sample.collateral === 12_000, "Collateral must map available.collateral");

  const forumCase = parseZerodhaEquityFunds({
    available: {
      cash: 4_158.3,
      opening_balance: 4_158.3,
      live_balance: 1_156_809.3,
      intraday_payin: 1_152_651,
      collateral: 69_469.35,
    },
  });

  assert(
    forumCase?.marginAvailable === 1_226_278,
    "Available margin must match live_balance + collateral",
  );

  const fallback = parseZerodhaEquityFunds({
    available: {
      cash: 50_000,
      collateral: 10_000,
    },
  });

  assert(
    fallback?.marginAvailable === 60_000,
    "Fallback deployable is cash + collateral",
  );

  const openingOnly = parseZerodhaEquityFunds({
    available: {
      cash: 0,
      opening_balance: 25_000,
      live_balance: 0,
      collateral: 0,
    },
  });

  assert(
    openingOnly?.marginAvailable === 25_000,
    "Opening balance must count when live_balance is zero",
  );

  const liveZeroNetPositive = parseZerodhaEquityFunds({
    net: 8_500,
    available: {
      cash: 0,
      live_balance: 0,
      collateral: 0,
    },
  });

  assert(
    liveZeroNetPositive?.marginAvailable === 8_500,
    "Net must be used when live_balance is explicitly zero",
  );

  const netOnly = parseZerodhaEquityFunds({
    net: 12_500,
    available: {},
  });
  assert(netOnly?.marginAvailable === 12_500, "Net-only margins must parse");

  const emptyAccount = parseZerodhaEquityFunds({
    net: 0,
    available: { cash: 0, collateral: 0, live_balance: 0 },
  });
  assert(emptyAccount?.marginAvailable === 0, "Zero-balance account must parse");

  assert(computeTotalCapital(400_000, 50_000) === 450_000, "Total capital sums portfolio + ledger cash");
}
