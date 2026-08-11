"use client";

import { useState } from "react";
import type { InvestmentStyle } from "@/types/operatingProfile";
import { describeInvestmentStyle, OPERATING_MANUAL } from "@/lib/dailyLoop/operatingManualCopy";
import { apiFetch, parseApiJson, readApiErrorMessage } from "@/lib/api/clientFetch";
import { writeLocalOperatingProfile } from "@/lib/operatingProfile/clientStore";
import type { OperatingProfile } from "@/types/operatingProfile";
import {
  ApexBody,
  ApexCard,
  ApexEyebrow,
  ApexTitle,
} from "@/components/ui/apex";

const STYLE_OPTIONS: Array<{
  value: InvestmentStyle;
  label: string;
}> = [
  {
    value: "long_term_only",
    label: "Long-term only",
  },
  {
    value: "core_plus_tactical",
    label: "Core + tactical (recommended)",
  },
  {
    value: "tactical_only",
    label: "Tactical swing only",
  },
];

type Props = {
  onComplete?: (profile: OperatingProfile) => void;
  stepHint?: string;
};

export default function InvestmentStyleSetup({ onComplete, stepHint }: Props) {
  const [selectedStyle, setSelectedStyle] = useState<InvestmentStyle | null>(
    "core_plus_tactical",
  );
  const [intradayAcknowledged, setIntradayAcknowledged] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!selectedStyle || !intradayAcknowledged) {
      setError("Choose a style and confirm the intraday rule to continue.");
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const profile: OperatingProfile = {
        investmentStyle: selectedStyle,
        intradayAcknowledgedAt: new Date().toISOString(),
      };

      const res = await apiFetch("/api/operating-profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          investmentStyle: selectedStyle,
          intradayAcknowledged: true,
        }),
      });

      const data = await parseApiJson<{ status?: string; message?: string }>(
        res,
        "Operating profile",
      );

      if (res.ok) {
        writeLocalOperatingProfile(profile);
        onComplete?.(profile);
        return;
      }

      if (res.status === 503) {
        writeLocalOperatingProfile(profile);
        onComplete?.(profile);
        return;
      }

      throw new Error(readApiErrorMessage(data, "Could not save profile"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save profile");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <ApexCard hover={false}>
      {stepHint ? <ApexEyebrow>{stepHint}</ApexEyebrow> : null}
      <ApexBody className={stepHint ? "mt-2 italic" : "italic"}>
        One last step — how you invest, so Today speaks your language.
      </ApexBody>

      <ApexTitle className="mt-4 text-[18px]">
        How do you want APEX to operate?
      </ApexTitle>
      <ApexEyebrow className="mt-1">
        This sets your operating manual on Today
      </ApexEyebrow>

      <div className="mt-4 space-y-2">
        {STYLE_OPTIONS.map((option) => {
          const selected = selectedStyle === option.value;

          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={selected}
              onClick={() => setSelectedStyle(option.value)}
              className={[
                "w-full rounded-xl border px-4 py-3 text-left transition-all duration-200",
                selected
                  ? "border-blue-500/30 bg-blue-500/10 text-blue-100"
                  : "border-apex-border bg-apex-bg text-apex-text hover:bg-white/[0.03]",
              ].join(" ")}
            >
              <span className="block text-[14px] font-medium">{option.label}</span>
              <span className="mt-1 block text-[12px] text-apex-muted/80">
                {describeInvestmentStyle(option.value)}
              </span>
            </button>
          );
        })}
      </div>

      <label className="mt-5 flex cursor-pointer items-start gap-3 rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-3">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 rounded border-apex-border"
          checked={intradayAcknowledged}
          onChange={(event) => setIntradayAcknowledged(event.target.checked)}
        />
        <span className="text-sm leading-snug text-apex-text/85">
          {OPERATING_MANUAL.intradayAck}
        </span>
      </label>

      {error ? (
        <p className="mt-3 text-sm text-amber-200/90">{error}</p>
      ) : null}

      <button
        type="button"
        disabled={isSaving || !selectedStyle || !intradayAcknowledged}
        onClick={() => void handleSubmit()}
        className="mt-4 w-full rounded-xl bg-blue-500/90 px-4 py-3 text-sm font-medium text-white transition-opacity hover:bg-blue-500 disabled:opacity-50"
      >
        {isSaving ? "Saving…" : "Continue to Today"}
      </button>
    </ApexCard>
  );
}
