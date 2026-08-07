import type { Intent } from "@/types/intent";

export function formatInr(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

/** Conservative deployable amount for grow intent (~65%, rounded to ₹1,000). */
export function safeInvestAmount(availableCash: number): number {
  if (availableCash <= 0) {
    return 0;
  }

  const conservative = Math.min(
    availableCash,
    Math.round(availableCash * 0.65),
  );

  if (conservative < 1000) {
    return Math.round(availableCash);
  }

  return Math.round(conservative / 1000) * 1000;
}

export function fundsGuidanceText(
  availableCash: number,
  intent: Intent,
): string {
  if (availableCash <= 0) {
    return "No funds available. Consider selling to free capital";
  }

  if (intent === "grow") {
    const safe = safeInvestAmount(availableCash);
    return `You can invest ${formatInr(safe)} safely`;
  }

  if (intent === "explore") {
    return `Allocate your ${formatInr(availableCash)} across opportunities`;
  }

  return "Ready to deploy today";
}
