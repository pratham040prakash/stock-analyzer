import type { DailyVerdict, DailyVerdictPresentation } from "@/lib/dailyLoop/dailyVerdict";
import type { TodayExecutionKind } from "@/lib/dailyLoop/todaySurface";
import type { UserIntent } from "@/types/intent";
import { formatInr } from "@/lib/funds";

function formatMarkInr(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}

export const FIRST_BUY_HOLD_LABEL = "2–8 weeks";

export type FirstBuySize = {
  cashInr: number;
  ticketInr: number;
  leftoverInr: number;
};

export type FirstBuyPlanLines = {
  entryInr: number | null;
  stopInr: number | null;
  holdLabel: string | null;
};

export function isEmptyBook(input: {
  openHoldingsCount: number;
  portfolioValue?: number | null;
}): boolean {
  const value = input.portfolioValue;
  const valueEmpty =
    value === null || value === undefined || !Number.isFinite(value) || value <= 0;
  return input.openHoldingsCount === 0 && valueEmpty;
}

export function isStarterBook(input: {
  openHoldingsCount: number;
  portfolioValue?: number | null;
}): boolean {
  const value = input.portfolioValue;
  const hasValue =
    value !== null && value !== undefined && Number.isFinite(value) && value > 0;
  return input.openHoldingsCount === 1 && hasValue;
}

export function isYoungBook(input: {
  openHoldingsCount: number;
  portfolioValue?: number | null;
}): boolean {
  const value = input.portfolioValue;
  const hasValue =
    value !== null && value !== undefined && Number.isFinite(value) && value > 0;
  return hasValue && input.openHoldingsCount >= 1 && input.openHoldingsCount <= 2;
}

export type YoungBookHolding = {
  tradingsymbol?: string | null;
  quantity?: number | null;
  last_price?: number | null;
  average_price?: number | null;
  value?: number | null;
};

export function youngBookHoldingValue(holding: YoungBookHolding): number {
  const marked = holding.value;
  if (marked !== null && marked !== undefined && Number.isFinite(marked) && marked > 0) {
    return marked;
  }

  const quantity = holding.quantity ?? 0;
  const last = holding.last_price ?? 0;
  if (!Number.isFinite(quantity) || !Number.isFinite(last) || quantity <= 0 || last <= 0) {
    return 0;
  }

  return quantity * last;
}

export function orderYoungBookHoldings<T extends YoungBookHolding>(holdings: T[]): T[] {
  return [...holdings].sort((left, right) => {
    const quantityDelta = (right.quantity ?? 0) - (left.quantity ?? 0);
    if (quantityDelta !== 0) {
      return quantityDelta;
    }

    const valueDelta = youngBookHoldingValue(right) - youngBookHoldingValue(left);
    if (valueDelta !== 0) {
      return valueDelta;
    }

    return (left.tradingsymbol ?? "").localeCompare(right.tradingsymbol ?? "");
  });
}

export function buildYoungBookWaitCopy(input: {
  symbols?: Array<string | null | undefined>;
  nextSymbol?: string | null;
  tapeHardWait?: boolean;
}): { headline: string; subline: string } {
  const names = [...new Set(
    (input.symbols ?? [])
      .map((symbol) => symbol?.trim().toUpperCase())
      .filter((symbol): symbol is string => Boolean(symbol)),
  )];
  const next = input.nextSymbol?.trim().toUpperCase();

  if (names.length === 2) {
    return {
      headline: `Hold ${names[0]} and ${names[1]}`,
      subline: input.tapeHardWait
        ? "Index is range-bound. No add, no trim."
        : next
          ? `Two names are the book. Cash waits on ${next}.`
          : "Two names are the book. No trim today.",
    };
  }

  if (names.length === 1) {
    return buildStarterBookWaitCopy({ symbol: names[0] });
  }

  return {
    headline: "Hold the book",
    subline: "No add, no trim today.",
  };
}

export function buildYoungBookCashCopy(input: {
  cashInr?: number | null;
  nextSymbol?: string | null;
}): {
  amountLabel: string;
  line: string;
} | null {
  const cashInr = input.cashInr;
  if (cashInr === null || cashInr === undefined || !Number.isFinite(cashInr) || cashInr <= 0) {
    return null;
  }

  const next = input.nextSymbol?.trim().toUpperCase();
  return {
    amountLabel: formatInr(cashInr),
    line: next
      ? `Stays in cash until ${next} confirms.`
      : "Stays in cash. No third name today.",
  };
}

export function isFirstBuyCandidate(input: {
  emptyBook: boolean;
  executionKind: TodayExecutionKind;
  symbol?: string;
  deployAmount?: number;
}): boolean {
  return (
    input.emptyBook &&
    input.executionKind === "BUY" &&
    Boolean(input.symbol?.trim()) &&
    (input.deployAmount ?? 0) > 0
  );
}

export function buildFirstBuySize(cashInr: number, ticketInr: number): FirstBuySize {
  const cash = Math.max(0, Math.round(cashInr));
  const rawTicket = Math.max(0, Math.round(ticketInr));
  const ticket = cash > 0 ? Math.min(rawTicket, cash) : rawTicket;
  return {
    cashInr: cash,
    ticketInr: ticket,
    leftoverInr: Math.max(0, cash - ticket),
  };
}

export function formatFirstBuySizeLine(size: FirstBuySize): string {
  return `${formatInr(size.cashInr)} cash → ${formatInr(size.ticketInr)} ticket → ${formatInr(size.leftoverInr)} stays in cash`;
}

export function clampFirstBuyTicket(ticketInr: number, cashInr: number): number {
  const cash = Math.max(0, Math.round(cashInr));
  const ticket = Math.max(0, Math.round(ticketInr));
  if (cash <= 0) {
    return ticket;
  }

  return Math.min(Math.max(1, ticket), cash);
}

export function hasCompleteFirstBuyPlan(plan: FirstBuyPlanLines): boolean {
  return (
    plan.entryInr !== null &&
    plan.entryInr > 0 &&
    plan.stopInr !== null &&
    plan.stopInr > 0 &&
    Boolean(plan.holdLabel)
  );
}

export function buildFirstBuyWhy(input: {
  symbol: string;
  size: FirstBuySize;
  holdLabel: string | null;
}): string {
  const hold = input.holdLabel ?? FIRST_BUY_HOLD_LABEL;
  return `${input.symbol} is the first position — one ticket from cash, hold ${hold}.`;
}

export function buildFirstBuyHeadline(symbol: string, ticketInr: number): string {
  return `Start your book with ${formatInr(ticketInr)} in ${symbol}`;
}

export function applyFirstBuyPresentation(input: {
  presentation: DailyVerdictPresentation;
  firstBuy: boolean;
  planReady: boolean;
  symbol: string;
  ticketInr: number;
  why: string;
  brokerDone: boolean;
}): DailyVerdictPresentation {
  if (!input.firstBuy || input.brokerDone) {
    return input.presentation;
  }

  if (input.presentation.verdict === "pause") {
    return input.presentation;
  }

  if (!input.planReady) {
    return {
      ...input.presentation,
      verdict: "wait",
      displayWord: "Wait",
      headline: "Wait — first-buy plan is not ready",
      subline:
        "Need an entry, a stop, and a hold window before you start the book.",
      ctaLabel: "I waited",
      doneForToday: false,
      tradingLocked: true,
    };
  }

  if (input.presentation.verdict === "wait") {
    return {
      ...input.presentation,
      headline: input.presentation.headline,
      subline: input.why,
    };
  }

  return {
    ...input.presentation,
    displayWord: "Start",
    headline: buildFirstBuyHeadline(input.symbol, input.ticketInr),
    subline: input.why,
    ctaLabel: "Review first position",
    doneForToday: false,
    tradingLocked: false,
  };
}

export function buildEmptyBookWaitCopy(input: {
  symbol?: string;
  livePriceInr?: number | null;
  triggerInr?: number | null;
}): { headline: string; subline: string } {
  const symbol = input.symbol?.trim().toUpperCase();
  const live =
    input.livePriceInr !== null &&
    input.livePriceInr !== undefined &&
    input.livePriceInr > 0
      ? input.livePriceInr
      : null;
  const trigger =
    input.triggerInr !== null &&
    input.triggerInr !== undefined &&
    input.triggerInr > 0
      ? input.triggerInr
      : null;

  if (symbol && live && trigger) {
    return {
      headline: `Wait — ${symbol} is at ${formatInr(live)}, not through it`,
      subline: `Buy above ${formatInr(trigger)}. Cash stays put until it confirms.`,
    };
  }

  if (symbol && trigger) {
    return {
      headline: `Wait — ${symbol} has not confirmed`,
      subline: `Buy above ${formatInr(trigger)}. Cash stays put.`,
    };
  }

  return {
    headline: "Wait — cash stays in the account",
    subline: "No first position until a name confirms.",
  };
}

export type StarterBookHoldLines = {
  symbol: string;
  sharesLabel: string;
  position: string;
  marks: string;
  lastLabel: string | null;
  avgLabel: string | null;
  dayPnlLabel: string | null;
  dayPnlInr: number | null;
  vsBuyLabel: string | null;
  vsBuyInr: number | null;
  vsBuyPct: number | null;
  plan: string | null;
  holdLabel: string | null;
  stopLabel: string | null;
  cashLabel: string | null;
  next: string | null;
  nextEyebrow: string | null;
};

export function buildStarterBookHoldLines(input: {
  symbol?: string | null;
  quantity?: number | null;
  averagePriceInr?: number | null;
  lastPriceInr?: number | null;
  dayPnlInr?: number | null;
  stopInr?: number | null;
  holdLabel?: string | null;
  cashInr?: number | null;
}): StarterBookHoldLines | null {
  const symbol = input.symbol?.trim().toUpperCase();
  const quantity = input.quantity;
  if (!symbol || quantity === null || quantity === undefined || quantity <= 0) {
    return null;
  }

  const sharesLabel = quantity === 1 ? "1 share" : `${Math.round(quantity)} shares`;
  const avg = input.averagePriceInr;
  const last = input.lastPriceInr;
  const dayPnl = input.dayPnlInr;
  const hasAvg = avg !== null && avg !== undefined && Number.isFinite(avg) && avg > 0;
  const hasLast = last !== null && last !== undefined && Number.isFinite(last) && last > 0;
  const marks: string[] = [];
  const avgLabel = hasAvg ? `Avg ${formatMarkInr(avg)}` : null;
  const lastLabel = hasLast ? formatMarkInr(last) : null;

  if (avgLabel) {
    marks.push(avgLabel);
  }
  if (hasLast) {
    marks.push(`Last ${formatInr(last)}`);
  }

  let dayPnlLabel: string | null = null;
  let dayPnlInr: number | null = null;
  if (dayPnl !== null && dayPnl !== undefined && Number.isFinite(dayPnl)) {
    dayPnlInr = dayPnl;
    dayPnlLabel =
      dayPnl === 0
        ? "Flat today"
        : `${dayPnl > 0 ? "+" : "−"}${formatInr(Math.abs(dayPnl))} today`;
    marks.push(dayPnlLabel);
  }

  let vsBuyInr: number | null = null;
  let vsBuyPct: number | null = null;
  let vsBuyLabel: string | null = null;
  if (hasAvg && hasLast) {
    vsBuyInr = last - avg;
    vsBuyPct = (vsBuyInr / avg) * 100;
    vsBuyLabel =
      Math.abs(vsBuyInr) < 0.5
        ? "At your buy"
        : vsBuyInr > 0
          ? `${formatInr(vsBuyInr)} above your buy`
          : `${formatInr(Math.abs(vsBuyInr))} below your buy`;
  }

  const stop = input.stopInr;
  const holdLabel = input.holdLabel?.trim() || null;
  const hasStop = stop !== null && stop !== undefined && Number.isFinite(stop) && stop > 0;
  const stopLabel = hasStop ? `Stop ${formatInr(stop)}` : null;
  const planParts = [stopLabel, holdLabel ? `Hold ${holdLabel}` : null].filter(
    (part): part is string => Boolean(part),
  );

  const cash = input.cashInr;
  const hasCash = cash !== null && cash !== undefined && Number.isFinite(cash) && cash > 0;
  const cashLabel = hasCash ? formatInr(cash) : null;
  const next = hasCash
    ? `Waits for a second name — not more ${symbol} today.`
    : "No cash to add. The work today is to hold.";

  return {
    symbol,
    sharesLabel,
    position: `${symbol} · ${sharesLabel}`,
    marks: marks.join(" · ") || `${symbol} is live on Zerodha`,
    lastLabel,
    avgLabel,
    dayPnlLabel,
    dayPnlInr,
    vsBuyLabel,
    vsBuyInr,
    vsBuyPct,
    plan: planParts.length > 0 ? planParts.join(" · ") : null,
    holdLabel,
    stopLabel,
    cashLabel,
    next,
    nextEyebrow: hasCash ? "Ready for the next name" : "Hold the book",
  };
}

export function buildYoungBookHoldLines(input: {
  holdings: YoungBookHolding[];
}): StarterBookHoldLines[] {
  const tickets: StarterBookHoldLines[] = [];

  for (const holding of orderYoungBookHoldings(input.holdings)) {
    const lines = buildStarterBookHoldLines({
      symbol: holding.tradingsymbol,
      quantity: holding.quantity,
      averagePriceInr: holding.average_price,
      lastPriceInr: holding.last_price,
    });
    if (!lines) {
      continue;
    }

    tickets.push({
      ...lines,
      cashLabel: null,
      next: null,
      nextEyebrow: null,
    });
  }

  return tickets;
}

export function buildStarterBookWaitCopy(input: {
  symbol?: string | null;
}): { headline: string; subline: string } {
  const symbol = input.symbol?.trim().toUpperCase();
  if (symbol) {
    return {
      headline: `Hold ${symbol}`,
      subline: "One name is the book. No add today.",
    };
  }

  return {
    headline: "Hold the book",
    subline: "One name is enough. No add today.",
  };
}

export function applyStarterBookPresentation(input: {
  presentation: DailyVerdictPresentation;
  starterBook: boolean;
}): DailyVerdictPresentation {
  if (!input.starterBook || input.presentation.verdict === "trade") {
    return input.presentation;
  }

  return {
    ...input.presentation,
    ctaLabel: "I waited",
    doneForToday: false,
    tradingLocked: true,
  };
}

export function applyEmptyBookPresentation(input: {
  presentation: DailyVerdictPresentation;
  emptyBook: boolean;
  lens: UserIntent;
}): DailyVerdictPresentation {
  if (!input.emptyBook) {
    return input.presentation;
  }

  if (input.presentation.verdict === "pause") {
    return input.presentation;
  }

  if (input.lens === "protect") {
    return {
      ...input.presentation,
      verdict: "wait",
      displayWord: "Wait",
      headline: "No book to protect",
      subline: "Risk has no work until you hold a position.",
      ctaLabel: "I waited",
      doneForToday: false,
      tradingLocked: true,
    };
  }

  return {
    ...input.presentation,
    doneForToday: false,
  };
}

export function resolveEmptyBookCommitLabel(input: {
  emptyBook: boolean;
  firstBuy: boolean;
  starterBook?: boolean;
  planReady: boolean;
  verdict: DailyVerdict;
  marketOpen: boolean;
  brokerDone: boolean;
}): string | null {
  if (input.starterBook && !input.firstBuy && !input.emptyBook) {
    return input.verdict === "trade" ? null : "I waited";
  }

  if (!input.emptyBook && !input.firstBuy) {
    return null;
  }

  return resolveFirstBuyCommitLabel({
    firstBuy: input.emptyBook || input.firstBuy,
    planReady: input.planReady,
    verdict: input.verdict,
    marketOpen: input.marketOpen,
    brokerDone: input.brokerDone,
  });
}

export function resolveFirstBuyCommitLabel(input: {
  firstBuy: boolean;
  planReady: boolean;
  verdict: DailyVerdict;
  marketOpen: boolean;
  brokerDone: boolean;
}): string | null {
  if (!input.firstBuy) {
    return null;
  }

  if (input.brokerDone) {
    return "I started the book in Kite";
  }

  if (
    input.verdict === "wait" ||
    input.verdict === "pause" ||
    !input.planReady
  ) {
    return "I waited";
  }

  if (!input.marketOpen) {
    return "I will place this at open";
  }

  return "I started the book in Kite";
}

export function runFirstBuyTodaySelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`First-buy today self-check failed: ${message}`);
    }
  };

  assert(
    isEmptyBook({ openHoldingsCount: 0, portfolioValue: 0 }),
    "Zero book must be empty",
  );
  assert(
    !isEmptyBook({ openHoldingsCount: 1, portfolioValue: 0 }),
    "Open holding is not an empty book",
  );
  assert(
    isStarterBook({ openHoldingsCount: 1, portfolioValue: 1730 }),
    "One live holding is a starter book",
  );
  assert(
    !isStarterBook({ openHoldingsCount: 0, portfolioValue: 0 }),
    "Empty book is not a starter book",
  );
  assert(
    !isStarterBook({ openHoldingsCount: 2, portfolioValue: 10_000 }),
    "Two holdings are not a starter book",
  );
  assert(
    isYoungBook({ openHoldingsCount: 2, portfolioValue: 3_455 }),
    "Two live holdings are a young book",
  );
  assert(
    !isYoungBook({ openHoldingsCount: 3, portfolioValue: 50_000 }),
    "Three holdings are not a young book",
  );
  const orderedYoung = orderYoungBookHoldings([
    {
      tradingsymbol: "ADANIPORTS",
      quantity: 1,
      last_price: 1760,
      value: 1760,
    },
    {
      tradingsymbol: "COALINDIA",
      quantity: 4,
      last_price: 433,
      value: 1732,
    },
  ]);
  assert(
    orderedYoung[0]?.tradingsymbol === "COALINDIA" &&
      orderedYoung[1]?.tradingsymbol === "ADANIPORTS",
    "Young-book order is the larger stake first",
  );
  const youngTickets = buildYoungBookHoldLines({ holdings: orderedYoung });
  assert(youngTickets.length === 2, "Young-book tickets cover both names");
  assert(
    youngTickets[0]?.symbol === "COALINDIA" &&
      youngTickets[0]?.lastLabel !== null,
    "Young-book first ticket is the live first position",
  );
  assert(
    youngTickets.every((ticket) => !ticket.next && !ticket.cashLabel),
    "Young-book tickets are positions, not a cash fork",
  );
  const twoNameHold = buildYoungBookWaitCopy({
    symbols: orderedYoung.map((holding) => holding.tradingsymbol),
  });
  assert(
    twoNameHold.headline === "Hold COALINDIA and ADANIPORTS",
    "Young-book Wait names the first position first",
  );
  assert(
    twoNameHold.headline.includes("COALINDIA") &&
      twoNameHold.headline.includes("ADANIPORTS"),
    "Young-book Wait must name both holdings",
  );
  assert(
    twoNameHold.subline.includes("No trim"),
    "Young-book Wait must not be a skipped trim",
  );
  const youngCash = buildYoungBookCashCopy({ cashInr: 10_722 });
  assert(
    Boolean(
      youngCash &&
        youngCash.amountLabel.includes("10,722") &&
        youngCash.line.includes("No third name"),
    ),
    "Young-book Wait must place leftover cash",
  );
  assert(
    buildYoungBookCashCopy({
      cashInr: 10_722,
      nextSymbol: "DIVISLAB",
    })?.line.includes("DIVISLAB") === true,
    "Young-book cash must name the third-name watch",
  );
  assert(
    buildYoungBookCashCopy({ cashInr: 0 }) === null,
    "No cash line when leftover cash is empty",
  );
  assert(
    buildYoungBookWaitCopy({
      symbols: ["COALINDIA", "ADANIPORTS"],
      nextSymbol: "DIVISLAB",
    }).subline.includes("DIVISLAB"),
    "Young-book Wait must name where cash waits",
  );
  assert(
    !twoNameHold.headline.toLowerCase().includes("trim") &&
      !twoNameHold.subline.toLowerCase().includes("skip"),
    "Young-book Wait must not read as a skipped trim",
  );

  const youngWait = applyStarterBookPresentation({
    presentation: {
      verdict: "wait",
      displayWord: "Wait",
      headline: twoNameHold.headline,
      subline: twoNameHold.subline,
      ctaLabel: "You're done for today",
      doneForToday: true,
      tradingLocked: true,
    },
    starterBook: true,
  });
  assert(!youngWait.doneForToday, "Young-book Wait must not close the morning");
  assert(youngWait.ctaLabel === "I waited", "Young-book commit is I waited");
  assert(
    isFirstBuyCandidate({
      emptyBook: true,
      executionKind: "BUY",
      symbol: "COALINDIA",
      deployAmount: 2844,
    }),
    "Cash-only BUY must be first-buy",
  );
  assert(
    !isFirstBuyCandidate({
      emptyBook: false,
      executionKind: "BUY",
      symbol: "COALINDIA",
      deployAmount: 2844,
    }),
    "Existing book is not first-buy",
  );

  const size = buildFirstBuySize(14_213, 2_844);
  assert(size.leftoverInr === 11_369, "Leftover cash must follow ticket");
  assert(
    formatFirstBuySizeLine(size).includes("ticket"),
    "Size line must show ticket",
  );

  assert(
    hasCompleteFirstBuyPlan({
      entryInr: 415,
      stopInr: 390,
      holdLabel: FIRST_BUY_HOLD_LABEL,
    }),
    "Entry + stop + hold is a complete plan",
  );
  assert(
    !hasCompleteFirstBuyPlan({
      entryInr: 415,
      stopInr: null,
      holdLabel: FIRST_BUY_HOLD_LABEL,
    }),
    "Missing stop is not a complete plan",
  );

  const waitBase: DailyVerdictPresentation = {
    verdict: "trade",
    displayWord: "Trade",
    headline: "Deploy ₹2,844 into COALINDIA today",
    subline: "Exceeding allocation adds risk.",
    ctaLabel: "Review entry plan",
    doneForToday: false,
    tradingLocked: false,
  };

  const blocked = applyFirstBuyPresentation({
    presentation: waitBase,
    firstBuy: true,
    planReady: false,
    symbol: "COALINDIA",
    ticketInr: 2844,
    why: "ignored",
    brokerDone: false,
  });
  assert(blocked.verdict === "wait", "Incomplete plan must not Trade");
  assert(blocked.displayWord === "Wait", "Incomplete plan word is Wait");

  const start = applyFirstBuyPresentation({
    presentation: waitBase,
    firstBuy: true,
    planReady: true,
    symbol: "COALINDIA",
    ticketInr: 2844,
    why: "COALINDIA is the first position — one ticket from cash, hold 2–8 weeks.",
    brokerDone: false,
  });
  assert(start.displayWord === "Start", "Ready first-buy word is Start");
  assert(start.headline.includes("Start your book"), "Ready first-buy headline");
  assert(!start.subline.includes("Exceeding allocation"), "Why must not be a warning");

  assert(
    resolveFirstBuyCommitLabel({
      firstBuy: true,
      planReady: false,
      verdict: "wait",
      marketOpen: true,
      brokerDone: false,
    }) === "I waited",
    "No plan commit is wait",
  );
  assert(
    resolveFirstBuyCommitLabel({
      firstBuy: true,
      planReady: true,
      verdict: "trade",
      marketOpen: false,
      brokerDone: false,
    }) === "I will place this at open",
    "After-hours commit is place at open",
  );
  assert(
    resolveFirstBuyCommitLabel({
      firstBuy: true,
      planReady: true,
      verdict: "trade",
      marketOpen: true,
      brokerDone: false,
    }) === "I started the book in Kite",
    "Open-market commit is started the book",
  );

  const namedWait = buildEmptyBookWaitCopy({
    symbol: "COALINDIA",
    livePriceInr: 431,
    triggerInr: 431,
  });
  assert(
    namedWait.headline.includes("COALINDIA") && namedWait.headline.includes("431"),
    "Empty-book Wait must name the setup and price",
  );

  const risk = applyEmptyBookPresentation({
    presentation: waitBase,
    emptyBook: true,
    lens: "protect",
  });
  assert(risk.headline === "No book to protect", "Empty Risk must not invent a name");
  assert(!risk.doneForToday, "Empty-book Wait must not close the morning");

  assert(
    resolveEmptyBookCommitLabel({
      emptyBook: true,
      firstBuy: false,
      planReady: false,
      verdict: "wait",
      marketOpen: true,
      brokerDone: false,
    }) === "I waited",
    "Empty-book Wait commit is I waited",
  );

  const starterWait = applyStarterBookPresentation({
    presentation: {
      ...waitBase,
      verdict: "wait",
      displayWord: "Wait",
      headline: "100% of available cash stays idle.",
      doneForToday: true,
    },
    starterBook: true,
  });
  assert(!starterWait.doneForToday, "Starter-book Wait must not close the morning");
  assert(starterWait.ctaLabel === "I waited", "Starter-book commit is I waited");

  const namedHold = buildStarterBookWaitCopy({ symbol: "COALINDIA" });
  assert(
    namedHold.headline === "Hold COALINDIA",
    "Starter-book Wait must name the holding",
  );

  const holdCard = buildStarterBookHoldLines({
    symbol: "COALINDIA",
    quantity: 4,
    averagePriceInr: 432,
    lastPriceInr: 431,
    dayPnlInr: -1,
    stopInr: 390,
    holdLabel: FIRST_BUY_HOLD_LABEL,
    cashInr: 14_213,
  });
  if (!holdCard) {
    throw new Error("First-buy today self-check failed: Starter hold card must build");
  }
  assert(holdCard.position.includes("4 shares"), "Hold card must show size");
  assert(holdCard.marks.includes("Avg"), "Hold card must show average");
  assert(holdCard.lastLabel !== null, "Hold card must show last price");
  assert(Boolean(holdCard.vsBuyLabel), "Hold card must show vs-buy");
  assert(Boolean(holdCard.plan?.includes("390")), "Hold card must show the stop");

  const holdCardNoHorizon = buildStarterBookHoldLines({
    symbol: "COALINDIA",
    quantity: 4,
    averagePriceInr: 432,
    lastPriceInr: 433,
    cashInr: 12_489,
  });
  if (!holdCardNoHorizon) {
    throw new Error("First-buy today self-check failed: Hold card without horizon");
  }
  assert(
    holdCardNoHorizon.holdLabel === null,
    "Starter hold card must not invent a 2–8 week path",
  );
  assert(
    Boolean(holdCard.next?.includes("second name")),
    "Hold card must say what leftover cash is for",
  );

  assert(
    resolveEmptyBookCommitLabel({
      emptyBook: false,
      firstBuy: false,
      starterBook: true,
      planReady: false,
      verdict: "wait",
      marketOpen: true,
      brokerDone: false,
    }) === "I waited",
    "Starter-book Wait commit is I waited",
  );
}
