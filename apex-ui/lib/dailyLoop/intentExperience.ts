import type { UserIntent } from "@/types/intent";
import { INTENT_UI_LABELS } from "@/lib/onboarding/intentLabels";

export type IntentExperience = {
  tagline: string;
  cardGradient: string;
  showExecution: boolean;
  showSafety: boolean;
  showExploreInsights: boolean;
  executionTitle: string;
  exploreTitle: string;
  safetyTitle: string;
  mindsetTitle: string;
  trustTitle: string;
};

const EXPERIENCE: Record<UserIntent, Omit<IntentExperience, "tagline">> = {
  grow: {
    cardGradient: "from-emerald-500/[0.05]",
    showExecution: true,
    showSafety: false,
    showExploreInsights: false,
    executionTitle: "How to deploy",
    exploreTitle: "Capital on hold",
    safetyTitle: "Capital safety",
    mindsetTitle: "Mindset",
    trustTitle: "Your discipline",
  },
  protect: {
    cardGradient: "from-amber-500/[0.05]",
    showExecution: false,
    showSafety: true,
    showExploreInsights: false,
    executionTitle: "How to act today",
    exploreTitle: "Capital on hold",
    safetyTitle: "Stay protected",
    mindsetTitle: "Mindset",
    trustTitle: "Your discipline",
  },
  explore: {
    cardGradient: "from-blue-500/[0.05]",
    showExecution: false,
    showSafety: false,
    showExploreInsights: true,
    executionTitle: "How to act today",
    exploreTitle: "No deployment today",
    safetyTitle: "Capital safety",
    mindsetTitle: "Mindset",
    trustTitle: "Your discipline",
  },
};

export function getIntentExperience(intent: UserIntent): IntentExperience {
  return {
    ...EXPERIENCE[intent],
    tagline: INTENT_UI_LABELS[intent].tagline,
  };
}
