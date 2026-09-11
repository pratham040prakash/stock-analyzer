import type { ExplicitUnknown, MarketTrend } from "@/types/decision";

/**
 * Wave 2 fail-closed freshness policy.
 *
 * Freshness is derived from real source `observed_at` timestamps only —
 * never from the fact that a call succeeded. When a source is missing,
 * partial, or older than the allowed window it is downgraded to
 * `unknown` with a named reason, which the artifact builder turns into
 * a blocker and non-executable WAIT.
 */

export const SOURCE_STALENESS_MS = {
  portfolio: 30 * 60 * 1000,
  capital: 15 * 60 * 1000,
  broker: 15 * 60 * 1000,
  market: 60 * 60 * 1000,
  entry: 10 * 60 * 1000,
} as const;

export type FreshnessKey = keyof typeof SOURCE_STALENESS_MS;

function ageMs(observedAt: string, now: string): number {
  const observed = Date.parse(observedAt);
  const nowMs = Date.parse(now);
  if (!Number.isFinite(observed) || !Number.isFinite(nowMs)) {
    return Number.POSITIVE_INFINITY;
  }
  return Math.max(0, nowMs - observed);
}

export function isStale(
  key: FreshnessKey,
  observedAt: string,
  now: string,
): boolean {
  return ageMs(observedAt, now) > SOURCE_STALENESS_MS[key];
}

function unknownStale<T>(
  key: FreshnessKey,
  observedAt: string,
): ExplicitUnknown<T> {
  const minutes = Math.round(SOURCE_STALENESS_MS[key] / 60_000);
  return {
    status: "unknown",
    value: null,
    observed_at: null,
    reason: `${key} data is stale (older than ${minutes}m, observed_at=${observedAt})`,
  };
}

export function enforceFreshness<T>(
  key: FreshnessKey,
  source: ExplicitUnknown<T>,
  now: string,
): ExplicitUnknown<T> {
  if (source.status !== "known") {
    return source;
  }
  return isStale(key, source.observed_at, now)
    ? unknownStale<T>(key, source.observed_at)
    : source;
}

export function enforcePortfolioFreshness(
  observedAt: string | null,
  now: string,
): { observedAt: string | null; blocker: string | null } {
  if (!observedAt) {
    return { observedAt: null, blocker: null };
  }
  if (isStale("portfolio", observedAt, now)) {
    return {
      observedAt: null,
      blocker: `portfolio data is stale (older than ${Math.round(
        SOURCE_STALENESS_MS.portfolio / 60_000,
      )}m, observed_at=${observedAt})`,
    };
  }
  return { observedAt, blocker: null };
}

export type FreshnessSources = {
  portfolioObservedAt: string | null;
  capital: ExplicitUnknown<{
    available_cash_inr: number;
    portfolio_value_inr: number;
  }>;
  broker: ExplicitUnknown<{ broker: "zerodha"; connection: "connected" }>;
  market: ExplicitUnknown<{ trend: MarketTrend; session: string }>;
  entry: ExplicitUnknown<{ confirmed: boolean; reason: string }>;
};

export type FreshnessResult = {
  sources: FreshnessSources;
  extraBlockers: string[];
};

export function applyFreshnessPolicy(
  sources: FreshnessSources,
  now: string,
): FreshnessResult {
  const portfolio = enforcePortfolioFreshness(sources.portfolioObservedAt, now);
  const capital = enforceFreshness("capital", sources.capital, now);
  const broker = enforceFreshness("broker", sources.broker, now);
  const market = enforceFreshness("market", sources.market, now);
  const entry = enforceFreshness("entry", sources.entry, now);

  const extraBlockers = [portfolio.blocker].filter(
    (blocker): blocker is string => Boolean(blocker),
  );

  return {
    sources: {
      portfolioObservedAt: portfolio.observedAt,
      capital,
      broker,
      market,
      entry,
    },
    extraBlockers,
  };
}

export function runFreshnessSelfCheck(): void {
  const now = "2026-09-11T10:00:00.000Z";
  const known = "2026-09-11T09:59:00.000Z";
  const oldForCapital = "2026-09-11T08:00:00.000Z";
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Freshness self-check failed: ${message}`);
    }
  };

  assert(
    !isStale("capital", known, now),
    "One-minute observation must not be stale",
  );

  assert(
    isStale("capital", oldForCapital, now),
    "30-minute-old capital must be stale",
  );

  const stale = enforceFreshness(
    "capital",
    {
      status: "known",
      value: { available_cash_inr: 1000, portfolio_value_inr: 5000 },
      observed_at: oldForCapital,
    },
    now,
  );
  assert(
    stale.status === "unknown",
    "Stale known capital must downgrade to unknown",
  );

  const fresh = enforceFreshness(
    "broker",
    {
      status: "known",
      value: { broker: "zerodha", connection: "connected" },
      observed_at: known,
    },
    now,
  );
  assert(
    fresh.status === "known",
    "Fresh known broker must be preserved",
  );

  const policy = applyFreshnessPolicy(
    {
      portfolioObservedAt: oldForCapital,
      capital: {
        status: "known",
        value: { available_cash_inr: 0, portfolio_value_inr: 0 },
        observed_at: oldForCapital,
      },
      broker: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "not connected",
      },
      market: {
        status: "known",
        value: { trend: "sideways", session: "market_open" },
        observed_at: known,
      },
      entry: {
        status: "known",
        value: { confirmed: false, reason: "" },
        observed_at: known,
      },
    },
    now,
  );

  assert(
    policy.sources.portfolioObservedAt === null,
    "Stale portfolio timestamp must be dropped",
  );
  assert(
    policy.sources.capital.status === "unknown",
    "Stale capital must be downgraded",
  );
  assert(
    policy.sources.broker.status === "unknown",
    "Unknown broker must remain unknown",
  );
  assert(
    policy.sources.market.status === "known",
    "Fresh market must be preserved",
  );
  assert(
    policy.extraBlockers.length === 1 &&
      policy.extraBlockers[0].startsWith("portfolio data is stale"),
    "Stale portfolio must produce a named blocker",
  );
}
