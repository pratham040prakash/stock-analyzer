import { formatInr } from "@/lib/funds";
import type { TodayContract } from "@/lib/dailyLoop/todayContract";

export type TodayLoopState = "open" | "followed_wait" | "placed_watch" | "broke_wait";

export type TodayLoop = {
  state: TodayLoopState;
  line: string;
  watchSymbol?: string;
};

export function normalizeSymbols(
  symbols?: Array<string | null | undefined>,
): string[] {
  return [
    ...new Set(
      (symbols ?? [])
        .map((symbol) => symbol?.trim().toUpperCase())
        .filter((symbol): symbol is string => Boolean(symbol)),
    ),
  ];
}

export function resolveTodayLoop(input: {
  contract?: TodayContract | null;
  liveHeldSymbols?: Array<string | null | undefined>;
  watchFilledToday?: boolean;
  committedWait?: boolean;
}): TodayLoop {
  const contract = input.contract;
  const watch = contract?.watchSymbol?.trim().toUpperCase();
  const book = normalizeSymbols(contract?.heldSymbols);
  const live = normalizeSymbols(input.liveHeldSymbols);
  const added = live.filter((symbol) => !book.includes(symbol));

  if (watch && (input.watchFilledToday || added.includes(watch))) {
    return {
      state: "placed_watch",
      line: `Placed ${watch} in Kite.`,
      watchSymbol: watch,
    };
  }

  if (book.length > 0 && added.length > 0) {
    return {
      state: "broke_wait",
      line: `Book added ${added[0]} off-plan.`,
      watchSymbol: watch,
    };
  }

  if (input.committedWait) {
    return {
      state: "followed_wait",
      line: watch ? `Followed. No ${watch} fill.` : "Followed. Day closed.",
      watchSymbol: watch,
    };
  }

  return {
    state: "open",
    line: "",
    watchSymbol: watch,
  };
}

export function buildDeskFlip(input: {
  through?: boolean;
  dead?: boolean;
  tapeHardWait?: boolean;
  watchSymbol?: string | null;
  ticketInr?: number | null;
  triggerInr?: number | null;
  waitHeadline: string;
  waitSubline: string;
}): { displayWord: string; headline: string; subline: string } {
  const symbol = input.watchSymbol?.trim().toUpperCase();

  if (input.tapeHardWait) {
    return {
      displayWord: "Wait",
      headline: input.waitHeadline,
      subline: input.waitSubline,
    };
  }

  if (input.through && symbol && input.ticketInr && input.triggerInr) {
    return {
      displayWord: "Place",
      headline: `Place ${formatInr(input.ticketInr)} of ${symbol}`,
      subline: `Above ${formatInr(input.triggerInr)} in Kite. Today stays Wait until you do.`,
    };
  }

  if (input.dead && symbol) {
    return {
      displayWord: "Wait",
      headline: "Cash stays put",
      subline: `${symbol} lost the setup.`,
    };
  }

  return {
    displayWord: "Wait",
    headline: input.waitHeadline,
    subline: input.waitSubline,
  };
}

export function runTodayLoopSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Today loop self-check failed: ${message}`);
    }
  };

  const contract = {
    dateKey: "2026-09-10",
    kiteLine: "Do nothing in Kite unless GRASIM trades above ₹3,371.",
    rule: "₹52 to the line",
    watchSymbol: "GRASIM",
    heldSymbols: ["COALINDIA", "ADANIPORTS"],
  };

  const followed = resolveTodayLoop({
    contract,
    liveHeldSymbols: ["COALINDIA", "ADANIPORTS"],
    committedWait: true,
  });
  assert(followed.state === "followed_wait", "Wait commit with no fill is followed");
  assert(followed.line.includes("GRASIM"), "Followed line must name the watch");

  const placed = resolveTodayLoop({
    contract,
    liveHeldSymbols: ["COALINDIA", "ADANIPORTS", "GRASIM"],
  });
  assert(placed.state === "placed_watch", "New watch holding is a Kite place");

  const filled = resolveTodayLoop({
    contract,
    liveHeldSymbols: ["COALINDIA", "ADANIPORTS"],
    watchFilledToday: true,
  });
  assert(filled.state === "placed_watch", "Broker fill on the watch closes the loop");

  const broke = resolveTodayLoop({
    contract,
    liveHeldSymbols: ["COALINDIA", "ADANIPORTS", "INFY"],
  });
  assert(broke.state === "broke_wait", "A different new name is off-plan");

  const flip = buildDeskFlip({
    through: true,
    watchSymbol: "GRASIM",
    ticketInr: 7000,
    triggerInr: 3371,
    waitHeadline: "Hold COALINDIA and ADANIPORTS",
    waitSubline: "Two names are the book. No trim today.",
  });
  assert(flip.displayWord === "Place", "Through the line must flip Today to Place");
  assert(flip.headline.includes("GRASIM"), "Place headline must name the ticket");
}
