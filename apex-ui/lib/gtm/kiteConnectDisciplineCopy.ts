/** T4-2 — Zerodha-adjacent GTM: after Kite connect → APEX discipline. */

export const KITE_CONNECT_DISCIPLINE = {
  connectTitle: "Connect Zerodha — discipline on your real portfolio",
  connectDescription:
    "Read-only Kite link. APEX reads holdings and cash, then gives one Wait · Trade · Pause verdict per day.",
  connectButton: "Connect Zerodha",
  connectSubtext: "Takes less than 10 seconds · read-only",
  connectBullets: [
    "Read-only — APEX never places trades without you.",
    "One daily verdict on tactical capital — most days are Wait.",
    "Sacred core holdings stay off Today.",
  ],
  firstRunConnectDetail:
    "Read-only Kite link — then APEX applies Wait · Trade · Pause to your real portfolio.",
  successEyebrow: "Discipline unlocked",
  successHeadline: "Zerodha linked — discipline starts on Today",
  successBody:
    "Most days APEX will say Wait. That is the product working — not missing out.",
  successSyncing: "Zerodha connected — syncing your portfolio now.",
  successSynced: "Portfolio synced — open Today for your first verdict.",
  successNext: "Finish the quick setup steps, then check Today.",
  welcomeBullets: [
    "Wait · Trade · Pause — one call per day on tactical capital",
    "Receipts log discipline — not hype or hot lists",
    "Review weekly to see follow-through vs broker truth",
  ],
} as const;

export function runKiteConnectDisciplineCopySelfCheck(): void {
  const requiredKeys = [
    "connectTitle",
    "connectDescription",
    "successHeadline",
    "successBody",
    "firstRunConnectDetail",
  ] as const;

  for (const key of requiredKeys) {
    const value = KITE_CONNECT_DISCIPLINE[key];

    if (!value || value.length < 16) {
      throw new Error(`Kite connect discipline self-check failed: ${key}`);
    }
  }

  if (!KITE_CONNECT_DISCIPLINE.connectBullets[0]?.includes("Read-only")) {
    throw new Error("Kite connect discipline self-check failed: read-only bullet");
  }

  if (!KITE_CONNECT_DISCIPLINE.successHeadline.includes("discipline")) {
    throw new Error("Kite connect discipline self-check failed: discipline framing");
  }
}
