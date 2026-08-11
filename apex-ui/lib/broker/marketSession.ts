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

/** NSE cash session (IST): 9:15–15:30, Mon–Fri. */
export function isNseCashSessionOpen(now: Date = new Date()): boolean {
  const day = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    weekday: "short",
  }).format(now);

  if (day === "Sat" || day === "Sun") {
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
  if (isNseCashSessionOpen(now)) {
    return "Market open";
  }

  const day = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    weekday: "short",
  }).format(now);

  if (day === "Sat" || day === "Sun") {
    return "Weekend";
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
}
