import { buildFirstBuySize, type FirstBuySize } from "@/lib/dailyLoop/firstBuyToday";
import { formatInr, safeInvestAmount } from "@/lib/funds";

export type SecondNamePick = {
  stock: string;
  score: number;
  price?: number;
  activationLevel?: number;
};

export type SecondNameWatch = {
  symbol: string;
  livePriceInr: number | null;
  triggerInr: number | null;
  through: boolean;
  size: FirstBuySize;
  lastLabel: string | null;
  triggerLabel: string | null;
  ticketLabel: string;
  leftoverLabel: string;
  statusLine: string;
  eyebrow: string;
};

export function pickSecondName<T extends SecondNamePick>(input: {
  heldSymbol?: string | null;
  picks?: T[] | null;
}): T | null {
  const held = input.heldSymbol?.trim().toUpperCase();
  const ranked = [...(input.picks ?? [])]
    .filter((pick) => {
      const symbol = pick.stock.trim().toUpperCase();
      return symbol.length > 0 && symbol !== held;
    })
    .sort((left, right) => (right.score ?? 0) - (left.score ?? 0));

  return ranked[0] ?? null;
}

export function buildSecondNameWatch<T extends SecondNamePick>(input: {
  heldSymbol?: string | null;
  picks?: T[] | null;
  cashInr: number;
  livePriceInr?: number | null;
  ticketInr?: number | null;
}): SecondNameWatch | null {
  const cash = Math.max(0, Math.round(input.cashInr));
  if (cash <= 0) {
    return null;
  }

  const pick = pickSecondName(input);
  if (!pick) {
    return null;
  }

  const symbol = pick.stock.trim().toUpperCase();
  const liveHint = input.livePriceInr ?? pick.price ?? null;
  const live =
    liveHint !== null && liveHint !== undefined && Number.isFinite(liveHint) && liveHint > 0
      ? liveHint
      : null;
  const trigger =
    pick.activationLevel !== null &&
    pick.activationLevel !== undefined &&
    Number.isFinite(pick.activationLevel) &&
    pick.activationLevel > 0
      ? pick.activationLevel
      : null;
  const ticketHint =
    input.ticketInr !== null &&
    input.ticketInr !== undefined &&
    Number.isFinite(input.ticketInr) &&
    input.ticketInr > 0
      ? input.ticketInr
      : safeInvestAmount(cash);
  const size = buildFirstBuySize(cash, ticketHint);

  if (size.ticketInr <= 0) {
    return null;
  }

  const through = live !== null && trigger !== null && live >= trigger;
  const statusLine = through
    ? `${symbol} is at the buy line. Place in Kite — Today stays Wait until you do.`
    : trigger
      ? `Buy above ${formatInr(trigger)}. Cash stays put until it confirms.`
      : `Watch ${symbol}. No buy line yet — cash stays put.`;

  return {
    symbol,
    livePriceInr: live,
    triggerInr: trigger,
    through,
    size,
    lastLabel: live !== null ? formatInr(live) : null,
    triggerLabel: trigger !== null ? `Buy above ${formatInr(trigger)}` : null,
    ticketLabel: `${formatInr(size.ticketInr)} ticket`,
    leftoverLabel: `${formatInr(size.leftoverInr)} stays in cash`,
    statusLine,
    eyebrow: "Next name",
  };
}

export function runSecondNameTodaySelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Second-name today self-check failed: ${message}`);
    }
  };

  const picks = [
    { stock: "COALINDIA", score: 90, price: 433, activationLevel: 433 },
    { stock: "DIVISLAB", score: 72, price: 9500, activationLevel: 9575 },
    { stock: "INFY", score: 60, price: 1800, activationLevel: 1820 },
  ];

  const picked = pickSecondName({ heldSymbol: "COALINDIA", picks });
  assert(picked?.stock === "DIVISLAB", "Second name must skip the held name");

  assert(
    pickSecondName({
      heldSymbol: "COALINDIA",
      picks: [{ stock: "COALINDIA", score: 90 }],
    }) === null,
    "No second name when the book is the only pick",
  );

  assert(
    buildSecondNameWatch({
      heldSymbol: "COALINDIA",
      picks,
      cashInr: 0,
    }) === null,
    "No second name without leftover cash",
  );

  const watch = buildSecondNameWatch({
    heldSymbol: "COALINDIA",
    picks,
    cashInr: 12_489,
    livePriceInr: 9500,
  });
  if (!watch) {
    throw new Error("Second-name today self-check failed: Watch must build");
  }
  assert(watch.symbol === "DIVISLAB", "Watch must name DIVISLAB");
  assert(watch.through === false, "Below the line must stay Wait");
  assert(Boolean(watch.triggerLabel?.includes("9,575")), "Watch must show buy-above");
  assert(watch.size.ticketInr > 0, "Watch must size a ticket from cash");
  assert(watch.size.leftoverInr >= 0, "Watch must leave leftover cash");
  assert(watch.statusLine.includes("confirms"), "Watch must wait for confirmation");
}
