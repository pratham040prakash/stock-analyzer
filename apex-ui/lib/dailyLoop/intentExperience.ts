import type { UserIntent } from "@/types/intent";

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

const EXPERIENCE: Record<UserIntent, IntentExperience> = {
  grow: {
    tagline: "Prepare to deploy capital",
    cardGradient: "from-emerald-500/[0.05]",
    showExecution: true,
    showSafety: false,
    showExploreInsights: false,
    executionTitle: "How to act today",
    exploreTitle: "What's interesting today",
    safetyTitle: "Capital safety",
    mindsetTitle: "Mindset",
    trustTitle: "Your discipline",
  },
  protect: {
    tagline: "Capital protection mode",
    cardGradient: "from-amber-500/[0.05]",
    showExecution: false,
    showSafety: true,
    showExploreInsights: false,
    executionTitle: "How to act today",
    exploreTitle: "What's interesting today",
    safetyTitle: "Stay protected",
    mindsetTitle: "Mindset",
    trustTitle: "Your discipline",
  },
  explore: {
    tagline: "No pressure. Just observe.",
    cardGradient: "from-blue-500/[0.05]",
    showExecution: false,
    showSafety: false,
    showExploreInsights: true,
    executionTitle: "How to act today",
    exploreTitle: "What's interesting today",
    safetyTitle: "Capital safety",
    mindsetTitle: "Mindset",
    trustTitle: "Your discipline",
  },
};

export function getIntentExperience(intent: UserIntent): IntentExperience {
  return EXPERIENCE[intent];
}
