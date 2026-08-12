"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ADVISOR_PILOT_COPY,
  formatAdvisorSeatsLabel,
} from "@/lib/gtm/advisorPilotCopy";
import {
  downloadAdvisorReviewPackMarkdown,
  type AdvisorReviewPack,
} from "@/services/review/assembleAdvisorReviewPack";
import { ApexBody, ApexButton, ApexCard, ApexEyebrow } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";

type AdvisorPackResponse = {
  status: string;
  enabled: boolean;
  seats: number;
  pack: AdvisorReviewPack | null;
};

type Props = {
  compact?: boolean;
};

export default function AdvisorReviewPilotPanel({ compact = false }: Props) {
  const [enabled, setEnabled] = useState(false);
  const [seats, setSeats] = useState(0);
  const [pack, setPack] = useState<AdvisorReviewPack | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPack = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch("/api/review/advisor-pack", {
        cache: "no-store",
      });
      const data = await parseApiJson<AdvisorPackResponse>(
        response,
        "Advisor review pack",
      );

      if (!response.ok || !data) {
        setEnabled(false);
        return;
      }

      setEnabled(Boolean(data.enabled));
      setSeats(data.seats ?? 0);
      setPack(data.pack ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load advisor pack");
      setEnabled(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPack();
  }, [loadPack]);

  if (loading || !enabled || !pack) {
    return null;
  }

  return (
    <ApexCard hover={false} padding={compact ? "compact" : "default"}>
      <ApexEyebrow className="mb-1">{ADVISOR_PILOT_COPY.panelTitle}</ApexEyebrow>
      <ApexBody className="max-w-xl">{ADVISOR_PILOT_COPY.panelBody}</ApexBody>
      <p className="mt-2 text-xs text-apex-muted/75">
        {formatAdvisorSeatsLabel(seats)}
      </p>
      <p className="mt-1 text-xs text-apex-muted/65">{ADVISOR_PILOT_COPY.seatsDetail}</p>
      <p className="mt-3 text-xs text-apex-muted/70">
        {pack.week_headline} · {pack.receipt_count} receipt
        {pack.receipt_count === 1 ? "" : "s"}
      </p>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <ApexButton
          variant="secondary"
          className="w-full sm:w-auto"
          onClick={() => downloadAdvisorReviewPackMarkdown(pack)}
        >
          {ADVISOR_PILOT_COPY.exportButton}
        </ApexButton>
        <p className="text-xs text-apex-muted/60">{ADVISOR_PILOT_COPY.exportHint}</p>
      </div>

      {error ? <p className="mt-2 text-xs text-amber-200/85">{error}</p> : null}
    </ApexCard>
  );
}
