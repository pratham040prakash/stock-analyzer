import { shiftIstDateKey, tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { readTodayContract } from "@/lib/dailyLoop/todayContract";
import type { TodayContract } from "@/lib/dailyLoop/todayContract";
import type { TodayLoop } from "@/lib/dailyLoop/todayLoop";
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
}
