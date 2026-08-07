type BrokerLogLevel = "info" | "error";

function redact(value: unknown): unknown {
  if (typeof value !== "object" || value === null) return value;

  const redacted: Record<string, unknown> = {};
  for (const [key, entry] of Object.entries(value as Record<string, unknown>)) {
    if (/token|secret|checksum|encrypted/i.test(key) && typeof entry === "string") {
      redacted[key] = entry.length > 8 ? `${entry.slice(0, 4)}…${entry.slice(-4)}` : "[redacted]";
    } else {
      redacted[key] = entry;
    }
  }
  return redacted;
}

function writeBrokerLog(level: BrokerLogLevel, message: string, detail?: unknown): void {
  const payload =
    detail !== undefined
      ? { level, message, detail: redact(detail) }
      : { level, message };

  if (level === "error") {
    console.error("[APEX Zerodha]", payload);
    return;
  }

  console.info("[APEX Zerodha]", payload);
}

export function brokerLog(message: string, detail?: unknown): void {
  writeBrokerLog("info", message, detail);
}

export function brokerError(message: string, detail?: unknown): void {
  writeBrokerLog("error", message, detail);
}
