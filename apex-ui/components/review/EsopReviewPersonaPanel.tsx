"use client";

import { useCallback, useEffect, useState } from "react";
import { ESOP_REVIEW_PERSONA_COPY } from "@/lib/gtm/esopReviewPersonaCopy";
import {
  downloadEsopReviewBriefMarkdown,
  type EsopReviewBrief,
} from "@/services/review/assembleEsopReviewBrief";
import { ApexBody, ApexButton, ApexCard, ApexEyebrow } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";

type EsopBriefResponse = {
  status: string;
  enabled: boolean;
  brief: EsopReviewBrief | null;
};

type Props = {
  compact?: boolean;
};

export default function EsopReviewPersonaPanel({ compact = false }: Props) {
  const [enabled, setEnabled] = useState(false);
  const [brief, setBrief] = useState<EsopReviewBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const loadBrief = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch("/api/review/esop-brief", {
        cache: "no-store",
      });
      const data = await parseApiJson<EsopBriefResponse>(
        response,
        "ESOP review brief",
      );

      if (!response.ok || !data) {
        setEnabled(false);
        return;
      }

      setEnabled(Boolean(data.enabled));
      setBrief(data.brief ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load ESOP brief");
      setEnabled(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadBrief();
  }, [loadBrief]);

  const handleCopy = useCallback(async () => {
    if (!brief?.share_text) {
      return;
    }

    try {
      await navigator.clipboard.writeText(brief.share_text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      setError("Could not copy — select and copy the text manually.");
    }
  }, [brief?.share_text]);

  if (loading || !enabled || !brief) {
    return null;
  }

  return (
    <ApexCard hover={false} padding={compact ? "compact" : "default"}>
      <ApexEyebrow className="mb-1">
        {compact
          ? ESOP_REVIEW_PERSONA_COPY.settingsTitle
          : ESOP_REVIEW_PERSONA_COPY.panelTitle}
      </ApexEyebrow>
      <ApexBody className="max-w-xl">
        {compact
          ? ESOP_REVIEW_PERSONA_COPY.settingsBody
          : ESOP_REVIEW_PERSONA_COPY.panelBody}
      </ApexBody>
      <p className="mt-3 text-xs text-apex-muted/70">{brief.week_headline}</p>
      <p className="mt-1 text-xs text-apex-muted/65">{brief.investment_style_line}</p>
      <p className="mt-1 text-xs text-apex-muted/60">
        {ESOP_REVIEW_PERSONA_COPY.antiTrading}
      </p>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <ApexButton
          variant="secondary"
          className="w-full sm:w-auto"
          onClick={() => void handleCopy()}
        >
          {ESOP_REVIEW_PERSONA_COPY.copyButton}
        </ApexButton>
        <ApexButton
          variant="ghost"
          className="w-full sm:w-auto"
          onClick={() => downloadEsopReviewBriefMarkdown(brief)}
        >
          {ESOP_REVIEW_PERSONA_COPY.downloadButton}
        </ApexButton>
      </div>

      <p className="mt-2 text-xs text-apex-muted/60">
        {copied
          ? ESOP_REVIEW_PERSONA_COPY.copySuccess
          : ESOP_REVIEW_PERSONA_COPY.downloadHint}
      </p>

      {error ? <p className="mt-2 text-xs text-amber-200/85">{error}</p> : null}
    </ApexCard>
  );
}
