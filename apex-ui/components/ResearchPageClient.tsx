"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import ExploreResearchHandoff from "@/components/research/ExploreResearchHandoff";
import InvestmentThesisPanel from "@/components/research/InvestmentThesisPanel";
import ResearchWorkbench from "@/components/research/ResearchWorkbench";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { useExploreTriggers } from "@/lib/useExploreTriggers";
import type { StockPick } from "@/types/decision";
import type { ResearchSummaryViewModel } from "@/types/researchSummary";

type Props = {
  initialSymbol: string | null;
};

type SummaryResponse = {
  status: string;
  summary: ResearchSummaryViewModel;
};

type TodayDecisionResponse = {
  decision?: { picks?: StockPick[] };
};

export default function ResearchPageClient({ initialSymbol }: Props) {
  const [symbol, setSymbol] = useState(initialSymbol ?? "RELIANCE");
  const [query, setQuery] = useState(symbol);
  const [summary, setSummary] = useState<ResearchSummaryViewModel | null>(null);
  const [hasSearched, setHasSearched] = useState(Boolean(initialSymbol));
  const [loading, setLoading] = useState(Boolean(initialSymbol));
  const [error, setError] = useState<string | null>(null);
  const [explorePicks, setExplorePicks] = useState<StockPick[]>([]);

  const { triggers: exploreTriggers, loading: exploreLoading } = useExploreTriggers({
    enabled: explorePicks.length > 0,
    picks: explorePicks,
  });

  const loadExplorePicks = useCallback(async () => {
    const response = await apiFetch("/api/decision/today", { cache: "no-store" });
    const data = await parseApiJson<TodayDecisionResponse>(response, "Today decision");

    if (response.ok && data?.decision?.picks) {
      setExplorePicks(data.decision.picks);
    }
  }, []);

  const loadSummary = useCallback(async (nextSymbol: string) => {
    const normalized = nextSymbol.trim().toUpperCase();

    if (!normalized) {
      setSummary(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch(
        `/api/research/summary?symbol=${encodeURIComponent(normalized)}`,
        { cache: "no-store" },
      );
      const data = await parseApiJson<SummaryResponse>(response, "Research summary");

      if (response.ok && data?.summary) {
        setSummary(data.summary);
        setSymbol(normalized);
        setHasSearched(true);
      } else {
        setError("Could not build research summary for this symbol.");
      }
    } catch (loadError) {
      setError(
        loadError instanceof Error ? loadError.message : "Research request failed.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialSymbol) {
      void loadSummary(initialSymbol);
    }
    void loadExplorePicks();
  }, [initialSymbol, loadExplorePicks, loadSummary]);

  const helper = useMemo(() => {
    if (!symbol) {
      return "Enter a symbol to run the seven-question research workflow.";
    }

    return `Research workspace for ${symbol} — answer before acting on Today.`;
  }, [symbol]);

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>Research</ApexTitle>
          <p className="text-sm text-apex-muted">{helper}</p>
          <Link href="/app/explore" className="text-sm text-blue-200/90 hover:text-blue-100">
            Open Explore triggers →
          </Link>
        </div>
      </header>

      <section className="mb-4 rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
        <label className="block text-xs font-medium uppercase tracking-wide text-apex-muted">
          Symbol
        </label>
        <div className="flex flex-wrap gap-2">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value.trim().toUpperCase())}
            className="min-w-[12rem] flex-1 rounded-lg border border-apex-border/20 bg-transparent px-3 py-2 text-sm text-apex-text outline-none focus:border-blue-400/40"
            placeholder="e.g. RELIANCE"
          />
          <button
            type="button"
            onClick={() => void loadSummary(query)}
            disabled={loading || !query.trim()}
            className="rounded-lg border border-blue-500/25 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100 disabled:opacity-50"
          >
            Research
          </button>
        </div>
      </section>

      <ExploreResearchHandoff triggers={exploreTriggers} loading={exploreLoading} />

      {hasSearched && summary ? (
        <>
          <ResearchWorkbench summary={summary} loading={loading} error={error} />
          <InvestmentThesisPanel symbol={symbol} />
        </>
      ) : (
        <p className="text-sm text-apex-muted/70">
          Run research on a symbol to see the seven-question decision workflow.
        </p>
      )}
    </ApexShell>
  );
}
