import type { PortfolioHoldingRow } from "@/types/portfolioApi";

export type HoldingHealthGrade = "Strong" | "Watch" | "Risk";

export type HoldingHealthChip = {
  symbol: string;
  grade: HoldingHealthGrade;
  score: number;
  reason: string;
};

function gradeFromScore(score: number): HoldingHealthGrade {
  if (score >= 70) {
    return "Strong";
  }

  if (score >= 45) {
    return "Watch";
  }

  return "Risk";
}

export function scoreHoldingHealth(
  holding: PortfolioHoldingRow,
  options?: {
    concentrated?: boolean;
    isTopHolding?: boolean;
  },
): HoldingHealthChip {
  let score = 60;
  const reasons: string[] = [];

  const pnlPct =
    holding.average_price > 0
      ? ((holding.last_price - holding.average_price) / holding.average_price) * 100
      : 0;

  if (pnlPct >= 5) {
    score += 10;
    reasons.push("Unrealized gain");
  } else if (pnlPct <= -8) {
    score -= 18;
    reasons.push("Drawdown vs cost");
  }

  if (holding.allocation_pct > 50) {
    score -= 15;
    reasons.push("High concentration");
  } else if (holding.allocation_pct > 30) {
    score -= 8;
    reasons.push("Elevated weight");
  }

  if (options?.concentrated && options?.isTopHolding) {
    score -= 6;
    reasons.push("Portfolio concentrated");
  }

  score = Math.max(0, Math.min(100, Math.round(score)));

  return {
    symbol: holding.tradingsymbol,
    grade: gradeFromScore(score),
    score,
    reason: reasons[0] ?? "Within normal range",
  };
}

export function scoreAllHoldings(
  holdings: PortfolioHoldingRow[],
  options?: { concentrated?: boolean; topSymbol?: string },
): HoldingHealthChip[] {
  return holdings.map((holding) =>
    scoreHoldingHealth(holding, {
      concentrated: options?.concentrated,
      isTopHolding:
        options?.topSymbol?.trim().toUpperCase() ===
        holding.tradingsymbol.trim().toUpperCase(),
    }),
  );
}

export function runHoldingHealthSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Holding health self-check failed: ${message}`);
    }
  };

  const chip = scoreHoldingHealth({
    tradingsymbol: "RELIANCE",
    quantity: 10,
    average_price: 100,
    last_price: 120,
    pnl: 200,
    value: 1200,
    allocation_pct: 55,
  });

  assert(chip.grade === "Watch" || chip.grade === "Strong", "Healthy gain must not be Risk");
  assert(chip.score >= 45, "Score must remain in mid band");
}
