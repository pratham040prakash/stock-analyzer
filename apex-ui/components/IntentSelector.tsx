"use client";

import type { Intent } from "@/types/intent";
import { ApexCard, ApexEyebrow } from "@/components/ui/apex";

export type { Intent } from "@/types/intent";
export { decisionTodayApiPath } from "@/types/intent";

const OPTIONS: { value: Intent; label: string }[] = [
  { value: "grow", label: "Grow" },
  { value: "risk", label: "Protect" },
  { value: "explore", label: "Explore" },
];

type Props = {
  intent: Intent;
  onIntentChange: (intent: Intent) => void;
};

export default function IntentSelector({ intent, onIntentChange }: Props) {
  return (
    <ApexCard hover={false} padding="compact">
      <ApexEyebrow className="mb-3">What matters most today?</ApexEyebrow>

      <div className="flex flex-col gap-2 sm:flex-row">
        {OPTIONS.map((option) => {
          const selected = intent === option.value;

          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={selected}
              onClick={() => onIntentChange(option.value)}
              className={[
                "flex-1 rounded-xl border px-4 py-3 text-[14px] font-medium transition-all duration-200 ease-out",
                selected
                  ? "border-blue-500/30 bg-blue-500/10 text-blue-100"
                  : "border-apex-border bg-apex-bg text-apex-muted hover:bg-white/[0.03] hover:text-apex-text",
              ].join(" ")}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </ApexCard>
  );
}
