type LogLevel = "debug" | "info" | "warn" | "error";

export type LogFields = Record<string, unknown>;

const REDACT_KEYS = /token|secret|password|cookie|authorization/i;

function sanitizeFields(fields: LogFields): LogFields {
  const sanitized: LogFields = {};

  for (const [key, value] of Object.entries(fields)) {
    if (REDACT_KEYS.test(key)) {
      sanitized[key] = "[redacted]";
      continue;
    }

    sanitized[key] = value;
  }

  return sanitized;
}

function emit(level: LogLevel, message: string, fields: LogFields = {}): void {
  const payload = {
    level,
    msg: message,
    ts: new Date().toISOString(),
    ...sanitizeFields(fields),
  };

  const line = JSON.stringify(payload);

  if (level === "error") {
    console.error(line);
    return;
  }

  if (level === "warn") {
    console.warn(line);
    return;
  }

  console.log(line);
}

export const logger = {
  debug: (message: string, fields?: LogFields) => emit("debug", message, fields),
  info: (message: string, fields?: LogFields) => emit("info", message, fields),
  warn: (message: string, fields?: LogFields) => emit("warn", message, fields),
  error: (message: string, fields?: LogFields) => emit("error", message, fields),
};

export function runLoggerSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Logger self-check failed: ${message}`);
    }
  };

  const sanitized = sanitizeFields({
    access_token: "secret-value",
    userId: "abc",
  });

  assert(sanitized.access_token === "[redacted]", "Secrets must be redacted");
  assert(sanitized.userId === "abc", "Non-secret fields must pass through");
}
