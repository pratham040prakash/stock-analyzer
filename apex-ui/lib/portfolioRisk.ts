export type PortfolioRiskLevel = "High" | "Medium" | "Low";

export function portfolioRiskScore(topAllocationPct: number): number {
  if (topAllocationPct > 80) {
    return 9;
  }
  if (topAllocationPct > 60) {
    return 7;
  }
  return 4;
}

export function portfolioRiskLevel(score: number): PortfolioRiskLevel {
  if (score >= 8) {
    return "High";
  }
  if (score >= 6) {
    return "Medium";
  }
  return "Low";
}

export function portfolioRiskFromAllocation(topAllocationPct: number): {
  risk_score: number;
  risk_level: PortfolioRiskLevel;
} {
  const risk_score = portfolioRiskScore(topAllocationPct);
  return {
    risk_score,
    risk_level: portfolioRiskLevel(risk_score),
  };
}

export function portfolioRiskLabel(topAllocationPct: number): string {
  const { risk_score, risk_level } = portfolioRiskFromAllocation(topAllocationPct);
  return `Risk Score: ${risk_score}/10 (${risk_level})`;
}
