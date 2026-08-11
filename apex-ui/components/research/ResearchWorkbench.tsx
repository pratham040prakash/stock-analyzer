"use client";

import type { ResearchSummaryViewModel } from "@/types/researchSummary";

type Props = {
  summary: ResearchSummaryViewModel;
  loading?: boolean;
  error?: string | null;
};

function verdictTone(verdict: ResearchSummaryViewModel["verdict"]): string {
  switch (verdict) {
    case "YES":
      return "text-emerald-200";
    case "NO":
      return "text-amber-200";
    default:
      return "text-blue-100";
  }
}

export default function ResearchWorkbench({ summary, loading, error }: Props) {
  if (loading) {
    return <p className="text-sm text-apex-muted/70">Building research view…</p>;
  }

  if (error) {
    return <p className="text-sm text-amber-200/85">{error}</p>;
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Investment decision
        </p>
        <p className={`text-4xl font-semibold ${verdictTone(summary.verdict)}`}>
          {summary.verdict_label}
        </p>
        <p className="text-sm text-apex-text/90">{summary.headline}</p>
        <p className="text-sm text-apex-muted/85">{summary.summary}</p>
        <div className="flex flex-wrap gap-3 text-xs text-apex-muted/75">
          {summary.score !== null ? <span>Score {summary.score}/100</span> : null}
          {summary.grade ? <span>Grade {summary.grade}</span> : null}
          {summary.risk_level ? <span>Risk · {summary.risk_level}</span> : null}
          <span>Source · {summary.source.replace("_", " ")}</span>
        </div>
        {!summary.alpha_available ? (
          <p className="text-xs text-apex-muted/65">
            Alpha AI deep report runs when Python analyzer is available locally.
          </p>
        ) : null}
      </section>

      <section className="space-y-3">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Seven questions
        </p>
        {summary.questions.map((question) => (
          <article
            key={question.id}
            className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 space-y-1"
          >
            <p className="text-sm font-medium text-apex-text/90">{question.prompt}</p>
            <p className="text-sm text-apex-muted/85">{question.answer}</p>
            <p className="text-xs text-apex-muted/55">
              Confidence · {question.confidence}
            </p>
          </article>
        ))}
      </section>

      {summary.gaps.length > 0 ? (
        <section className="rounded-xl border border-amber-500/15 bg-amber-500/5 px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-amber-100/80">
            Data gaps
          </p>
          <ul className="mt-2 space-y-1 text-xs text-amber-50/80">
            {summary.gaps.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
