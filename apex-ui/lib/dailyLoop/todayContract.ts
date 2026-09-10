import { formatInr } from "@/lib/funds";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";

export type TodayContractWatch = {
  symbol: string;
  through: boolean;
  dead?: boolean;
  triggerInr: number | null;
  killInr?: number | null;
  ticketInr: number;
  gapLabel?: string | null;
};

export type TodayContract = {
  dateKey: string;
  kiteLine: string;
  rule: string;
  watchSymbol?: string;
  gapLabel?: string | null;
  heldSymbols?: string[];
  outcome?: string;
  outcomeLine?: string;
  watchThrough?: boolean;
  watchDead?: boolean;
  triggerInr?: number | null;
  sessionHighBySymbol?: Record<string, number>;
  sessionLowBySymbol?: Record<string, number>;
  campaignDay?: number;
  campaignStartedOn?: string;
  gttId?: string;
  gttStatus?: string;
  closeLetter?: string;
  holdCutsBySymbol?: Record<string, number>;
};

const STORAGE_PREFIX = "apex_today_contract";

function storageKey(dateKey = tradingDateKey()): string {
  return `${STORAGE_PREFIX}:${dateKey}`;
}

export function buildTodayContract(input: {
  heldSymbols?: Array<string | null | undefined>;
  watch?: TodayContractWatch | null;
  tapeHardWait?: boolean;
  dateKey?: string;
}): TodayContract {
  const dateKey = input.dateKey ?? tradingDateKey();
  const names = [...new Set(
    (input.heldSymbols ?? [])
      .map((symbol) => symbol?.trim().toUpperCase())
      .filter((symbol): symbol is string => Boolean(symbol)),
  )];
  const book =
    names.length === 2
      ? `Hold ${names[0]} and ${names[1]}.`
      : names.length === 1
        ? `Hold ${names[0]}.`
        : "Hold the book.";
  const watch = input.watch;
  const watchState = {
    watchThrough: watch?.through,
    watchDead: watch?.dead,
    triggerInr: watch?.triggerInr ?? null,
  };

  if (input.tapeHardWait) {
    return {
      dateKey,
      kiteLine: "Do nothing in Kite. The index is range-bound.",
      rule: book,
      watchSymbol: watch?.symbol,
      gapLabel: watch?.gapLabel ?? null,
      heldSymbols: names,
      ...watchState,
    };
  }

  if (watch?.dead) {
    return {
      dateKey,
      kiteLine: `Do nothing in Kite. ${watch.symbol} lost the setup.`,
      rule: "Cash stays put.",
      watchSymbol: watch.symbol,
      gapLabel: watch.gapLabel ?? "Lost the line",
      heldSymbols: names,
      ...watchState,
    };
  }

  if (watch?.through && watch.triggerInr) {
    return {
      dateKey,
      kiteLine: `In Kite: place ${formatInr(watch.ticketInr)} of ${watch.symbol} above ${formatInr(watch.triggerInr)}.`,
      rule: `Today stays Wait until you place it.`,
      watchSymbol: watch.symbol,
      gapLabel: watch.gapLabel ?? "At the line",
      heldSymbols: names,
      ...watchState,
    };
  }

  if (watch?.triggerInr) {
    const drop =
      watch.killInr
        ? ` Drop below ${formatInr(watch.killInr)}.`
        : "";
    return {
      dateKey,
      kiteLine: `Do nothing in Kite unless ${watch.symbol} trades above ${formatInr(watch.triggerInr)}.${drop}`,
      rule: watch.gapLabel ?? `Cash waits on ${watch.symbol}.`,
      watchSymbol: watch.symbol,
      gapLabel: watch.gapLabel ?? null,
      heldSymbols: names,
      ...watchState,
    };
  }

  if (watch) {
    return {
      dateKey,
      kiteLine: `Do nothing in Kite. Watch ${watch.symbol} — no buy line yet.`,
      rule: book,
      watchSymbol: watch.symbol,
      gapLabel: watch.gapLabel ?? null,
      heldSymbols: names,
      ...watchState,
    };
  }

  return {
    dateKey,
    kiteLine: "Do nothing in Kite today.",
    rule: book,
    heldSymbols: names,
  };
}

export function rememberDeskFields(
  next: TodayContract,
  previous?: TodayContract | null,
): TodayContract {
  if (!previous) {
    return next;
  }

  return {
    ...next,
    sessionHighBySymbol: previous.sessionHighBySymbol ?? next.sessionHighBySymbol,
    sessionLowBySymbol: previous.sessionLowBySymbol ?? next.sessionLowBySymbol,
    campaignDay: next.campaignDay ?? previous.campaignDay,
    campaignStartedOn: previous.campaignStartedOn ?? next.campaignStartedOn,
    gttId: previous.gttId ?? next.gttId,
    gttStatus: previous.gttStatus ?? next.gttStatus,
    closeLetter: previous.closeLetter ?? next.closeLetter,
    holdCutsBySymbol: next.holdCutsBySymbol ?? previous.holdCutsBySymbol,
  };
}

export function persistTodayContract(contract: TodayContract): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(storageKey(contract.dateKey), JSON.stringify(contract));
}

export function readTodayContract(dateKey = tradingDateKey()): TodayContract | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(storageKey(dateKey));
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as TodayContract;
    if (!parsed?.kiteLine || !parsed?.rule) {
      return null;
    }

    return parsed;
  } catch {
    return null;
  }
}

export function runTodayContractSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Today contract self-check failed: ${message}`);
    }
  };

  const waiting = buildTodayContract({
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    watch: {
      symbol: "DIVISLAB",
      through: false,
      triggerInr: 9575,
      ticketInr: 7000,
    },
    dateKey: "2026-09-10",
  });
  assert(
    waiting.kiteLine.includes("DIVISLAB") && waiting.kiteLine.includes("9,575"),
    "Wait contract must name the Kite trigger",
  );
  assert(waiting.watchSymbol === "DIVISLAB", "Wait contract must name the watch");
  assert(
    waiting.heldSymbols?.includes("COALINDIA") === true,
    "Contract must remember the morning book",
  );
  assert(!waiting.rule.includes("COALINDIA"), "Watch contract must not restate the book");

  const through = buildTodayContract({
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    watch: {
      symbol: "DIVISLAB",
      through: true,
      triggerInr: 9575,
      ticketInr: 7000,
    },
    dateKey: "2026-09-10",
  });
  assert(through.kiteLine.includes("place"), "Through the line must name a Kite ticket");

  const band = buildTodayContract({
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    watch: {
      symbol: "DIVISLAB",
      through: false,
      triggerInr: 9575,
      killInr: 9298,
      ticketInr: 7000,
    },
    dateKey: "2026-09-10",
  });
  assert(band.kiteLine.includes("Drop below"), "Live watch must name the kill level");

  const dead = buildTodayContract({
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    watch: {
      symbol: "DIVISLAB",
      through: false,
      dead: true,
      triggerInr: 9575,
      ticketInr: 7000,
    },
    dateKey: "2026-09-10",
  });
  assert(dead.kiteLine.includes("lost the setup"), "Dead watch must keep cash idle");

  const chop = buildTodayContract({
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    tapeHardWait: true,
    dateKey: "2026-09-10",
  });
  assert(chop.kiteLine.includes("range-bound"), "Chop contract is do nothing");
}
