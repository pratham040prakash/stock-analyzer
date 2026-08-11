export type ParsedInvalidationRule =
  | { kind: "price_below"; threshold: number }
  | { kind: "drawdown_pct"; threshold: number }
  | { kind: "text_only" };

export function parseInvalidationRule(text: string): ParsedInvalidationRule {
  const normalized = text.trim().toLowerCase();

  const priceMatch = normalized.match(
    /(?:below|under|breaks?|close[s]? below)\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)/i,
  );

  if (priceMatch?.[1]) {
    const threshold = Number(priceMatch[1].replace(/,/g, ""));

    if (Number.isFinite(threshold) && threshold > 0) {
      return { kind: "price_below", threshold };
    }
  }

  const drawdownMatch = normalized.match(/(?:down|loss|drop|drawdown)\s*([\d]+(?:\.\d+)?)\s*%/i);

  if (drawdownMatch?.[1]) {
    const threshold = Number(drawdownMatch[1]);

    if (Number.isFinite(threshold) && threshold > 0) {
      return { kind: "drawdown_pct", threshold };
    }
  }

  return { kind: "text_only" };
}

export function runParseInvalidationRuleSelfCheck(): void {
  const price = parseInvalidationRule("Break below ₹2500");

  if (price.kind !== "price_below" || price.threshold !== 2500) {
    throw new Error("Invalidation parse self-check failed: price");
  }

  const drawdown = parseInvalidationRule("Down 20% from cost");

  if (drawdown.kind !== "drawdown_pct" || drawdown.threshold !== 20) {
    throw new Error("Invalidation parse self-check failed: drawdown");
  }
}
