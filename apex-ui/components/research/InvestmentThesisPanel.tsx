"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { InvestmentThesisRow } from "@/types/investmentThesis";

type Props = {
  symbol: string;
};

type ThesisResponse = {
  status: string;
  theses: InvestmentThesisRow[];
};

export default function InvestmentThesisPanel({ symbol }: Props) {
  const [thesis, setThesis] = useState("");
  const [invalidation, setInvalidation] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadThesis = useCallback(async () => {
    const response = await apiFetch("/api/thesis", { cache: "no-store" });
    const data = await parseApiJson<ThesisResponse>(response, "Thesis");

    if (response.ok && data?.theses) {
      const row = data.theses.find((item) => item.symbol === symbol);
      setThesis(row?.thesis ?? "");
      setInvalidation(row?.invalidation ?? "");
    }
  }, [symbol]);

  useEffect(() => {
    void loadThesis();
  }, [loadThesis]);

  const save = async () => {
    setSaving(true);
    setMessage(null);

    try {
      const response = await apiFetch("/api/thesis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, thesis, invalidation }),
      });

      if (response.ok) {
        setMessage("Thesis saved.");
      } else {
        setMessage("Could not save thesis.");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Investment thesis · {symbol}
      </p>
      <textarea
        value={thesis}
        onChange={(event) => setThesis(event.target.value)}
        rows={3}
        placeholder="Why do you own this? What would change your mind?"
        className="w-full rounded-lg border border-apex-border/20 bg-transparent px-3 py-2 text-sm text-apex-text outline-none focus:border-blue-400/40"
      />
      <input
        value={invalidation}
        onChange={(event) => setInvalidation(event.target.value)}
        placeholder="Invalidation rule (optional)"
        className="w-full rounded-lg border border-apex-border/20 bg-transparent px-3 py-2 text-sm text-apex-text outline-none focus:border-blue-400/40"
      />
      <div className="flex items-center gap-3">
        <button
          type="button"
          disabled={saving || !thesis.trim()}
          onClick={() => void save()}
          className="rounded-lg border border-blue-500/25 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100 disabled:opacity-50"
        >
          Save thesis
        </button>
        {message ? <span className="text-xs text-apex-muted/75">{message}</span> : null}
      </div>
    </section>
  );
}
