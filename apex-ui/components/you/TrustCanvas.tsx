"use client";

import Link from "next/link";
import type { YouSnapshotViewModel } from "@/types/youSnapshot";

type Props = {
  snapshot: YouSnapshotViewModel;
  brokerConnected?: boolean;
};

export default function TrustCanvas({ snapshot, brokerConnected = false }: Props) {
  return (
    <div className="space-y-6">
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
