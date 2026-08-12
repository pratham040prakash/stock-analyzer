"use client";

import { useCallback, useEffect, useState } from "react";
import { SPOUSE_REVIEW_INVITE_COPY } from "@/lib/gtm/spouseReviewInviteCopy";
import type { SpouseReviewInvite } from "@/services/review/assembleSpouseReviewInvite";
import { ApexBody, ApexButton, ApexCard, ApexEyebrow } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";

type SpouseInviteResponse = {
  status: string;
  enabled: boolean;
  invite: SpouseReviewInvite | null;
};

type Props = {
  compact?: boolean;
};

export default function SpouseReviewInvitePanel({ compact = false }: Props) {
  const [enabled, setEnabled] = useState(false);
  const [invite, setInvite] = useState<SpouseReviewInvite | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const loadInvite = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch("/api/review/spouse-invite", {
        cache: "no-store",
      });
      const data = await parseApiJson<SpouseInviteResponse>(
        response,
        "Spouse review invite",
      );

      if (!response.ok || !data) {
        setEnabled(false);
        return;
      }

      setEnabled(Boolean(data.enabled));
      setInvite(data.invite ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load invite");
      setEnabled(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadInvite();
  }, [loadInvite]);

  const handleCopy = useCallback(async () => {
    if (!invite?.share_text) {
      return;
    }

    try {
      await navigator.clipboard.writeText(invite.share_text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      setError("Could not copy — select and copy the text manually.");
    }
  }, [invite?.share_text]);

  if (loading || !enabled || !invite) {
    return null;
  }

  return (
    <ApexCard hover={false} padding={compact ? "compact" : "default"}>
      <ApexEyebrow className="mb-1">
        {compact
          ? SPOUSE_REVIEW_INVITE_COPY.settingsTitle
          : SPOUSE_REVIEW_INVITE_COPY.panelTitle}
      </ApexEyebrow>
      <ApexBody className="max-w-xl">
        {compact
          ? SPOUSE_REVIEW_INVITE_COPY.settingsBody
          : SPOUSE_REVIEW_INVITE_COPY.panelBody}
      </ApexBody>
      <p className="mt-3 text-xs text-apex-muted/70">{invite.week_headline}</p>
      <p className="mt-1 text-xs text-apex-muted/60">
        {SPOUSE_REVIEW_INVITE_COPY.antiLeaderboard}
      </p>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <ApexButton
          variant="secondary"
          className="w-full sm:w-auto"
          onClick={() => void handleCopy()}
        >
          {SPOUSE_REVIEW_INVITE_COPY.copyButton}
        </ApexButton>
        <a
          href={invite.mailto_href}
          className="inline-flex min-h-[48px] w-full items-center justify-center rounded-xl px-4 py-3.5 text-[14px] font-semibold text-apex-muted transition-all duration-200 ease-out hover:bg-white/[0.03] hover:text-apex-text sm:w-auto"
        >
          {SPOUSE_REVIEW_INVITE_COPY.emailButton}
        </a>
      </div>

      <p className="mt-2 text-xs text-apex-muted/60">
        {copied
          ? SPOUSE_REVIEW_INVITE_COPY.copySuccess
          : SPOUSE_REVIEW_INVITE_COPY.emailHint}
      </p>

      {error ? <p className="mt-2 text-xs text-amber-200/85">{error}</p> : null}
    </ApexCard>
  );
}
