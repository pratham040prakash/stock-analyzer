export type SellTrimMode = "partial" | "full_exit";

export type SellTrimResolution = {
  mode: SellTrimMode;
  quantity: number;
  holdingQty: number;
  requestedPercent: number;
  effectivePercent: number;
};

export function isPartialTrimPossible(
  holdingQty: number,
  sellPercent: number,
): boolean {
  if (holdingQty < 1 || !Number.isFinite(sellPercent)) {
    return false;
  }

  const pct = Math.min(100, Math.max(1, Math.round(sellPercent)));
  return Math.floor((holdingQty * pct) / 100) >= 1;
}

/** Maps portfolio trim % to whole-share quantity on Zerodha. */
export function resolveSellTrim(
  holdingQty: number,
  sellPercent: number,
): SellTrimResolution | null {
  if (holdingQty < 1 || !Number.isFinite(sellPercent)) {
    return null;
  }

  const requestedPercent = Math.min(100, Math.max(1, Math.round(sellPercent)));
  const partialQty = Math.floor((holdingQty * requestedPercent) / 100);

  if (partialQty >= 1) {
    return {
      mode: "partial",
      quantity: partialQty,
      holdingQty,
      requestedPercent,
      effectivePercent: Math.min(
        100,
        Math.round((partialQty / holdingQty) * 100),
      ),
    };
  }

  return {
    mode: "full_exit",
    quantity: holdingQty,
    holdingQty,
    requestedPercent,
    effectivePercent: 100,
  };
}

export function shareCountLabel(quantity: number): string {
  return quantity === 1 ? "1 share" : `${quantity} shares`;
}

export function buildSellTrimHeadline(
  symbol: string,
  resolution: SellTrimResolution,
): string {
  if (resolution.mode === "full_exit") {
    if (resolution.holdingQty === 1) {
      return `Sell your only share of ${symbol}`;
    }

    return `Sell all ${shareCountLabel(resolution.holdingQty)} of ${symbol}`;
  }

  if (resolution.effectivePercent === resolution.requestedPercent) {
    return `Trim ${resolution.requestedPercent}% of ${symbol}`;
  }

  return `Sell ${shareCountLabel(resolution.quantity)} of ${symbol}`;
}

export function buildSellTrimSubline(
  resolution: SellTrimResolution,
  options?: {
    currentWeight?: number;
    targetWeightAfter?: number;
  },
): string {
  if (resolution.mode === "full_exit") {
    const reason =
      resolution.holdingQty === 1
        ? `A ${resolution.requestedPercent}% trim is not possible with 1 share.`
        : `A ${resolution.requestedPercent}% trim needs more shares than you hold.`;

    return `${reason} Sell the full position to exit, or hold and skip today's trim.`;
  }

  const weightNote =
    options?.currentWeight !== undefined &&
    options?.targetWeightAfter !== undefined
      ? ` Position ${Math.round(options.currentWeight)}% → ~${Math.round(options.targetWeightAfter)}% after selling ${shareCountLabel(resolution.quantity)}.`
      : "";

  if (resolution.effectivePercent === resolution.requestedPercent) {
    return `Sells ${shareCountLabel(resolution.quantity)} on Zerodha.${weightNote}`;
  }

  return `Closest whole-share trim: ${shareCountLabel(resolution.quantity)} (~${resolution.effectivePercent}% of your position).${weightNote}`;
}

export function buildSellConfirmPrompt(
  symbol: string,
  resolution: SellTrimResolution,
): string {
  if (resolution.mode === "full_exit") {
    return `Sell entire position (${shareCountLabel(resolution.quantity)}) of ${symbol}?`;
  }

  if (resolution.effectivePercent === resolution.requestedPercent) {
    return `Sell ${shareCountLabel(resolution.quantity)} (${resolution.requestedPercent}% of ${symbol})?`;
  }

  return `Sell ${shareCountLabel(resolution.quantity)} (~${resolution.effectivePercent}% of ${symbol})?`;
}

export function runSellTrimSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Sell trim self-check failed: ${message}`);
    }
  };

  const oneShare = resolveSellTrim(1, 4);
  assert(oneShare?.mode === "full_exit", "1 share at 4% must require full exit");
  assert(oneShare?.quantity === 1, "Full exit must sell 1 share");

  const partial = resolveSellTrim(100, 25);
  assert(partial?.mode === "partial", "100 shares at 25% must allow partial trim");
  assert(partial?.quantity === 25, "25 shares must trim at 25%");

  const rounded = resolveSellTrim(8, 15);
  assert(rounded?.mode === "partial", "8 shares at 15% must allow 1-share trim");
  assert(rounded?.quantity === 1, "8 shares at 15% must sell 1 share");

  const tinyPartial = resolveSellTrim(2, 4);
  assert(
    tinyPartial?.mode === "full_exit",
    "2 shares at 4% cannot partial trim in whole shares",
  );

  assert(
    !isPartialTrimPossible(1, 4),
    "Partial trim must be impossible for 1 share at 4%",
  );
  assert(
    isPartialTrimPossible(25, 4),
    "Partial trim must be possible with enough shares",
  );

  if (!oneShare) {
    throw new Error("Sell trim self-check failed: expected oneShare resolution");
  }

  const headline = buildSellTrimHeadline("HEROMOTOCO", oneShare);
  assert(
    headline.includes("only share"),
    "Headline must explain single-share full exit",
  );
}
