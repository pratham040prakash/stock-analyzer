"use client";

import { useCallback, useEffect, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import ReflectionCanvas from "@/components/you/ReflectionCanvas";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { YouSnapshotViewModel } from "@/types/youSnapshot";

type SnapshotResponse = {
  status: string;
  snapshot: YouSnapshotViewModel;
};

export default function YouPageClient({ userName }: { userName: string }) {
  const [snapshot, setSnapshot] = useState<YouSnapshotViewModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch("/api/you/snapshot", { cache: "no-store" });
      const data = await parseApiJson<SnapshotResponse>(response, "You snapshot");

      if (response.ok && data?.snapshot) {
        setSnapshot(data.snapshot);
      } else {
        setError("Could not load your trader snapshot.");
      }
    } catch (loadError) {
      setError(
        loadError instanceof Error ? loadError.message : "Could not load snapshot.",
      );
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
        <div className="space-y-2">
          <ApexTitle>You</ApexTitle>
          <p className="text-sm text-apex-muted">
            How {userName} is becoming a better investor — not a brokerage dashboard.
          </p>
        </div>
      </header>

      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading reflection…</p>
      ) : error ? (
        <p className="text-sm text-amber-200/85">{error}</p>
      ) : snapshot ? (
        <ReflectionCanvas snapshot={snapshot} />
      ) : null}
    </ApexShell>
  );
}
