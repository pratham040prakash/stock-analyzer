/** Position size from deployable funds, decision confidence, and portfolio risk score. */
export function getPositionSize(
  funds: number,
  confidence: number,
  risk: number,
): number {
  if (funds <= 0) {
    return 0;
  }

  const base = funds * (confidence / 100);

  const riskAdjustment = risk > 7 ? 0.5 : risk > 5 ? 0.7 : 1;

  return Math.round(base * riskAdjustment);
}
