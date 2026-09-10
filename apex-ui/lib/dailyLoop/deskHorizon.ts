import { formatInr } from "@/lib/funds";
import {
  getMarketSessionPhase,
  isDeskClosedForNewPicks,
} from "@/lib/broker/marketSession";
import { deskHeartbeatLine } from "@/lib/dailyLoop/deskOs";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import type { TodayContract } from "@/lib/dailyLoop/todayContract";

export type HorizonHistoryRow = Pick<
  TodayContract,
  | "dateKey"
  | "watchSymbol"
  | "watchDead"
  | "watchThrough"
  | "outcome"
  | "outcomeLine"
  | "heldSymbols"
  | "triggerInr"
  | "closeLetter"
  | "cashMandate"
  | "holdCutsBySymbol"
  | "nameDiary"
>;

export function stampKiteFill(input: {
  symbol: string;
  quantity: number;
  now?: Date;
}): { fillStampedAt: string; line: string } {
  const symbol = input.symbol.trim().toUpperCase();
  const at = (input.now ?? new Date()).toISOString();
  return {
    fillStampedAt: at,
    line: `Kite filled ${input.quantity} ${symbol} without the tab.`,
  };
}

export function buildRuleTapeLine(input: {
  symbol?: string | null;
  triggerInr?: number | null;
  sessionHigh?: number | null;
  sessionLow?: number | null;
  last?: number | null;
}): string | null {
  const symbol = input.symbol?.trim().toUpperCase();
  const trigger = input.triggerInr;
  if (!symbol || !trigger || trigger <= 0) {
    return null;
  }

  const high = input.sessionHigh ?? input.last;
  if (high === null || high === undefined || !Number.isFinite(high)) {
    return `${symbol} · no tape yet. The wait is still open.`;
  }

  if (high >= trigger) {
    return `${symbol} traded through ${formatInr(trigger)}. The wait is over.`;
  }

  const gap = Math.round(trigger - high);
  return `${symbol} high ${formatInr(high)} · ${formatInr(gap)} short of ${formatInr(trigger)}. The wait was hard.`;
}

export function sessionClockLine(now = new Date()): string {
  return getMarketSessionPhase(now);
}

/** One sentence for Today. Review keeps the year book. */
export function buildTodayDeskLine(input: {
  held?: Array<string | null | undefined>;
  watchSymbol?: string | null;
  marketOpen?: boolean;
  lastWatchAt?: string | null;
  now?: Date;
}): string {
  const names = [
    ...new Set(
      (input.held ?? [])
        .map((symbol) => symbol?.trim().toUpperCase())
        .filter((symbol): symbol is string => Boolean(symbol)),
    ),
  ];
  const book =
    names.length === 2
      ? `Hold ${names[0]} and ${names[1]}.`
      : names.length === 1
        ? `Hold ${names[0]}.`
        : "Hold the book.";
  const watch = input.watchSymbol?.trim().toUpperCase();
  const cash = watch
    ? `Cash waits on ${watch}.`
    : "Cash idle until a line exists.";

  if (input.marketOpen) {
    return `${deskHeartbeatLine({
      lastWatchAt: input.lastWatchAt,
      marketOpen: true,
      now: input.now,
    })} ${book} ${cash}`;
  }

  return `${sessionClockLine(input.now)}. ${book} ${cash}`;
}

export function dualLineGttPlan(input: {
  buyAbove: number;
  killBelow: number;
  last: number;
  ticketInr: number;
}): { buy: { triggerPrice: number; side: "BUY" }; kill: { triggerPrice: number; side: "SELL" }; quantity: number } {
  const quantity = Math.max(1, Math.floor(input.ticketInr / input.buyAbove));
  return {
    buy: { triggerPrice: input.buyAbove, side: "BUY" },
    kill: { triggerPrice: input.killBelow, side: "SELL" },
    quantity,
  };
}

export function bookSellGttPlan(input: {
  symbol: string;
  cutInr: number;
  quantity: number;
  last: number;
}): { tradingsymbol: string; triggerPrice: number; quantity: number; lastPrice: number; side: "SELL" } {
  return {
    tradingsymbol: input.symbol.trim().toUpperCase(),
    triggerPrice: input.cutInr,
    quantity: Math.max(1, Math.floor(input.quantity)),
    lastPrice: input.last,
    side: "SELL",
  };
}

export function markDeskSat(now = new Date()): { deskSatAt: string; line: string } {
  const deskSatAt = now.toISOString();
  const stamped = now.toLocaleTimeString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
  });
  return { deskSatAt, line: `You saw the interrupt · ${stamped} IST.` };
}

export function freezeNewWatch<T extends { symbol: string }>(
  ranked: T | null,
  previous: { watchSymbol?: string | null } | null,
  now = new Date(),
): T | null {
  if (!isDeskClosedForNewPicks(now)) {
    return ranked;
  }

  const frozen = previous?.watchSymbol?.trim().toUpperCase();
  if (!frozen) {
    return null;
  }

  if (ranked?.symbol.trim().toUpperCase() === frozen) {
    return ranked;
  }

  return null;
}

export function eventPauseLine(input: {
  resultsDay?: boolean;
  through?: boolean;
}): string | null {
  if (!input.resultsDay) {
    return null;
  }

  return input.through
    ? "Results day. The line is already through — the ticket stands."
    : "Results day. Do nothing unless the line is already through.";
}

export function rehearsalTicketLine(input: {
  ticketInr: number;
  leftoverInr: number;
  symbol: string;
}): string {
  return `Rehearsal: ${formatInr(input.ticketInr)} of ${input.symbol.trim().toUpperCase()} is the Kite ticket. ${formatInr(input.leftoverInr)} stays idle.`;
}

export function prePlaceConfirmLine(input: {
  held: string[];
  leftoverInr: number;
  watch?: string | null;
}): string {
  const book = input.held.length > 0 ? input.held.join(" · ") : "empty book";
  const next = input.watch?.trim().toUpperCase() || "none";
  return `Pre-place: ${book}. Leftover ${formatInr(input.leftoverInr)}. Next watch ${next}.`;
}

export function clampTicketToMandate(ticketInr: number, leftoverInr: number): number {
  const leftover = Math.max(0, Math.round(leftoverInr));
  return Math.min(Math.max(0, Math.round(ticketInr)), leftover);
}

export function thirdNameWeightCeiling(input: {
  bookValueInr: number;
  ticketInr: number;
}): { allowed: boolean; line: string } {
  const book = Math.max(0, input.bookValueInr);
  const ticket = Math.max(0, input.ticketInr);
  const total = book + ticket;
  const weight = total > 0 ? ticket / total : 0;
  if (weight > 0.34) {
    return {
      allowed: false,
      line: `Third name would be ${Math.round(weight * 100)}% of the book. Cap the ticket.`,
    };
  }

  return { allowed: true, line: "Third name stays a minority." };
}

export function concentrationTrimLine(input: {
  holdings: Array<{ symbol: string; valueInr: number }>;
}): string | null {
  const total = (input.holdings ?? []).reduce((sum, row) => sum + Math.max(0, row.valueInr), 0);
  if (total <= 0) {
    return null;
  }

  const top = [...input.holdings].sort((left, right) => right.valueInr - left.valueInr)[0];
  if (!top || top.valueInr / total < 0.5) {
    return null;
  }

  return `${top.symbol.trim().toUpperCase()} is the book. Sell-to-size. Do not add.`;
}

export function avgDownBanned(input: {
  last: number;
  cutInr: number;
}): boolean {
  return input.last > 0 && input.cutInr > 0 && input.last < input.cutInr;
}

export function corporateActionVoidsLine(action?: string | null): string | null {
  const kind = action?.trim().toLowerCase();
  if (!kind) {
    return null;
  }

  if (kind === "split" || kind === "bonus" || kind === "rights") {
    return `${kind} voids the line. Rewrite the cut before the desk defends it.`;
  }

  return null;
}

export function liquidityVeto(input: {
  avgDailyValueInr?: number | null;
  ticketInr: number;
}): string | null {
  const adv = input.avgDailyValueInr;
  if (adv === null || adv === undefined || !Number.isFinite(adv) || adv <= 0) {
    return null;
  }

  if (input.ticketInr * 10 > adv) {
    return "A line you cannot exit in one ticket is not a line.";
  }

  return null;
}

export function waitFingerprint(history: HorizonHistoryRow[]): string {
  const waits = history.filter((row) => row.outcome === "followed_wait");
  const breaks = history.filter(
    (row) => row.outcome === "broke_wait" || row.outcome === "chased",
  );
  if (waits.length >= 3 && breaks.length === 0) {
    return "You wait well when the gap is wide.";
  }

  const idleCashDays = history.filter(
    (row) => !row.watchSymbol && (row.cashMandate ?? "").toLowerCase().includes("idle"),
  ).length;
  if (idleCashDays >= 4) {
    return "You break when cash sits four days.";
  }

  return "Fingerprint forming. Keep grading the wait.";
}

export function counterfactualClose(input: {
  placedAt?: string | null;
  leftoverAfterInr?: number | null;
}): string | null {
  if (!input.placedAt || input.leftoverAfterInr === null || input.leftoverAfterInr === undefined) {
    return null;
  }

  const clock = new Date(input.placedAt).toLocaleTimeString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
  });
  return `If you had placed at ${clock}, leftover would be ${formatInr(input.leftoverAfterInr)}.`;
}

export function circuitBreakerTripped(history: HorizonHistoryRow[]): boolean {
  const week = history.slice(0, 7);
  const broken = week.filter(
    (row) => row.outcome === "broke_wait" || row.outcome === "chased",
  );
  return broken.length >= 2;
}

export function forgottenCutLine(input: {
  writtenAt?: string | null;
  defaultPct?: boolean;
  now?: Date;
}): string | null {
  if (!input.defaultPct) {
    return null;
  }

  const written = input.writtenAt ? new Date(input.writtenAt).getTime() : NaN;
  const now = (input.now ?? new Date()).getTime();
  if (!Number.isFinite(written)) {
    return "Default 3% cut. Write your line.";
  }

  if (now - written >= 30 * 24 * 60 * 60 * 1000) {
    return "Forgotten cut. The 3% default is 30 days old. Write your line.";
  }

  return null;
}

export function campaignAutopsyLine(input: {
  day: number;
  through?: boolean;
  placed?: boolean;
  symbol?: string | null;
}): string | null {
  if (input.day < 6 || !input.symbol) {
    return null;
  }

  const name = input.symbol.trim().toUpperCase();
  if (input.placed || input.through) {
    return `Day ${input.day} of ${name}: tagged.`;
  }

  return `Day ${input.day} of ${name}: never. Ban it or place it.`;
}

export function assembleYearBook(history: HorizonHistoryRow[]): string {
  let waits = 0;
  let places = 0;
  let breaks = 0;
  for (const row of history) {
    if (row.outcome === "followed_wait") {
      waits += 1;
    } else if (row.outcome === "placed_watch") {
      places += 1;
    } else if (row.outcome === "broke_wait" || row.outcome === "chased") {
      breaks += 1;
    }
  }

  return `${history.length} sessions · ${waits} waits · ${places} places · ${breaks} breaks. Process, not rupees.`;
}

export function waitStreak(history: HorizonHistoryRow[]): number {
  let streak = 0;
  const ordered = [...history].sort((left, right) => right.dateKey.localeCompare(left.dateKey));
  for (const row of ordered) {
    if (row.outcome !== "followed_wait") {
      break;
    }
    streak += 1;
  }

  return streak;
}

export function firstWrongName(history: HorizonHistoryRow[]): string | null {
  const ordered = [...history].sort((left, right) => left.dateKey.localeCompare(right.dateKey));
  for (const row of ordered) {
    if (row.outcome === "wrong_name" && row.watchSymbol) {
      return row.watchSymbol.trim().toUpperCase();
    }
  }

  return null;
}

export function monthlyDoctorFromContracts(history: HorizonHistoryRow[]): string {
  const waits = history.filter((row) => row.outcome === "followed_wait").length;
  const places = history.filter((row) => row.outcome === "placed_watch").length;
  return `Month from contracts: ${waits} waits, ${places} places. Not only receipts.`;
}

export function brokerReconcileVerdict(input: {
  kiteSymbols: string[];
  contractSymbols: string[];
}): string {
  const kite = new Set(input.kiteSymbols.map((name) => name.trim().toUpperCase()).filter(Boolean));
  const desk = new Set(
    input.contractSymbols.map((name) => name.trim().toUpperCase()).filter(Boolean),
  );
  if (kite.size === desk.size && [...desk].every((name) => kite.has(name))) {
    return "Kite and APEX agree.";
  }

  return "Kite and APEX do not agree.";
}

export function classifyOffPlan(input: {
  plannedSymbol?: string | null;
  actualSymbol?: string | null;
  plannedTicket?: number | null;
  actualTicket?: number | null;
  hadGtt?: boolean;
}): string {
  const planned = input.plannedSymbol?.trim().toUpperCase();
  const actual = input.actualSymbol?.trim().toUpperCase();
  if (actual && planned && actual !== planned) {
    return "Off-plan: different name.";
  }

  if (
    input.plannedTicket &&
    input.actualTicket &&
    Math.abs(input.actualTicket - input.plannedTicket) / input.plannedTicket > 0.15
  ) {
    return "Off-plan: different size.";
  }

  if (planned && input.hadGtt === false) {
    return "Off-plan: no GTT.";
  }

  return "On-plan.";
}

export function proofPackHref(dateKey: string): string {
  return `/app/review?date=${encodeURIComponent(dateKey)}&proof=1`;
}

export function spouseBlotterLine(contract: TodayContract): string {
  const book = contract.heldSymbols?.join(" · ") ?? "the book";
  return `Wait · ${book} · ${contract.cashMandate ?? "leftover idle"}. No trade buttons.`;
}

export function advisorPacketLine(contract: TodayContract): string {
  return `Process pack: ${contract.rule}. Share the rule, not a stock.`;
}

export function taxAwarePause(input: {
  boughtOn?: string | null;
  now?: Date;
}): string | null {
  if (!input.boughtOn) {
    return null;
  }

  const bought = new Date(`${input.boughtOn}T12:00:00+05:30`).getTime();
  const now = (input.now ?? new Date()).getTime();
  if (!Number.isFinite(bought)) {
    return null;
  }

  const days = (now - bought) / (24 * 60 * 60 * 1000);
  if (days >= 330 && days < 365) {
    return "Tax-aware Pause. Do not harvest an 11-month winner to rebalance.";
  }

  return null;
}

export function firstNinetyOs(input: { bookAgeDays: number; heldCount: number }): string {
  if (input.bookAgeDays > 90) {
    return "First 90 days are over. The book is the book.";
  }

  if (input.heldCount <= 1) {
    return "First 90 days: one name. Then two. Then a watch.";
  }

  if (input.heldCount === 2) {
    return "First 90 days: two names. The watch is optional.";
  }

  return "First 90 days: three names is the ceiling. Not a 20-name model book.";
}

export function newCapitalMandate(freshCashInr: number): string {
  return `New capital ${formatInr(freshCashInr)} gets a mandate before a pick.`;
}

export function answerVoiceDesk(input: {
  question: string;
  contract: TodayContract | null;
}): { headline: string; reason: string } | null {
  const q = input.question.trim().toLowerCase();
  const contract = input.contract;
  if (!contract) {
    return null;
  }

  if (/\b(book|holdings|what.?s the book)\b/.test(q)) {
    const book = contract.heldSymbols?.join(" and ") ?? "the book";
    return {
      headline: `Hold ${book}.`,
      reason: contract.cashMandate ?? contract.rule,
    };
  }

  const watch = contract.watchSymbol?.trim().toUpperCase();
  if (watch && (q.includes(watch.toLowerCase()) || /confirm/.test(q))) {
    return {
      headline: contract.watchThrough
        ? `${watch} confirmed.`
        : `${watch} has not confirmed.`,
      reason: contract.kiteLine,
    };
  }

  return null;
}

export function watchFaceState(contract: TodayContract | null): {
  word: "Wait" | "Through" | "Dead";
  symbol: string | null;
  label: string;
} {
  if (!contract?.watchSymbol) {
    return { word: "Wait", symbol: null, label: "Wait" };
  }

  if (contract.watchDead) {
    return { word: "Dead", symbol: contract.watchSymbol, label: `${contract.watchSymbol} dead` };
  }

  if (contract.watchThrough) {
    return {
      word: "Through",
      symbol: contract.watchSymbol,
      label: `${contract.watchSymbol} through`,
    };
  }

  return { word: "Wait", symbol: contract.watchSymbol, label: `${contract.watchSymbol} wait` };
}

export function closeLetterCalendarIcs(dateKey = tradingDateKey()): string {
  const compact = dateKey.replaceAll("-", "");
  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//APEX//Close letter//EN",
    "BEGIN:VEVENT",
    `DTSTART;TZID=Asia/Kolkata:${compact}T153100`,
    `DTEND;TZID=Asia/Kolkata:${compact}T154100`,
    "SUMMARY:APEX close letter",
    "DESCRIPTION:Grade the rule. Not P&L.",
    "END:VEVENT",
    "END:VCALENDAR",
    "",
  ].join("\r\n");
}

export function morningBookLocked(input: {
  now?: Date;
  writtenAt?: string | null;
}): boolean {
  const now = input.now ?? new Date();
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata",
    hour: "numeric",
    minute: "numeric",
    hour12: false,
    weekday: "short",
  }).formatToParts(now);
  const weekday = parts.find((part) => part.type === "weekday")?.value ?? "";
  if (weekday === "Sat" || weekday === "Sun") {
    return true;
  }

  const hour = Number(parts.find((part) => part.type === "hour")?.value ?? 0);
  const minute = Number(parts.find((part) => part.type === "minute")?.value ?? 0);
  const afterOpenLock = hour * 60 + minute >= 9 * 60 + 20;
  return afterOpenLock && Boolean(input.writtenAt);
}

export function guestDeskView(contract: TodayContract): {
  kiteLine: string;
  rule: string;
  tradeEnabled: false;
} {
  return {
    kiteLine: contract.kiteLine,
    rule: contract.rule,
    tradeEnabled: false,
  };
}

export function exportYearLetters(history: HorizonHistoryRow[]): string {
  const letters = history
    .filter((row) => row.closeLetter?.trim())
    .map((row) => `${row.dateKey}\n${row.closeLetter ?? ""}`);
  if (letters.length === 0) {
    return "No close letters this year.";
  }

  return letters.join("\n\n");
}

export function disasterModeLine(kiteDown: boolean): string | null {
  return kiteDown ? "Kite is down. The rule stands. Do nothing." : null;
}

export function refuseSharedLeftover(goal?: string | null): string | null {
  const name = goal?.trim().toLowerCase();
  if (name === "esop" || name === "sip") {
    return "Second book later. ESOP and SIP never share this blotter's leftover.";
  }

  return null;
}

export function refuseModelBook(input: { heldCount: number; modelCount: number }): string | null {
  if (input.heldCount <= 3 && input.modelCount >= 10) {
    return "APEX will not show a 15-name ideal portfolio against your two names.";
  }

  return null;
}

export function researchYieldsToContract(input: {
  watch?: string | null;
  researchSymbol?: string | null;
}): string | null {
  const watch = input.watch?.trim().toUpperCase();
  const research = input.researchSymbol?.trim().toUpperCase();
  if (!watch || !research || watch === research) {
    return null;
  }

  return `Today's watch is ${watch}. This page does not shop.`;
}

export function assembleHorizonLines(input: {
  contract: TodayContract | null;
  history?: HorizonHistoryRow[];
  leftoverInr?: number | null;
  bookValueInr?: number;
  ticketInr?: number;
  kiteDown?: boolean;
  resultsDay?: boolean;
  pickCount?: number;
  defaultCuts?: boolean;
  now?: Date;
}): string[] {
  const lines: string[] = [];
  const contract = input.contract;
  const history = input.history ?? [];
  const now = input.now ?? new Date();

  lines.push(sessionClockLine(now));

  const tape = contract
    ? buildRuleTapeLine({
        symbol: contract.watchSymbol,
        triggerInr: contract.triggerInr,
        sessionHigh: contract.watchSymbol
          ? contract.sessionHighBySymbol?.[contract.watchSymbol]
          : null,
      })
    : null;
  if (tape) {
    lines.push(tape);
  }

  if (isDeskClosedForNewPicks(now) && contract?.watchSymbol) {
    lines.push(`Weekend freeze. ${contract.watchSymbol} stays the watch.`);
  }

  const event = eventPauseLine({
    resultsDay: input.resultsDay,
    through: contract?.watchThrough,
  });
  if (event) {
    lines.push(event);
  }

  if (contract?.watchSymbol && input.ticketInr && input.leftoverInr !== undefined) {
    lines.push(
      rehearsalTicketLine({
        ticketInr: clampTicketToMandate(input.ticketInr, input.leftoverInr ?? 0),
        leftoverInr: Math.max(0, (input.leftoverInr ?? 0) - clampTicketToMandate(input.ticketInr, input.leftoverInr ?? 0)),
        symbol: contract.watchSymbol,
      }),
    );
  }

  if (contract && input.leftoverInr !== undefined && input.leftoverInr !== null) {
    lines.push(
      prePlaceConfirmLine({
        held: contract.heldSymbols ?? [],
        leftoverInr: input.leftoverInr,
        watch: contract.watchSymbol,
      }),
    );
  }

  if (input.bookValueInr && input.ticketInr) {
    const ceiling = thirdNameWeightCeiling({
      bookValueInr: input.bookValueInr,
      ticketInr: input.ticketInr,
    });
    if (!ceiling.allowed) {
      lines.push(ceiling.line);
    }
  }

  const trim = concentrationTrimLine({
    holdings: (contract?.heldSymbols ?? []).map((symbol) => ({
      symbol,
      valueInr: (input.bookValueInr ?? 0) / Math.max(1, contract?.heldSymbols?.length ?? 1),
    })),
  });
  if (trim && (contract?.heldSymbols?.length ?? 0) === 1) {
    lines.push(trim);
  }

  const forgotten = forgottenCutLine({ defaultPct: input.defaultCuts === true, now });
  if (forgotten) {
    lines.push(forgotten);
  }

  if (circuitBreakerTripped(history)) {
    lines.push("Two broken waits. Today defaults to Pause.");
  }

  if (history.length > 0) {
    lines.push(waitFingerprint(history));
    lines.push(assembleYearBook(history));
    const streak = waitStreak(history);
    if (streak > 0) {
      lines.push(`${streak} waits in a row were right. Process, not rupees.`);
    }
    const wrong = firstWrongName(history);
    if (wrong) {
      lines.push(`First wrong name: ${wrong}. It stays named.`);
    }
    lines.push(monthlyDoctorFromContracts(history));
  }

  if (contract) {
    lines.push(spouseBlotterLine(contract));
    lines.push(advisorPacketLine(contract));
    const age = history.length > 0
      ? Math.max(
          1,
          history.filter((row) => row.heldSymbols && row.heldSymbols.length > 0).length,
        )
      : 1;
    lines.push(firstNinetyOs({ bookAgeDays: age, heldCount: contract.heldSymbols?.length ?? 0 }));
  }

  const disaster = disasterModeLine(input.kiteDown === true);
  if (disaster) {
    lines.push(disaster);
  }

  const model = refuseModelBook({
    heldCount: contract?.heldSymbols?.length ?? 0,
    modelCount: input.pickCount ?? 0,
  });
  if (model) {
    lines.push(model);
  }

  const esop = refuseSharedLeftover("esop");
  if (esop) {
    lines.push(esop);
  }

  return lines.filter((line) => line.trim().length > 0);
}

export function runDeskHorizonSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Desk horizon self-check failed: ${message}`);
    }
  };

  assert(
    stampKiteFill({ symbol: "grasim", quantity: 2 }).line.includes("GRASIM"),
    "Postback fill must name the stamp",
  );
  assert(
    (buildRuleTapeLine({
      symbol: "GRASIM",
      triggerInr: 3371,
      sessionHigh: 3319,
    }) ?? "").includes("short"),
    "Rule tape must show the hard wait",
  );
  assert(
    dualLineGttPlan({ buyAbove: 3371, killBelow: 3270, last: 3319, ticketInr: 7000 }).kill.side ===
      "SELL",
    "Dual GTT must author the kill",
  );
  assert(
    bookSellGttPlan({ symbol: "COALINDIA", cutInr: 419, quantity: 4, last: 433 }).side === "SELL",
    "Book GTT is sell-side",
  );
  assert(markDeskSat(new Date("2026-09-10T10:00:00+05:30")).line.includes("saw"), "Desk sat receipt");

  const saturday = new Date("2026-09-12T12:00:00+05:30");
  assert(
    freezeNewWatch({ symbol: "TCS" }, { watchSymbol: "GRASIM" }, saturday) === null,
    "Saturday must not invent a new pick",
  );
  assert(
    (eventPauseLine({ resultsDay: true, through: false }) ?? "").includes("Do nothing"),
    "Results day is Pause",
  );
  assert(
    rehearsalTicketLine({ ticketInr: 7000, leftoverInr: 3722, symbol: "GRASIM" }).includes("7,000"),
    "Rehearsal is the Kite ticket",
  );
  assert(
    prePlaceConfirmLine({
      held: ["COALINDIA", "ADANIPORTS"],
      leftoverInr: 3722,
      watch: null,
    }).includes("none"),
    "Pre-place names leftover and no next watch",
  );
  assert(clampTicketToMandate(9000, 3722) === 3722, "Ticket cannot exceed leftover");
  assert(
    thirdNameWeightCeiling({ bookValueInr: 3492, ticketInr: 10722 }).allowed === false,
    "Third name cannot become the book",
  );
  assert(
    (concentrationTrimLine({
      holdings: [
        { symbol: "JIOFIN", valueInr: 9000 },
        { symbol: "COALINDIA", valueInr: 1000 },
      ],
    }) ?? "").includes("Sell-to-size"),
    "Concentration is sell-to-size",
  );
  assert(avgDownBanned({ last: 400, cutInr: 419 }) === true, "Avg-down is banned below the line");
  assert(
    (corporateActionVoidsLine("split") ?? "").includes("voids"),
    "Split voids the line",
  );
  assert(
    (liquidityVeto({ avgDailyValueInr: 50_000, ticketInr: 20_000 }) ?? "").includes("cannot exit"),
    "Illiquid line is vetoed",
  );
  assert(
    waitFingerprint([
      { dateKey: "2026-09-07", outcome: "followed_wait" },
      { dateKey: "2026-09-08", outcome: "followed_wait" },
      { dateKey: "2026-09-09", outcome: "followed_wait" },
    ]).includes("wait well"),
    "Wide-gap waits are the fingerprint",
  );
  assert(
    (counterfactualClose({
      placedAt: "2026-09-10T06:12:00.000Z",
      leftoverAfterInr: 3722,
    }) ?? "").includes("3,722"),
    "Counterfactual names leftover",
  );
  assert(
    circuitBreakerTripped([
      { dateKey: "2026-09-09", outcome: "broke_wait" },
      { dateKey: "2026-09-10", outcome: "chased" },
    ]) === true,
    "Two broken waits trip Pause",
  );
  assert(
    (forgottenCutLine({
      defaultPct: true,
      writtenAt: "2026-08-01T00:00:00.000Z",
      now: new Date("2026-09-10T00:00:00.000Z"),
    }) ?? "").includes("30 days"),
    "Forgotten 3% cut is flagged",
  );
  assert(
    (campaignAutopsyLine({ day: 6, symbol: "GRASIM", through: false, placed: false }) ?? "").includes(
      "Ban",
    ),
    "Day 6 autopsy is ban or place",
  );
  assert(assembleYearBook([{ dateKey: "2026-09-10", outcome: "followed_wait" }]).includes("waits"), "Year book");
  assert(waitStreak([{ dateKey: "2026-09-10", outcome: "followed_wait" }]) === 1, "Wait streak");
  assert(
    firstWrongName([{ dateKey: "2026-09-01", outcome: "wrong_name", watchSymbol: "IDEA" }]) ===
      "IDEA",
    "First wrong name stays named",
  );
  assert(
    monthlyDoctorFromContracts([{ dateKey: "2026-09-10", outcome: "followed_wait" }]).includes(
      "contracts",
    ),
    "Monthly doctor uses contracts",
  );
  assert(
    brokerReconcileVerdict({
      kiteSymbols: ["COALINDIA", "ADANIPORTS"],
      contractSymbols: ["COALINDIA", "ADANIPORTS"],
    }).includes("agree"),
    "Reconcile is a verdict",
  );
  assert(
    classifyOffPlan({ plannedSymbol: "GRASIM", actualSymbol: "TCS" }) === "Off-plan: different name.",
    "Off-plan taxonomy",
  );
  assert(proofPackHref("2026-09-10").includes("proof=1"), "Proof pack is one link");
  assert(
    spouseBlotterLine({
      dateKey: "2026-09-10",
      kiteLine: "Do nothing",
      rule: "Wait",
      heldSymbols: ["COALINDIA"],
      cashMandate: "Idle on purpose.",
    }).includes("No trade"),
    "Spouse blotter is read-only",
  );
  assert(
    advisorPacketLine({
      dateKey: "2026-09-10",
      kiteLine: "Do nothing",
      rule: "Wait GRASIM",
    }).includes("not a stock"),
    "Advisor packet is process",
  );
  assert(
    (taxAwarePause({
      boughtOn: "2025-10-01",
      now: new Date("2026-09-10T00:00:00.000Z"),
    }) ?? "").includes("11-month"),
    "Tax-aware Pause",
  );
  assert(
    firstNinetyOs({ bookAgeDays: 12, heldCount: 2 }).includes("two names"),
    "First 90 days OS",
  );
  assert(newCapitalMandate(50_000).includes("mandate"), "Fresh cash gets a mandate");
  assert(
    (answerVoiceDesk({
      question: "What's the book?",
      contract: {
        dateKey: "2026-09-10",
        kiteLine: "Do nothing in Kite unless GRASIM trades above ₹3,371.",
        rule: "Wait",
        heldSymbols: ["COALINDIA", "ADANIPORTS"],
        cashMandate: "Sit for GRASIM.",
      },
    })?.headline ?? "").includes("COALINDIA"),
    "Voice desk answers the book",
  );
  assert(
    watchFaceState({
      dateKey: "2026-09-10",
      kiteLine: "x",
      rule: "y",
      watchSymbol: "GRASIM",
      watchDead: true,
    }).word === "Dead",
    "Watch face is not a ticker",
  );
  assert(closeLetterCalendarIcs("2026-09-10").includes("153100"), "Calendar block at 15:31");
  assert(
    morningBookLocked({
      now: new Date("2026-09-10T09:45:00+05:30"),
      writtenAt: "2026-09-10T03:30:00.000Z",
    }) === true,
    "Morning book freezes at 9:20",
  );
  assert(
    guestDeskView({
      dateKey: "2026-09-10",
      kiteLine: "Do nothing",
      rule: "Wait",
    }).tradeEnabled === false,
    "Guest is read-only",
  );
  assert(
    exportYearLetters([
      { dateKey: "2026-09-10", closeLetter: "Followed. No GRASIM fill." },
    ]).includes("Followed"),
    "Year export is the close letters",
  );
  assert(
    (disasterModeLine(true) ?? "").includes("Do nothing"),
    "Disaster mode keeps the rule",
  );
  assert((refuseSharedLeftover("esop") ?? "").includes("never share"), "Second book later");
  assert(
    (refuseModelBook({ heldCount: 2, modelCount: 15 }) ?? "").includes("ideal portfolio"),
    "Model-book refusal",
  );
  assert(
    (researchYieldsToContract({ watch: "GRASIM", researchSymbol: "TCS" }) ?? "").includes(
      "does not shop",
    ),
    "Research cannot outrank the contract",
  );
  assert(
    buildTodayDeskLine({
      held: ["COALINDIA", "ADANIPORTS"],
      marketOpen: false,
      now: new Date("2026-09-10T20:18:00+05:30"),
    }) === "After hours. Hold COALINDIA and ADANIPORTS. Cash idle until a line exists.",
    "Today must be one after-hours sentence",
  );
  assert(
    !buildTodayDeskLine({
      held: ["COALINDIA", "ADANIPORTS"],
      marketOpen: false,
      now: new Date("2026-09-10T20:18:00+05:30"),
    }).includes("Telegram"),
    "Today must not nag Vercel",
  );
  assert(
    assembleHorizonLines({
      contract: {
        dateKey: "2026-09-10",
        kiteLine: "Do nothing in Kite unless GRASIM trades above ₹3,371.",
        rule: "₹52 to the line",
        watchSymbol: "GRASIM",
        triggerInr: 3371,
        sessionHighBySymbol: { GRASIM: 3319 },
        heldSymbols: ["COALINDIA", "ADANIPORTS"],
        cashMandate: "Sit for GRASIM.",
      },
      leftoverInr: 10722,
      ticketInr: 7000,
      bookValueInr: 3492,
      kiteDown: true,
      pickCount: 15,
      now: new Date("2026-09-10T15:00:00+05:30"),
    }).some((line) => line.includes("Last hour")),
    "Horizon pack must include the session clock",
  );
}
