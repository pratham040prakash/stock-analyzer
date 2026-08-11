import type { TierFeatures } from "@/services/subscription/tier";

export type PremiumFeatureKey = keyof TierFeatures;

export type PremiumFeatureCopy = {
  title: string;
  body: string;
  roi: string;
};

export const PREMIUM_FEATURE_COPY: Record<PremiumFeatureKey, PremiumFeatureCopy> = {
  marginMode: {
    title: "Margin deploy mode",
    body: "Deploy tactical capital with cash plus collateral under APEX dams — not unlimited leverage.",
    roi: "Pay for controlled deployment, not bigger bets.",
  },
  decisionDepth: {
    title: "Full decision depth",
    body: "Reasoning, watch items, and setup context when you need to understand why — not tips.",
    roi: "Pay for clarity on hard days, not more noise.",
  },
  decisionHistory: {
    title: "Decision history",
    body: "Review the last two weeks of verdicts, commits, and discipline — your audit trail.",
    roi: "Pay for memory that improves tomorrow's process.",
  },
  reviewDigest: {
    title: "Weekly review digest",
    body: "Telegram or email summary: plan follow-through, monthly doctor, quarterly check-in.",
    roi: "Pay for the ritual reaching you — even when you skip opening the app.",
  },
  thesisExport: {
    title: "Investment book export",
    body: "Download every saved thesis as one markdown investment book.",
    roi: "Pay for a portable record of why you own what you own.",
  },
  trustCdqsHistory: {
    title: "CDQS trend history",
    body: "Track how calibrated decision quality moves over closed trades — not hit rate.",
    roi: "Pay for proof the system learns with your money, not marketing.",
  },
};

export const PREMIUM_VALUE_HEADLINE =
  "Premium pays for discipline infrastructure — not tips or green days.";

export const PREMIUM_VALUE_DETAIL =
  "Free tier keeps Today Wait · Trade · Pause, broker truth, and weekly review. Premium adds depth, exports, digests, and trust history when you want the full operating system.";

export function runPremiumCopySelfCheck(): void {
  const keys = Object.keys(PREMIUM_FEATURE_COPY) as PremiumFeatureKey[];

  if (keys.length !== 6) {
    throw new Error("Premium copy self-check failed: feature count");
  }

  for (const key of keys) {
    const copy = PREMIUM_FEATURE_COPY[key];

    if (!copy.title || !copy.body || !copy.roi) {
      throw new Error(`Premium copy self-check failed: missing fields for ${key}`);
    }
  }
}
