"use client";

import type { Intent } from "@/types/intent";
import { INTENT_UI_LABELS } from "@/lib/onboarding/intentLabels";
import { ApexCard, ApexEyebrow } from "@/components/ui/apex";

export type { Intent } from "@/types/intent";
export { decisionTodayApiPath } from "@/types/intent";

const OPTIONS: { value: Intent; label: string; hint: string; lens: string }[] = (
  ["grow", "protect", "explore"] as const
).map((value) => ({
  value,
  label: INTENT_UI_LABELS[value].label,
  hint: INTENT_UI_LABELS[value].hint,
  lens: INTENT_UI_LABELS[value].lens,
}));

type Props = {
  intent: Intent;
  onIntentChange: (intent: Intent) => void;
  previews?: Partial<Record<Intent, string>>;
};

export default function IntentSelector({ intent, onIntentChange, previews }: Props) {
  return (
    <ApexCard hover={false} padding="compact">
      <ApexEyebrow className="mb-1">Today</ApexEyebrow>
      <p className="mb-1 text-[14px] font-medium text-apex-text">
        Pick your lens for today
      </p>
      <p className="mb-3 text-[12px] leading-snug text-apex-muted">
        Same daily verdict — each view shows you something different.
      </p>

      <div className="flex flex-col gap-2 sm:flex-row">
        {OPTIONS.map((option) => {
          const selected = intent === option.value;
          const preview = previews?.[option.value];

          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={selected}
              onClick={() => onIntentChange(option.value)}
              className={[
                "flex-1 rounded-xl border px-4 py-3 text-left transition-all duration-200 ease-out",
                "hover:scale-[1.01] active:scale-[0.99]",
                selected
                  ? "border-blue-500/35 bg-blue-500/10 text-blue-100 shadow-[0_0_0_1px_rgba(59,130,246,0.15)]"
                  : "border-apex-border bg-apex-bg text-apex-muted hover:bg-white/[0.03] hover:text-apex-text",
              ].join(" ")}
            >
              <span className="block text-[14px] font-semibold">{option.label}</span>
              <span className="mt-0.5 block text-[11px] font-normal opacity-80">
                {option.hint}
              </span>
              <span
                className={[
                  "mt-2 block text-[11px] leading-snug",
                  selected ? "text-blue-100/90" : "text-apex-muted/80",
                ].join(" ")}
              >
                {preview ?? option.lens}
              </span>
            </button>
          );
        })}
      </div>
    </ApexCard>
  );
}
