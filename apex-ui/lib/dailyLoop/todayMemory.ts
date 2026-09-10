import { shiftIstDateKey, tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { readTodayContract } from "@/lib/dailyLoop/todayContract";
import type { TodayContract } from "@/lib/dailyLoop/todayContract";
import type { TodayLoop } from "@/lib/dailyLoop/todayLoop";
import { formatInr } from "@/lib/funds";
import { gradeFromTape } from "@/lib/dailyLoop/deskNight";
import { parseInvalidationRule } from "@/services/thesis/parseInvalidationRule";

export function buildLoopReceiptBody(input: {
  loop: TodayLoop;
  contract: TodayContract;
}): {
  symbol: string;
  executionKind: "BUY" | "WAIT";
  verdictWord: string;
  headline: string;
  subline: string;
  orderId: string;
} | null {
  if (input.loop.state === "open" || !input.loop.line) {
    return null;
  }

  const symbol =
    input.loop.watchSymbol ||
    input.contract.heldSymbols?.[0] ||
    "BOOK";

  return {
    symbol,
    executionKind: input.loop.state === "placed_watch" ? "BUY" : "WAIT",
    verdictWord:
      input.loop.state === "placed_watch"
        ? "Placed"
        : input.loop.state === "broke_wait"
          ? "Off-plan"
          : "Followed",
    headline: input.loop.line,
    subline: input.contract.kiteLine,
    orderId: `loop:${input.contract.dateKey}:${input.loop.state}`,
  };
}

function weekdayShort(dateKey: string): string {
  return new Date(`${dateKey}T12:00:00+05:30`).toLocaleDateString("en-IN", {
    weekday: "short",
    timeZone: "Asia/Kolkata",
  });
}

export function formatLoopMemoryLine(headline: string, receiptDate: string): string {
  return `${weekdayShort(receiptDate)}: ${headline}`;
}

export function readYesterdayLoopLine(dateKey = tradingDateKey()): string | null {
  const yday = shiftIstDateKey(dateKey, -1);
  const contract = readTodayContract(yday);
  if (!contract?.outcomeLine) {
    return null;
  }

  return formatLoopMemoryLine(contract.outcomeLine, yday);
}

export function pickYesterdayLoopLine(
  receipts: Array<{
    receipt_date?: string | null;
    headline?: string | null;
    order_id?: string | null;
  }>,
  dateKey = tradingDateKey(),
): string | null {
  const yday = shiftIstDateKey(dateKey, -1);
  const row = receipts.find(
    (receipt) =>
      receipt.receipt_date === yday &&
      Boolean(receipt.order_id?.startsWith("loop:")) &&
      Boolean(receipt.headline?.trim()),
  );

  if (row?.headline) {
    return formatLoopMemoryLine(row.headline, yday);
  }

  return readYesterdayLoopLine(dateKey);
}

export function pickReviewLoopLine(
  receipts: Array<{
    receipt_date?: string | null;
    headline?: string | null;
    order_id?: string | null;
  }>,
  dateKey = tradingDateKey(),
): string | null {
  const yesterday = pickYesterdayLoopLine(receipts, dateKey);
  if (yesterday) {
    return yesterday;
  }

  const latest = receipts.find(
    (receipt) =>
      Boolean(receipt.order_id?.startsWith("loop:")) && Boolean(receipt.headline?.trim()),
  );
  if (!latest?.headline) {
    return null;
  }

  return latest.receipt_date
    ? formatLoopMemoryLine(latest.headline, latest.receipt_date)
    : latest.headline;
}

export function watchNotifyKey(input: {
  symbol?: string | null;
  through?: boolean;
  dead?: boolean;
}): string {
  const symbol = input.symbol?.trim().toUpperCase() || "NONE";
  if (input.dead) {
    return `${symbol}:dead`;
  }

  if (input.through) {
    return `${symbol}:through`;
  }

  return `${symbol}:live`;
}

export function shouldNotifyWatch(previousKey: string | null, nextKey: string): boolean {
  if (!nextKey.endsWith(":through") && !nextKey.endsWith(":dead")) {
    return false;
  }

  return previousKey !== nextKey;
}

export function buildWatchInterruptCopy(input: {
  symbol: string;
  through?: boolean;
  dead?: boolean;
  gapLabel?: string | null;
}): { title: string; body: string } {
  const symbol = input.symbol.trim().toUpperCase();

  if (input.dead) {
    return {
      title: `${symbol} lost the setup`,
      body: "Cash stays put. Do nothing in Kite.",
    };
  }

  return {
    title: `${symbol} is through the line`,
    body: input.gapLabel || "Place the ticket in Kite. Today stays Wait until you do.",
  };
}

export function yesterdayWatchDied(contract?: TodayContract | null): boolean {
  if (!contract?.watchSymbol) {
    return false;
  }

  if (contract.watchDead) {
    return true;
  }

  const gap = (contract.gapLabel ?? "").toLowerCase();
  const kite = (contract.kiteLine ?? "").toLowerCase();
  return gap.includes("lost") || kite.includes("lost the setup");
}

export function yesterdayWatchThrough(contract?: TodayContract | null): boolean {
  if (!contract?.watchSymbol) {
    return false;
  }

  if (contract.watchThrough) {
    return true;
  }

  const gap = (contract.gapLabel ?? "").toLowerCase();
  const kite = (contract.kiteLine ?? "").toLowerCase();
  return gap.includes("at the line") || kite.toLowerCase().includes("place ");
}

export const WATCH_BAN_DAYS = 7;

export function bannedWatchSymbols(
  history: Array<TodayContract | null | undefined>,
  dateKey: string,
): string[] {
  const banned = new Set<string>();
  for (const row of history) {
    const symbol = row?.watchSymbol?.trim().toUpperCase();
    if (!row || !symbol || !yesterdayWatchDied(row)) {
      continue;
    }

    const until = shiftIstDateKey(row.dateKey, WATCH_BAN_DAYS);
    if (row.dateKey < dateKey && dateKey <= until) {
      banned.add(symbol);
    }
  }

  return [...banned];
}

export function resolveWatchCarry(input: {
  today?: TodayContract | null;
  yesterday?: TodayContract | null;
  history?: Array<TodayContract | null | undefined>;
  dateKey?: string;
}): { preferredSymbol: string | null; bannedSymbols: string[] } {
  const dateKey = input.dateKey ?? tradingDateKey();
  const todayWatch = input.today?.watchSymbol?.trim().toUpperCase() || null;
  const yWatch = input.yesterday?.watchSymbol?.trim().toUpperCase() || null;
  const banned = bannedWatchSymbols(
    [...(input.history ?? []), input.yesterday, input.today],
    dateKey,
  );

  if (todayWatch && !banned.includes(todayWatch)) {
    return { preferredSymbol: todayWatch, bannedSymbols: banned };
  }

  if (
    yWatch &&
    !banned.includes(yWatch) &&
    input.yesterday?.outcome !== "placed_watch"
  ) {
    return { preferredSymbol: yWatch, bannedSymbols: banned };
  }

  return { preferredSymbol: null, bannedSymbols: banned };
}

export function triggerInrFromKiteLine(kiteLine?: string | null): number | null {
  const match = kiteLine?.match(/above\s*₹\s*([\d,]+)/i);
  if (!match?.[1]) {
    return null;
  }

  const value = Number(match[1].replace(/,/g, ""));
  return Number.isFinite(value) && value > 0 ? value : null;
}

export function buildRuleGrade(input: {
  watchSymbol?: string | null;
  triggerInr?: number | null;
  outcome?: string | null;
  through?: boolean;
  dead?: boolean;
  kiteLine?: string | null;
  gapLabel?: string | null;
  headline?: string | null;
}): string | null {
  const watch = input.watchSymbol?.trim().toUpperCase() || null;
  const headline = input.headline?.trim() || "";
  const outcome = input.outcome ?? "";
  const trigger =
    input.triggerInr && input.triggerInr > 0
      ? input.triggerInr
      : triggerInrFromKiteLine(input.kiteLine);
  const dead =
    input.dead ||
    yesterdayWatchDied({
      dateKey: "",
      kiteLine: input.kiteLine ?? "",
      rule: "",
      watchSymbol: watch ?? undefined,
      gapLabel: input.gapLabel,
      watchDead: input.dead,
    });
  const through =
    input.through ||
    yesterdayWatchThrough({
      dateKey: "",
      kiteLine: input.kiteLine ?? "",
      rule: "",
      watchSymbol: watch ?? undefined,
      gapLabel: input.gapLabel,
      watchThrough: input.through,
    });

  if (outcome === "placed_watch" || headline.toLowerCase().startsWith("placed")) {
    return watch
      ? `You placed ${watch}. The book added a name.`
      : "You placed the watch. The book added a name.";
  }

  if (outcome === "broke_wait" || headline.toLowerCase().includes("off-plan")) {
    return headline || "Off-plan. The book added a different name.";
  }

  const followed =
    outcome === "followed_wait" || headline.toLowerCase().includes("followed");
  if (!followed) {
    return null;
  }

  if (dead && watch) {
    return `You waited. ${watch} lost the setup.`;
  }

  if (through) {
    return watch
      ? `You waited. ${watch} went through and you didn't place.`
      : "You waited. It went through and you didn't place.";
  }

  if (watch && trigger) {
    return `You waited. ${watch} never traded above ${formatInr(trigger)}.`;
  }

  return watch ? `You waited. No ${watch} fill.` : "You waited.";
}

export function pickReviewRuleGrade(
  receipts: Array<{
    receipt_date?: string | null;
    headline?: string | null;
    subline?: string | null;
    order_id?: string | null;
    symbol?: string | null;
  }>,
  yesterday?: TodayContract | null,
  dateKey = tradingDateKey(),
): string | null {
  const yday = shiftIstDateKey(dateKey, -1);
  const tape = yesterday
    ? gradeFromTape({
        watchSymbol: yesterday.watchSymbol,
        triggerInr: yesterday.triggerInr,
        sessionHigh: yesterday.watchSymbol
          ? yesterday.sessionHighBySymbol?.[yesterday.watchSymbol]
          : null,
        sessionLow: yesterday.watchSymbol
          ? yesterday.sessionLowBySymbol?.[yesterday.watchSymbol]
          : null,
        killInr: yesterday.triggerInr
          ? Math.round(yesterday.triggerInr * 0.97)
          : null,
        outcome: yesterday.outcome,
      })
    : null;
  if (tape) {
    return tape;
  }

  const row = receipts.find(
    (receipt) =>
      receipt.receipt_date === yday && Boolean(receipt.order_id?.startsWith("loop:")),
  );
  const fromReceipt = row
    ? buildRuleGrade({
        watchSymbol: yesterday?.watchSymbol || row.symbol,
        outcome: row.order_id?.split(":")[2],
        headline: row.headline,
        kiteLine: row.subline ?? yesterday?.kiteLine,
        gapLabel: yesterday?.gapLabel,
        triggerInr: yesterday?.triggerInr,
        through: yesterday?.watchThrough,
        dead: yesterday?.watchDead,
      })
    : null;

  if (fromReceipt) {
    return fromReceipt;
  }

  if (!yesterday) {
    return null;
  }

  return buildRuleGrade({
    watchSymbol: yesterday.watchSymbol,
    outcome: yesterday.outcome,
    headline: yesterday.outcomeLine,
    kiteLine: yesterday.kiteLine,
    gapLabel: yesterday.gapLabel,
    triggerInr: yesterday.triggerInr,
    through: yesterday.watchThrough,
    dead: yesterday.watchDead,
  });
}

export function holdNotifyKey(symbol?: string | null): string {
  return `${symbol?.trim().toUpperCase() || "BOOK"}:broke`;
}

export function readHoldNotifyKeys(dateKey = tradingDateKey()): string[] {
  if (typeof window === "undefined") {
    return [];
  }

  const raw = window.localStorage.getItem(`apex_hold_notify:${dateKey}`);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed)
      ? parsed.filter((item): item is string => typeof item === "string")
      : [];
  } catch {
    return [];
  }
}

export function persistHoldNotifyKey(key: string, dateKey = tradingDateKey()): void {
  if (typeof window === "undefined") {
    return;
  }

  const next = [...new Set([...readHoldNotifyKeys(dateKey), key])];
  window.localStorage.setItem(`apex_hold_notify:${dateKey}`, JSON.stringify(next));
}

export function shouldNotifyHold(seen: string[], key: string): boolean {
  return key.endsWith(":broke") && !seen.includes(key);
}

export function buildHoldInterruptCopy(input: {
  symbol: string;
  cutLabel?: string | null;
}): { title: string; body: string } {
  const symbol = input.symbol.trim().toUpperCase();
  return {
    title: `${symbol} broke your line`,
    body: input.cutLabel
      ? `Below ${input.cutLabel}. Review in Kite.`
      : "Your line broke. Review in Kite.",
  };
}

export function cutInrFromInvalidation(text?: string | null): number | null {
  if (!text?.trim()) {
    return null;
  }

  const parsed = parseInvalidationRule(text);
  return parsed.kind === "price_below" ? parsed.threshold : null;
}

export function buildHumanThesis(input: {
  symbol: string;
  triggerInr?: number | null;
  fallback: string;
  research?: {
    summary?: string | null;
    questions?: Array<{ id?: string; answer?: string | null }>;
  } | null;
}): string {
  const fromQuestion =
    input.research?.questions?.find((question) => question.id === "decision")
      ?.answer ??
    input.research?.questions?.find((question) => question.id === "timing")
      ?.answer ??
    null;
  const raw = (fromQuestion || input.research?.summary || "").trim();
  const usable =
    raw.length > 24 &&
    !raw.toLowerCase().includes("use this workspace") &&
    !raw.toLowerCase().includes("unavailable");

  if (!usable) {
    return input.fallback;
  }

  const sentence = raw.split(/(?<=[.!?])\s+/)[0]?.trim() || raw;
  return sentence.length > 180 ? `${sentence.slice(0, 177).trim()}…` : sentence;
}

export function readWatchNotifyKey(dateKey = tradingDateKey()): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(`apex_watch_notify:${dateKey}`);
}

export function persistWatchNotifyKey(key: string, dateKey = tradingDateKey()): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(`apex_watch_notify:${dateKey}`, key);
}

export async function fireWatchInterrupt(copy: {
  title: string;
  body: string;
}): Promise<void> {
  if (typeof window === "undefined" || !("Notification" in window)) {
    return;
  }

  if (window.Notification.permission === "default") {
    await window.Notification.requestPermission();
  }

  if (window.Notification.permission === "granted") {
    new window.Notification(copy.title, { body: copy.body });
  }
}

export function runTodayMemorySelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Today memory self-check failed: ${message}`);
    }
  };

  const receipt = buildLoopReceiptBody({
    loop: {
      state: "followed_wait",
      line: "Followed. No GRASIM fill.",
      watchSymbol: "GRASIM",
    },
    contract: {
      dateKey: "2026-09-10",
      kiteLine: "Do nothing in Kite unless GRASIM trades above ₹3,371.",
      rule: "₹52 to the line",
      heldSymbols: ["COALINDIA", "ADANIPORTS"],
      watchSymbol: "GRASIM",
    },
  });
  assert(receipt?.orderId === "loop:2026-09-10:followed_wait", "Loop receipt must be idempotent");
  assert(receipt?.headline.includes("GRASIM") === true, "Loop receipt must name the watch");

  const yday = pickYesterdayLoopLine(
    [
      {
        receipt_date: "2026-09-09",
        headline: "Followed. No GRASIM fill.",
        order_id: "loop:2026-09-09:followed_wait",
      },
    ],
    "2026-09-10",
  );
  assert(yday?.includes("Wed") === true, "Review must remember yesterday");
  assert(
    pickReviewLoopLine(
      [
        {
          receipt_date: "2026-09-08",
          headline: "Followed. No GRASIM fill.",
          order_id: "loop:2026-09-08:followed_wait",
        },
      ],
      "2026-09-10",
    )?.includes("Followed") === true,
    "Review can fall back to the latest loop receipt",
  );

  assert(
    shouldNotifyWatch("GRASIM:live", "GRASIM:through"),
    "Through the line must interrupt",
  );
  assert(
    !shouldNotifyWatch("GRASIM:through", "GRASIM:through"),
    "Same flip must not spam",
  );

  const thesis = buildHumanThesis({
    symbol: "GRASIM",
    fallback: "Break ₹3,371 or stand aside.",
    research: {
      summary: "Grasim remains a quality compounder. Wait for the range high.",
      questions: [{ id: "decision", answer: "Wait for the break of the range high." }],
    },
  });
  assert(thesis.includes("range high"), "Human thesis must come from research");

  assert(cutInrFromInvalidation("Break below ₹1,714") === 1714, "Your line must parse");

  const carryLive = resolveWatchCarry({
    yesterday: {
      dateKey: "2026-09-09",
      kiteLine: "Do nothing in Kite unless GRASIM trades above ₹3,371.",
      rule: "₹52 to the line",
      watchSymbol: "GRASIM",
      outcome: "followed_wait",
    },
  });
  assert(carryLive.preferredSymbol === "GRASIM", "A live wait must keep yesterday's name");

  const carryDead = resolveWatchCarry({
    yesterday: {
      dateKey: "2026-09-09",
      kiteLine: "Do nothing in Kite. GRASIM lost the setup.",
      rule: "Cash stays put.",
      watchSymbol: "GRASIM",
      gapLabel: "Lost the line",
      watchDead: true,
      outcome: "followed_wait",
    },
  });
  assert(carryDead.bannedSymbols.includes("GRASIM"), "A dead setup must not return tomorrow");
  assert(carryDead.preferredSymbol === null, "A dead setup must not stay preferred");

  const weekBan = bannedWatchSymbols(
    [
      {
        dateKey: "2026-09-03",
        kiteLine: "Do nothing in Kite. GRASIM lost the setup.",
        rule: "Cash stays put.",
        watchSymbol: "GRASIM",
        watchDead: true,
      },
    ],
    "2026-09-10",
  );
  assert(weekBan.includes("GRASIM"), "A dead setup stays banned for a week");
  assert(
    !bannedWatchSymbols(
      [
        {
          dateKey: "2026-09-03",
          kiteLine: "Do nothing in Kite. GRASIM lost the setup.",
          rule: "Cash stays put.",
          watchSymbol: "GRASIM",
          watchDead: true,
        },
      ],
      "2026-09-11",
    ).includes("GRASIM"),
    "The ban must lift after a week",
  );

  assert(
    buildRuleGrade({
      watchSymbol: "GRASIM",
      outcome: "followed_wait",
      triggerInr: 3371,
    })?.includes("never traded above") === true,
    "Review must grade a wait that never confirmed",
  );
  assert(
    buildRuleGrade({
      watchSymbol: "GRASIM",
      outcome: "followed_wait",
      through: true,
    })?.includes("didn't place") === true,
    "Review must grade a wait that missed the through",
  );
  assert(
    shouldNotifyHold([], "COALINDIA:broke"),
    "A broken hold line must interrupt",
  );
  assert(
    !shouldNotifyHold(["COALINDIA:broke"], "COALINDIA:broke"),
    "The same broken line must not spam",
  );
}
