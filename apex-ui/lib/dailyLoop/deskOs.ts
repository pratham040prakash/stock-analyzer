import { shiftIstDateKey } from "@/lib/dailyLoop/disciplineDates";
import { gradeFromTape } from "@/lib/dailyLoop/deskNight";
import type { TodayContract } from "@/lib/dailyLoop/todayContract";

export type InterruptChannel = "telegram" | "webhook" | "none";

export type NameDiaryEntry = {
  dateKey: string;
  symbol: string;
  line: string;
};

export function describeInterruptChannel(env: {
  telegramToken?: string | null;
  telegramChatId?: string | null;
  webhookUrl?: string | null;
} = {
  telegramToken: process.env.TELEGRAM_BOT_TOKEN,
  telegramChatId: process.env.TELEGRAM_CHAT_ID,
  webhookUrl: process.env.APEX_DIGEST_WEBHOOK_URL,
}): { ready: boolean; channel: InterruptChannel } {
  if (env.webhookUrl?.trim()) {
    return { ready: true, channel: "webhook" };
  }

  if (env.telegramToken?.trim() && env.telegramChatId?.trim()) {
    return { ready: true, channel: "telegram" };
  }

  return { ready: false, channel: "none" };
}

export function deskHeartbeatLine(input: {
  lastWatchAt?: string | null;
  marketOpen?: boolean;
  now?: Date;
  staleAfterMs?: number;
}): string {
  const last = input.lastWatchAt ? new Date(input.lastWatchAt).getTime() : NaN;
  if (!Number.isFinite(last)) {
    return "Desk has not sat yet.";
  }

  const now = (input.now ?? new Date()).getTime();
  const age = now - last;
  const staleAfter = input.staleAfterMs ?? 20 * 60 * 1000;
  if (input.marketOpen && age > staleAfter) {
    return "Desk missed a ping.";
  }

  if (input.marketOpen) {
    return "Desk sitting.";
  }

  const stamped = new Date(last).toLocaleTimeString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
  });
  return `Desk sat · last ping ${stamped} IST.`;
}

export function interruptHealthLine(ready: boolean): string {
  return ready
    ? "Interrupt ready."
    : "Interrupt off. Add Telegram on Vercel.";
}

export function appendNameDiary(
  existing: NameDiaryEntry[] | undefined,
  entry: NameDiaryEntry,
): NameDiaryEntry[] {
  const symbol = entry.symbol.trim().toUpperCase();
  const line = entry.line.trim();
  if (!symbol || !line) {
    return existing ?? [];
  }

  const next: NameDiaryEntry = {
    dateKey: entry.dateKey,
    symbol,
    line,
  };
  const prior = existing ?? [];
  const last = prior[prior.length - 1];
  if (
    last &&
    last.dateKey === next.dateKey &&
    last.symbol === next.symbol &&
    last.line === next.line
  ) {
    return prior;
  }

  return [...prior, next].slice(-40);
}

export function latestDiaryLine(
  diary: NameDiaryEntry[] | undefined,
  symbol: string,
): NameDiaryEntry | null {
  const name = symbol.trim().toUpperCase();
  if (!name || !diary) {
    return null;
  }

  for (let index = diary.length - 1; index >= 0; index -= 1) {
    if (diary[index].symbol === name) {
      return diary[index];
    }
  }

  return null;
}

export function assembleSundayLetter(input: {
  weekOf: string;
  history: TodayContract[];
}): string {
  const days: string[] = [];
  for (let offset = 6; offset >= 0; offset -= 1) {
    const dateKey = shiftIstDateKey(input.weekOf, -offset);
    const row = input.history.find((item) => item.dateKey === dateKey);
    if (!row) {
      continue;
    }

    const grade =
      gradeFromTape({
        watchSymbol: row.watchSymbol,
        triggerInr: row.triggerInr,
        sessionHigh: row.watchSymbol
          ? row.sessionHighBySymbol?.[row.watchSymbol]
          : null,
        sessionLow: row.watchSymbol
          ? row.sessionLowBySymbol?.[row.watchSymbol]
          : null,
        killInr: row.triggerInr ? Math.round(row.triggerInr * 0.97) : null,
        outcome: row.outcome,
      }) ??
      row.outcomeLine ??
      row.rule;
    days.push(`${dateKey}: ${grade}`);
  }

  const book = input.history[0]?.heldSymbols?.join(" · ") ?? "the book";
  if (days.length === 0) {
    return `Sunday · week of ${input.weekOf}. No contract this week. The desk has nothing to grade.`;
  }

  return [
    `Sunday · week of ${input.weekOf}.`,
    ...days,
    `Held ${book}. The score is the rule, not P&L.`,
  ].join(" ");
}

export function runDeskOsSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Desk OS self-check failed: ${message}`);
    }
  };

  assert(
    describeInterruptChannel({ webhookUrl: "https://example.com" }).channel ===
      "webhook",
    "A webhook is a ready interrupt",
  );
  assert(
    describeInterruptChannel({
      telegramToken: "t",
      telegramChatId: "1",
    }).channel === "telegram",
    "Telegram is a ready interrupt",
  );
  assert(
    describeInterruptChannel({}).ready === false,
    "No channel means interrupt is off",
  );

  assert(
    deskHeartbeatLine({ lastWatchAt: null }).includes("not sat"),
    "No ping must say the desk has not sat",
  );
  assert(
    deskHeartbeatLine({
      lastWatchAt: "2026-09-10T09:00:00.000Z",
      now: new Date("2026-09-10T09:40:00.000Z"),
      marketOpen: true,
    }).includes("missed"),
    "A stale ping during the session must show",
  );

  const diary = appendNameDiary(
    [
      {
        dateKey: "2026-09-09",
        symbol: "COALINDIA",
        line: "Hold unless below ₹419.",
      },
    ],
    {
      dateKey: "2026-09-10",
      symbol: "coalindia",
      line: "Hold unless below ₹420 — your line.",
    },
  );
  assert(diary.length === 2, "Diary must keep the old line");
  assert(
    latestDiaryLine(diary, "COALINDIA")?.dateKey === "2026-09-10",
    "Diary must surface the latest line",
  );

  const letter = assembleSundayLetter({
    weekOf: "2026-09-10",
    history: [
      {
        dateKey: "2026-09-10",
        kiteLine: "Do nothing in Kite unless GRASIM trades above ₹3,371.",
        rule: "₹52 to the line",
        watchSymbol: "GRASIM",
        triggerInr: 3371,
        sessionHighBySymbol: { GRASIM: 3319 },
        heldSymbols: ["COALINDIA", "ADANIPORTS"],
        outcome: "followed_wait",
      },
    ],
  });
  assert(letter.includes("Sunday"), "Sunday letter must name the ritual");
  assert(letter.includes("never traded above"), "Sunday letter must grade the wait");
  assert(!letter.toLowerCase().includes("p&l chart"), "Sunday letter is not a P&L chart");
}
