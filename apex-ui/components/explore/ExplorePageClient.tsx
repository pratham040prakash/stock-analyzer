"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import ExploreResearchHandoff from "@/components/research/ExploreResearchHandoff";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { useExploreTriggers } from "@/lib/useExploreTriggers";
import type { StockPick } from "@/types/decision";

type DecisionResponse = {
  status: string;
  decision?: {
    picks?: StockPick[];
  };
};

type Props = {
  userName: string;
};

export default function ExplorePageClient({ userName }: Props) {
  const [picks, setPicks] = useState<StockPick[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPicks = useCallback(async () => {
    setLoading(true);

    try {
      const response = await apiFetch("/api/decision/today", { cache: "no-store" });
      const data = await parseApiJson<DecisionResponse>(response, "Today decision");

      if (response.ok && data?.decision?.picks) {
        setPicks(data.decision.picks);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPicks();
  }, [loadPicks]);

  const { triggers, loading: triggersLoading } = useExploreTriggers({
    enabled: picks.length > 0,
    picks,
  });

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>Explore</ApexTitle>
          <p className="text-sm text-apex-muted">
            Live setup triggers for {userName} — hand off to Research when ready.
          </p>
        </div>
      </header>

      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading explore picks…</p>
      ) : (
        <ExploreResearchHandoff triggers={triggers} loading={triggersLoading} />
      )}

      <Link href="/app" className="mt-6 inline-flex text-sm text-blue-200/90 hover:text-blue-100">
        Back to Today →
      </Link>
    </ApexShell>
  );
}
