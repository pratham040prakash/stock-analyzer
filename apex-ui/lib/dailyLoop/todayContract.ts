import { formatInr } from "@/lib/funds";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";

export type TodayContractWatch = {
  symbol: string;
  through: boolean;
  triggerInr: number | null;
  ticketInr: number;
};

export type TodayContract = {
  dateKey: string;
  kiteLine: string;
  rule: string;
  watchSymbol?: string;
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

  if (input.tapeHardWait) {
    return {
      dateKey,
      kiteLine: "Do nothing in Kite. The index is range-bound.",
      rule: book,
      watchSymbol: watch?.symbol,
    };
  }

  if (watch?.through && watch.triggerInr) {
    return {
      dateKey,
      kiteLine: `In Kite: place ${formatInr(watch.ticketInr)} of ${watch.symbol} above ${formatInr(watch.triggerInr)}.`,
      rule: `${book} Today stays Wait until you place it.`,
      watchSymbol: watch.symbol,
    };
  }

  if (watch?.triggerInr) {
    return {
      dateKey,
      kiteLine: `Do nothing in Kite unless ${watch.symbol} trades above ${formatInr(watch.triggerInr)}.`,
      rule: `${book} Cash waits on ${watch.symbol}.`,
      watchSymbol: watch.symbol,
    };
  }

  if (watch) {
    return {
      dateKey,
      kiteLine: `Do nothing in Kite. Watch ${watch.symbol} — no buy line yet.`,
      rule: book,
      watchSymbol: watch.symbol,
    };
  }

  return {
    dateKey,
    kiteLine: "Do nothing in Kite today.",
    rule: book,
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
  assert(waiting.rule.includes("COALINDIA"), "Wait contract must name the book");

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

  const chop = buildTodayContract({
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
    tapeHardWait: true,
    dateKey: "2026-09-10",
  });
  assert(chop.kiteLine.includes("range-bound"), "Chop contract is do nothing");
}
