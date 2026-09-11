"use client";

import type { MorningBriefViewModel } from "@/types/morningBrief";
import type { DailyDecisionArtifact } from "@/types/decision";
import { hydrateArtifactViews } from "@/types/decision";

type Props = {
  brief: MorningBriefViewModel;
  artifact?: DailyDecisionArtifact | null;
};

export default function ProofStructurePanel({ brief, artifact }: Props) {
  const graph = artifact
    ? hydrateArtifactViews(artifact).evidence_graph
    : {
        supporting_ids: brief.evidence.supporting_ids ?? [],
        conflicting_ids: brief.evidence.conflicting_ids ?? [],
      };
  const evidenceById = new Map(
    (artifact?.evidence ?? []).map((item) => [item.id, item]),
  );
  const supporting = (graph?.supporting_ids ?? [])
    .map((id) => evidenceById.get(id))
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
  const conflicting = (graph?.conflicting_ids ?? [])
    .map((id) => evidenceById.get(id))
    .filter((item): item is NonNullable<typeof item> => Boolean(item));

  const fallbackLevels = brief.evidence.supporting_signals
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
      {supporting.length > 0 ? (
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Supporting evidence
          </p>
          <ul className="space-y-1 text-xs text-apex-muted/85">
            {supporting.map((item) => (
              <li key={item.id}>
                {item.id} · {item.summary}
              </li>
            ))}
          </ul>
        </div>
      ) : fallbackLevels.length > 0 ? (
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Key levels
          </p>
          <ul className="space-y-1 text-xs text-apex-muted/85">
            {fallbackLevels.map((level) => (
              <li key={level}>{level}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {conflicting.length > 0 ? (
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-amber-100/80">
            Conflicting evidence
          </p>
          <ul className="space-y-1 text-xs text-amber-100/75">
            {conflicting.map((item) => (
              <li key={item.id}>
                {item.id} · {item.summary}
              </li>
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
