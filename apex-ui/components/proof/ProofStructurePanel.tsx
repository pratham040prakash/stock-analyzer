"use client";

import type { MorningBriefViewModel } from "@/types/morningBrief";

type Props = {
  brief: MorningBriefViewModel;
};

export default function ProofStructurePanel({ brief }: Props) {
  const levels = brief.evidence.supporting_signals
    .slice(0, 3)
    .map((signal) => `${signal.label}: ${signal.value}`);

  return (
    <section
      aria-label="Proof structure"
      className="rounded-xl border border-purple-500/15 bg-purple-500/5 px-4 py-4 space-y-3"
    >
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Why this structure
      </p>
      <p className="text-sm text-apex-text/90">{brief.trust.why_this_is_recommended}</p>
      {brief.evidence.key_reasons.length > 0 ? (
        <ul className="space-y-1 text-sm text-apex-text/85">
          {brief.evidence.key_reasons.slice(0, 3).map((reason) => (
            <li key={reason}>• {reason}</li>
          ))}
        </ul>
      ) : null}
      {levels.length > 0 ? (
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Key levels
          </p>
          <ul className="space-y-1 text-xs text-apex-muted/85">
            {levels.map((level) => (
              <li key={level}>{level}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {brief.evidence.gap_note ? (
        <p className="text-xs text-amber-100/80">{brief.evidence.gap_note}</p>
      ) : null}
    </section>
  );
}
