export type Intent = "grow" | "risk" | "explore";

export function parseUserIntent(
  value: string | null | undefined,
): Intent | null {
  if (value === "grow" || value === "risk" || value === "explore") {
    return value;
  }
  return null;
}

/** Default intent when none is selected — reduce-risk guidance. */
export function resolveIntent(intent: Intent | null | undefined): Intent {
  return intent ?? "risk";
}

export function decisionTodayApiPath(intent: Intent | null | undefined): string {
  return `/api/decision/today?intent=${encodeURIComponent(resolveIntent(intent))}`;
}
