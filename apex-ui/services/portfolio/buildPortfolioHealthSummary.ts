import type { HoldingHealthChip } from "@/services/portfolio/holdingHealth";

export type PortfolioHealthSummaryViewModel = {
  strong: number;
  watch: number;
  risk: number;
  headline: string;
  detail: string;
};

export function buildPortfolioHealthSummary(
  chips: HoldingHealthChip[],
): PortfolioHealthSummaryViewModel {
  const strong = chips.filter((chip) => chip.grade === "Strong").length;
  const watch = chips.filter((chip) => chip.grade === "Watch").length;
  const risk = chips.filter((chip) => chip.grade === "Risk").length;
  const total = chips.length;

  let headline = "Portfolio health looks balanced.";
  let detail = `${strong} strong · ${watch} watch · ${risk} risk`;

  if (total === 0) {
    return {
      strong: 0,
      watch: 0,
      risk: 0,
      headline: "Connect broker for health scoring.",
      detail: "Sync holdings to score position health.",
    };
  }

  if (risk >= 2) {
    headline = "Portfolio health needs attention.";
    detail = `${risk} positions flagged as risk — review thesis before adding.`;
  } else if (strong >= total - 1 && risk === 0) {
    headline = "Portfolio health is strong.";
    detail = `${strong} of ${total} holdings in good shape.`;
  }

  return { strong, watch, risk, headline, detail };
}

export function runPortfolioHealthSummarySelfCheck(): void {
  const summary = buildPortfolioHealthSummary([
    { symbol: "INFY", grade: "Strong", score: 80, reason: "Test" },
    { symbol: "TCS", grade: "Risk", score: 30, reason: "Test" },
    { symbol: "YESBANK", grade: "Risk", score: 25, reason: "Test" },
  ]);

  if (summary.risk !== 2 || !summary.headline.includes("attention")) {
    throw new Error("Portfolio health summary self-check failed");
  }
}
