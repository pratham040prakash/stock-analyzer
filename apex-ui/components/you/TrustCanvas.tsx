"use client";

import Link from "next/link";
import type { YouSnapshotViewModel } from "@/types/youSnapshot";

type Props = {
  snapshot: YouSnapshotViewModel;
  brokerConnected?: boolean;
};

export default function TrustCanvas({ snapshot, brokerConnected = false }: Props) {
  const cdqsDisplay =
    snapshot.cdqs_score_percent !== null
      ? `${snapshot.cdqs_score_percent}%`
      : "—";

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-4 space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-blue-100/80">
          Calibrated Decision Quality (CDQS)
        </p>
        <p className="text-5xl font-semibold text-apex-text">{cdqsDisplay}</p>
        <p className="text-lg text-apex-text/90">{snapshot.cdqs_headline}</p>
        <p className="text-sm text-apex-muted/85">{snapshot.cdqs_detail}</p>
        <p className="text-xs text-apex-muted/70">
          North star from APEX constitution — broker-verified outcomes vs stated confidence,
          not marketing hit rate.
        </p>
      </section>

      {snapshot.outcome_loop_visible ? (
        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Last broker-verified close
          </p>
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <p className="text-2xl font-semibold text-apex-text">
              {snapshot.outcome_loop_stock ?? "Position"}
            </p>
            {snapshot.outcome_loop_result ? (
              <span className="rounded-full border border-apex-border/25 px-2 py-0.5 text-xs text-apex-text/85">
                {snapshot.outcome_loop_result}
              </span>
            ) : null}
          </div>
          {snapshot.outcome_loop_summary ? (
            <p className="text-sm text-apex-text/85">{snapshot.outcome_loop_summary}</p>
          ) : null}
          <div className="grid gap-2 text-xs text-apex-muted/80 sm:grid-cols-3">
            {snapshot.outcome_loop_discipline !== null ? (
              <p>Discipline {snapshot.outcome_loop_discipline}/100</p>
            ) : null}
            {snapshot.outcome_loop_execution !== null ? (
              <p>Execution {snapshot.outcome_loop_execution}/100</p>
            ) : null}
            {snapshot.outcome_loop_trust_delta !== null ? (
              <p>
                Trust {snapshot.outcome_loop_trust_delta >= 0 ? "+" : ""}
                {snapshot.outcome_loop_trust_delta}
              </p>
            ) : null}
          </div>
          <p className="text-xs text-apex-muted/70">
            Compared to broker truth via outcomeEngine — not coach hope.
          </p>
        </section>
      ) : null}

      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Override discipline (14 days)
        </p>
        <p className="text-lg font-medium text-apex-text">{snapshot.override_headline}</p>
        <p className="text-sm text-apex-muted/85">{snapshot.override_detail}</p>
        {snapshot.override_count_14d > 0 ? (
          <p className="text-xs text-amber-100/85">
            Traded when Wait was shown: {snapshot.override_count_14d} day
            {snapshot.override_count_14d === 1 ? "" : "s"} — this metric should trend down.
          </p>
        ) : null}
      </section>

      <section className="space-y-3">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          I&apos;ve been reviewing every decision.
        </p>
        <p className="text-5xl font-semibold text-apex-text">{snapshot.trust_state}</p>
        <p className="text-lg text-apex-text/90">{snapshot.trust_narrative}</p>
      </section>

      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
        <div>
          <p className="text-xs text-apex-muted/70">Last week</p>
          <p className="text-sm text-apex-text/85">{snapshot.last_week_summary}</p>
        </div>
        <div>
          <p className="text-xs text-apex-muted/70">This week</p>
          <p className="text-sm text-apex-text/85">{snapshot.this_week_summary}</p>
        </div>
        {snapshot.visible_miss ? (
          <details className="text-sm text-amber-100/85">
            <summary className="cursor-pointer text-xs text-apex-muted/70 hover:text-apex-muted">
              What we got wrong
            </summary>
            <p className="mt-2">{snapshot.visible_miss}</p>
            <p className="mt-2 text-xs text-apex-muted/70">
              I acknowledge misses plainly — then tighten how risk is framed next time.
            </p>
          </details>
        ) : null}
      </section>

      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
        <p className="text-sm text-apex-text/85">
          I&apos;ll continue checking every recommendation against reality. That&apos;s
          how I improve.
        </p>
        <details className="text-xs text-apex-muted/75">
          <summary className="cursor-pointer hover:text-apex-muted">How I learn</summary>
          <p className="mt-2">
            Every ACT and WAIT receipt is compared to broker truth. Trust grows from honest
            memory — not marketing hit rates.
          </p>
        </details>
        <p className="text-xs text-apex-muted/70">
          Trust score {snapshot.trust_score}/100 — relationship, not hit rate.
        </p>
      </section>

      <div className="flex flex-wrap gap-3">
        <Link
          href="/app/you"
          className="inline-flex rounded-xl border border-apex-border/25 px-4 py-3 text-sm font-medium text-apex-text transition-colors hover:bg-white/[0.03]"
        >
          Back to You
        </Link>
        {!brokerConnected ? (
          <a
            href="/api/zerodha/login"
            className="inline-flex rounded-xl border border-blue-500/25 bg-blue-500/10 px-4 py-3 text-sm font-medium text-blue-100"
          >
            Connect Zerodha
          </a>
        ) : null}
      </div>
    </div>
  );
}
