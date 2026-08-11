"use client";

import { useCallback, useEffect, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import TrustCanvas from "@/components/you/TrustCanvas";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { YouSnapshotViewModel } from "@/types/youSnapshot";

type SnapshotResponse = {
  status: string;
  snapshot: YouSnapshotViewModel;
};

export default function TrustPageClient() {
  const [snapshot, setSnapshot] = useState<YouSnapshotViewModel | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);

    try {
      const response = await apiFetch("/api/you/snapshot", { cache: "no-store" });
      const data = await parseApiJson<SnapshotResponse>(response, "Trust snapshot");

      if (response.ok && data?.snapshot) {
        setSnapshot(data.snapshot);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <ApexTitle>Trust</ApexTitle>
      </header>

      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading trust canvas…</p>
      ) : snapshot ? (
        <TrustCanvas snapshot={snapshot} />
      ) : (
        <p className="text-sm text-apex-muted/70">Trust snapshot unavailable.</p>
      )}
    </ApexShell>
  );
}
