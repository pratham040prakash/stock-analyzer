"use client";

import type { Intent } from "@/types/intent";
import { INTENT_UI_LABELS } from "@/lib/onboarding/intentLabels";

export type { Intent } from "@/types/intent";
export { decisionTodayApiPath } from "@/types/intent";

const OPTIONS: { value: Intent; label: string }[] = (
  ["grow", "protect", "explore"] as const
).map((value) => ({
  value,
  label: INTENT_UI_LABELS[value].label,
}));

type Props = {
  intent: Intent;
  onIntentChange: (intent: Intent) => void;
  previews?: Partial<Record<Intent, string>>;
};

export default function IntentSelector({ intent, onIntentChange, previews }: Props) {
  return (
    <div className="flex justify-center">
      <div
        role="tablist"
        aria-label="Today view"
        className="inline-flex rounded-full border border-white/[0.08] bg-black/25 p-1"
      >
        {OPTIONS.map((option) => {
          const selected = intent === option.value;
          const preview = previews?.[option.value];

          return (
            <button
              key={option.value}
              type="button"
              role="tab"
              aria-selected={selected}
              title={preview ?? INTENT_UI_LABELS[option.value].hint}
              onClick={() => onIntentChange(option.value)}
              className={[
                "min-h-10 rounded-full px-4 text-[13px] font-medium transition-all duration-200",
                selected
                  ? "bg-white text-slate-950 shadow-[0_8px_24px_rgba(0,0,0,0.28)]"
                  : "text-apex-muted hover:text-apex-text",
              ].join(" ")}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
