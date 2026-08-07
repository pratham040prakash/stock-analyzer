"use client";

import { useEffect, useState } from "react";
import {
  readStoredUserIntent,
  storeUserIntent,
} from "@/lib/userIntent";
import type { Intent } from "@/types/intent";

export type { Intent } from "@/types/intent";

const OPTIONS: { value: Intent; label: string }[] = [
  { value: "grow", label: "Grow Portfolio" },
  { value: "risk", label: "Reduce Risk" },
  { value: "explore", label: "Find Opportunities" },
];

function buttonClass(selected: boolean, value: Intent): string {
  const base =
    "flex-1 min-w-0 px-4 py-3 rounded-xl text-sm font-medium border transition-all";

  if (!selected) {
    return `${base} bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:border-white/15`;
  }

  switch (value) {
    case "grow":
      return `${base} bg-blue-500/15 border-blue-500/40 text-blue-100 shadow-[0_0_20px_rgba(59,130,246,0.12)]`;
    case "risk":
      return `${base} bg-orange-500/15 border-orange-500/40 text-orange-100 shadow-[0_0_20px_rgba(249,115,22,0.12)]`;
    case "explore":
      return `${base} bg-purple-500/15 border-purple-500/40 text-purple-100 shadow-[0_0_20px_rgba(168,85,247,0.12)]`;
  }
}

type Props = {
  onIntentChange?: (intent: Intent | null) => void;
};

export default function IntentSelector({ onIntentChange }: Props) {
  const [intent, setIntent] = useState<Intent | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setIntent(readStoredUserIntent());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    storeUserIntent(intent);
    onIntentChange?.(intent);
  }, [intent, hydrated, onIntentChange]);

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-5 space-y-4">
      <p className="text-sm font-medium text-gray-200">
        What do you want to do today?
      </p>

      <div className="flex flex-col sm:flex-row gap-3">
        {OPTIONS.map((option) => {
          const selected = intent === option.value;

          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={selected}
              onClick={() => setIntent(option.value)}
              className={buttonClass(selected, option.value)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
