/** Trading-day key in IST (matches NSE session on Today). */
export function istDateKey(date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata",
  }).format(date);
}

/** Alias used by decisions, memory, risk limits, and discipline. */
export function tradingDateKey(date = new Date()): string {
  return istDateKey(date);
}

export function shiftIstDateKey(dateKey: string, dayOffset: number): string {
  const [year, month, day] = dateKey.split("-").map(Number);
  const shifted = new Date(Date.UTC(year, month - 1, day + dayOffset));
  return istDateKey(shifted);
}

export function runTradingDateSelfCheck(): void {
  const sample = istDateKey(new Date("2026-08-09T12:00:00+05:30"));
  if (!/^\d{4}-\d{2}-\d{2}$/.test(sample)) {
    throw new Error("tradingDate self-check failed: invalid date key format");
  }

  if (sample !== "2026-08-09") {
    throw new Error(
      `tradingDate self-check failed: expected 2026-08-09 IST, got ${sample}`,
    );
  }

  if (tradingDateKey(new Date("2026-08-09T12:00:00+05:30")) !== sample) {
    throw new Error("tradingDate self-check failed: alias mismatch");
  }
}
