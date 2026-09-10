import { buildFirstBuySize, type FirstBuySize } from "@/lib/dailyLoop/firstBuyToday";
import { formatInr, safeInvestAmount } from "@/lib/funds";

export const WATCH_BAND_PCT = 0.03;

export type SecondNamePick = {
  stock: string;
  score: number;
  price?: number;
  activationLevel?: number;
  signals?: {
    trend?: number;
    momentum?: number;
    volume?: number;
  };
};

export type SecondNameWatch = {
  symbol: string;
  livePriceInr: number | null;
  triggerInr: number | null;
  through: boolean;
  dead: boolean;
  size: FirstBuySize;
  lastLabel: string | null;
  triggerLabel: string | null;
  killInr: number | null;
  killLabel: string | null;
  ticketLabel: string;
  leftoverLabel: string;
  statusLine: string;
  whyLine: string | null;
  eyebrow: string;
  gapInr: number | null;
  gapLabel: string | null;
};

function heldSymbolSet(input: {
  heldSymbol?: string | null;
  heldSymbols?: Array<string | null | undefined>;
}): Set<string> {
  return new Set(
    [input.heldSymbol, ...(input.heldSymbols ?? [])]
      .map((symbol) => symbol?.trim().toUpperCase())
      .filter((symbol): symbol is string => Boolean(symbol)),
  );
}

export function rankSecondNames<T extends SecondNamePick>(input: {
  heldSymbol?: string | null;
  heldSymbols?: Array<string | null | undefined>;
  picks?: T[] | null;
}): T[] {
  const held = heldSymbolSet(input);
  return [...(input.picks ?? [])]
    .filter((pick) => {
      const symbol = pick.stock.trim().toUpperCase();
      return symbol.length > 0 && !held.has(symbol);
    })
    .sort((left, right) => (right.score ?? 0) - (left.score ?? 0));
}

export function pickSecondName<T extends SecondNamePick>(input: {
  heldSymbol?: string | null;
  heldSymbols?: Array<string | null | undefined>;
  picks?: T[] | null;
}): T | null {
  return rankSecondNames(input)[0] ?? null;
}

function triggerInrOf(pick: SecondNamePick): number | null {
  const trigger = pick.activationLevel;
  if (trigger === null || trigger === undefined || !Number.isFinite(trigger) || trigger <= 0) {
    return null;
  }

  return trigger;
}

function liveInrOf(
  pick: SecondNamePick,
  input: {
    livePriceInr?: number | null;
    livePriceBySymbol?: Map<string, number> | null;
  },
): number | null {
  const symbol = pick.stock.trim().toUpperCase();
  const mapped = input.livePriceBySymbol?.get(symbol);
  if (mapped !== undefined && Number.isFinite(mapped) && mapped > 0) {
    return mapped;
  }

  const listed = pick.price;
  if (listed !== null && listed !== undefined && Number.isFinite(listed) && listed > 0) {
    return listed;
  }

  const fallback = input.livePriceInr;
  if (fallback !== null && fallback !== undefined && Number.isFinite(fallback) && fallback > 0) {
    return fallback;
  }

  return null;
}

function killInrOf(trigger: number): number {
  return Math.round(trigger * (1 - WATCH_BAND_PCT));
}

export function buildWatchThesis(pick: SecondNamePick): string {
  const trigger = triggerInrOf(pick);
  const trend = pick.signals?.trend ?? 0;
  const momentum = pick.signals?.momentum ?? 0;
  const volume = pick.signals?.volume ?? 0;
  const parts: string[] = [];

  if (trend >= 55) {
    parts.push("trend");
  }
  if (momentum >= 55) {
    parts.push("momentum");
  }
  if (volume >= 55) {
    parts.push("volume");
  }

  if (trigger && parts.length >= 2) {
    return `Break ${formatInr(trigger)} — the recent range high — only if ${parts[0]} and ${parts[1]} hold. Otherwise cash.`;
  }

  if (trigger) {
    return `Break ${formatInr(trigger)} — the recent range high — or stand aside.`;
  }

  return `${pick.stock.trim().toUpperCase()} has no line yet. Cash stays put.`;
}

function buildWatchFromPick<T extends SecondNamePick>(
  pick: T,
  input: {
    cashInr: number;
    livePriceInr?: number | null;
    livePriceBySymbol?: Map<string, number> | null;
    ticketInr?: number | null;
    eyebrow?: string;
  },
): SecondNameWatch | null {
  const cash = Math.max(0, Math.round(input.cashInr));
  const symbol = pick.stock.trim().toUpperCase();
  const live = liveInrOf(pick, input);
  const trigger = triggerInrOf(pick);
  const ticketHint =
    input.ticketInr !== null &&
    input.ticketInr !== undefined &&
    Number.isFinite(input.ticketInr) &&
    input.ticketInr > 0
      ? input.ticketInr
      : safeInvestAmount(cash);
  const size = buildFirstBuySize(cash, ticketHint);

  if (cash <= 0 || size.ticketInr <= 0 || trigger === null || live === null) {
    return null;
  }

  const killInr = killInrOf(trigger);
  const through = live >= trigger;
  const dead = live < killInr;
  const gapInr = !through && !dead ? Math.round((trigger - live) * 100) / 100 : null;
  const gapLabel = dead
    ? "Lost the line"
    : through
      ? "At the line"
      : gapInr !== null
        ? `${formatInr(gapInr)} to the line`
        : null;
  const statusLine = dead
    ? "Setup failed. Cash stays put."
    : through
      ? `${symbol} is at the buy line. Place in Kite — Today stays Wait until you do.`
      : `Buy above ${formatInr(trigger)}. Drop below ${formatInr(killInr)}.`;

  return {
    symbol,
    livePriceInr: live,
    triggerInr: trigger,
    through,
    dead,
    size,
    lastLabel: formatInr(live),
    triggerLabel: `Buy above ${formatInr(trigger)}`,
    killInr,
    killLabel: formatInr(killInr),
    ticketLabel: `${formatInr(size.ticketInr)} ticket`,
    leftoverLabel: `${formatInr(size.leftoverInr)} stays in cash`,
    statusLine,
    whyLine: buildWatchThesis(pick),
    eyebrow: input.eyebrow?.trim() || "Next name",
    gapInr,
    gapLabel,
  };
}

export function buildSecondNameWatch<T extends SecondNamePick>(input: {
  heldSymbol?: string | null;
  heldSymbols?: Array<string | null | undefined>;
  picks?: T[] | null;
  cashInr: number;
  livePriceInr?: number | null;
  livePriceBySymbol?: Map<string, number> | null;
  ticketInr?: number | null;
  eyebrow?: string;
  preferredSymbol?: string | null;
}): SecondNameWatch | null {
  const cash = Math.max(0, Math.round(input.cashInr));
  if (cash <= 0) {
    return null;
  }

  const ranked = rankSecondNames(input);
  if (ranked.length === 0) {
    return null;
  }

  const preferred = input.preferredSymbol?.trim().toUpperCase();
  if (preferred) {
    const locked = ranked.find((pick) => pick.stock.trim().toUpperCase() === preferred);
    if (locked) {
      return buildWatchFromPick(locked, input);
    }
  }

  for (const pick of ranked) {
    const watch = buildWatchFromPick(pick, input);
    if (watch && !watch.dead) {
      return watch;
    }
  }

  return null;
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
  assert(watch.dead === false, "Inside the band must stay live");
  assert(Boolean(watch.triggerLabel?.includes("9,575")), "Watch must show buy-above");
  assert(Boolean(watch.killLabel), "Watch must name a drop level");
  assert(watch.size.ticketInr > 0, "Watch must size a ticket from cash");
  assert(watch.size.leftoverInr >= 0, "Watch must leave leftover cash");
  assert(watch.statusLine.includes("Drop below"), "Watch must be two-sided");
  assert(
    Boolean(watch.gapLabel?.includes("to the line")),
    "Watch must show distance to the buy line",
  );

  const farThenClose = buildSecondNameWatch({
    heldSymbol: "COALINDIA",
    picks: [
      { stock: "WIPRO", score: 99, price: 400, activationLevel: 500 },
      { stock: "DIVISLAB", score: 72, price: 9500, activationLevel: 9575 },
    ],
    cashInr: 10_722,
  });
  assert(farThenClose?.symbol === "DIVISLAB", "Far breakouts must not take leftover cash");

  const deadLocked = buildSecondNameWatch({
    heldSymbol: "COALINDIA",
    picks,
    cashInr: 10_722,
    preferredSymbol: "DIVISLAB",
    livePriceBySymbol: new Map([["DIVISLAB", 9000]]),
  });
  assert(deadLocked?.dead === true, "Today's name stays locked if it loses the line");
  assert(deadLocked?.gapLabel === "Lost the line", "Dead watch must say the line is lost");

  const thesis = buildWatchThesis({
    stock: "DIVISLAB",
    score: 72,
    price: 9500,
    activationLevel: 9575,
    signals: { trend: 70, momentum: 62, volume: 40 },
  });
  assert(thesis.includes("9,575"), "Thesis must name the range high");
  assert(thesis.includes("trend") && thesis.includes("momentum"), "Thesis must use live signals");

  const third = pickSecondName({
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    picks: [
      ...picks,
      { stock: "ADANIPORTS", score: 80, price: 1760, activationLevel: 1780 },
    ],
  });
  assert(third?.stock === "DIVISLAB", "Third name must skip both holdings");
  const thirdWatch = buildSecondNameWatch({
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    picks,
    cashInr: 10_722,
    livePriceInr: 9500,
    eyebrow: "Third name",
  });
  assert(thirdWatch?.eyebrow === "Third name", "Two-name leftover cash is a third-name watch");
  assert(thirdWatch?.symbol === "DIVISLAB", "Third-name watch skips the book");
}
