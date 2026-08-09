"use client";

import type { Intent } from "@/types/intent";
import { ApexCard, ApexEyebrow } from "@/components/ui/apex";

export type { Intent } from "@/types/intent";
export { decisionTodayApiPath } from "@/types/intent";

const OPTIONS: { value: Intent; label: string; hint: string }[] = [
  { value: "grow", label: "Grow", hint: "Deploy when setups qualify" },
  { value: "protect", label: "Protect", hint: "Capital safety first" },
  { value: "explore", label: "Explore", hint: "Observe without acting" },
];

type Props = {
  intent: Intent;
  onIntentChange: (intent: Intent) => void;
};

export default function IntentSelector({ intent, onIntentChange }: Props) {
  return (
    <ApexCard hover={false} padding="compact">
      <ApexEyebrow className="mb-1">Today</ApexEyebrow>
      <p className="mb-3 text-[14px] font-medium text-apex-text">
        What matters most today?
      </p>

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
                "flex-1 rounded-xl border px-4 py-3 text-left transition-all duration-200 ease-out",
                "hover:scale-[1.02] active:scale-[0.98]",
                selected
                  ? "border-blue-500/30 bg-blue-500/10 text-blue-100"
                  : "border-apex-border bg-apex-bg text-apex-muted hover:bg-white/[0.03] hover:text-apex-text",
              ].join(" ")}
            >
              <span className="block text-[14px] font-medium">{option.label}</span>
              <span className="mt-0.5 block text-[11px] font-normal opacity-70">
                {option.hint}
              </span>
            </button>
          );
        })}
      </div>
    </ApexCard>
  );
}
