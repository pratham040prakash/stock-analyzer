import { shiftIstDateKey } from "@/lib/dailyLoop/disciplineDates";
import { formatInr } from "@/lib/funds";

export function mergeSessionExtrema(
  previous: Record<string, number> | undefined,
  symbol: string,
  value: number | null | undefined,
  kind: "high" | "low",
): Record<string, number> {
  const next = { ...(previous ?? {}) };
  const key = symbol.trim().toUpperCase();
  if (!key || value === null || value === undefined || !Number.isFinite(value) || value <= 0) {
    return next;
  }

  const seen = next[key];
  if (seen === undefined) {
    next[key] = value;
    return next;
  }

  next[key] = kind === "high" ? Math.max(seen, value) : Math.min(seen, value);
  return next;
}

export function campaignDay(input: {
  watchSymbol?: string | null;
  dateKey: string;
  history: Array<{ dateKey: string; watchSymbol?: string | null; dead?: boolean }>;
}): number {
  const watch = input.watchSymbol?.trim().toUpperCase();
  if (!watch) {
    return 0;
  }

  let day = 0;
  for (let offset = 0; offset < 14; offset += 1) {
    const key = shiftIstDateKey(input.dateKey, -offset);
    const row = input.history.find((item) => item.dateKey === key);
    const symbol = row?.watchSymbol?.trim().toUpperCase();
    if (!row || symbol !== watch || row.dead) {
      break;
    }
    day += 1;
  }

  return day;
}

export function buildCampaignLine(input: {
  watchSymbol?: string | null;
  day: number;
}): string | null {
  const watch = input.watchSymbol?.trim().toUpperCase();
  if (!watch || input.day < 1) {
    return null;
  }

  return input.day === 1 ? `Day 1 of ${watch}` : `Day ${input.day} of ${watch}`;
}

export function buildPrefillPreview(input: {
  heldSymbols?: Array<string | null | undefined>;
  watchSymbol?: string | null;
  ticketInr?: number | null;
  leftoverInr?: number | null;
}): { headline: string; bookLine: string; leftoverLine: string } | null {
  const watch = input.watchSymbol?.trim().toUpperCase();
  if (!watch) {
    return null;
  }

  const held = [
    ...new Set(
      (input.heldSymbols ?? [])
        .map((symbol) => symbol?.trim().toUpperCase())
        .filter((symbol): symbol is string => Boolean(symbol) && symbol !== watch),
    ),
  ];
  const book = [...held, watch];
  const last = book[book.length - 1];
  const head = book.slice(0, -1);
  const bookLine =
    book.length === 1
      ? `Hold ${watch}`
      : `Hold ${head.join(", ")}${head.length ? ", and " : ""}${last}`;
  const ticket =
    input.ticketInr && input.ticketInr > 0 ? formatInr(input.ticketInr) : null;
  const leftover =
    input.leftoverInr !== null &&
    input.leftoverInr !== undefined &&
    Number.isFinite(input.leftoverInr)
      ? formatInr(Math.max(0, input.leftoverInr))
      : null;

  return {
    headline: ticket ? `If you place ${ticket} of ${watch}` : `If you place ${watch}`,
    bookLine,
    leftoverLine: leftover ? `${leftover} stays in cash` : "Cash after the fill stays put.",
  };
}

export function thesisNeedsCheckIn(
  updatedAt?: string | null,
  now = new Date(),
  days = 30,
): boolean {
  if (!updatedAt) {
    return false;
  }

  const then = new Date(updatedAt).getTime();
  if (!Number.isFinite(then)) {
    return false;
  }

  return now.getTime() - then >= days * 24 * 60 * 60 * 1000;
}

export function buildStillTrueLine(symbol: string, thesis?: string | null): string {
  const name = symbol.trim().toUpperCase();
  const why = thesis?.trim();
  if (why && why.length > 8) {
    const sentence = why.split(/(?<=[.!?])\s+/)[0] ?? why;
    return `Still true for ${name}? ${sentence}`;
  }

  return `Still true for ${name}? You wrote a line. Confirm or rewrite it.`;
}

export function gradeFromTape(input: {
  watchSymbol?: string | null;
  triggerInr?: number | null;
  sessionHigh?: number | null;
  sessionLow?: number | null;
  killInr?: number | null;
  outcome?: string | null;
}): string | null {
  const watch = input.watchSymbol?.trim().toUpperCase();
  const trigger = input.triggerInr;
  const high = input.sessionHigh;
  const low = input.sessionLow;
  const hasTrigger = trigger !== null && trigger !== undefined && trigger > 0;
  const hasHigh = high !== null && high !== undefined && high > 0;
  const followed = input.outcome === "followed_wait" || !input.outcome;

  if (!watch || !hasTrigger) {
    return null;
  }

  if (input.outcome === "placed_watch") {
    return `You placed ${watch}. The book added a name.`;
  }

  if (input.outcome === "broke_wait") {
    return "Off-plan. The book added a different name.";
  }

  const through = hasHigh && high >= trigger;
  const dead =
    input.killInr !== null &&
    input.killInr !== undefined &&
    input.killInr > 0 &&
    low !== null &&
    low !== undefined &&
    low > 0 &&
    low < input.killInr;

  if (followed && through) {
    return `You waited. ${watch} tagged ${formatInr(trigger)} and you didn't place.`;
  }

  if (followed && dead) {
    return `You waited. ${watch} lost the setup.`;
  }

  if (followed && hasHigh && high < trigger) {
    return `You waited. ${watch} never traded above ${formatInr(trigger)}.`;
  }

  return null;
}

export function assembleCloseLetter(input: {
  dateKey: string;
  heldSymbols?: string[];
  watchSymbol?: string | null;
  gapLabel?: string | null;
  outcome?: string | null;
  grade?: string | null;
  campaignDay?: number;
}): string {
  const book =
    input.heldSymbols && input.heldSymbols.length > 0
      ? input.heldSymbols.join(" · ")
      : "the book";
  const watch = input.watchSymbol?.trim().toUpperCase();
  const campaign =
    watch && input.campaignDay && input.campaignDay > 1
      ? `Day ${input.campaignDay} of ${watch}. `
      : "";
  const grade = input.grade?.trim();
  const gap = input.gapLabel?.trim();
  const outcome =
    input.outcome === "placed_watch"
      ? "Placed."
      : input.outcome === "broke_wait"
        ? "Off-plan."
        : input.outcome === "followed_wait"
          ? "Followed."
          : "Open.";

  return [
    `Close · ${input.dateKey}.`,
    `Held ${book}.`,
    watch ? `${campaign}${watch}${gap ? ` · ${gap}` : ""}. ${outcome}` : outcome,
    grade ?? "Tomorrow opens on this contract.",
  ].join(" ");
}

export function runDeskNightSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Desk night self-check failed: ${message}`);
    }
  };

  const highs = mergeSessionExtrema({ GRASIM: 3320 }, "GRASIM", 3375, "high");
  assert(highs.GRASIM === 3375, "Session high must ratchet");

  assert(
    campaignDay({
      watchSymbol: "GRASIM",
      dateKey: "2026-09-10",
      history: [
        { dateKey: "2026-09-10", watchSymbol: "GRASIM" },
        { dateKey: "2026-09-09", watchSymbol: "GRASIM" },
        { dateKey: "2026-09-08", watchSymbol: "GRASIM" },
      ],
    }) === 3,
    "Campaign must count consecutive days",
  );
  assert(
    campaignDay({
      watchSymbol: "GRASIM",
      dateKey: "2026-09-10",
      history: [
        { dateKey: "2026-09-10", watchSymbol: "GRASIM" },
        { dateKey: "2026-09-09", watchSymbol: "GRASIM", dead: true },
      ],
    }) === 1,
    "A dead day must reset the campaign",
  );

  const prefill = buildPrefillPreview({
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    watchSymbol: "GRASIM",
    ticketInr: 7000,
    leftoverInr: 3722,
  });
  assert(prefill?.bookLine.includes("GRASIM") === true, "Prefill must show the three-name book");
  assert(prefill?.headline.includes("7,000") === true, "Prefill must name the ticket");

  assert(
    thesisNeedsCheckIn("2026-08-01T10:00:00.000Z", new Date("2026-09-10T10:00:00.000Z")),
    "A 30-day thesis must ask still true",
  );
  assert(
    !thesisNeedsCheckIn("2026-09-09T10:00:00.000Z", new Date("2026-09-10T10:00:00.000Z")),
    "A fresh thesis must not nag",
  );

  assert(
    gradeFromTape({
      watchSymbol: "GRASIM",
      triggerInr: 3371,
      sessionHigh: 3319,
      outcome: "followed_wait",
    })?.includes("never traded above") === true,
    "Tape grade must use the session high",
  );
  assert(
    gradeFromTape({
      watchSymbol: "GRASIM",
      triggerInr: 3371,
      sessionHigh: 3380,
      outcome: "followed_wait",
    })?.includes("tagged") === true,
    "A session that tagged the line must say so",
  );

  const letter = assembleCloseLetter({
    dateKey: "2026-09-10",
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    watchSymbol: "GRASIM",
    gapLabel: "₹52 to the line",
    outcome: "followed_wait",
    grade: "You waited. GRASIM never traded above ₹3,371.",
    campaignDay: 3,
  });
  assert(letter.includes("Day 3"), "Close letter must name the campaign");
  assert(letter.includes("never traded above"), "Close letter must carry the grade");
}
