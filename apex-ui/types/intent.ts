/** User's daily focus — drives decision, execution, and home experience. */
export type UserIntent = "grow" | "protect" | "explore";

/** @deprecated Use UserIntent — kept for gradual migration. */
export type Intent = UserIntent;

export function parseUserIntent(
  value: string | null | undefined,
): Intent | null {
  if (value === "grow" || value === "protect" || value === "explore") {
    return value;
  }

  // Legacy stored value
  if (value === "risk") {
    return "protect";
  }

  return null;
}

/** Default intent when none is selected — capital protection first. */
export function resolveIntent(intent: Intent | null | undefined): Intent {
  return intent ?? "protect";
}

export function decisionTodayApiPath(intent: Intent | null | undefined): string {
  return `/api/decision/today?intent=${encodeURIComponent(resolveIntent(intent))}`;
}

export function isGrowIntent(intent: Intent): boolean {
  return intent === "grow";
}

export function isProtectIntent(intent: Intent): boolean {
  return intent === "protect";
}

export function isExploreIntent(intent: Intent): boolean {
  return intent === "explore";
}
