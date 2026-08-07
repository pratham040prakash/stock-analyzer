import { parseUserIntent, type Intent } from "@/types/intent";

export const USER_INTENT_STORAGE_KEY = "apex_user_intent";

export function readStoredUserIntent(): Intent | null {
  if (typeof globalThis.window === "undefined") {
    return null;
  }

  try {
    return parseUserIntent(localStorage.getItem(USER_INTENT_STORAGE_KEY));
  } catch {
    return null;
  }
}

export function storeUserIntent(intent: Intent | null): void {
  if (typeof globalThis.window === "undefined") {
    return;
  }

  try {
    if (intent === null) {
      localStorage.removeItem(USER_INTENT_STORAGE_KEY);
    } else {
      localStorage.setItem(USER_INTENT_STORAGE_KEY, intent);
    }
  } catch {
    // Ignore storage failures (private mode, quota, etc.)
  }
}
