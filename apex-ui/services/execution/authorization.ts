import type {
  DailyDecisionArtifact,
} from "@/types/decision";
import { validateDailyDecisionArtifact } from "@/types/decision";

/**
 * Single canonical entry point for authorising any broker-facing action
 * against the frozen daily decision artifact.
 *
 * The artifact is the only source of truth for what may execute today.
 * Client-supplied symbol/side/size are treated as *claims* that must
 * match the artifact exactly. Anything unproven fails closed with a
 * WAIT-style reason.
 */

export type ExecutionRequest = {
  side: "buy" | "sell";
  symbol?: string | null;
  amount?: number | null;
  sellPercent?: number | null;
};

export type ExecutionAuthorizationOk = {
  ok: true;
  side: "buy" | "sell";
  symbol: string;
  amount?: number;
  sellPercent?: number;
  frozenAt: string;
  decisionId: string;
};

export type ExecutionAuthorizationDenyCode =
  | "artifact_missing"
  | "trading_locked"
  | "wrong_side"
  | "wrong_symbol"
  | "symbol_unknown"
  | "wrong_size"
  | "entry_not_confirmed"
  | "capital_unknown"
  | "broker_unknown"
  | "market_unknown";

export type ExecutionAuthorizationDeny = {
  ok: false;
  code: ExecutionAuthorizationDenyCode;
  reason: string;
  blockers: string[];
};

export type ExecutionAuthorization =
  | ExecutionAuthorizationOk
  | ExecutionAuthorizationDeny;

function normalizeSymbolCasing(value: string | null | undefined): string {
  return (value ?? "").trim().toUpperCase();
}

function deny(
  code: ExecutionAuthorizationDenyCode,
  reason: string,
  blockers: string[] = [],
): ExecutionAuthorizationDeny {
  return { ok: false, code, reason, blockers };
}

export function validateExecutionAgainstArtifact(
  artifact: DailyDecisionArtifact | null | undefined,
  request: ExecutionRequest,
): ExecutionAuthorization {
  if (!artifact || !validateDailyDecisionArtifact(artifact)) {
    return deny(
      "artifact_missing",
      "No frozen decision for today — refresh before trading.",
    );
  }

  if (artifact.tradingLocked) {
    return deny(
      "trading_locked",
      "Today's decision is locked — trading is not authorised.",
      artifact.blockers,
    );
  }

  const requestedSide = request.side;
  const artifactSide = artifact.action === "buy" ? "buy" : "sell";
  const artifactIsSell =
    artifact.action === "sell" || artifact.action === "reduce";
  const artifactSideExpected: "buy" | "sell" = artifact.action === "buy"
    ? "buy"
    : artifactIsSell
      ? "sell"
      : "buy";

  if (requestedSide !== artifactSideExpected) {
    return deny(
      "wrong_side",
      `Today's decision is ${artifact.action} — cannot ${requestedSide}.`,
      artifact.blockers,
    );
  }

  if (artifact.symbol.status !== "known") {
    return deny(
      "symbol_unknown",
      "Today's decision has no confirmed symbol.",
      artifact.blockers,
    );
  }

  const artifactSymbol = normalizeSymbolCasing(artifact.symbol.value);
  const requestedSymbol = normalizeSymbolCasing(request.symbol);

  if (requestedSymbol && requestedSymbol !== artifactSymbol) {
    return deny(
      "wrong_symbol",
      `Today's decision authorises ${artifactSymbol} only — refused ${requestedSymbol}.`,
      artifact.blockers,
    );
  }

  if (artifact.capital_state.status !== "known") {
    return deny("capital_unknown", artifact.capital_state.reason, [
      ...artifact.blockers,
      artifact.capital_state.reason,
    ]);
  }

  if (artifact.broker_state.status !== "known") {
    return deny("broker_unknown", artifact.broker_state.reason, [
      ...artifact.blockers,
      artifact.broker_state.reason,
    ]);
  }

  if (artifact.market_state.status !== "known") {
    return deny("market_unknown", artifact.market_state.reason, [
      ...artifact.blockers,
      artifact.market_state.reason,
    ]);
  }

  if (artifact.action === "buy" && !artifact.entryConfirmed) {
    return deny(
      "entry_not_confirmed",
      "Entry is not confirmed — wait for the trigger before buying.",
      artifact.blockers,
    );
  }

  if (requestedSide === "buy") {
    if (artifact.approved_size.kind !== "buy_amount") {
      return deny(
        "wrong_size",
        "Today's decision has no approved buy amount.",
        artifact.blockers,
      );
    }

    const approved = artifact.approved_size.amount_inr;
    const requested = Math.round(Number(request.amount ?? 0));
    if (!Number.isFinite(requested) || requested <= 0) {
      return deny(
        "wrong_size",
        `Amount must equal today's approved ${approved} INR.`,
        artifact.blockers,
      );
    }

    if (requested !== approved) {
      return deny(
        "wrong_size",
        `Amount ${requested} does not match today's approved ${approved} INR.`,
        artifact.blockers,
      );
    }

    return {
      ok: true,
      side: "buy",
      symbol: artifactSymbol,
      amount: approved,
      frozenAt: artifact.frozen_at,
      decisionId: artifact.decision_id,
    };
  }

  if (artifact.approved_size.kind !== "sell_percent") {
    return deny(
      "wrong_size",
      "Today's decision has no approved sell percent.",
      artifact.blockers,
    );
  }

  const approvedPercent = artifact.approved_size.percent;
  const requestedPercent = Math.round(Number(request.sellPercent ?? 0));

  if (
    !Number.isFinite(requestedPercent) ||
    requestedPercent <= 0 ||
    requestedPercent > 100
  ) {
    return deny(
      "wrong_size",
      `Sell percent must equal today's approved ${approvedPercent}%.`,
      artifact.blockers,
    );
  }

  if (requestedPercent !== approvedPercent) {
    return deny(
      "wrong_size",
      `Sell percent ${requestedPercent}% does not match today's approved ${approvedPercent}%.`,
      artifact.blockers,
    );
  }

  return {
    ok: true,
    side: "sell",
    symbol: artifactSymbol,
    sellPercent: approvedPercent,
    frozenAt: artifact.frozen_at,
    decisionId: artifact.decision_id,
  };
}

export function runExecutionAuthorizationSelfCheck(): void {
  const now = "2026-09-11T09:00:00.000Z";
  const known = <T,>(value: T) => ({
    status: "known" as const,
    value,
    observed_at: now,
  });
  const unknown = <T,>(reason: string) => ({
    status: "unknown" as const,
    value: null,
    observed_at: null,
    reason,
  });

  const buyArtifact: DailyDecisionArtifact = {
    schema_version: "1",
    decision_id: "2026-09-11:test",
    decision_date: "2026-09-11",
    frozen_at: now,
    intent: "grow",
    action: "buy",
    symbol: known("HDFCBANK"),
    approved_size: { kind: "buy_amount", amount_inr: 5000 },
    daily_verdict: "trade",
    tradingLocked: false,
    entryConfirmed: true,
    capital_state: known({ available_cash_inr: 100000, portfolio_value_inr: 500000 }),
    broker_state: known({ broker: "zerodha", connection: "connected" }),
    market_state: known({ trend: "sideways", session: "market_open" }),
    source_timestamps: {
      portfolio: known(now),
      capital: known(now),
      broker: known(now),
      market: known(now),
      entry: known(now),
    },
    evidence_ids: ["reason"],
    evidence: [
      {
        id: "reason",
        type: "FACT",
        source: "decision_engine",
        summary: "Buy",
        observed_at: now,
      },
    ],
    blockers: [],
    decision_metadata: {
      producer: "getDecision/evaluateDailyDecision",
      confidence: 80,
      reason: "Buy",
      confidence_factors: [],
    },
    frozen_portfolio: { positions: [], total_value_inr: 0, pnl_inr: 0 },
    projection: {
      decision: "BUY_MORE",
      action: "buy",
      confidence: 80,
      reason: "Buy",
      confidence_factors: [],
      actions: [],
      stock: "HDFCBANK",
      amount: 5000,
    },
  };

  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Execution authorization self-check failed: ${message}`);
    }
  };

  assert(
    validateExecutionAgainstArtifact(null, { side: "buy", symbol: "HDFCBANK", amount: 5000 }).ok === false,
    "Missing artifact must be denied",
  );

  const ok = validateExecutionAgainstArtifact(buyArtifact, {
    side: "buy",
    symbol: "hdfcbank",
    amount: 5000,
  });
  assert(ok.ok === true && ok.symbol === "HDFCBANK" && ok.amount === 5000,
    "Case-insensitive symbol and exact amount must authorize",
  );

  const wrongSymbol = validateExecutionAgainstArtifact(buyArtifact, {
    side: "buy",
    symbol: "TCS",
    amount: 5000,
  });
  assert(wrongSymbol.ok === false && wrongSymbol.code === "wrong_symbol",
    "Wrong symbol must be refused",
  );

  const wrongSize = validateExecutionAgainstArtifact(buyArtifact, {
    side: "buy",
    symbol: "HDFCBANK",
    amount: 6000,
  });
  assert(wrongSize.ok === false && wrongSize.code === "wrong_size",
    "Wrong amount must be refused",
  );

  const wrongSide = validateExecutionAgainstArtifact(buyArtifact, {
    side: "sell",
    symbol: "HDFCBANK",
    sellPercent: 20,
  });
  assert(wrongSide.ok === false && wrongSide.code === "wrong_side",
    "Wrong side must be refused",
  );

  const lockedArtifact: DailyDecisionArtifact = {
    ...buyArtifact,
    tradingLocked: true,
    blockers: ["Capital unknown"],
  };
  const locked = validateExecutionAgainstArtifact(lockedArtifact, {
    side: "buy",
    symbol: "HDFCBANK",
    amount: 5000,
  });
  assert(locked.ok === false && locked.code === "trading_locked",
    "Locked artifact must refuse",
  );

  const entryPending: DailyDecisionArtifact = {
    ...buyArtifact,
    entryConfirmed: false,
  };
  const entryDenied = validateExecutionAgainstArtifact(entryPending, {
    side: "buy",
    symbol: "HDFCBANK",
    amount: 5000,
  });
  assert(entryDenied.ok === false && entryDenied.code === "entry_not_confirmed",
    "Unconfirmed entry must refuse buy",
  );

  const unknownCapital: DailyDecisionArtifact = {
    ...buyArtifact,
    capital_state: unknown<{ available_cash_inr: number; portfolio_value_inr: number }>("Capital state unavailable"),
  };
  const capitalDenied = validateExecutionAgainstArtifact(unknownCapital, {
    side: "buy",
    symbol: "HDFCBANK",
    amount: 5000,
  });
  assert(capitalDenied.ok === false && capitalDenied.code === "capital_unknown",
    "Unknown capital must refuse",
  );

  const sellArtifact: DailyDecisionArtifact = {
    ...buyArtifact,
    action: "sell",
    approved_size: { kind: "sell_percent", percent: 25 },
    entryConfirmed: true,
    projection: { ...buyArtifact.projection, action: "sell", decision: "REDUCE", suggested_sell_percent: 25 },
  };

  const sellOk = validateExecutionAgainstArtifact(sellArtifact, {
    side: "sell",
    symbol: "HDFCBANK",
    sellPercent: 25,
  });
  assert(sellOk.ok === true && sellOk.sellPercent === 25,
    "Exact sell percent must authorize",
  );

  const sellWrongPct = validateExecutionAgainstArtifact(sellArtifact, {
    side: "sell",
    symbol: "HDFCBANK",
    sellPercent: 50,
  });
  assert(sellWrongPct.ok === false && sellWrongPct.code === "wrong_size",
    "Wrong sell percent must refuse",
  );
}
