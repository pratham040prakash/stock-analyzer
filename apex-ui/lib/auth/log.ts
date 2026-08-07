import { devLog } from "@/lib/env";

type AuthLogLevel = "info" | "error";

function writeAuthLog(level: AuthLogLevel, message: string, detail?: unknown): void {
  if (process.env.NODE_ENV === "production") return;

  const payload =
    detail !== undefined ? { level, message, detail } : { level, message };

  if (level === "error") {
    console.error("[APEX Auth]", payload);
    return;
  }

  devLog("[APEX Auth]", payload);
}

export function authLog(message: string, detail?: unknown): void {
  writeAuthLog("info", message, detail);
}

export function authError(message: string, detail?: unknown): void {
  writeAuthLog("error", message, detail);
}

export function authDebug(message: string, detail?: unknown): void {
  if (process.env.NODE_ENV === "production") return;
  authLog(message, detail);
}
