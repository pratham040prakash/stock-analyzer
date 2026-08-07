export type Intent = "grow" | "risk" | "explore";

export function parseUserIntent(
  value: string | null | undefined,
): Intent | null {
  if (value === "grow" || value === "risk" || value === "explore") {
    return value;
  }
  return null;
}
