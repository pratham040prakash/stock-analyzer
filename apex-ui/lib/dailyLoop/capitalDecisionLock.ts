import type { CapitalDecision } from "@/lib/dailyLoop/capitalDecision";

export type DecisionLockType = "REDUCE" | "DEPLOY" | "HOLD";

export type CapitalDecisionLock = {
  type: DecisionLockType;
  messagePrimary: string;
  messageSecondary: string;
};

const DECISION_LOCK_COPY: Record<
  DecisionLockType,
  { messagePrimary: string; messageSecondary: string }
> = {
  HOLD: {
    messagePrimary: "No action required today.",
    messageSecondary: "Following this protects your capital.",
  },
  DEPLOY: {
    messagePrimary: "This allocation is within safe limits.",
    messageSecondary: "Do not exceed recommended deployment.",
  },
  REDUCE: {
    messagePrimary: "This reduction is required to control risk.",
    messageSecondary: "Delaying increases exposure.",
  },
};

export function resolveDecisionLockType(
  decision: CapitalDecision,
): DecisionLockType {
  if (decision.actions.some((action) => action.action === "SELL")) {
    return "REDUCE";
  }

  if (decision.deploymentPercentage > 0) {
    return "DEPLOY";
  }

  return "HOLD";
}

export function buildDecisionLock(
  decision: CapitalDecision,
): CapitalDecisionLock {
  const type = resolveDecisionLockType(decision);
  const copy = DECISION_LOCK_COPY[type];

  return {
    type,
    messagePrimary: copy.messagePrimary,
    messageSecondary: copy.messageSecondary,
  };
}

/** Adds execution confidence copy without changing decision logic. */
export function attachDecisionLock(decision: CapitalDecision): CapitalDecision {
  if (decision.mode === "explore") {
    return decision;
  }

  return {
    ...decision,
    decisionLock: buildDecisionLock(decision),
  };
}

export function runCapitalDecisionLockSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Capital decision-lock self-check failed: ${message}`);
    }
  };

  const base = {
    mode: "grow" as const,
    stance: "No Deployment" as const,
    availableCash: 100_000,
    portfolioValue: 400_000,
    totalCapital: 500_000,
    deployAmount: 0,
    cashPercentage: 100,
    deploymentPercentage: 0,
    exploreSetups: [],
    heroHeadline: "",
    heroSubline: "",
    heroAccountability: "",
    portfolioStance: "",
    portfolioStanceDetail: "",
    primaryAction: "",
    primaryActionDetail: "",
  };

  const holdLock = buildDecisionLock({ ...base, actions: [] });
  assert(holdLock.type === "HOLD", "Empty deployment must lock as HOLD");

  const deployLock = buildDecisionLock({
    ...base,
    deploymentPercentage: 20,
    deployAmount: 20_000,
    actions: [
      {
        symbol: "INFY",
        action: "BUY",
        deployPercentage: 20,
        deployAmount: 20_000,
        reason: { missing: "", confirm: "", timing: "" },
      },
    ],
  });
  assert(deployLock.type === "DEPLOY", "Active deployment must lock as DEPLOY");

  const reduceLock = buildDecisionLock({
    ...base,
    actions: [
      {
        symbol: "RELIANCE",
        action: "SELL",
        deployPercentage: 25,
        reason: { missing: "", confirm: "", timing: "" },
      },
    ],
  });
  assert(reduceLock.type === "REDUCE", "SELL actions must lock as REDUCE");
  assert(
    reduceLock.messagePrimary.includes("reduction"),
    "REDUCE lock must use risk reduction copy",
  );
}
