import type { InvestmentStyle } from "@/types/operatingProfile";

/** ETS-004 Operating Manual — ≤20 user-facing strings */
export const OPERATING_MANUAL = {
  planTitle: "Your plan",
  coreLine: "Long-term core · hold for years · not traded on Today",
  tacticalLine: "Tactical pool · swing 2–8 weeks · only on Trade days",
  intradayLine: "Intraday · not APEX — use Kite separately",
  waitDay: "Wait day — no tactical action required.",
  pauseDay: "Pause day — protect capital. No tactical trades today.",
  tradeTacticalPrefix: "Today applies to tactical capital only",
  helpLink: "How APEX works →",
  helpHref: "/app/you/how-it-works",
  damsTitle: "Capital dams",
  damsDailyLoss: "Daily loss limit",
  damsLossStreak: "Loss-day pause",
  damsSacredCore: "Sacred core · long-term holdings are not bought on Today",
  verdictDone: "Following Wait or Pause is a successful day.",
  styleLongTermOnly: "Long-term only — Today stays mostly Wait; core never traded here.",
  styleCorePlusTactical:
    "Core + tactical — long-term holdings plus a swing pool on Trade days.",
  styleTacticalOnly: "Tactical focus — swing trades only; keep core separate in Kite.",
  intradayAck:
    "I understand APEX is not for intraday trading — I will use Kite for that.",
} as const;

export function describeInvestmentStyle(style: InvestmentStyle): string {
  switch (style) {
    case "long_term_only":
      return OPERATING_MANUAL.styleLongTermOnly;
    case "tactical_only":
      return OPERATING_MANUAL.styleTacticalOnly;
    default:
      return OPERATING_MANUAL.styleCorePlusTactical;
  }
}

export function runOperatingManualCopySelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Operating manual copy self-check failed: ${message}`);
    }
  };

  const strings = Object.values(OPERATING_MANUAL);
  assert(strings.length <= 20, "Operating manual must stay ≤20 strings");
  assert(
    describeInvestmentStyle("core_plus_tactical").includes("tactical"),
    "Style copy must describe tactical pool",
  );
}
