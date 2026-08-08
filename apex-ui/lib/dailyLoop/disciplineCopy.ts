export function getDisciplineInterpretation(trustScore: number): string {
  const score = Number.isFinite(trustScore)
    ? Math.max(0, Math.min(100, Math.round(trustScore)))
    : 50;

  if (score >= 70) {
    return "You're trusting the process.";
  }

  if (score >= 40) {
    return "You're building consistency.";
  }

  return "Follow the system — small steps compound.";
}
