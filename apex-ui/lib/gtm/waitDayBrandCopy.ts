/** T4-1 — Wait day brand + anti-FOMO GTM copy (single source of truth). */

export const WAIT_DAY_BRAND = {
  tagline: "Most days, Wait is the win.",
  headline: "Stop guessing when to do nothing.",
  heroSubline:
    "APEX gives you one calm answer each day — Wait, Trade, or Pause — so you never chase the market.",
  landingCta: "Get Today's Decision",
  footerNote: "Not a trading app. Not a stock screener.",
  noOvertradingTitle: "No overtrading",
  noOvertradingBody:
    "Most days, the right move is to do nothing — and APEX treats that as success, not FOMO.",
  antiFomoRule:
    "APEX never surfaces FOMO — no missed opportunities, hot lists, or stocks that moved without you.",
  howItWorksStep2Title: "Wait · Trade · Pause",
  howItWorksStep2Body:
    "One verdict per day. Most days are Wait — staying in cash is discipline, not missing out.",
  playbookIntro:
    "Most days are Wait — staying in cash is success. Trade only when entry confirms and capital dams allow. Pause protects you after loss streaks or daily loss limits.",
  brandCardTitle: "The Wait day brand",
  brandCardBody:
    "APEX is anti-FOMO by design. We do not rank movers, surface missed gains, or push you to trade. A logged Wait receipt is a successful day — the same discipline serious investors use to protect capital.",
  pageTitle: "APEX — Wait day discipline for investors",
  metaDescription:
    "Most days, Wait is the win. APEX gives one calm daily verdict — Wait, Trade, or Pause — with no hype and no FOMO.",
  ogTitle: "APEX — Most days, Wait is the win",
  ogDescription:
    "One daily verdict. No hot lists. No missed-opportunity guilt. Discipline-first investing for Zerodha investors.",
  waitVerdictSubline: "Wait day — no tactical action required. That is success, not inaction.",
} as const;

export function runWaitDayBrandCopySelfCheck(): void {
  const requiredKeys = [
    "tagline",
    "headline",
    "heroSubline",
    "antiFomoRule",
    "howItWorksStep2Title",
    "metaDescription",
    "ogTitle",
  ] as const;

  for (const key of requiredKeys) {
    const value = WAIT_DAY_BRAND[key];

    if (!value || value.length < 12) {
      throw new Error(`Wait day brand self-check failed: ${key}`);
    }
  }

  if (!WAIT_DAY_BRAND.antiFomoRule.toLowerCase().includes("fomo")) {
    throw new Error("Wait day brand self-check failed: anti-FOMO rule");
  }

  if (!WAIT_DAY_BRAND.howItWorksStep2Title.includes("Wait")) {
    throw new Error("Wait day brand self-check failed: verdict framing");
  }
}
