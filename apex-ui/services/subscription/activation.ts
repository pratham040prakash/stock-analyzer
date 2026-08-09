import { timingSafeEqual } from "node:crypto";

const ACCESS_CODE_ENV = "APEX_PREMIUM_ACCESS_CODES";

export type PremiumActivationResult =
  | { status: "activated"; codeLabel: string }
  | { status: "invalid_code" }
  | { status: "disabled" };

function normalizeCode(value: string): string {
  return value.trim().toUpperCase();
}

function codesMatch(candidate: string, expected: string): boolean {
  const left = Buffer.from(normalizeCode(candidate));
  const right = Buffer.from(normalizeCode(expected));

  if (left.length !== right.length) {
    return false;
  }

  return timingSafeEqual(left, right);
}

export function readConfiguredAccessCodes(): string[] {
  const raw = process.env[ACCESS_CODE_ENV]?.trim();

  if (!raw) {
    return [];
  }

  return raw
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

export function isPremiumActivationEnabled(): boolean {
  return readConfiguredAccessCodes().length > 0;
}

export function resolveAccessCodeLabel(code: string): string | null {
  const normalizedInput = normalizeCode(code);

  if (!normalizedInput) {
    return null;
  }

  for (const configured of readConfiguredAccessCodes()) {
    if (codesMatch(normalizedInput, configured)) {
      return normalizeCode(configured);
    }
  }

  return null;
}

export function validatePremiumAccessCode(code: string): PremiumActivationResult {
  if (!isPremiumActivationEnabled()) {
    return { status: "disabled" };
  }

  const codeLabel = resolveAccessCodeLabel(code);

  if (!codeLabel) {
    return { status: "invalid_code" };
  }

  return { status: "activated", codeLabel };
}
