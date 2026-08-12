"use client";

import { useState } from "react";
import {
  computeTargetByDate,
  formatTimeTargetLabel,
  JOURNEY_TIME_PRESETS,
  type JourneyTimeSuggestion,
} from "@/lib/journey/journeyTimeTarget";
import { JOURNEY_COPY } from "@/lib/journey/journeyCopy";
import type { JourneyTimeUnit } from "@/types/investmentJourney";

export type JourneyTimeTargetPickerProps = {
  amount: number;
  unit: JourneyTimeUnit;
  startedAt?: string;
  onChange: (next: { amount: number; unit: JourneyTimeUnit }) => void;
  suggestion?: JourneyTimeSuggestion | null;
  compact?: boolean;
  className?: string;
};

const UNITS: JourneyTimeUnit[] = ["days", "weeks", "years"];

export default function JourneyTimeTargetPicker({
  amount,
  unit,
  startedAt,
  onChange,
  suggestion = null,
  compact = false,
  className = "",
}: JourneyTimeTargetPickerProps) {
  const [showAdjust, setShowAdjust] = useState(false);
  const startIso = startedAt ?? new Date().toISOString().slice(0, 10);
  const targetBy = computeTargetByDate(startIso, amount, unit);
  const targetLabel = formatTimeTargetLabel(amount, unit);
  const usingSuggestion =
    suggestion !== null &&
    suggestion.amount === amount &&
    suggestion.unit === unit;

  return (
    <div className={className}>
      <p
        className={[
          "font-medium text-apex-text/90",
          compact ? "text-xs" : "text-sm",
        ].join(" ")}
      >
        {JOURNEY_COPY.timeTargetTitle}
      </p>
      <p className="mt-0.5 text-[11px] text-apex-muted/70">{JOURNEY_COPY.timeSuggestLead}</p>

      {suggestion ? (
        <div className="mt-3 rounded-lg border border-sky-500/25 bg-sky-500/[0.08] px-3 py-3">
          <p className="text-base font-semibold tracking-tight text-sky-100">
            {suggestion.waitLabel}
          </p>
          <p className="mt-1 text-sm font-medium text-sky-50/95">{suggestion.patienceUntil}</p>
          <p className="mt-1 text-xs leading-relaxed text-sky-50/85">{suggestion.rationale}</p>
          <p className="mt-2 text-[11px] tabular-nums text-apex-muted/70">
            Target by {suggestion.targetByIso} · +{suggestion.movePctNeeded}% price move needed
          </p>
          {!usingSuggestion ? (
            <button
              type="button"
              onClick={() => onChange({ amount: suggestion.amount, unit: suggestion.unit })}
              className="mt-2 text-xs font-medium text-sky-200 underline underline-offset-2 hover:text-white"
            >
              {JOURNEY_COPY.timeSuggestUse}
            </button>
          ) : null}
        </div>
      ) : null}

      {!showAdjust && suggestion ? (
        <button
          type="button"
          onClick={() => setShowAdjust(true)}
          className="mt-3 text-xs text-apex-muted/75 underline underline-offset-2 hover:text-apex-text"
        >
          {JOURNEY_COPY.timeAdjust}
        </button>
      ) : (
        <>
          <div className="mt-3 flex flex-wrap gap-2">
            {JOURNEY_TIME_PRESETS.map((preset) => {
              const active = preset.amount === amount && preset.unit === unit;
              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => onChange({ amount: preset.amount, unit: preset.unit })}
                  className={[
                    "rounded-full border px-3 py-1 text-xs transition-colors",
                    active
                      ? "border-violet-400/50 bg-violet-500/20 text-violet-100"
                      : "border-apex-border/25 text-apex-muted/80 hover:border-apex-border/40",
                  ].join(" ")}
                >
                  {preset.label}
                </button>
              );
            })}
          </div>

          <div className="mt-3 flex flex-wrap items-end gap-3">
            <label className="text-xs text-apex-muted/80">
              {JOURNEY_COPY.timeAmountLabel}
              <input
                type="number"
                min={1}
                max={unit === "years" ? 10 : unit === "weeks" ? 52 : 365}
                value={amount}
                onChange={(event) => {
                  const next = Number(event.target.value);
                  if (Number.isFinite(next) && next > 0) {
                    onChange({ amount: Math.round(next), unit });
                  }
                }}
                className="mt-1 w-20 rounded-lg border border-apex-border/25 bg-black/20 px-3 py-2 text-sm tabular-nums text-apex-text"
              />
            </label>

            <label className="text-xs text-apex-muted/80">
              {JOURNEY_COPY.timeUnitLabel}
              <select
                value={unit}
                onChange={(event) =>
                  onChange({ amount, unit: event.target.value as JourneyTimeUnit })
                }
                className="mt-1 block rounded-lg border border-apex-border/25 bg-black/20 px-3 py-2 text-sm text-apex-text"
              >
                {UNITS.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <p className="text-xs text-apex-muted/75">
              {JOURNEY_COPY.timeTargetBy}{" "}
              <span className="text-apex-text/85">{targetBy}</span>
              <span className="text-apex-muted/55"> · {targetLabel}</span>
            </p>
          </div>
        </>
      )}
    </div>
  );
}
