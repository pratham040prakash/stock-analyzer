function getIstMinutes(now: Date): number {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata",
    hour: "numeric",
    minute: "numeric",
    hour12: false,
  }).formatToParts(now);
  const hour = Number(parts.find((part) => part.type === "hour")?.value ?? 0);
  const minute = Number(
    parts.find((part) => part.type === "minute")?.value ?? 0,
  );

  return hour * 60 + minute;
}

function istWeekday(now: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    weekday: "short",
  }).format(now);
}

function istDateKey(now: Date): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata",
  }).format(now);
}

/** NSE cash holidays + Diwali special session days (not a normal cash day). */
export const NSE_CASH_HOLIDAYS_2026 = new Set([
  "2026-01-26",
  "2026-03-03",
  "2026-03-31",
  "2026-04-03",
  "2026-04-14",
  "2026-05-01",
  "2026-08-15",
  "2026-10-02",
  "2026-10-20",
  "2026-11-08",
  "2026-11-09",
  "2026-12-25",
]);

export function isNseWeekend(now: Date = new Date()): boolean {
  const day = istWeekday(now);
  return day === "Sat" || day === "Sun";
}

export function isNseHoliday(now: Date = new Date()): boolean {
  return NSE_CASH_HOLIDAYS_2026.has(istDateKey(now));
}

export function isMuhuratSessionDay(now: Date = new Date()): boolean {
  return istDateKey(now) === "2026-11-08";
}

export function isDeskClosedForNewPicks(now: Date = new Date()): boolean {
  return isNseWeekend(now) || isNseHoliday(now);
}

/** NSE cash session (IST): 9:15–15:30, Mon–Fri, excluding holidays. */
export function isNseCashSessionOpen(now: Date = new Date()): boolean {
  if (isNseWeekend(now) || isNseHoliday(now)) {
    return false;
  }

  const minutes = getIstMinutes(now);
  const open = 9 * 60 + 15;
  const close = 15 * 60 + 30;

  return minutes >= open && minutes < close;
}

export function getMarketOrderBlockReason(now: Date = new Date()): string | null {
  if (isNseCashSessionOpen(now)) {
    return null;
  }

  return "Market is closed. NSE cash orders execute 9:15 AM – 3:30 PM IST, Monday–Friday.";
}

export function getMarketSessionPhase(now: Date = new Date()): string {
  if (isMuhuratSessionDay(now)) {
    return "Muhurat — not a normal cash day";
  }

  if (isNseHoliday(now)) {
    return "Holiday";
  }

  if (isNseWeekend(now)) {
    return "Weekend";
  }

  if (isNseCashSessionOpen(now)) {
    const minutes = getIstMinutes(now);
    return minutes >= 14 * 60 + 30 ? "Last hour" : "Market open";
  }

  const minutes = getIstMinutes(now);
  const open = 9 * 60 + 15;

  return minutes < open ? "Pre-market" : "After hours";
}

export function runMarketSessionSelfCheck(): void {
  const open = isNseCashSessionOpen(new Date("2026-08-11T10:00:00+05:30"));
  const closed = isNseCashSessionOpen(new Date("2026-08-11T08:30:00+05:30"));

  if (!open) {
    throw new Error("marketSession self-check failed: expected open at 10:00 IST");
  }

  if (closed) {
    throw new Error("marketSession self-check failed: expected closed at 8:30 IST");
  }

  if (isNseCashSessionOpen(new Date("2026-01-26T11:00:00+05:30"))) {
    throw new Error("marketSession self-check failed: Republic Day is not a cash day");
  }

  if (getMarketSessionPhase(new Date("2026-08-11T15:00:00+05:30")) !== "Last hour") {
    throw new Error("marketSession self-check failed: 15:00 IST is last hour");
  }

  if (getMarketSessionPhase(new Date("2026-09-12T12:00:00+05:30")) !== "Weekend") {
    throw new Error("marketSession self-check failed: Saturday freezes new picks");
  }
}
