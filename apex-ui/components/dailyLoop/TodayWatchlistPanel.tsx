"use client";

import { useState } from "react";
import type { ExploreSetup } from "@/lib/dailyLoop/capitalDecision";
import {
  formatExploreSetupBadge,
  formatExploreSetupSummary,
} from "@/lib/dailyLoop/exploreSetupPresentation";
import type { ExploreLiveTrigger } from "@/services/explore/liveTriggers";
import { formatInr } from "@/lib/funds";

type Props = {
  setups: ExploreSetup[];
  summary?: string;
  liveTriggers?: Map<string, ExploreLiveTrigger>;
  loading?: boolean;
  maxVisible?: number;
};

export default function TodayWatchlistPanel({
  setups,
  summary,
  liveTriggers,
  loading = false,
  maxVisible = 3,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? setups : setups.slice(0, maxVisible);
  const hiddenCount = Math.max(0, setups.length - maxVisible);

  if (setups.length === 0) {
    return (
      <section className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-4">
        <p className="text-sm font-medium text-apex-text">Nothing on your watchlist yet</p>
        <p className="mt-1 text-sm leading-snug text-apex-muted">
          APEX scans each morning. Check back tomorrow or open Research to add ideas.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-3">
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-apex-muted">
          Your watchlist
        </p>
        {summary ? (
          <p className="mt-1 text-sm font-medium text-apex-text/90">{summary}</p>
        ) : null}
        {loading ? (
          <p className="mt-1 text-xs text-apex-muted/70">Updating live prices…</p>
        ) : null}
      </div>

      <ul className="space-y-3">
        {visible.map((setup, index) => {
          const live = liveTriggers?.get(setup.symbol);
          const badge = live?.label ?? formatExploreSetupBadge(setup.stage);
          const headline = live?.liveScanLine ?? setup.scanLine;

          return (
            <li
              key={setup.symbol}
              className={[
                "rounded-xl border px-4 py-3",
                index === 0
                  ? "border-blue-400/25 bg-blue-500/[0.07]"
                  : "border-apex-border/20 bg-white/[0.02]",
              ].join(" ")}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-base font-semibold text-apex-text">{setup.symbol}</p>
                <span className="rounded-full border border-blue-300/25 bg-blue-500/10 px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wide text-blue-100/90">
                  {badge}
                </span>
              </div>
              <p className="mt-1 text-sm font-medium leading-snug text-apex-text/90">
                {headline}
              </p>
              {live ? (
                <p className="mt-1 text-xs text-apex-muted/75">
                  Live {formatInr(live.livePrice)}
                  {live.gapPct !== undefined && live.activationLevel
                    ? ` · ${live.gapPct}% to ${formatInr(live.activationLevel)}`
                    : null}
                </p>
              ) : null}
              <p className="mt-2 text-sm leading-snug text-apex-text/75">
                {formatExploreSetupSummary(setup)}
              </p>
            </li>
          );
        })}
      </ul>

      {!expanded && hiddenCount > 0 ? (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="text-sm font-medium text-blue-200/90 transition-colors hover:text-blue-100"
        >
          Show {hiddenCount} more on watchlist
        </button>
      ) : null}
    </section>
  );
}
