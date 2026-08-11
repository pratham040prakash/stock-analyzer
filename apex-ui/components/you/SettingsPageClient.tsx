"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import PremiumFeatureGate from "@/components/dailyLoop/PremiumFeatureGate";
import PremiumValueCard from "@/components/subscription/PremiumValueCard";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { usePremiumTier } from "@/lib/usePremiumTier";
import type { InvestmentThesisRow } from "@/types/investmentThesis";

type ThesisResponse = {
  status: string;
  theses: InvestmentThesisRow[];
};

type DigestResponse = {
  status: string;
  delivery?: { sent: boolean; detail: string };
};

const DIGEST_PREF_KEY = "apex.digest.channel";

export default function SettingsPageClient({ userName }: { userName: string }) {
  const { tier, features, activationEnabled, refresh: refreshTier } = usePremiumTier(true);
  const [theses, setTheses] = useState<InvestmentThesisRow[]>([]);
  const [digestChannel, setDigestChannel] = useState<"telegram" | "email">("telegram");
  const [digestMessage, setDigestMessage] = useState<string | null>(null);
  const [digestSending, setDigestSending] = useState(false);

  const loadTheses = useCallback(async () => {
    const response = await apiFetch("/api/thesis", { cache: "no-store" });
    const data = await parseApiJson<ThesisResponse>(response, "Thesis");

    if (response.ok && data?.theses) {
      setTheses(data.theses);
    }
  }, []);

  useEffect(() => {
    void loadTheses();

    const saved = window.localStorage.getItem(DIGEST_PREF_KEY);

    if (saved === "email" || saved === "telegram") {
      setDigestChannel(saved);
    }
  }, [loadTheses]);

  const saveDigestPref = (channel: "telegram" | "email") => {
    setDigestChannel(channel);
    window.localStorage.setItem(DIGEST_PREF_KEY, channel);
  };

  const exportInvestmentBook = () => {
    if (!features.thesisExport) {
      return;
    }

    window.open("/api/thesis/export", "_blank", "noopener,noreferrer");
  };

  const sendDigestPreview = async () => {
    if (!features.reviewDigest) {
      return;
    }

    setDigestSending(true);
    setDigestMessage(null);

    try {
      const response = await apiFetch("/api/review/digest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: digestChannel }),
      });
      const data = await parseApiJson<DigestResponse>(response, "Review digest");

      if (response.ok) {
        setDigestMessage(data?.delivery?.detail ?? "Digest request sent.");
      } else if (response.status === 403) {
        setDigestMessage("Weekly digest delivery requires APEX Premium.");
      } else {
        setDigestMessage("Could not send digest.");
      }
    } finally {
      setDigestSending(false);
    }
  };

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>Settings</ApexTitle>
          <p className="text-sm text-apex-muted">
            Broker, tier, exports, and notifications for {userName}.
          </p>
        </div>
      </header>

      <div className="space-y-4">
        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Broker
          </p>
          <p className="text-sm text-apex-text/85">
            Reconnect Zerodha when sessions expire or portfolio looks stale.
          </p>
          <a
            href="/api/zerodha/login"
            className="inline-flex rounded-lg border border-blue-500/25 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100"
          >
            Connect / refresh Zerodha
          </a>
        </section>

        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Subscription
          </p>
          <p className="text-sm text-apex-text/85">
            Current tier · <span className="capitalize">{tier}</span>
          </p>
          <p className="text-xs text-apex-muted/75">
            Margin mode {features.marginMode ? "enabled" : "locked"} · Decision history{" "}
            {features.decisionHistory ? "enabled" : "preview"} · Digest{" "}
            {features.reviewDigest ? "enabled" : "locked"} · Export{" "}
            {features.thesisExport ? "enabled" : "locked"}
          </p>
          {activationEnabled && tier === "free" ? (
            <Link href="/app/you" className="text-sm text-blue-200/90 hover:text-blue-100">
              Activate premium on You →
            </Link>
          ) : null}
        </section>

        {tier === "free" ? (
          <PremiumValueCard tier={tier} activationEnabled={activationEnabled} compact />
        ) : null}

        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3" aria-labelledby="settings-exports">
          <p id="settings-exports" className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Exports
          </p>
          {features.thesisExport ? (
            <>
              <p className="text-sm text-apex-text/85">
                Receipt and monthly doctor markdown exports live on Review. Download your full
                investment book here.
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={exportInvestmentBook}
                  className="rounded-lg border border-blue-500/25 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100"
                >
                  Download investment book
                </button>
                <Link
                  href="/app/review?tab=receipts"
                  className="rounded-lg border border-apex-border/25 px-4 py-2 text-sm text-apex-muted"
                >
                  Open receipts
                </Link>
              </div>
            </>
          ) : (
            <PremiumFeatureGate
              feature="thesisExport"
              compact
              activationEnabled={activationEnabled}
              onActivated={() => void refreshTier()}
            />
          )}
        </section>

        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Investment theses
          </p>
          {theses.length === 0 ? (
            <p className="text-sm text-apex-muted/85">
              No theses saved yet. Add them from Research.
            </p>
          ) : (
            <ul className="space-y-2 text-sm text-apex-text/85">
              {theses.slice(0, 8).map((row) => (
                <li key={row.id}>
                  <Link
                    href={`/app/research?symbol=${encodeURIComponent(row.symbol)}`}
                    className="text-blue-200/90 hover:text-blue-100"
                  >
                    {row.symbol}
                  </Link>
                  <span className="text-apex-muted/70">
                    {" "}
                    · {row.thesis.slice(0, 72)}
                    {row.thesis.length > 72 ? "…" : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Review digest
          </p>
          {features.reviewDigest ? (
            <>
              <p className="text-sm text-apex-text/85">
                Requires <code className="text-xs">APEX_REVIEW_DIGEST_ENABLED=true</code> and
                Telegram or webhook env on the server.
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => saveDigestPref("telegram")}
                  className={
                    digestChannel === "telegram"
                      ? "rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-xs text-blue-100"
                      : "rounded-lg border border-apex-border/20 px-3 py-1.5 text-xs text-apex-muted"
                  }
                >
                  Telegram
                </button>
                <button
                  type="button"
                  onClick={() => saveDigestPref("email")}
                  className={
                    digestChannel === "email"
                      ? "rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-xs text-blue-100"
                      : "rounded-lg border border-apex-border/20 px-3 py-1.5 text-xs text-apex-muted"
                  }
                >
                  Email (webhook)
                </button>
              </div>
              <button
                type="button"
                disabled={digestSending}
                onClick={() => void sendDigestPreview()}
                className="rounded-lg border border-apex-border/25 px-4 py-2 text-sm text-apex-text/90 disabled:opacity-50"
              >
                {digestSending ? "Sending…" : "Send test digest"}
              </button>
              {digestMessage ? (
                <p className="text-xs text-apex-muted/75">{digestMessage}</p>
              ) : null}
            </>
          ) : (
            <PremiumFeatureGate
              feature="reviewDigest"
              compact
              activationEnabled={activationEnabled}
              onActivated={() => void refreshTier()}
            />
          )}
        </section>

        <Link href="/app/you" className="text-sm text-apex-muted/80 hover:text-apex-text">
          ← Back to You
        </Link>
      </div>
    </ApexShell>
  );
}
