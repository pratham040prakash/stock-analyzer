"use client";

import { useMemo, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import { ApexShell, ApexTitle } from "@/components/ui/apex";

type Props = {
  initialSymbol: string | null;
};

export default function ResearchPageClient({ initialSymbol }: Props) {
  const [symbol, setSymbol] = useState(initialSymbol ?? "RELIANCE");

  const prompt = useMemo(() => {
    if (!symbol) {
      return "Enter a symbol to start research.";
    }

    return `Research workspace for ${symbol} — decision memory and Alpha AI reports will attach here.`;
  }, [symbol]);

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>Research</ApexTitle>
          <p className="text-sm text-apex-muted">{prompt}</p>
        </div>
      </header>

      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
        <label className="block text-xs font-medium uppercase tracking-wide text-apex-muted">
          Symbol
        </label>
        <input
          value={symbol}
          onChange={(event) => setSymbol(event.target.value.trim().toUpperCase())}
          className="w-full rounded-lg border border-apex-border/20 bg-transparent px-3 py-2 text-sm text-apex-text outline-none focus:border-blue-400/40"
          placeholder="e.g. RELIANCE"
        />
        <p className="text-sm text-apex-text/85">
          Use Portfolio to spot concentration, then research the symbol here before acting on
          Today&apos;s verdict.
        </p>
      </section>
    </ApexShell>
  );
}
