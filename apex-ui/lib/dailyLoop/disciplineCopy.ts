import { formatJudgment } from "@/lib/dailyLoop/apexVoice";

export function getDisciplineInterpretation(trustScore: number): string {
  const score = Number.isFinite(trustScore)
    ? Math.max(0, Math.min(100, Math.round(trustScore)))
    : 50;

  if (score >= 70) {
    return "You are trusting the process.";
  }

  if (score >= 40) {
    return "You are building consistency.";
  }

  return formatJudgment("Discipline is still forming", "patience matters");
}
