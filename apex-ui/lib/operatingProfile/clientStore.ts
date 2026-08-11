import type { OperatingProfile } from "@/types/operatingProfile";
import { parseInvestmentStyle } from "@/types/operatingProfile";

const STORAGE_KEY = "apex_operating_profile_v1";

function getStorage(): Storage | null {
  if (typeof globalThis.localStorage === "undefined") {
    return null;
  }

  return globalThis.localStorage;
}

export function readLocalOperatingProfile(): OperatingProfile | null {
  const storage = getStorage();
  if (!storage) {
    return null;
  }

  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as {
      investmentStyle?: unknown;
      intradayAcknowledgedAt?: unknown;
    };
    const investmentStyle = parseInvestmentStyle(parsed.investmentStyle);

    if (
      !investmentStyle ||
      typeof parsed.intradayAcknowledgedAt !== "string" ||
      !parsed.intradayAcknowledgedAt
    ) {
      return null;
    }

    return {
      investmentStyle,
      intradayAcknowledgedAt: parsed.intradayAcknowledgedAt,
    };
  } catch {
    return null;
  }
}

export function writeLocalOperatingProfile(profile: OperatingProfile): void {
  const storage = getStorage();
  if (!storage) {
    return;
  }

  storage.setItem(STORAGE_KEY, JSON.stringify(profile));
}

export function runOperatingProfileClientStoreSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Operating profile client store self-check failed: ${message}`);
    }
  };

  const store = new Map<string, string>();
  const original = globalThis.localStorage;

  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
    },
  });

  try {
    const profile: OperatingProfile = {
      investmentStyle: "core_plus_tactical",
      intradayAcknowledgedAt: "2026-08-11T00:00:00.000Z",
    };

    writeLocalOperatingProfile(profile);
    const restored = readLocalOperatingProfile();
    assert(restored?.investmentStyle === profile.investmentStyle, "Must round-trip profile");
  } finally {
    if (original) {
      Object.defineProperty(globalThis, "localStorage", {
        configurable: true,
        value: original,
      });
    } else {
      delete (globalThis as { localStorage?: Storage }).localStorage;
    }
  }
}
